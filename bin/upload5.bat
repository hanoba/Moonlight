@echo off
set BOSSAC=C:\Users\Harald\AppData\Local\Arduino15\packages\arduino\tools\bossac\1.6.1-arduino/bossac.exe
set BIN=Moonlight.ino.bin
set PORT=COM5
echo Erzwinge Reset durch oeffnen/schliessen mit 1200 bps auf dem Port %PORT%
mode %PORT%:1200
:: timeout /T 10 wartet 10 Sekunden, die Wartezeit kann mit einer beliebigen Taste übersprungen werden, um dies zu verhindern gibt es den Parameter: /nobreak
timeout /T 1 >nul
echo.
echo Uploading file %BIN%
echo.
:: Usage: bossac.exe [OPTION...] [FILE]
:: Basic Open Source SAM-BA Application (BOSSA) Version 1.6.1-arduino
:: Flash programmer for Atmel SAM devices.
:: Copyright (c) 2011-2012 ShumaTech (http://www.shumatech.com)
:: 
:: Examples:
::   bossac -e -w -v -b image.bin   # Erase flash, write flash with image.bin,
::                                  # verify the write, and set boot from flash
::   bossac -r0x10000 image.bin     # Read 64KB from flash and store in image.bin
:: 
:: Options:
::   -e, --erase           erase the entire flash (keep the 8KB of bootloader for SAM Dxx)
::   -w, --write           write FILE to the flash; accelerated when
::                         combined with erase option
::   -r, --read[=SIZE]     read SIZE from flash and store in FILE;
::                         read entire flash if SIZE not specified
::   -v, --verify          verify FILE matches flash contents
::   -p, --port=PORT       use serial PORT to communicate to device;
::                         default behavior is to auto-scan all serial ports
::   -b, --boot[=BOOL]     boot from ROM if BOOL is 0;
::                         boot from FLASH if BOOL is 1 [default];
::                         option is ignored on unsupported devices
::   -c, --bod[=BOOL]      no brownout detection if BOOL is 0;
::                         brownout detection is on if BOOL is 1 [default]
::   -t, --bor[=BOOL]      no brownout reset if BOOL is 0;
::                         brownout reset is on if BOOL is 1 [default]
::   -l, --lock[=REGION]   lock the flash REGION as a comma-separated list;
::                         lock all if not given [default]
::   -u, --unlock[=REGION] unlock the flash REGION as a comma-separated list;
::                         unlock all if not given [default]
::   -s, --security        set the flash security flag
::   -i, --info            display device information
::   -d, --debug           print debug messages
::   -h, --help            display this help text
::   -U, --force_usb_port=true/false override USB port autodetection
::   -R, --reset           reset CPU (if supported)
%BOSSAC% -i --port=%PORT% -U false -e -w -b %BIN% -R 
pause
