// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

/*
  SD card serial logger
*/

#ifndef SDSERIAL_H
#define SDSERIAL_H

#include <HardwareSerial.h>
#include <Arduino.h>
#include <SD.h>



class SDSerial: public Stream{
  public:
    String logFileName;
    String gpsLogFileName;
    File logFile;
    File gpsLogFile;
    char packetBuffer[100];          // buffer to packet
    int packetIdx;
    bool sdStarted;
    bool sdActive;
    virtual void begin(unsigned long baud);
    void beginSD();
    void writeSD(char *buf);
    void writeGpsLogSD(char *buf);
    virtual size_t write(uint8_t);
    virtual int available();
    virtual int read();
    virtual int peek();    
    virtual void flush();
private:
   bool SdCardLoggingDisableFlag = false;
};

extern SDSerial sdSerial; // Making it available as sdSerial


#endif
