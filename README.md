# File-Sharing-Protocol

Options:   connect 
           exit
           send <commands>

# Commands
===========
=IndexGet flag
Display ‘name’, ‘size’, ‘timestamp’ of the shared files on the connected system.

flag = [shortlist start_time_stamp end_time_stamp,longlist,regex]

-short list: print the details of the files between a specific set of timestamps.
Details include 

-long list:Print the entire listing of the shared folder/directory including   

= FileHash ​<flag>
flag = [verify <filename>,checkall]

-verify: Should check for the specific   file   name   provided   as   
command line argument and return its 'checksum' and 'last modified' timestamp.

-checkall: flag should perform what 'verify' does for all the files in the shared folder and print the filename as well. 

=File Download <filename>

- Used to download files from the shared folder of connected user to our shared folder.If a socket is not avialable, it should be created and both clients must use this socket for file transfer.Should print the filename,filesize,last modified timestamp and MD5 hash of the requested file as well.  
