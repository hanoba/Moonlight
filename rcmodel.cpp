// Ardumower Moonlight 


#include "src/esp/WiFiEsp.h"
#include "src/esp/WiFiEspUdp.h"

#include "config.h"
#include "rcmodel.h"
#include "robot.h"

//static WiFiEspUDP rcUdp;

//static unsigned int rcLocalPort = 4213;  // local port 

void RCModel::begin()
{ 
   //rcUdp.begin(rcLocalPort);  
} 


void RCModel::DoRemoteControl(String cmd)
{
   if (cmd.length() < 6) return;
   int counter = 0;
   int lastCommaIdx = 0;
   int slowDown=1;
   for (int idx = 0; idx < cmd.length(); idx++) 
   {
       char ch = cmd[idx];
       if ((ch == ',') || (idx == cmd.length() - 1)) 
       {
           int intValue = cmd.substring(lastCommaIdx + 1, idx + 1).toInt();

           if (intValue < -2500) intValue = -2500;
           if (intValue > 2500) intValue = 2500;

           if (counter == 1) iLinear = intValue;
           else if (counter == 2) iAngular = intValue;
           else if (counter == 3) 
           {   
               motor.enableMowMotor = intValue>>3 & 1;
               motor.setMowState(intValue>>3 & 1);
               slowDown = 1 + (intValue & 3);
           }
           counter++;
           lastCommaIdx = idx;
       }
   }
   // mowerSpeed = 0.5 * iLinear / 2048       # m/s
   // mowerRotation = 1 * iAngular / 2048     # rad/s
   if (counter > 2)
   {
      static const float cLinear = 0.5 / 2048.;
      static const float cAngular = 1.0 / 2048.;
 
      if (stateOp == OP_IDLE) motor.setLinearAngularSpeed(iLinear*cLinear/slowDown, iAngular*cAngular, false);    
      dataFlag = true;
   }
}


void RCModel::run()
{
   //int len = 0;
   //const int SIZE = 32;
   //static char packetBuf[SIZE];
   //int packetSize = rcUdp.parsePacket();
   //if (packetSize)
   //{
   //   len = rcUdp.read(packetBuf, SIZE);
   //   if (len > 0) 
   //   {
   //      packetBuf[len] = 0;
   //      DoRemoteControl(packetBuf);
   //   }
   //}
   if (millis() > nextRcOutputTime)
   {
      nextRcOutputTime += 1000;
      if (dataFlag != lastDataFlag)
      {
         if (dataFlag) CONSOLE.println(stateOp == OP_IDLE ? F("=RC connected") : F("=RC ERROR: Switch to IDLE mode"));
         else CONSOLE.println(F("=RC disconnected"));
      }
      lastDataFlag = dataFlag;
      if (dataFlag)
      {
         CONSOLE.print("[RC] ");
         CONSOLE.print(iLinear);
         CONSOLE.print(",");
         CONSOLE.println(iAngular);
      }
      dataFlag = false;
   }
}
