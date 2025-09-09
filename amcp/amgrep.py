#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from datetime import date
from config import GetLogFileName

def Usage():
    print("Usage: amgrep [--date=yyyy-mm-dd] grepArgs...")
    print("\nExamples:")
    print("    amgrep Moonlight     # find Ardumower reboots")
    print("    amgrep TTFF          # find time to first fix")

def main():
    i=0;
    datum = date.today().strftime("%Y-%m-%d")
    argc = len(sys.argv)
    if argc<2: 
        Usage()
        sys.exit()
    elif sys.argv[1].startswith("--date="):
        datum=sys.argv[1][7:]
        i=1;
        
    dateiname = GetLogFileName(datum)
    if not os.path.exists(dateiname):
        print(f"File not found: {dateiname}")
        sys.exit()

    grepCmd = sys.argv[i:]
    grepCmd[0] = "grep"
    grepCmd.append(dateiname)    
    print(grepCmd)
    
    try:
        subprocess.run(grepCmd, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode==1: print("Not found!")
        else: print("Fehler beim Ausführen:", e)
 
if __name__ == '__main__':
    main()
