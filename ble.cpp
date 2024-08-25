// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)


// Bluetooth BLE/4.0 module (HC-08/HM-10 ZS-040)
// https://www.marotronics.de/HM-10-Bluetooth-BLE-BT-40-CC2541-CC2540-fuer-Arduino-iOS-Android-Low-Energy
// docs:  http://denethor.wlu.ca/arduino/MLT-BT05-AT-commands-TRANSLATED.pdf

// to send/receive data from this module, use BLE characteristic write/read:  
// UART_CHARACTERISTIC = "0000ffe1-0000-1000-8000-00805f9b34fb";



#include "ble.h"
#include <Arduino.h>
#include "config.h"
#include "sim.h"

//#ifdef SUNRAY_HB_NO_BT
//String BLEConfig::read(){ String s;   CONSOLE.print(F("BLE: "));   return s; }
//String BLEConfig::exec(String cmd){ String s; return s; }
//void BLEConfig::run(){ CONSOLE.print(F("trying to detect Bluetooth 4.0/BLE module (make sure your phone is NOT connected)")); }
//#else

//extern bool simulationFlag;


#define BTserial Serial2
void bleConsoleTest()
{
    char c=' ';
    boolean NL = true;

    if (simulationFlag) return;

    Serial.println(F("Enter BT AT commands - Press ( to exit testmode"));
    
    while (true)
    {
        watchdogReset();
        // Read from the Bluetooth module and send to the Arduino Serial Monitor
        if (BTserial.available())
        {
            c = BTserial.read();
            Serial.write(c);
        }

        // Read from the Serial Monitor and send to the Bluetooth module
        if (Serial.available())
        {
            c = Serial.read();
            if (c == '(') return;
            if (c!=10 && c!=13 ) BTserial.write(c);
            Serial.write(c);
        }
    }
}


String BLEConfig::read()
{
  String res;

  if (simulationFlag) return "";

  delay(500);
  while (BLE.available()){
    char ch = BLE.read();
    CONSOLE.print(ch);
    //CONSOLE.write(ch);
    res += ch;
    //delay(10);
  }
  CONSOLE.println();
  return res;
}

String BLEConfig::exec(String cmd)
{
   if (simulationFlag) return "";

   CONSOLE.print(F("BLE: "));
   CONSOLE.println(cmd);
   //for (int i=0; i<cmd.length(); i++)
   //{
   //    CONSOLE.print(cmd[i], HEX);
   //    CONSOLE.print(" ");
   //}
   //CONSOLE.println(".");
   
   //for (int i=0; i<cmd.length(); i++)
   //{
   //  char ch=cmd[i];
   //  BLE.write(ch);
   //  CONSOLE.write(ch);
   //  //delay(4);
   //}
   BLE.print(cmd);
   return read();
}

// HB: Changed for DSD-TECH HM-10 Module
void BLEConfig::run()
{  
  int baud;
  bool found = false;

  if (simulationFlag) return;

#if 0
  //while (true){    
    for (int i=0; i < 2; i++){
      switch(i){
        case 0: baud=115200; break;  
        case 1: baud=9600; break;  
        default: continue;
      }
      CONSOLE.print(F("trying to detect Bluetooth 4.0/BLE module (make sure your phone is NOT connected)"));
      CONSOLE.print(baud);
      CONSOLE.println(F("..."));
      BLE.begin(baud);    
      //BLE.flush();
      //HB String res = exec("AT\r\n");
      String res = exec("AT");
      if (res.indexOf("OK") != -1){
        CONSOLE.println(F("Bluetooth 4.0/BLE module found!"));
        if (baud == BLE_BAUDRATE) {
          found = true;
          break;
        } else {
          if (BLE_BAUDRATE==9600)         exec("AT+BAUD0");  // 4
          else if (BLE_BAUDRATE==115200)  exec("AT+BAUD4");  // 8
          else {
              CONSOLE.println(F("Illegal BLE baud rate"));
              while(true)
                  ;
          }
          exec("AT+RESET");     // HB: switch to new baud rate
          BLE.begin(BLE_BAUDRATE);
          found = true;
          break;
        }
      }
    }
#else
    BLE.begin(BLE_BAUDRATE);
    exec("AT");
    String res = exec("AT");
    found = res.indexOf("OK") != -1;
    //bleConsoleTest();
#endif
    if (found) {
      //bleConsoleTest();
      exec("AT+HELP?");
      //exec("AT+LADDR\r\n");
      exec("AT+ADDR?");
#if defined(BLE_NAME)
      //HB exec("AT+NAME" BLE_NAME "\r\n");
      //exec("AT+NAME\r\n");
      exec("AT+NAME?");
#endif
      delay(200);
      //exec("AT+CHAR\r\n");
      //exec("AT+VERSION\r\n");
      //exec("AT+RESET\r\n");
      exec("AT+CHAR?");
      exec("AT+VERS?");
      exec("AT+RESET");
      return;
    }
    //delay(1000);
  //}
}
//#endif
