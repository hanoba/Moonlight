#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import socket
from time import sleep
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

#if os.environ['COMPUTERNAME']=="HBA004":
#   clientAddr = ('192.168.178.71', 4211)
#else:
#   clientAddr = ('192.168.20.100', 4211)

hostName = socket.gethostname()
if hostName=="HBA004" or hostName=="magic-mirror":
   clientAddr = ('192.168.178.71', 4211)
else:
   clientAddr = ('192.168.20.100', 4211)

# Receive message if available
def ReceiveRaw():
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
      #if msg[0] == '0':
      #   msg = ':' + msg
      if msg[0] == ':':
         fields = msg.split()
         n=5
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
   #print("[udp.send] SENT:", send_data)

def close():
  UDPSock.close()
  print ("[udp] terminating ...")
  
def ExecCmd(cmd):
   sleep(0.1)
   for transmission in range(3):
      print("[udp.ExecCmd] " + cmd)
      send(cmd)
      
      print("[udp.ExecCmd] Wait for answer: " + cmd[3])
      timeOutCounter = 5
      # longer timeout for N, C and S commands
      if cmd[3]=="N" or cmd[3]=="C" or cmd[3]=="S" or cmd[3]=="R": timeOutCounter = 20
      while True:
         answer = receive()
         if answer != "":
            print(answer, end='')
            if answer[0] == cmd[3]: return answer
         sleep(0.1)
         timeOutCounter = timeOutCounter - 1
         if timeOutCounter == 0: break;
      #print("[udp.ExecCmd] TIMEOUT ERROR - Transmission #", transmission)
   print("[udp.ExecCmd] ERROR: Transmission failed")
   return ""


#def GetSummary():     # moved to mower.py
#   answer = ExecCmd("AT+S")
#   if answer=="": return
#   fields = answer.split(",")
#   checkSum = int(fields[16])
#   print("BatteryVoltage =", float(fields[1]))
#   print("MowPoint.Index =", int(fields[7]))
#   print("MapCRC =", checkSum)
#   return checkSum

#def close():   # duplicated
#   UDPSock.close()

#def OldSendCmd(cmd):
#   sleep(0.1)
#   for transmission in range(3):
#      print("[maps.SendCmd] " + cmd)
#      udp.send(cmd)
#      
#      print("[maps.SendCmd] Wait for answer: " + cmd[3])
#      timeOutCounter = 5
#      # longer timeout for N and C commands
#      if cmd[3]=="N" or cmd[3]=="C": timeOutCounter = 20
#      while True:
#         answer = udp.receive()
#         if answer != "":
#            print(answer, end='')
#            if answer[0] == cmd[3]: return answer
#         sleep(0.1)
#         timeOutCounter = timeOutCounter - 1
#         if timeOutCounter == 0: break;
#      print("[maps.SendCmd] TIMEOUT ERROR - Transmission #", transmission);
#   return ""


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
