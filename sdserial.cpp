// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include "sdserial.h"
#include <SD.h>
#include "console.h"
#include "rtc.h"


//#if defined(_SAM3XA_)                 // Arduino Due
//  //#define CONSOLE SerialUSB
//  #define CONSOLE Serial
//#else
//  #define CONSOLE Serial
//#endif


#if !defined(NO_GLOBAL_INSTANCES) && !defined(NO_GLOBAL_SERIAL)
SDSerial sdSerial;
#endif



void SDSerial::begin(unsigned long baud){  
  logFileName = "";
  packetIdx = 0;
  sdStarted = false;
  sdActive = false;
  CONSOLE.begin(baud);
}  

void SDSerial::beginSD()
{  
   DateTime now;
   char buf[16];

   GetDateTime(now);

   sprintf(buf, "%02d%02d%02d%02d.txt", now.month, now.monthday, now.hour, now.minute);
   logFileName = (String)buf;

   CONSOLE.print("logfile: ");
   CONSOLE.println(logFileName);    
   sdStarted = true;

   // for (int i=10; i < 99; i++){
   //   logFileName = time;
   //   logFileName += i;
   //   logFileName += ".txt";    
   //   if (!SD.exists(logFileName)) {
   //     CONSOLE.print("logfile: ");
   //     CONSOLE.println(logFileName);    
   //     sdStarted = true;
   //     break; 
   //     //SD.remove(UPDATE_FILE);
   //     //updateFile.close();
   //     //uint32_t updateSize = updateFile.size();
   //     //updateFile.seek(SDU_SIZE);      
   //   }
   // }  
}

//HB write SD is used in "udpserial.cpp"
void SDSerial::writeSD(char *buf)
{
   logFile = SD.open(SDSerial::logFileName, FILE_WRITE);
   if (logFile){        
     logFile.write(buf);              
     logFile.flush();
     logFile.close();            
   } else {
     CONSOLE.println("ERROR opening file for writing");
   }
}


size_t SDSerial::write(uint8_t data){
  if ((sdStarted) && (!sdActive)) {
    sdActive = true;
    packetBuffer[packetIdx] = char(data);
    packetIdx++;
    if (packetIdx == 99){
      packetBuffer[packetIdx] = '\0';            
      //logFile = SD.open(logFileName, FILE_WRITE);
      //if (logFile){        
      //  logFile.write(packetBuffer);              
      //  logFile.flush();
      //  logFile.close();            
      //} else {
      //  CONSOLE.println("ERROR opening file for writing");
      //}
      writeSD(packetBuffer);
      packetIdx = 0;            
    }
    sdActive = false;
  }  
  CONSOLE.write(data);
  return 1; 
}
  
  
int SDSerial::available(){
  return CONSOLE.available();
}


int SDSerial::read(){
  return CONSOLE.read();
}


int SDSerial::peek(){
  return CONSOLE.peek();
}

void SDSerial::flush(){  
  CONSOLE.flush();    
}
