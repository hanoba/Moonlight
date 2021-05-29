#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import sys
import socket
import os

host = ""
port = 4210
bufsize = 256


addr = (host, port)
UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock.bind(addr)
UDPSock.setblocking(0)

#print("waiting for messages (port: " + str(port) + ") ...")

#clientAddr = ""   
#clientAddr = ('192.168.178.71', 4211)
#clientAddr = ('192.168.20.100', 4211)
#ping ESP-17C64F garten
if os.environ['COMPUTERNAME']=="HBA004":
   clientAddr = ('192.168.178.71', 4211)
else:
   clientAddr = ('192.168.20.100', 4211)



# Receive message if available
def receive():
   global clientAddr
   msg = ""
   try: 
      (data, clientAddr) = UDPSock.recvfrom(bufsize)
   except socket.error:
      pass
   else:   
      msg = data.decode('utf-8', errors="ignore")
      #msg = data
   return msg

def CheckSum(send_data):
   checkSum = 0
   for i in range(len(send_data)):
      checkSum += ord(send_data[i])
   checkSum = checkSum & 255
   return checkSum

def send(send_data):
   #print(clientAddr)
   send_data = send_data + str.format(',0x{:02X}', CheckSum(send_data))
   UDPSock.sendto(send_data.encode('utf-8'), clientAddr)
   #print("SENT:", send_data)

def main():
    argc = len(sys.argv)
    if argc > 1: cmd = sys.argv[1]
    if argc == 3 and cmd == "cat":
        send("AT+$C,"+sys.argv[2])
    elif argc == 3 and cmd == "cp":
        send("AT+$C,"+sys.argv[2])
        file = open(sys.argv[2],"wb")
    elif argc == 2 and cmd == "ls":
        send("AT+$L")
    elif argc == 3 and sys.argv[1] == "ls":
        send("AT+$L,"+sys.argv[2])
    elif argc == 2 and cmd == "dir":
        send("AT+$L")
        file = open("dir.txt","wb")
    elif argc == 3 and cmd == "dir":
        send("AT+$L,"+sys.argv[2])
        file = open("dir.txt","wb")
    elif argc == 2 and cmd == "log":
        print("Stop logging with Ctrl-C")
    elif argc == 3 and sys.argv[1] == "rm":
        send("AT+$R,"+sys.argv[2])
    else:
        print("Ardumower SD Card File System Access")
        print("")
        print("Usage: amfs ls [<file_pattern>]      # list files to stdout")
        print("       amfs dir [<file_pattern>]     # list files to dir.txt")
        print("       amfs rm [<file_pattern>]      # remove files")
        print("       amfs cat <file_name>          # output file to stdout")
        print("       amfs cp <file_name>           # copy file to current directory")
        print("       amfs log                      # display logging output(stop with Ctrl-C)")
        print("<file_pattern> can include the wild card * at the end")
        return
    try:
        if cmd != "log":
            while True:
                msg = receive();
                if msg.find("$$$SOF$$$") >= 0: break;
        numLines = 0
        while True:
            msg = receive();
            if msg != "":
               #mm = msg.decode('ascii', errors="ignore")
               if msg.find("$$$EOF$$$") >= 0: break;
               numLines += 1
               #n = len(msg)
               #msg2=""
               #for ch in msg:
               #    n = ord(ch)
               #    if n == 10 and n == 13: break;
               #    msg2 = msg2 + chr(n)
               #i=1
               #for ch in msg:
               #    n = ord(ch)
               #    print(str.format('{:02X} ', n), end='')
               #    if i==50:
               #        print("")
               #        i=1
               #    else:
               #        i = i+1
               #print("")
               #msg2 = msg2 + "\r\n"
               #print(msg2, end='\r\n')
               # b = bytes(msg, 'utf-8')
               #b.append(10)
               #sys.stdout.buffer.write(b'\x0A')
               #if n>=3 and msg[n-3] == "\r": msg = msg[0:n-3]
               #if n>=3: msg = msg[0:n-3]
               #msg.replace("\r\n","\n")
               #print (msg, end='', flush=True)
               #msg = msg.replace("\r","")
               #msg = msg.replace("\n","")
               #msg = msg + "\n"
               #print (msg, end='\n', flush=True)
               #if cmd=="log": print(msg, end='', flush=True)
               if cmd=="cp":
                  if (numLines & 31) == 0: print(numLines, end='\r', flush=True)
                  file.write(bytes(msg, 'cp850'))
               elif cmd=="dir": 
                  file.write(bytes(msg, 'cp850'))
               else: 
                  print(msg, end='', flush=True)
               #elif cmd=="cat": 
               #    #print(msg, end='', flush=True)
               #    print(msg, end='')
               #else: sys.stdout.buffer.write(bytes(msg, 'utf-8'))
               #print(msg2, flush=True)
               # print(msg, end='', flush=True)
               #print("\n", end='', flush=True)
    except KeyboardInterrupt:
        print ("terminating ...")
    UDPSock.close()
    print(numLines)
    if cmd=="cp" or cmd=="dir": file.close()


if __name__ == '__main__':
    main()
