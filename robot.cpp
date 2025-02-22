// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)

#include <Arduino.h>
#include <SD.h>
#include <stdio.h>
#include <stdarg.h>

#include "robot.h"
#include "LineTracker.h"
#include "comm.h"
#include "src/esp/WiFiEsp.h"
#include "src/mpu/SparkFunMPU9250-DMP.h"
#include "SparkFunHTU21D.h"
#include "RunningMedian.h"
#include "pinman.h"
#include "ble.h"
#include "motor.h"
#include "src/driver/AmRobotDriver.h"
#include "src/driver/SerialRobotDriver.h"
#include "battery.h"
#include "src/ublox/ublox.h"
#include "buzzer.h"
#include "rcmodel.h"
#include "map.h"
#include "config.h"
#include "helper.h"
#include "pid.h"
#include "reset.h"
#include "cpu.h"
#include "i2c.h"
#include "sim.h"
#include "rtc.h"
#include "fix_display.h"


// #define I2C_SPEED  10000
#define _BV(x) (1 << (x))

Sim sim;

const signed char orientationMatrix[9] = {
  1, 0, 0,
  0, 1, 0,
  0, 0, 1
};

File stateFile;
MPU9250_DMP imu;
#ifdef DRV_SERIAL_ROBOT
  SerialRobotDriver robotDriver;
  SerialMotorDriver motorDriver(robotDriver);
  SerialBatteryDriver batteryDriver(robotDriver);
  SerialBumperDriver bumper(robotDriver);
  SerialStopButtonDriver stopButton(robotDriver);
#else
  AmRobotDriver robotDriver;
  AmMotorDriver motorDriver;
  AmBatteryDriver batteryDriver;
  AmBumperDriver bumper;
  AmStopButtonDriver stopButton;
#endif
Motor motor;
Battery battery;
PinManager pinMan;
UBLOX gps(GPS,GPS_BAUDRATE);
BLEConfig bleConfig;
Buzzer buzzer;
Sonar sonar;
VL53L0X tof(VL53L0X_ADDRESS_DEFAULT);
Map maps;
HTU21D myHumidity;
RCModel rcmodel;
PID pidLine(0.2, 0.01, 0); // not used
PID pidAngle(2, 0.1, 0);  // not used

FixDisplay fixDisplay;

OperationType stateOp = OP_IDLE; // operation-mode
Sensor stateSensor = SENS_NONE; // last triggered sensor
unsigned long controlLoops = 0;
float stateX = 0;  // position-east (m)
float stateY = 0;  // position-north (m)
float stateDelta = 0;  // direction (rad)
float stateRoll = 0;
float statePitch = 0;
float stateDeltaGPS = 0;
float stateDeltaIMU = 0;
float stateGroundSpeed = 0; // m/s
float stateTemp = 0; // degreeC
float stateHumidity = 0; // percent

unsigned long stateLeftTicks = 0;
unsigned long stateRightTicks = 0;
unsigned long lastFixTime = 0;
int fixTimeout = 0;
bool absolutePosSource = false;
double absolutePosSourceLon = 0;
double absolutePosSourceLat = 0;
bool finishAndRestart = false;
bool resetLastPos = true;
bool stateChargerConnected = false;
bool imuIsCalibrating = false;
int imuCalibrationSeconds = 0;
unsigned long nextImuCalibrationSecond = 0;
float rollChange = 0;
float pitchChange = 0;
float lastGPSMotionX = 0;
float lastGPSMotionY = 0;
unsigned long nextGPSMotionCheckTime = 0;

float maxPitch = -PI;      //HB Used for pitch display only
bool upHillFlag = false;   //HB vermeiden, dass Mower kippt bei grossen Steigungen
bool upHillDetectionFlag = false;

UBLOX::SolType lastSolution = UBLOX::SOL_INVALID;    
unsigned long nextStatTime = 0;
unsigned long nextToFTime = 0;
unsigned long statIdleDuration = 0; // seconds
unsigned long statChargeDuration = 0; // seconds
unsigned long statMowDurationInvalid = 0; // seconds
unsigned long statMowDuration = 0; // seconds
unsigned long statMowDurationFloat = 0; // seconds
unsigned long statMowDurationFix = 0; // seconds
unsigned long statMowFloatToFixRecoveries = 0; // counter
unsigned long statMowInvalidRecoveries = 0; // counter
unsigned long statImuRecoveries = 0; // counter
unsigned long statMowObstacles = 0 ; // counter
unsigned long statMowBumperCounter = 0; 
unsigned long statMowSonarCounter = 0;
unsigned long statMowLiftCounter = 0;
unsigned long statMowGPSMotionTimeoutCounter = 0;
unsigned long statGPSJumps = 0; // counter
float statTempMin = 9999; 
float statTempMax = -9999; 
float statMowMaxDgpsAge = 0; // seconds
float statMowDistanceTraveled = 0; // meter

double stateCRC = 0;

float lastPosN = 0;
float lastPosE = 0;

unsigned long linearMotionStartTime = 0;
unsigned long bumperDeadTime = 0;
unsigned long sonarDeadTime = 0;
unsigned long driveReverseStopTime = 0;
unsigned long nextControlTime = 0;
unsigned long lastComputeTime = 0;

unsigned long nextImuTime = 0;
unsigned long nextTempTime = 0;
unsigned long imuDataTimeout = 0;
unsigned long nextSaveTime = 0;
bool imuFound = false;
float lastIMUYaw = 0; 

bool wifiFound = false;
WiFiEspServer server(80);
WiFiEspClient client = NULL;
int status = WL_IDLE_STATUS;     // the Wifi radio's status

float dockSignal = 0;
float dockAngularSpeed = 0.1;
bool dockingInitiatedByOperator = true;
bool gpsJump = false;

RunningMedian<unsigned int,3> tofMeasurements;


// must be defined to override default behavior
void watchdogSetup (void){} 


// get free memory
// https://learn.adafruit.com/memories-of-an-arduino/measuring-free-memory
int freeMemory() {
  char top;
  return &top - reinterpret_cast<char*>(sbrk(0));
}

// reset motion measurement
void resetLinearMotionMeasurement()
{
   linearMotionStartTime = millis();  
   bumperDeadTime = linearMotionStartTime + BUMPER_DEAD_TIME;
   //stateGroundSpeed = 1.0;
}

void resetGPSMotionMeasurement(){
  nextGPSMotionCheckTime = millis() + GPS_MOTION_DETECTION_TIMEOUT * 1000;     
}


void dumpState(){
  CONSOLE.print(F("dumpState: "));
  CONSOLE.print(F(" X="));
  CONSOLE.print(stateX);
  CONSOLE.print(F(" Y="));
  CONSOLE.print(stateY);
  CONSOLE.print(F(" delta="));
  CONSOLE.print(stateDelta);
  CONSOLE.print(F(" mapCRC="));
  CONSOLE.print(maps.mapCRC);
  CONSOLE.print(F(" mowPointsIdx="));
  CONSOLE.print(maps.mowPointsIdx);
  CONSOLE.print(F(" dockPointsIdx="));
  CONSOLE.print(maps.freePointsIdx);
  CONSOLE.print(F(" freePointsIdx="));
  CONSOLE.print(maps.freePointsIdx);
  CONSOLE.print(F(" wayMode="));
  CONSOLE.print(maps.wayMode);
  CONSOLE.print(F(" op="));
  CONSOLE.print(stateOp);
  CONSOLE.print(F(" sensor="));
  CONSOLE.print(stateSensor);
  CONSOLE.print(F(" sonar.enabled="));
  CONSOLE.print(sonar.enabled);
  CONSOLE.print(F(" fixTimeout="));
  CONSOLE.print(fixTimeout);
  CONSOLE.print(F(" absolutePosSource="));
  CONSOLE.print(absolutePosSource);
  CONSOLE.print(F(" lon="));
  CONSOLE.print(absolutePosSourceLon);
  CONSOLE.print(F(" lat="));
  CONSOLE.println(absolutePosSourceLat);
}

double calcStateCRC(){
 return (stateOp *10 + maps.mowPointsIdx + maps.dockPointsIdx + maps.freePointsIdx + ((byte)maps.wayMode) 
   + sonar.enabled + fixTimeout 
   + ((byte)absolutePosSource) + absolutePosSourceLon + absolutePosSourceLat);
}

bool loadState(){
#if defined(ENABLE_SD_RESUME)
  CONSOLE.println(F("resuming is activated"));
  CONSOLE.print(F("state load... "));
  if (!SD.exists("state.bin")) {
    CONSOLE.println(F("no state file!"));
    return false;
  }
  stateFile = SD.open("state.bin", FILE_READ);
  if (!stateFile){        
    CONSOLE.println(F("ERROR opening file for reading"));
    return false;
  }
  uint32_t marker = 0;
  stateFile.read((uint8_t*)&marker, sizeof(marker));
  maps.mapID = marker & 0x1F;
  if (maps.mapID==0 || maps.mapID > MAX_MAP_ID) maps.mapID==3;
  if ((marker & 0xFFFFffE0) != 0x10001000)
  {
    CONSOLE.print(F("ERROR: invalid marker: "));
    CONSOLE.println(marker, HEX);
    return false;
  }
  long crc = 0;
  stateFile.read((uint8_t*)&crc, sizeof(crc));
  if (crc != maps.mapCRC){
    CONSOLE.print(F("ERROR: non-matching map CRC:"));
    CONSOLE.print(crc);
    CONSOLE.print(F(" expected: "));
    CONSOLE.println(maps.mapCRC);
    return false;
  }
  bool res = true;
  OperationType savedOp;
  res &= (stateFile.read((uint8_t*)&stateX, sizeof(stateX)) != 0);
  res &= (stateFile.read((uint8_t*)&stateY, sizeof(stateY)) != 0);
  res &= (stateFile.read((uint8_t*)&stateDelta, sizeof(stateDelta)) != 0);
  res &= (stateFile.read((uint8_t*)&maps.mowPointsIdx, sizeof(maps.mowPointsIdx)) != 0);
  res &= (stateFile.read((uint8_t*)&maps.dockPointsIdx, sizeof(maps.dockPointsIdx)) != 0);
  res &= (stateFile.read((uint8_t*)&maps.freePointsIdx, sizeof(maps.freePointsIdx)) != 0);
  res &= (stateFile.read((uint8_t*)&maps.wayMode, sizeof(maps.wayMode)) != 0);
  res &= (stateFile.read((uint8_t*)&savedOp, sizeof(savedOp)) != 0);
  res &= (stateFile.read((uint8_t*)&stateSensor, sizeof(stateSensor)) != 0);
  res &= (stateFile.read((uint8_t*)&sonar.enabled, sizeof(sonar.enabled)) != 0);
  res &= (stateFile.read((uint8_t*)&fixTimeout, sizeof(fixTimeout)) != 0);
  res &= (stateFile.read((uint8_t*)&setSpeed, sizeof(setSpeed)) != 0);
  res &= (stateFile.read((uint8_t*)&absolutePosSource, sizeof(absolutePosSource)) != 0);
  res &= (stateFile.read((uint8_t*)&absolutePosSourceLon, sizeof(absolutePosSourceLon)) != 0);
  res &= (stateFile.read((uint8_t*)&absolutePosSourceLat, sizeof(absolutePosSourceLat)) != 0); 
  stateFile.close();  
  CONSOLE.println("ok");
  stateCRC = calcStateCRC();
  dumpState();
  if (getResetCause() == RST_WATCHDOG){
    CONSOLE.println(F("resuming operation due to watchdog trigger"));
    stateOp = savedOp;
    setOperation(stateOp, true, true);
  }
#endif
  return true;
}


bool saveState(){   
  bool res = true;
#if defined(ENABLE_SD_RESUME)
  double crc = calcStateCRC();
  //CONSOLE.print(F("stateCRC="));
  //CONSOLE.print(stateCRC);
  //CONSOLE.print(F(" crc="));
  //CONSOLE.println(crc);
  if (crc == stateCRC) return true;
  stateCRC = crc;
  dumpState();
  CONSOLE.print(F("save state... "));
  stateFile = SD.open("state.bin",  O_WRITE | O_CREAT);
  if (!stateFile){        
    CONSOLE.println(F("ERROR opening file for writing"));
    return false;
  }
  if (maps.mapID==0 || maps.mapID > MAX_MAP_ID) maps.mapID==3;
  uint32_t marker = 0x10001000 | maps.mapID;
  res &= (stateFile.write((uint8_t*)&marker, sizeof(marker)) != 0); 
  res &= (stateFile.write((uint8_t*)&maps.mapCRC, sizeof(maps.mapCRC)) != 0); 

  res &= (stateFile.write((uint8_t*)&stateX, sizeof(stateX)) != 0);
  res &= (stateFile.write((uint8_t*)&stateY, sizeof(stateY)) != 0);
  res &= (stateFile.write((uint8_t*)&stateDelta, sizeof(stateDelta)) != 0);
  res &= (stateFile.write((uint8_t*)&maps.mowPointsIdx, sizeof(maps.mowPointsIdx)) != 0);
  res &= (stateFile.write((uint8_t*)&maps.dockPointsIdx, sizeof(maps.dockPointsIdx)) != 0);
  res &= (stateFile.write((uint8_t*)&maps.freePointsIdx, sizeof(maps.freePointsIdx)) != 0);
  res &= (stateFile.write((uint8_t*)&maps.wayMode, sizeof(maps.wayMode)) != 0);
  res &= (stateFile.write((uint8_t*)&stateOp, sizeof(stateOp)) != 0);
  res &= (stateFile.write((uint8_t*)&stateSensor, sizeof(stateSensor)) != 0);
  res &= (stateFile.write((uint8_t*)&sonar.enabled, sizeof(sonar.enabled)) != 0);
  res &= (stateFile.write((uint8_t*)&fixTimeout, sizeof(fixTimeout)) != 0);
  res &= (stateFile.write((uint8_t*)&setSpeed, sizeof(setSpeed)) != 0);
  res &= (stateFile.write((uint8_t*)&absolutePosSource, sizeof(absolutePosSource)) != 0);
  res &= (stateFile.write((uint8_t*)&absolutePosSourceLon, sizeof(absolutePosSourceLon)) != 0);
  res &= (stateFile.write((uint8_t*)&absolutePosSourceLat, sizeof(absolutePosSourceLat)) != 0);
  if (res){
    CONSOLE.println("ok");
  } else {
    CONSOLE.println(F("ERROR saving state"));
  }
  stateFile.flush();
  stateFile.close();
#endif
  return res; 
}


void sensorTest(){
  CONSOLE.println(F("testing sensors for 60 seconds..."));
  unsigned long stopTime = millis() + 60000;  
  unsigned long nextMeasureTime = 0;
  while (millis() < stopTime){
    sonar.run();
    bumper.run();
    if (millis() > nextMeasureTime){
      nextMeasureTime = millis() + 1000;      
      if (SONAR_ENABLE){
        CONSOLE.print(F("sonar (enabled,left,center,right,triggered): "));
        CONSOLE.print(sonar.enabled);
        CONSOLE.print("\t");
        CONSOLE.print(sonar.distanceLeft);
        CONSOLE.print("\t");
        CONSOLE.print(sonar.distanceCenter);
        CONSOLE.print("\t");
        CONSOLE.print(sonar.distanceRight);
        CONSOLE.print("\t");
        CONSOLE.print(((int)sonar.obstacle()));
        CONSOLE.print("\t");
      }
      if (TOF_ENABLE){   
        CONSOLE.print(F("ToF (dist): "));
        int v = tof.readRangeContinuousMillimeters();        
        if (!tof.timeoutOccurred()) {     
          CONSOLE.print(v/10);
        }
        CONSOLE.print("\t");
      }    
      if (cfgBumperEnable){
        CONSOLE.print(F("bumper (triggered): "));
        CONSOLE.print(((int)bumper.obstacle()));
        CONSOLE.print("\t");
       
      } 
      CONSOLE.println();  
      watchdogReset();
      robotDriver.run();   
    }
  }
  CONSOLE.println(F("end of sensor test - please ignore any IMU/GPS errors"));
}

#if 0
static void checkWiFi(int baud)
{
  CONSOLE.print(F("Trying WIFI Baudrate:")); CONSOLE.println(baud);
  WIFI.begin(baud); 
  WIFI.print(F("AT\r\n"));  
  delay(1000);  //HB 500
  String res = "";  
  while (WIFI.available()){
    char ch = WIFI.read();    
    res += ch;
  }
  if (res.indexOf("OK") == -1){
    CONSOLE.print(F("WIFI (ESP8266) not found! If the problem persist, you may need to flash your ESP to firmware 2.2.1  RESULT:")); CONSOLE.println(res);
    return;
  }    
  CONSOLE.println(F("Wifi Found!"));
}
#endif

void startWIFI()
{
   const char *ssid = simulationFlag ? WIFI_SSID_HOME : WIFI_SSID;    // your network SSID (name)
   const char *pass = simulationFlag ? WIFI_PASS_HOME : WIFI_PASS;    // your network password
   bool tryHomeFirstFlag = simulationFlag;

   WIFI.begin(WIFI_BAUDRATE); 
   WIFI.print(F("AT\r\n"));  
   delay(500);
   String res = "";  
   while (WIFI.available())
   {
     char ch = WIFI.read();    
     res += ch;
   }
   if (res.indexOf("OK") == -1)
   {
      CONSOLE.println(F("WIFI (ESP8266) not found! If the problem persist, you may need to flash your ESP to firmware 2.2.1")); 
      return;
   }    
   CONSOLE.println(F("Wifi Found!"));
   WiFi.init(&WIFI);  
   if (WiFi.status() == WL_NO_SHIELD) 
   {
      CONSOLE.println(F("ERROR: WiFi not present"));       
   } 
   else 
   {
      wifiFound = true;
      CONSOLE.println(F("WiFi found!"));       
      if (START_AP)
      {
         CONSOLE.print(F("Attempting to start AP "));  
         CONSOLE.println(ssid);
         // uncomment these two lines if you want to set the IP address of the AP
         #ifdef WIFI_IP  
            IPAddress localIp(WIFI_IP);
            WiFi.configAP(localIp);  
         #endif            
         // start access point
         status = WiFi.beginAP(ssid, 10, pass, ENC_TYPE_WPA2_PSK);         
     } 
     else 
     {
         //while ( status != WL_CONNECTED) 
         while (true)
         {
            if (tryHomeFirstFlag)
            {
               watchdogReset();
               WiFi.disconnect();
               delay(500);
               watchdogReset();
               CONSOLE.print(F("Attempting to connect to WPA SSID: "));
               CONSOLE.println(WIFI_SSID_HOME);      
               status = WiFi.begin(WIFI_SSID_HOME, WIFI_PASS_HOME);
               if (status == WL_CONNECTED)
               {
                  sim.homeFlag = true;
                  break;
               }
            }
            tryHomeFirstFlag = true;
            watchdogReset();
            WiFi.disconnect();
            delay(500);
            watchdogReset();
            CONSOLE.print(F("Attempting to connect to WPA SSID: "));
            CONSOLE.println(WIFI_SSID);      
            status = WiFi.begin(WIFI_SSID, WIFI_PASS);
            if (status == WL_CONNECTED)
            {
               sim.homeFlag = false;
               break;
            }
 
            #ifdef WIFI_IP  
              IPAddress localIp(WIFI_IP);
              WiFi.config(localIp);  
            #endif
         }    
      }        
#if defined(ENABLE_UDP)
      udpSerial.beginUDP();  
#endif    
      CONSOLE.print(F("You're connected with SSID="));    
      CONSOLE.print(WiFi.SSID());
      CONSOLE.print(F(" and IP="));        
      IPAddress ip = WiFi.localIP();    
      CONSOLE.println(ip);   
      if (ENABLE_SERVER)
      {
         server.begin();
      }
   }    
}


// https://learn.sparkfun.com/tutorials/9dof-razor-imu-m0-hookup-guide#using-the-mpu-9250-dmp-arduino-library
// start IMU sensor and calibrate
bool startIMU(bool forceIMU){    
  // detect MPU9250
  uint8_t data = 0;
  int counter = 0;  
  while ((forceIMU) || (counter < 1)){          
     I2CreadFrom(0x69, 0x75, 1, &data, 1); // whoami register
     CONSOLE.print(F("MPU ID=0x"));
     CONSOLE.println(data, HEX);     
     #if defined MPU6050 || defined MPU9150      
       if (data == 0x68) {
         CONSOLE.println(F("MPU6050/9150 found"));
         imuFound = true;
         break;
       }
     #endif
     #if defined MPU9250 
       if (data == 0x73) {
         CONSOLE.println(F("MPU9255 found"));
         imuFound = true;
         break;
       } else if (data == 0x71) {
         CONSOLE.println(F("MPU9250 found"));
         imuFound = true;
         break;
       }
     #endif
     CONSOLE.println(F("MPU6050/9150/9250/9255 not found - Did you connect AD0 to 3.3v and choose it in config.h?"));          
     I2Creset();  
     Wire.begin();    
     #ifdef I2C_SPEED
       Wire.setClock(I2C_SPEED);   
     #endif
     counter++;
     if (counter > 5){    
       // no I2C recovery possible - this should not happen (I2C module error)
       CONSOLE.println(F("ERROR IMU not found"));
       stateSensor = SENS_IMU_TIMEOUT;
       setOperation(OP_ERROR);      
       //buzzer.sound(SND_STUCK, true);            
       return false;
     }
     watchdogReset();          
  }  
  if (!imuFound) return false;  
  counter = 0;  
  while (true){    
    if (imu.begin() == INV_SUCCESS) break;
    CONSOLE.print(F("Unable to communicate with IMU."));
    CONSOLE.print(F("Check connections, and try again."));
    CONSOLE.println();
    delay(1000);    
    counter++;
    if (counter > 5){
      stateSensor = SENS_IMU_TIMEOUT;
      setOperation(OP_ERROR);      
      //buzzer.sound(SND_STUCK, true);            
      return false;
    }
    watchdogReset();     
  }     
  //imu.setAccelFSR(2);
	       
  imu.dmpBegin(DMP_FEATURE_6X_LP_QUAT  // Enable 6-axis quat
               |  DMP_FEATURE_GYRO_CAL // Use gyro calibration
             //  | DMP_FEATURE_SEND_RAW_ACCEL
              , 5); // Set DMP FIFO rate to 5 Hz
  // DMP_FEATURE_LP_QUAT can also be used. It uses the 
  // accelerometer in low-power mode to estimate quat's.
  // DMP_FEATURE_LP_QUAT and 6X_LP_QUAT are mutually exclusive    
  //imu.dmpSetOrientation(orientationMatrix);
  imuIsCalibrating = true;   
  nextImuCalibrationSecond = millis() + 1000;
  imuCalibrationSeconds = 0;
  return true;
}


// read IMU sensor (and restart if required)
// I2C recovery: It can be minutes or hours, then there's an I2C error (probably due an spike on the 
// SCL/SDA lines) and the I2C bus on the pcb1.3 (and the arduino library) hangs and communication is delayed. 
// We check if the communication is significantly (10ms instead of 1ms) delayed, if so we restart the I2C 
// bus (by clocking out any garbage on the I2C bus) and then restarting the IMU module.
// https://learn.sparkfun.com/tutorials/9dof-razor-imu-m0-hookup-guide/using-the-mpu-9250-dmp-arduino-library
void readIMU(){
  if (!imuFound) return;
  // Check for new data in the FIFO  
  unsigned long startTime = millis();
  bool avail = (imu.fifoAvailable() > 0);
  // check time for I2C access : if too long, there's an I2C issue and we need to restart I2C bus...
  unsigned long duration = millis() - startTime;    
  //CONSOLE.print(F("duration:"));
  //CONSOLE.println(duration);  
  if ((duration > 10) || (millis() > imuDataTimeout)) {
    setOperation(OP_ERROR);
    if (millis() > imuDataTimeout){
      CONSOLE.println(F("=ERROR IMU data timeout"));  
    } else {
      CONSOLE.print(F("=ERROR IMU timeout: "));
      CONSOLE.println(duration);          
    }
    stateSensor = SENS_IMU_TIMEOUT;
    motor.stopImmediately(true);    
    statImuRecoveries++;            
    if (!startIMU(true)){ // restart I2C bus
      return;
    }    
    return;
  } 
  
  if (avail) {        
    //CONSOLE.println(F("fifoAvailable"));
    // Use dmpUpdateFifo to update the ax, gx, mx, etc. values
    if ( imu.dmpUpdateFifo() == INV_SUCCESS)
    {      
      // computeEulerAngles can be used -- after updating the
      // quaternion values -- to estimate roll, pitch, and yaw
      //  toEulerianAngle(imu.calcQuat(imu.qw), imu.calcQuat(imu.qx), imu.calcQuat(imu.qy), imu.calcQuat(imu.qz), imu.roll, imu.pitch, imu.yaw);
      imu.computeEulerAngles(false);   
      if (motorDriver.reverseDrive ? !motorDriver.frontWheelDrive : motorDriver.frontWheelDrive)
      {
         imu.yaw = imu.yaw>0 ? imu.yaw-PI : imu.yaw+PI;
         imu.pitch = -imu.pitch;
         imu.roll = -imu.roll;
      }
      //CONSOLE.print(imu.ax);
      //CONSOLE.print(",");
      //CONSOLE.print(imu.ay);
      //CONSOLE.print(",");
      //CONSOLE.println(imu.az);
#if 0
      static const int maxPitchCnt = 4;
      static int pitchCnt = 0;
      static int pitchSum;
      pitchSum += (int) (scalePI(imu.pitch)*180.0/PI);
      if (++pitchCnt == maxPitchCnt)
      {
         CONSOLE.print(F("Steigung: "));
         CONSOLE.print(pitchSum/maxPitchCnt);
         CONSOLE.println("°");
         pitchCnt = 0;
         pitchSum = 0;
      }
#endif
      float deltaPitch = imu.pitch - statePitch;
      statePitch = imu.pitch;
      if (cfgEnableTiltDetection)
      {
         rollChange += (imu.roll-stateRoll);
         pitchChange += deltaPitch;
         rollChange = 0.95 * rollChange;
         pitchChange = 0.95 * pitchChange;
         stateRoll = imu.roll;        
         //CONSOLE.print(rollChange/PI*180.0);
         //CONSOLE.print(",");
         //CONSOLE.println(pitchChange/PI*180.0);
         if ( (fabs(scalePI(imu.roll)) > 60.0/180.0*PI) || (fabs(scalePI(imu.pitch)) > 100.0/180.0*PI)
              || (fabs(rollChange) > 30.0/180.0*PI) || (fabs(pitchChange) > 60.0/180.0*PI)   )  
         {
            CONSOLE.println(F("=ERROR IMU tilt"));
            CONSOLE.print(F("imu ypr="));
            CONSOLE.print(imu.yaw/PI*180.0);
            CONSOLE.print(",");
            CONSOLE.print(imu.pitch/PI*180.0);
            CONSOLE.print(",");
            CONSOLE.print(imu.roll/PI*180.0);
            CONSOLE.print(F(" rollChange="));
            CONSOLE.print(rollChange/PI*180.0);
            CONSOLE.print(F(" pitchChange="));
            CONSOLE.println(pitchChange/PI*180.0);
            stateSensor = SENS_IMU_TILT;
            setOperation(OP_ERROR);
         }           
      }
      motor.robotPitch = scalePI(imu.pitch);
      maxPitch = max(maxPitch, motor.robotPitch);
      //if (upHillDetectionFlag)
      //{
      //   static const float pitchHiThreshold = 10.0 / 180.0 *PI;
      //   static const float pitchLoThreshold =  5.0 / 180.0 *PI;
      //   bool lastupHillFlag = upHillFlag;
      //   upHillFlag = motor.robotPitch > (upHillFlag ? pitchLoThreshold : pitchHiThreshold);    //HB Hysterese
      //   if (lastupHillFlag != upHillFlag) 
      //   {
      //      CONSOLE.print(F("=Steigung="));
      //      CONSOLE.println(upHillFlag);
      //   }
      //}
      //else upHillFlag = false;

      // Kippschutz
      static const float pitchThreshold = 0;  // 2. / 180. * PI;	// 2 degrees
      bool frontFlag = motorDriver.reverseDrive ? !motorDriver.frontWheelDrive : motorDriver.frontWheelDrive;
      motor.deltaPwm = deltaPitch < 0 || imu.pitch < pitchThreshold || frontFlag ? 0 : deltaPitch * cfgPitchPwmFactor;

      imu.yaw = scalePI(imu.yaw);
      //CONSOLE.println(imu.yaw / PI * 180.0);
      lastIMUYaw = scalePI(lastIMUYaw);
      lastIMUYaw = scalePIangles(lastIMUYaw, imu.yaw);
      stateDeltaIMU = -scalePI ( distancePI(imu.yaw, lastIMUYaw) );  
      //CONSOLE.print(imu.yaw);
      //CONSOLE.print(",");
      //CONSOLE.print(stateDeltaIMU/PI*180.0);
      //CONSOLE.println();
      lastIMUYaw = imu.yaw;      
      imuDataTimeout = millis() + 10000;
    }     
  }     
}

// check for RTC module
bool checkAT24C32() {
  byte b = 0;
  int r = 0;
  unsigned int address = 0;
  Wire.beginTransmission(AT24C32_ADDRESS);
  if (Wire.endTransmission() == 0) {
    Wire.beginTransmission(AT24C32_ADDRESS);
    Wire.write(address >> 8);
    Wire.write(address & 0xFF);
    if (Wire.endTransmission() == 0) {
      Wire.requestFrom(AT24C32_ADDRESS, 1);
      while (Wire.available() > 0 && r < 1) {        
        b = (byte)Wire.read();        
        r++;
      }
    }
  }
  return (r == 1);
}


// robot start routine
void start()
{    
  pinMan.begin();       
  // keep battery switched ON
  pinMode(pinBatterySwitch, OUTPUT);    
  pinMode(pinDockingReflector, INPUT);
  digitalWrite(pinBatterySwitch, HIGH);         
  pinMode(pinButton, INPUT_PULLUP);
  buzzer.begin();      
  CONSOLE.begin(CONSOLE_BAUDRATE);  


  CONSOLE.println(VER);

#if defined(ENABLE_RASPI_SHUTDOWN)
    CONSOLE.println(F("RASPI_SHUTDOWN enabled"));
    pinMode(RASPI_SHUTDOWN_REQ_N, OUTPUT);    
    pinMode(RASPI_SHUTDOWN_ACK_N, INPUT_PULLUP);
    digitalWrite(RASPI_SHUTDOWN_REQ_N, HIGH);         
#endif

  Wire.begin();      
  analogReadResolution(12);  // configure ADC 12 bit resolution
  //unsigned long timeout = millis() + 2000;
  //while (millis() < timeout)
  //{
  //  if (!checkAT24C32())
  //  {
  //    CONSOLE.println(F("PCB not powered ON or RTC module missing"));      
  //    simulationFlag = true;
  //    CONSOLE.println(F("Simulation mode enabled!"));
  //    I2Creset();
  //    Wire.begin();    
  //    #ifdef I2C_SPEED
  //      Wire.setClock(I2C_SPEED);     
  //    #endif
  //  } else break;
  //}  
  //delay(1500);
  if (ReadAT24C32(0) == 56)
  {
     simulationFlag = true;
     CONSOLE.println(F("Simulation mode enabled!"));
  }


#if defined(ENABLE_SD)
  if (SD.begin(SDCARD_SS_PIN))
  {
     CONSOLE.println(F("SD card found!"));
     SdCardDateTimeInit();
#if defined(ENABLE_SD_LOG)        
     sdSerial.beginSD();
#endif
  }
  else
  {
     CONSOLE.println(F("no SD card found"));
  }
#endif 
  startWIFI();
  outputConsoleInit();

  logResetCause();
  
  CONSOLE.println(VER);          
  CONSOLE.print(F("compiled for: "));
  CONSOLE.println(BOARD);
  
  batteryDriver.begin();
  robotDriver.begin();
  motorDriver.begin();  
  battery.begin();      
  stopButton.begin();

  bleConfig.run();   
  BLE.println(VER);  
    
  motor.begin();
  sonar.begin();
  bumper.begin();

#ifdef MOONLIGHT_ENABLE_FIX_DISPLAY
  fixDisplay.begin();
#endif
  
  if (TOF_ENABLE){
    tof.setTimeout(500);
    if (!tof.init())
    {
      CONSOLE.println(F("Failed to detect and initialize tof sensor"));
      delay(1000);
    }
    tof.startContinuous(100);
  }        
  
  CONSOLE.print(F("SERIAL_BUFFER_SIZE="));
  CONSOLE.print(SERIAL_BUFFER_SIZE);
  CONSOLE.println(F(" (increase if you experience GPS checksum errors)"));
  CONSOLE.println(F("-----------------------------------------------------"));
  CONSOLE.println(F("NOTE: if you experience GPS checksum errors, try to increase UART FIFO size:"));
  CONSOLE.println(F("1. Arduino IDE->File->Preferences->Click on 'preferences.txt' at the bottom"));
  CONSOLE.println(F("2. Locate file 'packages/arduino/hardware/sam/xxxxx/cores/arduino/RingBuffer.h"));
  CONSOLE.println(F("   for Grand Central M4 'packages/adafruit/hardware/samd/xxxxx/cores/arduino/RingBuffer.h"));  
  CONSOLE.println(F("change:     #define SERIAL_BUFFER_SIZE 128     into into:     #define SERIAL_BUFFER_SIZE 1024"));
  CONSOLE.println(F("-----------------------------------------------------"));
  
  gps.begin();   
  maps.begin();      
  //maps.clipperTest();
  
  if (!simulationFlag) myHumidity.begin();    

  // initialize ESP module
  //HB startWIFI();  moved up

  rcmodel.begin();  
  
  watchdogEnable(10000L);   // 10 seconds  
  
  startIMU(false);        
  
  buzzer.sound(SND_READY);  
  battery.resetIdle();        
  loadState();
}


// calculate statistics
void calcStats(){
  if (millis() >= nextStatTime){
    nextStatTime = millis() + 1000;
    switch (stateOp){
      case OP_IDLE:
        statIdleDuration++;
        break;
      case OP_MOW:      
        statMowDuration++;
        if (gps.solution == UBLOX::SOL_FIXED) statMowDurationFix++;
          else if (gps.solution == UBLOX::SOL_FLOAT) statMowDurationFloat++;   
          else if (gps.solution == UBLOX::SOL_INVALID) statMowDurationInvalid++;
        if (gps.solution != lastSolution){      
          if ((lastSolution == UBLOX::SOL_FLOAT) && (gps.solution == UBLOX::SOL_FIXED)) statMowFloatToFixRecoveries++;
          if (lastSolution == UBLOX::SOL_INVALID) statMowInvalidRecoveries++;
          lastSolution = gps.solution;
        } 
        statMowMaxDgpsAge = max(statMowMaxDgpsAge, (millis() - gps.dgpsAge)/1000.0);        
        break;
      case OP_CHARGE:
        statChargeDuration++;
        break;
    }     
  }   
}


// compute robot state (x,y,delta)
// uses complementary filter ( https://gunjanpatel.wordpress.com/2016/07/07/complementary-filter-design/ )
// to fusion GPS heading (long-term) and IMU heading (short-term)
// with IMU: heading (stateDelta) is computed by gyro (stateDeltaIMU)
// without IMU: heading (stateDelta) is computed by odometry (deltaOdometry)
void computeRobotState()
{
  static int lastGpsSolution = UBLOX::SOL_INVALID;
  if (sim.ComputeRobotState()) return;

  long leftDelta = motor.motorLeftTicks-stateLeftTicks;
  long rightDelta = motor.motorRightTicks-stateRightTicks;  
  stateLeftTicks = motor.motorLeftTicks;
  stateRightTicks = motor.motorRightTicks;    
    
  float distLeft = ((float)leftDelta) / ((float)motor.ticksPerCm);
  float distRight = ((float)rightDelta) / ((float)motor.ticksPerCm);  
  float distOdometry = (distLeft + distRight) / 2.0;
  float deltaOdometry = -(distLeft - distRight) / motor.wheelBaseCm;    
  
  float posN = 0;
  float posE = 0;
  if (absolutePosSource){
    relativeLL(absolutePosSourceLat, absolutePosSourceLon, gps.lat, gps.lon, posN, posE);    
  } else {
    posN = gps.relPosN;  
    posE = gps.relPosE;     
  }   
  
  if (fabs(motor.linearSpeedSet) < 0.001){       
    resetLastPos = true;
  }
  
#define USE_SUNRAY_FIX_OR_FLOAT 1
#if USE_SUNRAY_FIX_OR_FLOAT
  if ((gps.solutionAvail) && ((gps.solution == UBLOX::SOL_FIXED) || (gps.solution == UBLOX::SOL_FLOAT))  )
#else
  if ((gps.solutionAvail) && gps.solution == UBLOX::SOL_FIXED)
#endif
  {
      gps.solutionAvail = false;        
      bool useGps = maps.useGpsSolution(stateX, stateY);
      // to get an accurate delta estimation, both current and last GPS solutions must be SOL_FIXED.
      bool useGpsForDeltaEstimation = gps.solution == UBLOX::SOL_FIXED && lastGpsSolution == UBLOX::SOL_FIXED;
      if (gps.solution == UBLOX::SOL_FLOAT && maps.useGPSfloatForDeltaEstimation) useGpsForDeltaEstimation = true;
      lastGpsSolution = gps.solution;
      
      stateGroundSpeed = 0.9 * stateGroundSpeed + 0.1 * abs(gps.groundSpeed);    
      //CONSOLE.println(stateGroundSpeed);
      float distGPS = sqrt( sq(posN-lastPosN)+sq(posE-lastPosE) );
#if MOONLIGHT_GPS_JUMP
      // Detect jumps relative to current robot position (stateX/stateY)
      float distGpsState = sqrt( sq(posN-stateY)+sq(posE-stateX) );
      const float DIST_GPS_STATE = 2.0;     //HB in meter
      if (distGpsState > DIST_GPS_STATE)
      {
             //gpsJump = true;
             //statGPSJumps++;
             CONSOLE.print(F("ML GPS jump: "));
             CONSOLE.println(distGpsState);
      } 
#endif
      const float DIST_GPS_JUMP = 0.3;     //HB in meter
      if ((distGPS > DIST_GPS_JUMP) || (resetLastPos))
      {
#define ENABLE_GPS_JUMP_DETECTION 0     //HB
#if ENABLE_GPS_JUMP_DETECTION
         if (distGPS > DIST_GPS_JUMP) {
            gpsJump = true;
            statGPSJumps++;
            CONSOLE.print(F("GPS jump: "));
            CONSOLE.println(distGPS);
         }
#endif
          resetLastPos = false;
          lastPosN = posN;
          lastPosE = posE;
      } 
      else if (distGPS > 0.1) 
      {       
          if ( (fabs(motor.linearSpeedSet) > 0) && (fabs(motor.angularSpeedSet) /PI *180.0 < 45) ) {  
            stateDeltaGPS = scalePI(atan2(posN-lastPosN, posE-lastPosE));    
            if (motor.linearSpeedSet < 0) stateDeltaGPS = scalePI(stateDeltaGPS + PI); // consider if driving reverse
            //stateDeltaGPS = scalePI(2*PI-gps.heading+PI/2);
            float diffDelta = distancePI(stateDelta, stateDeltaGPS);                 
            if (useGps && useGpsForDeltaEstimation)
            {   // allows planner to use float solution?         
              if (fabs(diffDelta/PI*180) > 45){ // IMU-based heading too far away => use GPS heading
                stateDelta = stateDeltaGPS;
                stateDeltaIMU = 0;
              } else {
                // delta fusion (complementary filter, see above comment)
                stateDeltaGPS = scalePIangles(stateDeltaGPS, stateDelta);
                stateDelta = scalePI(fusionPI(0.9, stateDelta, stateDeltaGPS));               
              }            
            }
          }
          lastPosN = posN;
          lastPosE = posE;
      } 
      if (gps.solution == UBLOX::SOL_FIXED && useGps)
      {
          // fix
          lastFixTime = millis();
          stateX = posE;
          stateY = posN;        
      } 
      else 
      {
          // float
          if (maps.useGPSfloatForPosEstimation && useGps){ // allows planner to use float solution?
            stateX = posE;
            stateY = posN;              
          }
      }
  } 
  
  // odometry
  stateX += distOdometry/100.0 * cos(stateDelta);
  stateY += distOdometry/100.0 * sin(stateDelta);        
  if (stateOp == OP_MOW) statMowDistanceTraveled += distOdometry/100.0;
  
  if ((imuFound) && (maps.useIMU)) {
    // IMU available and should be used by planner
    stateDelta = scalePI(stateDelta + stateDeltaIMU );      
  } else {
    // odometry
    stateDelta = scalePI(stateDelta + deltaOdometry);  
  }
  //CONSOLE.println(stateDelta / PI * 180.0);
  stateDeltaIMU = 0;
}


// should robot move?
bool robotShouldMove(){
   bool shouldMoveFlag;
   if (sim.RobotShouldMove(shouldMoveFlag)) return shouldMoveFlag;
   return ( (fabs(motor.linearSpeedSet) > 0.001) ||  (fabs(motor.angularSpeedSet) > 0.001) );
}


void triggerObstacle(bool isBumperWithSwitch)
{
    statMowObstacles++;
    //CONSOLE.print(F("=triggerObstacle "));
    //CONSOLE.println(statMowObstacles);
    //if ((OBSTACLE_AVOIDANCE) && (maps.wayMode != WAY_DOCK))

    // handle obstacle maps
    if (isBumperWithSwitch)
    {
        if (maps.obstacle()) return;
    }

    // handle other map types
    if (cfgBumperEnable && maps.wayMode == WAY_MOW)
    {
        driveReverseStopTime = millis() + 3000;
    }
    //else 
    //{ 
    //    stateSensor = SENS_OBSTACLE;
    //    setOperation(OP_ERROR);
    //    buzzer.sound(SND_ERROR, true);        
    //}
}


// detect sensor malfunction
void detectSensorMalfunction(){  
  if (ENABLE_ODOMETRY_ERROR_DETECTION){
    if (motor.odometryError){
      CONSOLE.println(F("odometry error!"));    
      stateSensor = SENS_ODOMETRY_ERROR;
      setOperation(OP_ERROR);
      buzzer.sound(SND_ERROR, true); 
      return;      
    }
  }
  if (ENABLE_OVERLOAD_DETECTION){
    if (motor.motorOverloadDuration > 20000){
      CONSOLE.println(F("overload!"));    
      stateSensor = SENS_OVERLOAD;
      setOperation(OP_ERROR);
      buzzer.sound(SND_ERROR, true);        
      return;
    }  
  }
  if (ENABLE_FAULT_DETECTION){
    if (motor.motorError){
      motor.motorError = false;
      CONSOLE.println(F("motor error!"));
      stateSensor = SENS_MOTOR_ERROR;
      setOperation(OP_ERROR);
      buzzer.sound(SND_ERROR, true);       
      return;       
    }  
  }
}


// detect obstacle (bumper, sonar, ToF) 
void detectObstacle()
{  
   if (!robotShouldMove()) return;  
   if (TOF_ENABLE)
   {
     if (millis() >= nextToFTime){
       nextToFTime = millis() + 200;
       int v = tof.readRangeContinuousMillimeters();        
       if (!tof.timeoutOccurred()) {     
         tofMeasurements.add(v);        
         float avg = 0;
         if (tofMeasurements.getAverage(avg) == tofMeasurements.OK){
           //CONSOLE.println(avg);
           if (avg < TOF_OBSTACLE_CM * 10){
             CONSOLE.println(F("ToF obstacle!"));
             triggerObstacle();                
             return; 
           }
         }      
       } 
     }    
   }   
   
   //if (cfgBumperEnable)
   {
      if (millis() > bumperDeadTime && bumper.obstacle())
      {  
          bool leftBumperFreeWheel;
          bool rightBumperWithSwitch;
          bumper.getTriggeredBumper(leftBumperFreeWheel, rightBumperWithSwitch);

          bumperDeadTime = millis() + BUMPER_DEAD_TIME;

          // Check trigger from FreeWheelSensor
          if (leftBumperFreeWheel && cfgBumperEnable)
          {
              CONSOLE.println(F("=ERROR BumperFreeWheel triggered"));
              stateSensor = SENS_BUMPER;
              setOperation(OP_ERROR);
              return;
          }

          // Check trigger from BumperWithSwitch
          if (rightBumperWithSwitch)
          {
              static const bool isBumperWithSwitch = true;
              statMowBumperCounter++;
              CONSOLE.print(F("=BumperSwitch obstacle "));
              CONSOLE.println(statMowBumperCounter);
              triggerObstacle(isBumperWithSwitch);
          }
          return;

      }
   }
   if (sonar.enabled && cfgSonarObstacleDist != 0)
   {
       if (millis() > sonarDeadTime && sonar.obstacle() && (maps.wayMode != WAY_DOCK))
       {
           sonarDeadTime = millis() + SONAR_DEAD_TIME;
           statMowSonarCounter++;
           CONSOLE.print(F("=sonar obstacle "));
           CONSOLE.println(statMowSonarCounter);
           triggerObstacle();

           return;
       }        
   }  
   // check if GPS motion (obstacle detection)  
   if (millis() > nextGPSMotionCheckTime)
   {        
     resetGPSMotionMeasurement();  
     if (GPS_MOTION_DETECTION)
     {
         float dX = lastGPSMotionX - stateX;
         float dY = lastGPSMotionY - stateY;
         float delta = sqrt( sq(dX) + sq(dY) );    
         if (delta < 0.05)
         {
             CONSOLE.println(F("=gps no motion => obstacle!"));
             statMowGPSMotionTimeoutCounter++;
             triggerObstacle();
             return;
         }
     }
     lastGPSMotionX = stateX;      
     lastGPSMotionY = stateY;      
   }    
}


// robot main loop
void run()
{  
   robotDriver.run();
   buzzer.run();
   stopButton.run();
   battery.run();
   batteryDriver.run();
   motorDriver.run();
   //------------------------------------------------------------------------------------------------- 
   // Handle IMU & motor
   //------------------------------------------------------------------------------------------------- 
   if (millis() > nextImuTime)
   {
       nextImuTime = millis() + 50;   //HB was 150;
       //imu.resetFifo();    
       if (imuIsCalibrating) {
           motor.stopImmediately(true);
           if (millis() > nextImuCalibrationSecond) {
               nextImuCalibrationSecond = millis() + 1000;
               imuCalibrationSeconds++;
               CONSOLE.print(F("IMU gyro calibration (robot must be static)... "));
               CONSOLE.println(imuCalibrationSeconds);
               buzzer.sound(SND_PROGRESS, true);
               if (imuCalibrationSeconds >= 9) {
                   imuIsCalibrating = false;
                   CONSOLE.println();
                   lastIMUYaw = 0;
                   imu.resetFifo();
                   imuDataTimeout = millis() + 10000;
               }
           }
       }
       else {
           readIMU();
       }
       motor.run();
   }
   sonar.run();
   maps.run();  
#ifdef MOONLIGHT_ENABLE_FIX_DISPLAY
   fixDisplay.run();
#endif
 
   //------------------------------------------------------------------------------------------------- 
   // state saving every 5 sec
   //------------------------------------------------------------------------------------------------- 
   if (millis() >= nextSaveTime)
   {  
      nextSaveTime = millis() + 5000;
      saveState();
   }
   
   //------------------------------------------------------------------------------------------------- 
   // Handle temperature and humidity
   //------------------------------------------------------------------------------------------------- 
   if (millis() > nextTempTime)
   {
      // https://learn.sparkfun.com/tutorials/htu21d-humidity-sensor-hookup-guide
      nextTempTime = millis() + 60000;
      if (simulationFlag)
      {
         stateTemp = 25.0;
         stateHumidity = 50.0;
      }
      else
      {
         stateTemp = myHumidity.readTemperature();
         stateHumidity = myHumidity.readHumidity();
      }
 	   statTempMin = min(statTempMin, stateTemp);
 	   statTempMax = max(statTempMax, stateTemp);
      //CONSOLE.print(F("temp="));
      //CONSOLE.print(stateTemp,1);
      //CONSOLE.print(F("  humidity="));
      //CONSOLE.print(stateHumidity,0);    
      //CONSOLE.print(" ");    
      //logCPUHealth();    
   }

   
   //-------------------------------------------------------------------------------------------------
   // Handle GPS and compute Statistics
   //------------------------------------------------------------------------------------------------- 
   gps.run();
   calcStats();  
   
   //------------------------------------------------------------------------------------------------- 
   // Control robot every 20 ms
   //------------------------------------------------------------------------------------------------- 
   if (millis() >= nextControlTime)
   {        
      nextControlTime = millis() + 20; 
      controlLoops++;    
      
      computeRobotState();
      
      //if (gpsJump)
      //{
      //   // gps jump: restart current operation from new position
      //   CONSOLE.println(F("restarting due to gps jump"));
      //   gpsJump = false;
      //   motor.stopImmediately(true);
      //   setOperation(stateOp, true);    // restart current operation
      //}

      // MOONLIGHT extension: Stop docking immediately in case there is no FIX
      //if (stateOp == OP_DOCK && gps.solution != UBLOX::SOL_FIXED)
      //{
      //   CONSOLE.println(F("Stop docking due to missing FIX"));
      //   motor.stopImmediately(true);
      //   setOperation(OP_ERROR);    // restart current operation
      //}
      
      //-------------------------------------------------------------------------------------------------
      // Handle charging / docking station
      //------------------------------------------------------------------------------------------------- 
      if (battery.chargerConnected() != stateChargerConnected) 
      {    
         stateChargerConnected = battery.chargerConnected(); 
         if (stateChargerConnected)
         {      
           stateChargerConnected = true;
           setOperation(OP_CHARGE);                
         }           
      }     
      if (battery.chargerConnected())
      {
         if ((stateOp == OP_IDLE) || (stateOp == OP_CHARGE))
         {
            maps.setIsDocked(true);               
            // get robot position and yaw from map
            // sensing charging contacts means we are in docking station - we use docking point coordinates to get rid of false fix positions in
            // docking station
            maps.setRobotStatePosToDockingPos(stateX, stateY, stateDelta);                       
         }
         battery.resetIdle();        
      } 
      else 
      {
         if ((stateOp == OP_IDLE) || (stateOp == OP_CHARGE))
         {
            maps.setIsDocked(false);
         }
      }
            
      if (!imuIsCalibrating)
      {       
         //------------------------------------------------------------------------------------------------- 
         // Handle drive reverse to undock
         //------------------------------------------------------------------------------------------------- 
         if (stateOp == OP_UNDOCK) 
         {              
            if (driveReverseStopTime > 0)
            {
               // obstacle avoidance
               motor.setLinearAngularSpeed(-0.2,0);
               if (millis() > driveReverseStopTime)
               {
                  CONSOLE.println(F("=undock complete"));
                  //motor.stopImmediately(false);
                  motor.setLinearAngularSpeed(0.,0.);
                  driveReverseStopTime = 0;
                  setOperation(OP_IDLE);   
               }
            } 
         }
         //------------------------------------------------------------------------------------------------- 
         // Handle drive reverse after obstacle detection
         //------------------------------------------------------------------------------------------------- 
         else if ((stateOp == OP_MOW) ||  (stateOp == OP_DOCK)) 
         {              
            if (driveReverseStopTime > 0)
            {
               // obstacle avoidance
               motor.setLinearAngularSpeed(-0.2,0);
               if (millis() > driveReverseStopTime)
               {
                  CONSOLE.println(F("driveReverseStopTime"));
                  motor.stopImmediately(false);
                  driveReverseStopTime = 0;
                  if (MOONLIGHT_ADD_OBSTACLE_TO_MAP) 
                  {
                     maps.addObstacle(stateX, stateY);
                     Point pt;
                     if (!maps.findObstacleSafeMowPoint(pt))
                     {
                        setOperation(OP_DOCK, true); // dock if no more (valid) mowing points
                     }  else setOperation(stateOp, true);    // continue current operation
                  }
                  else 
                  {
                      maps.skipNextMowingPoint();
                      maps.skipNextMowingPoint();
                      setOperation(stateOp, true);    // continue current operation
                      bumperDeadTime = millis() + BUMPER_DEAD_TIME;
                  }
               }
            } 
            //-------------------------------------------------------------------------------------------------
            // Line tracking
            //-------------------------------------------------------------------------------------------------
            else 
            {          
               trackLine();
               detectSensorMalfunction();
               detectObstacle();       
            }        
            battery.resetIdle();
            if (battery.underVoltage())
            {
               stateSensor = SENS_BAT_UNDERVOLTAGE;
               CONSOLE.println(F("=Low battery Mowing stopped"));
               setOperation(OP_IDLE);
               //buzzer.sound(SND_OVERCURRENT, true);        
            } 
            if (battery.shouldGoHome())
            {
               if (DOCKING_STATION)
               {
                  setOperation(OP_DOCK);
               }
            }
            if (stopButton.triggered())
            {
               CONSOLE.println(F("=stopButton triggered!"));
               stateSensor = SENS_STOP_BUTTON;
               setOperation(OP_IDLE);
            }
         }
         else if (stateOp == OP_CHARGE){      
           if (battery.chargerConnected()){
             if (battery.chargingHasCompleted()){
               if ((DOCKING_STATION) && (!dockingInitiatedByOperator)) {
                 if (maps.mowPointsIdx > 0){  // if mowing not completed yet
                   if (DOCK_AUTO_START) { // automatic continue mowing allowed?
                     setOperation(OP_MOW); // continue mowing
                   }
                 }
               }
             }
           } else {
             setOperation(OP_IDLE);        
           }
         }
      } // !imuIsCalibrating
      if (stopButton.LongKeyPress())
      {
         setOperation(OP_IDLE);
         battery.switchOff();
      }
      rcmodel.run();
   } // robot control every 20 ms
     
   //------------------------------------------------------------------------------------------------- 
   // read serial input (BT/UDP/console)
   //------------------------------------------------------------------------------------------------- 
   processComm();
   outputConsole();       
   watchdogReset();     
}




// set new robot operation
void setOperation(OperationType op, bool allowRepeat, bool initiatedbyOperator){  
  static bool SMOOTH_CURVES_saved = SMOOTH_CURVES_DEFAULT;
  if ((stateOp == op) && (!allowRepeat)) return;  
  if (stateOp == OP_DOCK && op != OP_DOCK) cfgSmoothCurves = SMOOTH_CURVES_saved;
  CONSOLE.print(F("setOperation op="));
  CONSOLE.print(op);
  bool error = false;
  switch (op){
    case OP_IDLE:
      CONSOLE.println(F(" OP_IDLE"));
      dockingInitiatedByOperator = true;
      motor.setLinearAngularSpeed(0,0);
      motor.setMowState(false);
      //HB: reservseDrive might be true in cases of ObstacleMaps!
      motorDriver.reverseDrive = false;
      break;
    case OP_UNDOCK:
      CONSOLE.println(F(" OP_UNDOCK"));
      // drive 6 seconds backwards to undock from charging station
      driveReverseStopTime = millis()+6000;
      break;
    case OP_DOCK:
      // cfgSmoothCurves==false during docking and it is restored after docking is complete
      if (stateOp != OP_DOCK) SMOOTH_CURVES_saved = cfgSmoothCurves;
      cfgSmoothCurves = false;
      CONSOLE.println(F(" OP_DOCK"));
      if (initiatedbyOperator) maps.clearObstacles();
      dockingInitiatedByOperator = initiatedbyOperator;      
      motor.setLinearAngularSpeed(0,0);
      motor.setMowState(false);                
      if (maps.startDocking(stateX, stateY)){       
        if (maps.nextPoint(true)) {
          maps.repeatLastMowingPoint();
          resetGPSMotionMeasurement;
          lastFixTime = millis();                
          maps.setLastTargetPoint(stateX, stateY);        
          stateSensor = SENS_NONE;                  
        } else {
          error = true;
          CONSOLE.println(F("error: no waypoints!"));
          //op = stateOp;                
        }
      } else error = true;
      if (error){
        stateSensor = SENS_MAP_NO_ROUTE;
        op = OP_ERROR;
        motor.setMowState(false);
      }
      break;
    case OP_MOW:      
      CONSOLE.println(F(" OP_MOW"));      
      if (initiatedbyOperator) maps.clearObstacles();
      motor.setLinearAngularSpeed(0,0);
      if (maps.startMowing(stateX, stateY))
      {
         if (maps.nextPoint(true)) 
         {
            resetGPSMotionMeasurement();
            lastFixTime = millis();                
            maps.setLastTargetPoint(stateX, stateY);        
            stateSensor = SENS_NONE;
            motor.setMowState(true);     
         } else {
            error = true;
            CONSOLE.println(F("error: no waypoints!"));
            //op = stateOp;                
         }
      } else error = true;
      if (error){
        stateSensor = SENS_MAP_NO_ROUTE;
        op = OP_ERROR;
        motor.setMowState(false);
      }
      break;
    case OP_CHARGE:
      CONSOLE.println(F(" OP_CHARGE"));
      motor.stopImmediately(true); // do not use PID to get to stop 
      //motor.setLinearAngularSpeed(0,0, false);
      //motor.setMowState(false);     
      break;
    case OP_ERROR:            
      CONSOLE.println(F(" OP_ERROR")); 
      motor.stopImmediately(true); // do not use PID to get to stop 
      //motor.setLinearAngularSpeed(0,0);
      //motor.setMowState(false);      
      break;
  }
  stateOp = op;  
  saveState();
}


char *Sprintf(const char *format, ...)
{
   static char text[128];
   va_list args;
   va_start(args, format);
   vsnprintf(text, 128, format, args);
   va_end(args);
   return text;
}

