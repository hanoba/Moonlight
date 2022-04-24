#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import sys
#import socket
import udp
import mower
import maps
#import os

#host = ""
#port = 4210
#bufsize = 256
#
#
#addr = (host, port)
#UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#UDPSock.bind(addr)
#UDPSock.setblocking(0)
#
##print("waiting for messages (port: " + str(port) + ") ...")
#
##clientAddr = ""   
##clientAddr = ('192.168.178.71', 4211)
##clientAddr = ('192.168.20.100', 4211)
##ping ESP-17C64F garten
#hostName = socket.gethostname()
#if hostName=="HBA004" or hostName=="magic-mirror":
#   clientAddr = ('192.168.178.71', 4211)
#else:
#   clientAddr = ('192.168.20.100', 4211)
#


# Receive message if available
#def udp.ReceiveRaw():
#   global clientAddr
#   msg = ""
#   try: 
#      (data, clientAddr) = UDPSock.recvfrom(bufsize)
#   except socket.error:
#      pass
#   else:   
#      msg = data.decode('utf-8', errors="ignore")
#      #msg = data
#   return msg

def CheckSum(send_data):
   checkSum = 0
   for i in range(len(send_data)):
      checkSum += ord(send_data[i])
   checkSum = checkSum & 255
   return checkSum

#def send(send_data):
#   #print(clientAddr)
#   send_data = send_data + str.format(',0x{:02X}', CheckSum(send_data))
#   UDPSock.sendto(send_data.encode('utf-8'), clientAddr)
#   #print("SENT:", send_data)

def main():
   argc = len(sys.argv)
   if argc > 1: maps.LoadMaps()
   logFlag = True
   if argc > 1: cmd = sys.argv[1]
   if argc == 3 and cmd == "cat":
       udp.send("AT+$C,"+sys.argv[2])
       logFlag = False
   elif argc == 3 and cmd == "cp":
       udp.send("AT+$C,"+sys.argv[2])
       file = open(sys.argv[2],"wb")
       logFlag = False
   elif argc == 2 and cmd == "ls":
       udp.send("AT+$L")
       logFlag = False
   elif argc == 3 and sys.argv[1] == "ls":
       udp.send("AT+$L,"+sys.argv[2])
       logFlag = False
   elif argc == 2 and cmd == "dir":
       udp.send("AT+$L")
       file = open("dir.txt","wb")
       logFlag = False
   elif argc == 2 and cmd == "tree":
       udp.send("AT+$T")
       print("Recursive directory tree is written to Serial output only")
       logFlag = False
       return
   elif argc == 3 and cmd == "dir":
       udp.send("AT+$L,"+sys.argv[2])
       file = open("dir.txt","wb")
       logFlag = False
   elif argc == 2 and cmd == "log":
       print("Stop logging with Ctrl-C")
   elif argc == 3 and cmd == "rm":
       udp.send("AT+$R,"+sys.argv[2])
   else:
      if argc == 2 and cmd == "srtc":  mower.SyncRtc()
      elif argc == 2 and cmd == "grtc":  mower.GetRtcDateTime()
      elif argc == 2 and cmd == "csum":  mower.ComputeMapChecksum()
      elif argc == 2 and cmd == "ver":   mower.GetVersionNumber()
      elif argc == 2 and cmd == "tb":    mower.ToggleBluetoothLogging()
      elif argc == 2 and cmd == "tf":    mower.ToggleUseGPSfloatForDeltaEstimation()
      elif argc == 2 and cmd == "tp":    mower.ToggleUseGPSfloatForPosEstimation()
      elif argc == 3 and cmd == "rmap":  mower.ReadMapFromSdCard(int(sys.argv[2]))
      elif argc == 3 and cmd == "umap":  mower.UploadMap(int(sys.argv[2]))
      elif argc == 2 and cmd == "start": mower.StartMowing()
      elif argc == 2 and cmd == "stop":  mower.StopMowing()
      elif argc == 2 and cmd == "dock":  mower.StartDocking()
      elif argc == 2 and cmd == "off":   mower.SwitchOffRobot()
      elif argc == 2 and cmd == "ps":    mower.PrintStatistics()
      elif argc == 2 and cmd == "cs":    mower.ClearStatistics()
      elif argc == 2 and cmd == "gs":    mower.GetSummary()
      else:
         print("Ardumower Command Line Tool")
         print("")
         print("Usage: amcmd ls [<file_pattern>]      # list files to stdout")
         print("       amcmd dir [<file_pattern>]     # list files to dir.txt")
         print("       amcmd tree                     # list files including sub folders (Serial only)")
         print("       amcmd rm [<file_pattern>]      # remove files")
         print("       amcmd cat <file_name>          # output file to stdout")
         print("       amcmd cp <file_name>           # copy file to current directory")
         print("       amcmd log                      # display logging output(stop with Ctrl-C)")
         print("       amcmd gs                       # GetSummary")
         print("       amcmd srtc                     # SyncRtc")
         print("       amcmd grtc                     # GetRtcDateTime")
         print("       amcmd csum                     # ComputeMapChecksum")
         print("       amcmd ver                      # GetVersionNumber")
         print("       amcmd tb                       # ToggleBluetoothLogging")
         print("       amcmd tf                       # ToggleUseGPSfloatForDeltaEstimation")
         print("       amcmd tp                       # ToggleUseGPSfloatForPosEstimation")
         print("       amcmd start                    # StartMowing")
         print("       amcmd stop                     # StopMowing (IDLE mode)")
         print("       amcmd dock                     # Go to docking station")
         print("       amcmd off                      # SwitchOffRobot")
         print("       amcmd ps                       # PrintStatistics")
         print("       amcmd cs                       # ClearStatistics")
         print("       amcmd umap <mapId>             # UploadMap(<mapId>)")
         print("       amcmd rmap <mapId>             # ReadMapFromSdCard(<mapId>)")
         print("<file_pattern> can include the wild card * at the end")
      return
   try:
      if not logFlag:    # cmd != "log":
          while True:
              msg = udp.ReceiveRaw();
              if msg.find("$$$SOF$$$") >= 0: break;
      numLines = 0
      while True:
          msg = udp.ReceiveRaw();
          if msg != "":
             if msg.find("$$$EOF$$$") >= 0: break;
             numLines += 1
             if cmd=="cp":
                if (numLines & 31) == 0: print(numLines, end='\r', flush=True)
                file.write(bytes(msg, 'cp850'))
             elif cmd=="dir": 
                file.write(bytes(msg, 'cp850'))
             else: 
                print(msg, end='', flush=True)
   except KeyboardInterrupt:
      print ("terminating ...")
   udp.close()
   print(numLines)
   if cmd=="cp" or cmd=="dir": file.close()


if __name__ == '__main__':
    main()
