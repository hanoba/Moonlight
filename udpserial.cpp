// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include "udpserial.h"
#include "sdserial.h"
#include "src/esp/WiFiEsp.h"
#include "src/esp/WiFiEspUdp.h"
#include "console.h"

extern bool simulationFlag;

//#if defined(_SAM3XA_)                 // Arduino Due
//  #define CONSOLE SerialUSB
//#else
//  #define CONSOLE Serial
//#endif


#if !defined(NO_GLOBAL_INSTANCES) && !defined(NO_GLOBAL_SERIAL)
UdpSerial udpSerial;
#endif

unsigned int localPort = 4211;  // local port 


WiFiEspUDP Udp;
const int PACKET_BUFFER_SIZE = 256;
static char packetBuffer[PACKET_BUFFER_SIZE];          // buffer to packet
int packetIdx = 0;
bool udpStarted = false;
bool udpActive = false;


void UdpSerial::begin(unsigned long baud){  
  CONSOLE.begin(baud);
}  

void UdpSerial::beginUDP(){  
  Udp.begin(localPort);  
  ////Udp.beginPacket(remoteIP, UDP_SERVER_PORT);
  // Udp.endPacket();
  udpStarted = true;  
}


int UdpSerial::readPacket(char *packetBuf, int bufSize)
{
   int len = 0;
   int packetSize = Udp.parsePacket();
   if (packetSize)
   {
      len = Udp.read(packetBuf, bufSize);
      if (len > 0) 
      {
         packetBuf[len] = 0;
      }
   }
   return len;
}

size_t UdpSerial::write(uint8_t data)
{
   if ((udpStarted) && (!udpActive)) 
   {
      udpActive = true;
      packetBuffer[packetIdx] = char(data);
      packetIdx++;
      if (packetIdx == PACKET_BUFFER_SIZE-1 || data == '\n')
      {
         IPAddress remoteIP_sim(UDP_SERVER_IP_SIM);
         IPAddress remoteIP(UDP_SERVER_IP);
         packetBuffer[packetIdx] = 0;
         Udp.beginPacket(simulationFlag ? remoteIP_sim : remoteIP, UDP_SERVER_PORT);
         Udp.write(packetBuffer);              
         Udp.endPacket();
#ifdef ENABLE_SD_LOG
         if (!LoggingDisableFlag) sdSerial.writeSD(packetBuffer);    //HB: enable logging via UDP and to SD card
#endif
         packetIdx = 0;            
      }
      udpActive = false;
   } 
   // Log to CONSOLE if simulationFlag is true or if logging via UDP is not activated
   //if ((simulationFlag || !udpStarted) && !LoggingDisableFlag) CONSOLE.write(data);
   if (!LoggingDisableFlag) CONSOLE.write(data);
   return 1; 
}
  
  
int UdpSerial::available(){
  return CONSOLE.available();
}


int UdpSerial::read(){
  return CONSOLE.read();
}


int UdpSerial::peek(){
  return CONSOLE.peek();
}

void UdpSerial::flush(){  
  CONSOLE.flush();    
}
