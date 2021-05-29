#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import socket
import os

host = ""
port = 4210
bufsize = 256

stateX = -10.0
stateY = -10.0
targetX = 10.0
targetY = stateY
gpsX = stateX + 1
gpsY = stateY + 1

addr = (host, port)
UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock.bind(addr)
UDPSock.setblocking(0)

print("waiting for messages (port: " + str(port) + ") ...")

if os.environ['COMPUTERNAME']=="HBA004":
   clientAddr = ('192.168.178.71', 4211)
else:
   clientAddr = ('192.168.20.100', 4211)

# Receive message if available
def receive():
   global stateX, stateY
   global targetX, targetY
   global gpsX, gpsY
   global clientAddr
   msg = ""
   try: 
      (data, clientAddr) = UDPSock.recvfrom(bufsize)
   except socket.error:
      pass
   else:   
      #print (data.decode('utf-8'), end='', flush=True)      
      msg = data.decode(encoding='UTF-8',errors='ignore')
      #print (msg, end='', flush=True)
      #print(clientAddr)
      if msg[0] == '0':
         msg = ':' + msg
      if msg[0] == ':':
         fields = msg.split()
         n=6
         targetX = float(fields[n+0])
         targetY = float(fields[n+1])
         stateX = float(fields[n+2])
         stateY = float(fields[n+3])
         gpsX = float(fields[n+5])
         gpsY = float(fields[n+6])
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
   print("[udp.send] SENT:", send_data)

def close():
  UDPSock.close()
  print ("[udp] terminating ...")

def main():
    #send("AT+$L")
    send("AT+$C,LOG1059.TXT")
    try:
        while True:
            receive();
    except KeyboardInterrupt:
        close()

if __name__ == '__main__':
    main()
