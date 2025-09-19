#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ardumower logfile analyzer

import os
import sys
import argparse
import glob
from datetime import date
from config import GetLogFileName
from datetime import datetime, timedelta

def TimeDiff(t1: str, t2: str) -> str:
    fmt = "%H:%M:%S"
    dt1 = datetime.strptime(t1, fmt)
    dt2 = datetime.strptime(t2, fmt)

    # Handle crossing midnight
    if dt2 < dt1:
        dt2 += timedelta(days=1)

    # Difference in seconds
    total_seconds = int((dt2 - dt1).total_seconds())

    # Convert seconds -> hh:mm:ss
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours==0: return f"   {minutes:02}:{seconds:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Ardumower periodic logs
# 12:24:22 #Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy   Pitch    Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags  Map  WayPts 
#        0     1        2     3     4    5     6      7      8      9     10     11     12      13    14   15      16   17    18   19   20   21  22    23   24      25
#
# ['14:42:58', ':14:46:40', '0.02', 'MOW', '25.1', '47', '2.69', '10.65', '5.99', '5.27', '122°', '0.00', '0.00', '8°', '7.43', 'INV26', '58.7', '0', '/49', '558', '369', '286', '39°C', '47%', 'bpdKSF', 'MAP3', '3/54']
iTime = 0
iState = 3
iSol = 15
iSat = 17
iMap = 24
iWayPoint = 25


def main(dateiname, argMap, verbose):    
    #print(f"{dateiname} {argMap=}")
    datum = dateiname[:10]
    
    map = "MAP?"
    # Datei zeilenweise öffnen und lesen alle relevanten zeilen
    with open(dateiname, "r", encoding="latin-1") as file:
        oldMowerState = "IDLE"
        for zeilennummer, zeile in enumerate(file, start=1):
            zeile = zeile.strip()  # Entfernt Zeilenumbruch und Leerzeichen
            if not zeile:
                continue  # Leere Zeilen überspringen
    
            felder = zeile.split()  # Standardmäßig nach beliebigen Leerzeichen aufteilen
            numFelder = len(felder)
            if numFelder>1 and felder[1]=="[am]": felder.pop(1)  # remove "[am]" in amcmd logs (logs from amserver.py do not have this prefix)
    
            # fix problem with blanks in satellite display. Convert "0 /30" into "0/30" and "0 / 0" to "0/0"
            if numFelder >= 25 and felder[1][0]==":":
                sat = felder[iSat]
                if len(sat)==1:
                    felder.pop(iSat)
                    felder[iSat] = f"{sat}{felder[iSat]}"
                    
                    sat = felder[iSat]
                    if len(sat)==2:
                        felder.pop(iSat)
                        felder[iSat] = f"{sat}{felder[iSat]}"                    
    
            time = felder[iTime]
            
            # detect periodic log message
            if numFelder >= 25 and felder[1][0]==":":
                mowerState = felder[iState]
                solution = felder[iSol][:2]
                wayPoint = felder[iWayPoint]
                map = felder[iMap]
                
                # Konsistenz der Felder prüfen
                if map[:3] != "MAP":
                    print(f"{dateiname}: {zeile}")
                    for i in range(len(felder)):
                        print(i, felder[i])
                    sys.exit()
                    
                if mowerState=="MOW":
                    if oldMowerState!="MOW":
                        solCnt = 0
                        invalCnt = 0
                        floatCnt = 0
                        fixCnt = 0
                        numErrors = 0
                        mowStartTime = time                        
                        w = wayPoint.split("/")
                        firstWayPoint = w[0]
                        if map==argMap or argMap=="*": 
                            if (verbose): print(f"{datum} {time} {map:5} {wayPoint:7} MOW")
                    solCnt += 1
                    lastWayPoint=wayPoint
                    if solution=="IN": invalCnt += 1
                    elif solution=="FL": floatCnt += 1
                    elif solution=="FI": fixCnt += 1
                elif oldMowerState=="MOW":
                    if argMap=="*" or argMap==map:
                        if verbose or lastWayPoint[:2]!="0/":
                            print(f"{datum} {time} {map:5} {firstWayPoint:>3}-{lastWayPoint:7} {mowerState:5} Summary: "
                                  f"FIX:{100*fixCnt/solCnt:4.0f}%, FLOAT:{100*floatCnt/solCnt:4.0f}%, INVAL:{100*invalCnt/solCnt:4.0f}%, "
                                  f"{mowStartTime}, {TimeDiff(mowStartTime, time)}, {numErrors=}")
                oldMowerState = mowerState    
            
            # detect power-cycle and reboot
            elif "GPS receiver found!" in zeile:
               if (verbose): print(f"{datum} {time} power-cycle and reboot")
    
            # detect error messages
            elif ("error" in zeile.lower() or "=BumperFreeWheel" in zeile) and oldMowerState=="MOW" and (map==argMap or argMap=="*"):
                numErrors += 1
                if (verbose): print(f"{datum} {time} {map:5} {zeile}")
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ardumower Logfile Anaylzer")
    parser.add_argument("files", nargs="*", help="List of logfiles to be processed")
    parser.add_argument("-m", "--map", help="Search for specific map ", default="*")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    argFiles = args.files
    if len(argFiles)==0:
        datum = date.today().strftime("%Y-%m-%d")
        argFiles = [ GetLogFileName(datum) ]

    for f in argFiles:
        files = glob.glob(f) 
        for dateiname in files:
            if not os.path.exists(dateiname):
                print(f"File not found: {dateiname}")
                sys.exit()
            main(dateiname, args.map, args.verbose)
