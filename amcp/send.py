#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import socket
from time import sleep


host = ""
port = 4210

bufsize = 256

addr = (host, port)
UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock.bind(addr)
#UDPSock.setblocking(0)

print("waiting for messages (port: " + str(port) + ") ...")

# send (PC=192.168.178.50)
#try:
#  while True:
#    address = ('192.168.178.71', 4211)
#    send_data = "HELLO!\n"
#    UDPSock.sendto(send_data.encode('utf-8'), address)
#    UDPSock.setblocking(0)
#    sleep(0.5)
#except KeyboardInterrupt:
#  UDPSock.close()
#  print ("terminating ...")
#  exit(0)

# Endlosschleife fuer Empfang, Abbruch durch Strg-C
try:
  while True:
    try: 
      (data, addr) = UDPSock.recvfrom(bufsize)
    except socket.error:
      pass
    else:   
      #print (data.decode('utf-8'), end='', flush=True)      
      print (data.decode(encoding='UTF-8',errors='ignore'), end='', flush=True)      
      #send_data = "AT+V,0x16"  
      send_data = "HELLO!"
      UDPSock.sendto(send_data.encode('utf-8'), addr)
except KeyboardInterrupt:
  UDPSock.close()
  print ("terminating ...")
  exit(0)
  
