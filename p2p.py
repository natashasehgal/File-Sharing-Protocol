import socket
import threading
import sys
import os
import SocketServer
import hashlib
import re
import time
import datetime
import shelve

debug = False
date_time_str = '%Y-%m-%d %H:%M:%S'
time_stamp = lambda f: time.strftime(date_time_str,time.localtime(os.stat(os.path.abspath(f)).st_mtime))
rev_time_stamp = lambda date1 :  time.mktime(datetime.datetime.strptime(date1, date_time_str).timetuple())
file_size =  lambda f: str(os.stat(os.path.abspath(f)).st_size)
header_name = "Name : "
header_size = "Size : "
header_time = "Time : "
header_md5 = "MD5 : "
response_start = "====response====="
response_end = "====end===="
file_start = "====file===="
data_start = "====data===="

d = shelve.open("checksums")

def md5(fname):
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()

def verify(fname):
    try:
        f = open(fname, "rb")
        return fname+" : "+md5(fname) + " : " + time_stamp(fname)

    except IOError:
        return fname + " File not found"

def filelist_parse(files):
    resp = "file : time_stamp : file_size\n"
    for f in files:
        resp += f[0]+" : " + f[1] + " : " + f[2] + "\n"
    return resp

def req_handler(req):
    req = req.split(";")

    res = ""
    if req[0] == "connection":
        return ["response", "connection confirmed"]

    if req[0] == "disconnect":
        return ["response", "disconnected succesfully"]

    #IndexGet
    if req[0] == "IndexGet":
        files = []
        new_files = []
        for f in os.listdir("shared/"):
            F = "shared/" + f
            files.append([f, time_stamp(F), file_size(F)])
        if req[1] == "longlist":
            new_files = files

        if req[1] == "regex":
            for f in files:
                if re.search(f[0], req[2]) !=  None:
                    new_files.append(f)
       
        if req[1] == "shortlist":
            date1 = req[2] + " " + req[3]
            date2 = req[4] + " " + req[5]

            try:
                date1 = rev_time_stamp(date1)
                date2 = rev_time_stamp(date2)
            except:
                return ["response", "Invalid Dates"] 

            for f in files:
                t = rev_time_stamp(f[1])
                if (t >= date1 and  t <= date2):
                    new_files.append(f)

        return ["response", filelist_parse(new_files)]

    #FileHash
    if req[0] == "FileHash":
        if req[1] == "verify":
            return ["response", verify("shared/"+req[2])]
        elif req[1] == "checkall":
            res = ""
            for f in os.listdir("shared/"):
                res += "\n" + verify(os.path.abspath("shared/"+f)) 
            return ["response", res]
        else:
            return ["response", "incorrect option"]
                 
    #FileDownload 
    if req[0] == "FileDownload":
        try:
            f = open("shared/"+req[1], "r")
        except:
            return ["response", "File Not Present"]

        resp = header_name + req[1] + "\n" + header_size + file_size("shared/"+req[1]) + "\n" + header_time + time_stamp("shared/"+req[1]) + "\n" +  header_md5 + md5("shared/"+req[1]) + "\n"  

        return ["file", resp, f.read()]
    return ["response", " ".join(req)]


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        response = "{} wrote: {}".format(self.client_address[0], data)

        try:
            resp = req_handler(data)
        except IndexError:
            resp = ["response", "missing commands"]

        if resp[0] == "response":
            self.request.send(response_start)
            if resp[1]:
                self.request.send(resp[1])
            self.request.send(response_end)

        if resp[0] == "file":
            self.request.send(file_start)
            if resp[1]:
                self.request.send(resp[1])
            self.request.send(data_start)
            if resp[2]:
                self.request.send(resp[2])
            self.request.send(response_end)



class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def file_parser(resp):
    if resp == "":
        print "Empty"
        return None, None, None, None, None

    size = resp.find(header_size)
    time = resp.find(header_time)
    Md5 = resp.find(header_md5)
    data = resp.find(data_start)
    
    name_str = resp[:size]
    size_str = resp[size:time]
    time_str = resp[time:Md5]
    md5_str = resp[Md5:data]
    data_str = resp[data:]

    name =  name_str[len(header_name):].rstrip("\n")
    size =  size_str[len(header_size):].rstrip("\n")
    time = time_str[len(header_time):].rstrip("\n")
    Md5 =  md5_str[len(header_md5):].rstrip("\n")
    data = data_str[len(data_start):]

    f = open("download/"+name, "w+")
    f.write(data)
    f.close()

    new_md5 = md5("download/"+name)

    if new_md5 == Md5:
        print os.path.abspath("download/"+name)
        d[os.path.abspath(name)] = new_md5
        print "File Dowloaded Successfully"
    else:
        print "MD5 checksum is not same", new_md5, Md5
    return name, size, time, Md5, data

def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024)
        resp = ""
        while(response):
            resp += response
            response = sock.recv(1024)
            
        if (resp.startswith(response_start)):
            resp = resp[len(response_start):]

            if (resp.endswith(response_end)):
                resp = resp[:-len(response_end)]
            else :
                print "Bad response (not completed)"
                resp = ""
        

        if (resp.startswith(file_start)):
            resp = resp[len(file_start):]

            if (resp.endswith(response_end)):
                resp = resp[:-len(response_end)]
            else:
                print "Bad Response (not completed)"
                resp = ""

            print "resp", resp
            file_name, file_size, file_time, file_md5, file_data = file_parser(resp)  
            resp = resp[:resp.find(data_start)]
            

        print "Received: \n{}".format(resp)
    finally:
        sock.close()

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 0

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print "Server running at ", server.server_address
    ip ,port = server.server_address


    while True:
        command = raw_input("$: ")

        command_split = command.split(" ")
        command_split[0] = command_split[0].upper()

        #connect
        if command_split[0] == "CONNECT":
            try:
                ip = raw_input("SERVER IP ADDRESS: ")
                port = int(raw_input("SERVER PORT: "))
            except:
                print "Invalid ip, trying local server"
                ip, port = server.server_address

          

        # exit
        if command_split[0] == "EXIT":
            server.shutdown()
            server.server_close()
            sys.exit(0)

        # send request
        if command_split[0] == "SEND":
            client(ip, port, ";".join(command_split[1:]))

