#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UDP server - receives UDP packets from Arduino
# to be run with Anaconda/Miniconda Python 3.7

import sys
import udp
import mower
import maps
import socket
import signal
import os
import time
import requests
import json
from udp import WriteLog


def SetDockingStation(onFlag):
    WriteLog(f"SetDockingStation={onFlag}")
    payload = json.dumps({"on":onFlag})
    resp = requests.put('http://localhost/api/5989D6C473/lights/3/state', data = payload)
    if resp.status_code != 200:
        # This means something went wrong.
        #raise ApiError('PUT /tasks/ {}'.format(resp.status_code))
        WriteLog ("[amserver] ERROR")
        WriteLog(resp)
        WriteLog(resp.content)


def ParseCmdLine(cmdLine):
   cmdLine = cmdLine.strip()
   if not cmdLine: return "ERROR"
   
   argv = cmdLine.split()
   argc = len(argv)
   if argc > 1: maps.LoadMaps()
   logFlag = True
   if argc > 1: cmd = argv[1]
   if argc == 3 and cmd == "cat":
       udp.send("AT+$C,"+argv[2])
       logFlag = False
   elif argc == 3 and cmd == "cp":
       udp.send("AT+$C,"+argv[2])
       file = open(argv[2],"wb")
       logFlag = False
   elif argc == 2 and cmd == "ls":
       udp.send("AT+$L")
       logFlag = False
   elif argc == 3 and argv[1] == "ls":
       udp.send("AT+$L,"+argv[2])
       logFlag = False
   elif argc == 2 and cmd == "dir":
       udp.send("AT+$L")
       file = open("dir.txt","wb")
       logFlag = False
   elif argc == 2 and cmd == "tree":
       udp.send("AT+$T")
       WriteLog("[amserver] Recursive directory tree is written to Serial output only")
       logFlag = False
       return "OK"
   elif argc == 3 and cmd == "dir":
       udp.send("AT+$L,"+argv[2])
       file = open("dir.txt","wb")
       logFlag = False
   #elif argc == 2 and cmd == "log":
   #    WriteLog("Stop logging with Ctrl-C")
   elif argc == 3 and cmd == "rm":
       udp.send("AT+$R,"+argv[2])
   else:
      if argc == 2 and cmd == "srtc":     mower.SyncRtc()
      elif argc == 2 and cmd == "grtc":   mower.GetRtcDateTime()
      elif argc == 2 and cmd == "csum":   mower.ComputeMapChecksum()
      elif argc == 2 and cmd == "ver":    mower.GetVersionNumber()
      elif argc == 2 and cmd == "tb":     mower.ToggleBluetoothLogging()
      elif argc == 2 and cmd == "td":     mower.ToggleUseGPSfloatForDeltaEstimation()
      elif argc == 2 and cmd == "tp":     mower.ToggleUseGPSfloatForPosEstimation()
      elif argc == 3 and cmd == "rmap":   mower.ReadMapFromSdCard(int(argv[2]))
      elif argc == 3 and cmd == "umap":   mower.UploadMap(int(argv[2]))
      elif argc == 2 and cmd == "start":  mower.StartMowing()
      elif argc == 2 and cmd == "stop":   mower.StopMowing()
      elif argc == 2 and cmd == "dock":   mower.StartDocking()
      elif argc == 2 and cmd == "undock": mower.StartUndocking()
      elif argc == 2 and cmd == "grb":    mower.GnssReboot()
      elif argc == 2 and cmd == "off":    mower.SwitchOffRobot()
      elif argc == 2 and cmd == "ps":     mower.PrintStatistics()
      elif argc == 2 and cmd == "cs":     mower.ClearStatistics()
      elif argc == 2 and cmd == "gs":     mower.GetSummary()
      else: return "ERROR"
   #try:

   if not logFlag:   # file I/O command
      while True:    # wait for start-of-file token
         msg = udp.ReceiveRaw();
         if msg.find("$$$SOF$$$") >= 0: break;
      numLines = 0
      while True:
          msg = udp.ReceiveRaw();
          if msg != "":
             if msg.find("$$$EOF$$$") >= 0: break;
             numLines += 1
             if cmd=="cp":
                if (numLines & 31) == 0: WriteLog(numLines, end='\r')
                file.write(bytes(msg, 'cp850'))
             elif cmd=="dir": 
                file.write(bytes(msg, 'cp850'))
             else: 
                WriteLog(msg, end='')
      if cmd=="cp" or cmd=="dir": file.close()
      WriteLog(f"[amserver] {numLines} lines")
   return udp.GetGuiMessage()
   #except KeyboardInterrupt:
   #   print ("terminating ...")
   #udp.close()





SOCKET_PATH = "/tmp/amlog.sock"

connections = []
server = None

def cleanup_and_exit(signum, frame):
    WriteLog(f"\n[amserver] Signal {signum} empfangen. Server wird beendet...")
    if server:
        server.close()
    for conn in connections:
        conn.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    udp.close()
    sys.exit(0)


def main():
   global server
   maps.LoadMaps()
   
   # Signal-Handler registrieren
   signal.signal(signal.SIGINT, cleanup_and_exit)   # Ctrl+C
   signal.signal(signal.SIGTERM, cleanup_and_exit)  # kill
   # Optional: signal.signal(signal.SIGHUP, cleanup_and_exit)
   
   # Vorherige Socket-Datei löschen
   if os.path.exists(SOCKET_PATH):
      os.remove(SOCKET_PATH)
   
   # UNIX-Socket anlegen
   server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   server.bind(SOCKET_PATH)
   server.listen(5)

   # Non-blocking aktivieren
   server.setblocking(False)
   
   WriteLog("[amserver] Non-blocking Daemon läuft...")
   
   try:
      while True:
         # Neue Verbindung akzeptieren
         try:
               conn, _ = server.accept()
               WriteLog("[amserver] Neue Verbindung akzeptiert.")
               conn.setblocking(False)
               connections.append(conn)
         except BlockingIOError:
               pass  # keine neue Verbindung verfügbar
   
         # Bestehende Verbindungen abfragen
         for conn in connections[:]:
               try:
                  data = conn.recv(1024)
                  if data:
                     cmdLine = data.decode('utf-8')
                     WriteLog("[amserver] Empfangen:", cmdLine)
                     conn.sendall(ParseCmdLine(cmdLine).encode("utf-8"))
                  else:
                     WriteLog("[amserver] Verbindung geschlossen.")
                     conn.close()
                     connections.remove(conn)
               except BlockingIOError:
                  pass  # keine Daten verfügbar
   
         # receive Ardumower output
         msg = udp.ReceiveRaw();
         if msg!="": WriteLog(msg, end='')

         # Optional: CPU schonen
         time.sleep(0.1)
   except Exception as e:
      WriteLog(f"[amserver] Fehler: {e}")
   finally:
      cleanup_and_exit(0, 0)  # falls Schleife anders endet


if __name__ == '__main__':
    main()
