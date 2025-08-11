#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import socket
from time import sleep
from datetime import date;
from datetime import datetime
import os
import version
from config import GetLogFileName

logHeadline = "Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy     Gd     Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags Map Info    "
logMessage = " "

guiMessage = version.versionString

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   if msg != "": WriteLog("[GuiMessage] " + guiMessage)

# Logging to screen and to file
def WriteLog(text, end="\n"):
   now = datetime.now()
   time = now.strftime("%H:%M:%S ")
   if end!='':
      i=len(text)
      while i>0:
         if ord(text[i-1])==10 or ord(text[i-1])==13: i-=1
         else: break
      text = text[0:i] + "\n"
   #print(time+text, end=str(end), flush=True)
   print(time+text, end='', flush=True)
   with open(GetLogFileName(date.today().strftime("%Y-%m-%d")), 'a') as f:
      f.write(time+text)
      f.close

stateX = -10.0
stateY = -10.0
stateDeltaDegree = 0
targetX = 10.0
targetY = stateY
gpsX = stateX + 1
gpsY = stateY + 1

# UDP socket for Ardumower
host = ""
port = 4210
bufsize = 256

addr = (host, port)
UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock.bind(addr)
UDPSock.setblocking(0)

# UDP socket for remote control
hostRc = ""
portRc = 4215

addrRc = (hostRc, portRc)
UDPSockRc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSockRc.bind(addrRc)
UDPSockRc.setblocking(0)

#LogFileName = today.strftime("log/%Y-%m-%d-amcp-log.txt")
#print(LogFileName)

WriteLog("[udp] waiting for messages (port: " + str(port) + ") ...")

#if os.environ['COMPUTERNAME']=="HBA004":
#   clientAddr = ('192.168.178.71', 4211)
#else:
#   clientAddr = ('192.168.20.100', 4211)

hostName = socket.gethostname()
if hostName=="AZ-KENKO" or hostName=="magic-mirror":
   clientAddr = ('192.168.178.71', 4211)
else:
   clientAddr = ('192.168.20.102', 4211)
print(f"Client IP address: {clientAddr}")

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


# Forward RC message to Ardumower - if available
def ForwardRemoteControlMessage():
   try: 
      (data, clientAddrRc) = UDPSockRc.recvfrom(bufsize)
   except socket.error:
      pass
   else:   
      msg = data.decode('utf-8', errors="ignore")
      UDPSock.sendto(msg.encode('utf-8'), clientAddr)
   return

# Receive message from ArduMower - if available
def ReceiveMowerMessage():
   global stateX, stateY, stateDeltaDegree
   global targetX, targetY
   global gpsX, gpsY
   global logMessage
   global logHeadline
   
   msg = ReceiveRaw()
   if msg != "":
      WriteLog("[am] " + msg)
      if msg[0] == ':':
         fields = msg.split()
         n=5
         targetX = float(fields[n+0])
         targetY = float(fields[n+1])
         stateX = float(fields[n+2])
         stateY = float(fields[n+3])
         f = fields[n+4]
         f = f[0:len(f)-1]
         stateDeltaDegree = float(f)
         gpsX = float(fields[n+5])
         gpsY = float(fields[n+6])
         logMessage = msg[1:len(msg)-2]
      elif msg[0] == '#':
         logHeadline = msg[1:len(msg)-2]
      elif msg[0] == '=':
         PrintGuiMessage(msg[1:len(msg)-2])
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
   WriteLog("[udp.ExecCmd] " + cmd)
   for transmission in range(3):
      send(cmd)
      
      WriteLog("[udp.ExecCmd] Wait for answer: " + cmd[3])
      timeOutCounter = 5
      # longer timeout for N, C and S commands
      if cmd[3]=="N" or cmd[3]=="C" or cmd[3]=="S" or cmd[3]=="X" or cmd[3]=="W": timeOutCounter = 20
      if cmd[3]=="R": timeOutCounter = 100
      while True:
         answer = ReceiveMowerMessage()
         if answer != "":
            #WriteLog("[am] " + answer)
            if answer[0] == cmd[3]: 
               WriteLog("[udp.ExecCmd] Received answer: " + answer)
               return answer
         sleep(0.1)
         timeOutCounter = timeOutCounter - 1
         if timeOutCounter == 0: break;
      WriteLog("[udp.ExecCmd] Retransmission #" + str(transmission+1))
   WriteLog("[udp.ExecCmd] ERROR: Transmission failed")
   return ""

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
