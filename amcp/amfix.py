#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import date
from config import GetLogFileName

def ZeichneBalkendiagramm(uhrzeit, x, symbol='█', breite=50):
    max_wert = 100  # max(daten.values())
    for i in range(len(x)):
        balkenlaenge = int((x[i] / max_wert) * breite)
        balken = symbol * balkenlaenge
        print(f"{uhrzeit[i]:<6} | {balken} {x[i]}%")

solution="FIX"

def ProcessOption(option):
   global solution
   if option=='-float': solution="FLT"
   elif option=='-inval': solution="INV"
   else: 
      print("Usage: amfix [-float|-inval] [yyyy-mm-dd]")
      sys.exit()

def main():
   datum = date.today().strftime("%Y-%m-%d")
   argc = len(sys.argv)
   if argc==2:
      if sys.argv[1][0]=='-': ProcessOption(sys.argv[1])
      else : datum=sys.argv[1]
   elif argc==3: 
      ProcessOption(sys.argv[1])
      datum=sys.argv[2]
   dateiname = GetLogFileName()
   if not os.path.exists(dateiname):
      print(f"File not found: {dateiname}")
      sys.exit()

   fixTime = []
   fixValue = []
   
   # Datei zeilenweise öffnen und lesen alle relevanten zeilen
   with open(dateiname, "r", encoding="utf-8") as file:
       for zeilennummer, zeile in enumerate(file, start=1):
           zeile = zeile.strip()  # Entfernt Zeilenumbruch und Leerzeichen
           if not zeile:
               continue  # Leere Zeilen überspringen

           felder = zeile.split()  # Standardmäßig nach beliebigen Leerzeichen aufteilen

           if len(felder) > 16 and felder[1][0]==":":
               fixTime.append(felder[0][0:5])
               if felder[15][:3] == solution: fixValue.append(1)
               else: fixValue.append(0)

   # averaging und subsampling
   fixRate = []
   uhrzeit = []
   avWinSize = 12*30  # averaging over 30 minutes
   numInValues = len(fixValue)
   numOutValues = numInValues // avWinSize
   i = numInValues - numOutValues*avWinSize
   for k in range(numOutValues):
      numFixValues = 0
      for k in range(avWinSize):
         numFixValues += fixValue[i]
         i += 1
      uhrzeit.append(fixTime[i-1])
      fixRate.append(int(numFixValues/avWinSize*100+0.5))

   print(f"\n         {datum}: FIX Rate over time\n")
   ZeichneBalkendiagramm(uhrzeit, fixRate, symbol='=')


if __name__ == '__main__':
    main()
