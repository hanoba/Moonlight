#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import time
import requests
import json
import os
from datetime import date
from config import GetLogFileName


def PrintHelpText(): 
   print("Ardumower Command Line Tool")
   print("")
   print("Usage: amcmd ls [<file_pattern>]      # list files to stdout")
   print("       amcmd dir [<file_pattern>]     # list files to dir.txt")
   print("       amcmd tree                     # list files including sub folders (Serial only)")
   print("       amcmd rm [<file_pattern>]      # remove files")
   print("       amcmd cat <file_name>          # output file to stdout")
   print("       amcmd cp <file_name>           # copy file to current directory")
   print("       amcmd setds on|off             # switch docking station on or off")
   print("       amcmd gs                       # GetSummary")
   print("       amcmd srtc                     # SyncRtc")
   print("       amcmd log                      # Log Ardumower output to screen")
   print("       amcmd grtc                     # GetRtcDateTime")
   print("       amcmd csum                     # ComputeMapChecksum")
   print("       amcmd ver                      # GetVersionNumber")
   print("       amcmd tb                       # ToggleBluetoothLogging")
   print("       amcmd td                       # ToggleUseGPSfloatForDeltaEstimation")
   print("       amcmd tp                       # ToggleUseGPSfloatForPosEstimation")
   print("       amcmd reboot                   # Reboot and power-cycle Ardumower")
   print("       amcmd start                    # StartMowing")
   print("       amcmd stop                     # StopMowing (IDLE mode)")
   print("       amcmd dock                     # Go to docking station")
   print("       amcmd undock                   # Undock from docking station")
   print("       amcmd gwrb                     # GNSS Warm Reboot")
   print("       amcmd gcrb                     # GNSS Cold Reboot")
   print("       amcmd off                      # SwitchOffRobot")
   print("       amcmd ps                       # PrintStatistics")
   print("       amcmd cs                       # ClearStatistics")
   print("       amcmd umap <mapId>             # UploadMap (<mapId>=1...10)")
   print("       amcmd rmap <mapId>             # ReadMapFromSdCard (<mapId>=1..10)")
   print("<file_pattern> can include the wild card * at the end")


def SetDockingStation(onFlag):
    print(f"SetDockingStation={onFlag}")
    payload = json.dumps({"on":onFlag})
    resp = requests.put('http://localhost/api/5989D6C473/lights/3/state', data = payload)
    if resp.status_code != 200:
        # This means something went wrong.
        #raise ApiError('PUT /tasks/ {}'.format(resp.status_code))
        print ("[amcmd] ERROR")
        print(resp)
        print(resp.content)

def ExecCmd(cmdLine):
   with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
      client.connect(SOCKET_PATH)
      client.sendall(cmdLine.encode("utf-8"))
      response = client.recv(1024)
      result = response.decode()
      if result=="ERROR": PrintHelpText()
      else:
         os.system(f"tail -n 36 {GetLogFileName(today)}")
         print(result)


SOCKET_PATH = "/tmp/amlog.sock"

today =  date.today().strftime("%Y-%m-%d")
argc = len(sys.argv)
if argc==3 and sys.argv[1]=="setds":
   if sys.argv[2]=="off": SetDockingStation(False)
   elif sys.argv[2]=="on": SetDockingStation(True)
   else: PrintHelpText();
elif argc==2 and sys.argv[1]=="reboot":
   print("Rebooting Ardumower with power-cycle. Ardumower must be in docking station!")
   SetDockingStation(False)
   print("wait...")
   time.sleep(3)
   ExecCmd("amcmd off")
   print("wait...")
   time.sleep(3)
   SetDockingStation(True)
elif argc==2 and sys.argv[1]=="log":
   os.system(f"tail -f {GetLogFileName(today)}")
elif argc > 1: 
   cmdLine = sys.argv[0]
   for i in range(1, argc):
      cmdLine += " " + sys.argv[i]
   ExecCmd(cmdLine)
else: PrintHelpText()
