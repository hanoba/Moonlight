#include "comm.h"
#include "config.h"
#include "robot.h"
#include "reset.h"
#include "src/esp/WiFiEsp.h"
#include "file_cmds.h"
#include "sim.h"
#include "rtc.h"
#include "rcmodel.h"

static void processCmd(bool checkCrc, String cmd);

unsigned long nextInfoTime = 0;
bool triggerWatchdog = false;

String cmd;
String cmdResponse;

// use a ring buffer to increase speed and reduce memory allocation
ERingBuffer buf(8);
int reqCount = 0;                // number of requests received
unsigned long stopClientTime = 0;
float statControlCycleTime = 0;
float statMaxControlCycleTime = 0;


//HB New map control
//static uint8_t currentMapIndex = 0;
//static bool writeMapFlag = false;
bool cfgSmoothCurves = SMOOTH_CURVES_DEFAULT;
bool cfgEnablePathFinder = ENABLE_PATH_FINDER_DEFAULT;
bool cfgMoonlightLineTracking = MOONLIGHT_LINE_TRACKING_DEFAULT;
bool cfgBumperEnable = BUMPER_ENABLE_DEFAULT;
bool cfgEnableTiltDetection = ENABLE_TILT_DETECTION_DEFAULT;
int cfgSonarObstacleDist = 0;  //HB cm (0=disabled) was 10
int cfgSonarNearDist = 0;      //HB cm (0=disabled) was 60
float cfgSonarNearSpeed = 0.2;
//float cfgDeltaPitchPwmFactor = 0.5*255 / (PI/2);	   // Kippschutz: Factor to convert from delta pitch (in rad) to duty cycle (255=100%)
//float cfgPitchPwmFactor = 255. * 180. / PI / 45.0;	   // Kippschutz: Factor to convert from pitch (in rad) to duty cycle (255=100%)
float cfgPitchThresholdRad = 30. * PI / 180.0;
float cfgObstacleMapDistThreshold = 1.5;       // Slow speed distance threshold for ObstacleMowPoint
float cfgAngularSpeed = 0.5;
float cfgObstacleMapGpsThreshold = 1.0;        // in m*m
float cfgSlowSpeedObstacleMap = 0.1;     // for motor overload and close to target 
float cfgOmapOutsideFenceDist = 1.5;     // distance between fence and waypoint for obstacle maps


// answer Bluetooth with CRC
void cmdAnswer(String s)
{
   if (s.length() > 0)
   {
      byte crc = 0;
      for (int i=0; i < s.length(); i++) crc += s[i];
      s += F(",0x");
      if (crc <= 0xF) s += F("0");
      s += String(crc, HEX);
      s += F("\r\n");
      //CONSOLE.print(s);      
   }
   cmdResponse = s;
}

//void WriteMap(String cmd)
//{
//   if (!writeMapFlag) return;
//
//   char mapFileName[32];
//   sprintf(mapFileName, "MAP%d.TXT", maps.mapID);
//   SDFile mapFile;
//
//   if (cmd == "")
//   {
//      CONSOLE.print(F("Create map file "));
//      CONSOLE.println(mapFileName);
//      SD.remove(mapFileName);
//      return;
//   }
//   else
//   {
//      mapFile = SD.open(mapFileName, FILE_WRITE);
//      if (mapFile)
//      {
//         const int BUF_SIZE = 128;
//         char buf[BUF_SIZE];
//
//         cmd.toCharArray(buf, BUF_SIZE-2);
//         int i = strlen(buf);
//         buf[i++] = 13;
//         buf[i++] = 10;
//         buf[i] = 0;
//         mapFile.write(buf);
//         mapFile.flush();
//         mapFile.close();
//         return;
//      }
//   }
//   CONSOLE.println(F("=ERROR opening map file for writing"));
//}

// Get/set data/time of the RTC
void cmdRtc(String cmd)
{
   DateTime dateTime = {};
   String s = F("D,");

   if (cmd.length()<6)
   {
      GetDateTime(dateTime);
      String dateTimeText = DateTime2String(dateTime);
      CONSOLE.print(F("Current date and time: "));
      CONSOLE.println(dateTimeText);
      s += dateTimeText;
   }
   else
   {
      int counter = 0;
      int lastCommaIdx = 0;

      for (int idx = 0; idx < cmd.length(); idx++) 
      {
         char ch = cmd[idx];
         if ((ch == ',') || (idx == cmd.length() - 1)) 
         {
            int intValue = cmd.substring(lastCommaIdx + 1, idx + 1).toInt();
            if (counter == 1) dateTime.year = intValue % 100;
            else if (counter == 2) dateTime.month = intValue;
            else if (counter == 3) dateTime.monthday = intValue;
            else if (counter == 4) dateTime.hour = intValue;
            else if (counter == 5) dateTime.minute = intValue;
            else if (counter == 6) dateTime.second = intValue;
            else if (counter == 7) dateTime.weekday = intValue + 1;

            counter++;
            lastCommaIdx = idx;
         }
      }
      if (counter == 8
         && dateTime.month >= 1    && dateTime.month <= 12
         && dateTime.monthday >= 1 && dateTime.monthday <= 31
         && dateTime.hour >= 0     && dateTime.hour <= 23
         && dateTime.minute >= 0   && dateTime.minute <= 59
         && dateTime.second >= 0   && dateTime.second <= 59
         && dateTime.weekday >= 1  && dateTime.weekday <= 7)
      {
         DateTime newDateTime;
         SetDateTime(dateTime);
         outputConsoleInit();    // adjust timestamp

         GetDateTime(newDateTime);
         String dateTimeText = DateTime2String(newDateTime);
         CONSOLE.print(F("New date and time: "));
         CONSOLE.println(dateTimeText);
         s += dateTimeText;
      }
      else
      {
         CONSOLE.print(F("Illegal date/time: "));
         CONSOLE.println(cmd);
         s += F("ERROR");
      }
   }
   cmdAnswer(s);
}

static void cmdReadMapFile(String cmd)
{
   long mapCheckSum = 0;
   int mapId = cmd.substring(5).toInt();
   if (mapId<1 || mapId>MAX_MAP_ID)
   {
      CONSOLE.print(F("=Illegal MapId: "));
      CONSOLE.println(mapId);
   }
   else
   {
      char fileName[16];
      snprintf(fileName, 16, "MAP%d.BIN", mapId);
      maps.mapID = mapId;
      maps.load(fileName);
      mapCheckSum = maps.mapCRC;
      //HB CONSOLE.print(F("=Loading map from file "));
      //HB CONSOLE.println(fileName);
      //HB 
      //HB udpSerial.DisableLogging();
      //HB SDFile dataFile = SD.open(fileName);
      //HB 
      //HB // if the file is available, read it:
      //HB if (dataFile)
      //HB {
      //HB    const bool NO_CHECKSUM_CHECK = false;
      //HB    const int LINE_SIZE = 256;
      //HB    char line[LINE_SIZE];
      //HB    maps.mapID = mapId;
      //HB    int i = 0;
      //HB    while (dataFile.available())
      //HB    {
      //HB       char ch = dataFile.read();
      //HB       //CONSOLE.write(ch);
      //HB       if (ch != 10)
      //HB       {
      //HB          if (ch == 13 || i == LINE_SIZE - 1)
      //HB          {
      //HB             line[i] = 0;
      //HB             processCmd(NO_CHECKSUM_CHECK, line);
      //HB             i = 0;
      //HB             watchdogReset();
      //HB          }
      //HB          else
      //HB          {
      //HB             line[i++] = ch;
      //HB          }
      //HB       }
      //HB    }
      //HB    if (i)
      //HB    {
      //HB       line[i] = 0;
      //HB       processCmd(NO_CHECKSUM_CHECK, line);
      //HB    }
      //HB    mapCheckSum = maps.mapCRC;
      //HB }
      //HB else 
      //HB {
      //HB    CONSOLE.print(F("=error opening file "));
      //HB    CONSOLE.println(fileName);
      //HB }
      //HB dataFile.close();
      //HB udpSerial.EnableLogging();
   }
   String s = F("R,");
   s += mapCheckSum;
   cmdAnswer(s);
}

// request operation
void cmdControl(String cmd)
{
  if (cmd.length()<6) return;
  int counter = 0;
  int lastCommaIdx = 0;
  int mow=-1;
  int op = -1;
  float wayPerc = -1;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      int intValue = cmd.substring(lastCommaIdx+1, idx+1).toInt();
      float floatValue = cmd.substring(lastCommaIdx+1, idx+1).toFloat();
      if (counter == 1){
          if (intValue >= 0) {
            motor.enableMowMotor = (intValue == 1);
            motor.setMowState( (intValue == 1) );
          }
      } else if (counter == 2){
          if (intValue >= 0) op = intValue;
      } else if (counter == 3){
          if (floatValue >= 0) setSpeed = floatValue;
      } else if (counter == 4){
          if (intValue >= 0) fixTimeout = intValue;
      } else if (counter == 5){
          if (intValue >= 0) finishAndRestart = (intValue == 1);
      } else if (counter == 6){
          if (floatValue >= 0) maps.setMowingPointPercent(floatValue);
      } else if (counter == 7){
          if (intValue > 0) maps.skipNextMowingPoint();
      } else if (counter == 8){
          if (intValue >= 0) sonar.enabled = (intValue == 1);
      } else if (counter == 9) {  // bBumperEnable
          if (intValue == 0) cfgBumperEnable = false; 
          if (intValue == 1) cfgBumperEnable = true; 
      } else if (counter == 10) {  // bFrontWheelDrive
          if (intValue == 0) motorDriver.frontWheelDrive = false; 
          if (intValue == 1) motorDriver.frontWheelDrive = true; 
      } else if (counter == 11) {  // bMoonlightLineTracking
          if (intValue == 0) cfgMoonlightLineTracking = false; 
          if (intValue == 1) cfgMoonlightLineTracking = true; 
      } else if (counter == 12) { 
          if (intValue >= 0) maps.setMowingPoint(intValue); 
      } else if (counter == 13) {  
          if (intValue == 0) cfgEnableTiltDetection = false; 
          if (intValue == 1) cfgEnableTiltDetection = true; 
      } else if (counter == 14) {  
          if (floatValue >= 0) cfgAngularSpeed = floatValue; 
      } else if (counter == 15) {  
          if (intValue == 0) maps.useGPSfloatForPosEstimation = false; 
          if (intValue == 1) maps.useGPSfloatForPosEstimation = true; 
      } else if (counter == 16) {  
          if (intValue >= 0) {
              uint16_t distCm = intValue >> 2;
              cfgObstacleMapGpsThreshold = sq((float)distCm / 100.);
              maps.mapType = (MapType)(intValue & 3);
          }
      } else if (counter == 17) {
          if (floatValue >= 0) cfgObstacleMapDistThreshold = floatValue;
      } else if (counter == 18) {
          if (floatValue >= 0) cfgSlowSpeedObstacleMap = floatValue;
      } else if (counter == 19) {
          if (floatValue >= 0) cfgPitchThresholdRad = floatValue * PI / 180.0;
      } else if (counter == 20) {
          if (floatValue >= 0) cfgOmapOutsideFenceDist = floatValue;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  /*CONSOLE.print(F("linear="));
  CONSOLE.print(linear);
  CONSOLE.print(F(" angular="));
  CONSOLE.println(angular);*/
  if (op >= 0) setOperation((OperationType)op, false, true);
  String s = F("C");
  cmdAnswer(s);
}

void cmdSetGpsConfigFilter(String cmd)
{
    uint8_t minElev=10, nSV=10, minCN0=30;
    if (cmd.length() < 6) return;
    int counter = 0;
    int lastCommaIdx = 0;
    for (int idx = 0; idx < cmd.length(); idx++) {
        char ch = cmd[idx];
        if ((ch == ',') || (idx == cmd.length() - 1)) 
        {
            int intValue = cmd.substring(lastCommaIdx + 1, idx + 1).toInt();
            if (intValue >= 0 && intValue < 256)
            {
                if (counter == 1) minElev = intValue;
                else if (counter == 2) nSV = intValue;
                else if (counter == 3) minCN0 = intValue;
            }
            counter++;
            lastCommaIdx = idx;
        }
    }
    String s = F("A");
    cmdAnswer(s);
    gps.SetGpsConfigFilter(minElev, nSV, minCN0);
}

void cmdRemoteControl(String cmd)
{
   rcmodel.DoRemoteControl(cmd);
   // int iLinear, iAngular;
   // if (cmd.length() < 6) return;
   // int counter = 0;
   // int lastCommaIdx = 0;
   // for (int idx = 0; idx < cmd.length(); idx++) 
   // {
   //     char ch = cmd[idx];
   //     if ((ch == ',') || (idx == cmd.length() - 1)) 
   //     {
   //         int intValue = cmd.substring(lastCommaIdx + 1, idx + 1).toInt();
   //
   //         // ignore command if wrong values are received
   //         if (intValue < -2048 || intValue > 2048) return;
   //
   //         if (counter == 1) iLinear = intValue;
   //         else if (counter == 2) iAngular = intValue;
   //         counter++;
   //         lastCommaIdx = idx;
   //     }
   // }
   // // mowerSpeed = 0.5 * iLinear / 2048       # m/s
   // // mowerRotation = 1 * iAngular / 2048     # rad/s
   // static const float cLinear = 0.5 / 2048.;
   // static const float cAngular = 1.0 / 2048.;
   //
   // motor.setLinearAngularSpeed(iLinear*cLinear, iAngular*cAngular, false); 
}

// request motor
void cmdMotor(String cmd)
{
  if (cmd.length()<6) return;
  int counter = 0;
  int lastCommaIdx = 0;
  float linear=0;
  float angular=0;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      float value = cmd.substring(lastCommaIdx+1, idx+1).toFloat();
      if (counter == 1){
          linear = value;
      } else if (counter == 2){
          angular = value;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  /*CONSOLE.print(F("linear="));
  CONSOLE.print(linear);
  CONSOLE.print(F(" angular="));
  CONSOLE.println(angular);*/
  motor.setLinearAngularSpeed(linear, angular, false);
  String s = F("M");
  cmdAnswer(s);
}

void cmdMotorTest(){
  String s = F("E");
  cmdAnswer(s);
  motor.test();
}

void cmdSensorTest(){
  String s = F("F");
  cmdAnswer(s);
  sensorTest();
}

// request waypoint
void cmdWaypoint(String cmd)
{
  if (cmd.length()<6) return;
  //HB WriteMap(cmd);
  int counter = 0;
  int lastCommaIdx = 0;
  int widx=0;
  float x=0;
  float y=0;
  bool success = true;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      float intValue = cmd.substring(lastCommaIdx+1, idx+1).toInt();
      float floatValue = cmd.substring(lastCommaIdx+1, idx+1).toFloat();
      if (counter == 1){
          widx = intValue;
      } else if (counter == 2){
          x = floatValue;
      } else if (counter == 3){
          y = floatValue;
          if (!maps.setPoint(widx, x, y)){
            success = false;
            break;
          }
          widx++;
          counter = 1;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  /*CONSOLE.print(F("waypoint ("));
  CONSOLE.print(widx);
  CONSOLE.print("/");
  CONSOLE.print(count);
  CONSOLE.print(") ");
  CONSOLE.print(x);
  CONSOLE.print(",");
  CONSOLE.println(y);*/

  String s = F("W,");
  s += widx;
  cmdAnswer(s);

  if (!success){
    stateSensor = SENS_MEM_OVERFLOW;
    setOperation(OP_ERROR);
  }
}

// request waypoints count
void cmdWayCount(String cmd)
{
  if (cmd.length()<6) return;
  //HB WriteMap(cmd);
  int counter = 0;
  int lastCommaIdx = 0;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      float intValue = cmd.substring(lastCommaIdx+1, idx+1).toInt();
      float floatValue = cmd.substring(lastCommaIdx+1, idx+1).toFloat();
      if (counter == 1){
          if (!maps.setWayCount(WAY_PERIMETER, intValue)) return;
      } else if (counter == 2){
          if (!maps.setWayCount(WAY_EXCLUSION, intValue)) return;
      } else if (counter == 3){
          if (!maps.setWayCount(WAY_DOCK, intValue)) return;
      } else if (counter == 4){
          if (!maps.setWayCount(WAY_MOW, intValue)) return;
      } else if (counter == 5){
          if (!maps.setWayCount(WAY_FREE, intValue)) return;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  String s = F("N");
  cmdAnswer(s);
  //maps.dump();
}

// request exclusion count
void cmdExclusionCount(String cmd)
{
  if (cmd.length()<6) return;
  //HB WriteMap(cmd);
  //HB writeMapFlag = false;
  int counter = 0;
  int lastCommaIdx = 0;
  int widx=0;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      float intValue = cmd.substring(lastCommaIdx+1, idx+1).toInt();
      float floatValue = cmd.substring(lastCommaIdx+1, idx+1).toFloat();
      if (counter == 1){
          widx = intValue;
      } else if (counter == 2){
          if (!maps.setExclusionLength(widx, intValue)) return;
          widx++;
          counter = 1;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  String s = F("X,");
  s += widx;
  cmdAnswer(s);
}

// request position mode
void cmdPosMode(String cmd)
{
  if (cmd.length()<6) return;
  int counter = 0;
  int lastCommaIdx = 0;
  for (int idx=0; idx < cmd.length(); idx++){
    char ch = cmd[idx];
    //Serial.print(F("ch="));
    //Serial.println(ch);
    if ((ch == ',') || (idx == cmd.length()-1)){
      int intValue = cmd.substring(lastCommaIdx+1, idx+1).toInt();
      double doubleValue = cmd.substring(lastCommaIdx+1, idx+1).toDouble();
      if (counter == 1){
          absolutePosSource = bool(intValue);
      } else if (counter == 2){
          absolutePosSourceLon = doubleValue;
      } else if (counter == 3){
          absolutePosSourceLat = doubleValue;
      }
      counter++;
      lastCommaIdx = idx;
    }
  }
  CONSOLE.print(F("absolutePosSource="));
  CONSOLE.print(absolutePosSource);
  CONSOLE.print(F(" lon="));
  CONSOLE.print(absolutePosSourceLon, 8);
  CONSOLE.print(F(" lat="));
  CONSOLE.println(absolutePosSourceLat, 8);
  String s = F("P");
  cmdAnswer(s);
}

// request version
void cmdVersion(){
   Serial.println(F("cmdVersion"));
  String s = F("V,");
  s += F(VER);
  cmdAnswer(s);
}

// request add obstacle
void cmdObstacle(){
  String s = F("O");
  cmdAnswer(s);
  triggerObstacle(OT_BUMPER_SWITCH);
}

// perform pathfinder stress test
void cmdStressTest(){
  String s = F("Z");
  cmdAnswer(s);
  maps.stressTest();
}

// perform hang test (watchdog should trigger)
void cmdTriggerWatchdog(){
  String s = F("Y");
  cmdAnswer(s);
  setOperation(OP_IDLE);
  triggerWatchdog = true;
}

// perform hang test (watchdog should trigger)
void cmdGnssWarmRestart(){
  String s = F("Y2");
  cmdAnswer(s);
  CONSOLE.println(F("=GNSS Warm Restart"));
  gps.WarmRestart();
}

// perform hang test (watchdog should trigger)
void cmdGnssColdRestart()
{
  String s = F("YR");
  cmdAnswer(s);
  CONSOLE.println(F("=GNSS Cold Restart"));
  gps.ColdRestart();
}

// switch-off robot
void cmdSwitchOffRobot(){
  String s = F("Y3");
  cmdAnswer(s);
  setOperation(OP_IDLE);
  battery.switchOff();
}

// kidnap test (kidnap detection should trigger)
void cmdKidnap(){
  String s = F("K");
  cmdAnswer(s);
  CONSOLE.println(F("=kidnapping robot - kidnap detection should trigger"));
  stateX = 0;
  stateY = 0;
}

void cmdTriggerRaspiShutdown()
{
    String s = F("Y4");
    cmdAnswer(s);
    CONSOLE.println(F("=Trigger raspi shutdown"));
    batteryDriver.raspiShutdown();
}

void cmdStartUploadMap(String cmd)
{
   if (cmd.length()<6) return;
   int lastCommaIdx = 4;
   for (int idx = 5; idx < cmd.length(); idx++) 
   {
      char ch = cmd[idx];
      if ((ch == ',') || (idx == cmd.length() - 1)) 
      {
         maps.mapID = cmd.substring(lastCommaIdx + 1, idx + 1).toInt();
         CONSOLE.print(F("MapID="));
         CONSOLE.println(maps.mapID);
         //HB writeMapFlag = true;
         //HB WriteMap("");
         break;
      }
   }
   String s = F("U");
   cmdAnswer(s);
}

void cmdToggleUseIMU()
{
    String s = F("YI");
    cmdAnswer(s);
    USE_IMU = !USE_IMU;
    CONSOLE.print(F("=USE_IMU = "));
    CONSOLE.println(USE_IMU);
}

void cmdToggleSmoothCurves()
{
    String s = F("YS");
    cmdAnswer(s);
    cfgSmoothCurves = !cfgSmoothCurves;
    CONSOLE.print(F("=cfgSmoothCurves = "));
    CONSOLE.println(cfgSmoothCurves);
}

void cmdToggleEnablePathFinder()
{
    String s = F("YF");
    cmdAnswer(s);
    cfgEnablePathFinder = !cfgEnablePathFinder;
    CONSOLE.print(F("=cfgEnablePathFinder = "));
    CONSOLE.println(cfgEnablePathFinder);
}

void cmdToggleUseGPSfloatForPosEstimation()
{
    String s = F("YP");
    cmdAnswer(s);
    maps.useGPSfloatForPosEstimation = !maps.useGPSfloatForPosEstimation;    
    CONSOLE.print(F("=useGPSfloatForPosEstimation = "));
    CONSOLE.println(maps.useGPSfloatForPosEstimation);
}

void cmdToggleUseGPSfloatForDeltaEstimationEstimation()
{
    String s = F("YD");
    cmdAnswer(s);
    maps.useGPSfloatForDeltaEstimation = !maps.useGPSfloatForDeltaEstimation;
    CONSOLE.print(F("=USE_GPS_FLOAT_FOR_DELTA_ESTIMATION = "));
    CONSOLE.println(maps.useGPSfloatForDeltaEstimation);
}

void cmdToggleGpsLogging()    //HB disabled
{
    String s = F("YG");
    cmdAnswer(s);
    gps.verbose = !gps.verbose;
    CONSOLE.print(F("gps.verbose = "));
    CONSOLE.println(gps.verbose);
}

void cmdToggleUpHillDetectionFlag()
{
    String s = F("YG");
    cmdAnswer(s);
    upHillDetectionFlag = !upHillDetectionFlag;
    CONSOLE.print(F("=upHillDetectionFlag = "));
    CONSOLE.println(upHillDetectionFlag);
}

// toggle GPS solution (invalid,float,fix) for testing
void cmdToggleGPSSolution(){
  String s = F("G");
  cmdAnswer(s);
  CONSOLE.println(F("toggle GPS solution"));
  switch (gps.solution){
    case UBLOX::SOL_INVALID:
      gps.solutionAvail = true;
      gps.solution = UBLOX::SOL_FLOAT;
      gps.relPosN = stateY - 2.0;  // simulate pos. solution jump
      gps.relPosE = stateX - 2.0;
      lastFixTime = millis();
      stateGroundSpeed = 0.1;
      break;
    case UBLOX::SOL_FLOAT:
      gps.solutionAvail = true;
      gps.solution = UBLOX::SOL_FIXED;
      stateGroundSpeed = 0.1;
      gps.relPosN = stateY + 2.0;  // simulate undo pos. solution jump
      gps.relPosE = stateX + 2.0;
      break;
    case UBLOX::SOL_FIXED:
      gps.solutionAvail = true;
      gps.solution = UBLOX::SOL_INVALID;
      break;
  }
}

void cmdPing()
{
    String s = F("Y6");
    cmdAnswer(s);
}

// request summary
void cmdSummary(){
  String s = F("S,");
  s += battery.batteryVoltage;
  s += ",";
  s += stateX;
  s += ",";
  s += stateY;
  s += ",";
  s += stateDelta;
  s += ",";
  s += gps.solution;
  s += ",";
  s += stateOp;
  s += ",";
  s += maps.mowPointsIdx;
  s += ",";
  s += (millis() - gps.dgpsAge)/1000.0;
  s += ",";
  s += stateSensor;
  s += ",";
  s += maps.targetPoint.x();
  s += ",";
  s += maps.targetPoint.y();
  s += ",";
  s += gps.accuracy;
  s += ",";
  s += gps.numSV;
  s += ",";
  if (stateOp == OP_CHARGE) {
    s += "-";
    s += battery.chargingCurrent;
  } else {
    s += motor.motorsSenseLP;
  }
  s += ",";
  s += gps.numSVdgps;
  s += ",";
  s += maps.mapCRC;
  cmdAnswer(s);
}

// request statistics
void cmdStats(){
  String s = F("T,");
  s += statIdleDuration;
  s += ",";
  s += statChargeDuration;
  s += ",";
  s += statMowDuration;
  s += ",";
  s += statMowDurationFloat;
  s += ",";
  s += statMowDurationFix;
  s += ",";
  s += statMowFloatToFixRecoveries;
  s += ",";
  s += statMowDistanceTraveled;
  s += ",";
  s += statMowMaxDgpsAge;
  s += ",";
  s += statImuRecoveries;
  s += ",";
  s += statTempMin;
  s += ",";
  s += statTempMax;
  s += ",";
  s += gps.chksumErrorCounter;
  s += ",";
  //s += ((float)gps.dgpsChecksumErrorCounter) / ((float)(gps.dgpsPacketCounter));
  s += gps.dgpsChecksumErrorCounter;
  s += ",";
  s += statMaxControlCycleTime;
  s += ",";
  s += SERIAL_BUFFER_SIZE;
  s += ",";
  s += statMowDurationInvalid;
  s += ",";
  s += statMowInvalidRecoveries;
  s += ",";
  s += statMowObstacles;
  s += ",";
  s += freeMemory();
  s += ",";
  s += getResetCause();
  s += ",";
  s += statGPSJumps;
  s += ",";
  s += statMowSonarCounter;
  s += ",";
  s += statMowBumperCounter;
  s += ",";
  s += statMowGPSMotionTimeoutCounter;
  cmdAnswer(s);
  char text[64];
  sprintf(text, "=TTFF: %d sec", gps.ttffValue/1000);
  CONSOLE.println(text);
}

// clear statistics
void cmdClearStats(){
  String s = F("L");
  statIdleDuration = 0;
  statChargeDuration = 0;
  statMowDuration = 0;
  statMowDurationInvalid = 0;
  statMowDurationFloat = 0;
  statMowDurationFix = 0;
  statMowFloatToFixRecoveries = 0;
  statMowInvalidRecoveries = 0;
  statMowDistanceTraveled = 0;
  statMowMaxDgpsAge = 0;
  statImuRecoveries = 0;
  statTempMin = 9999;
  statTempMax = -9999;
  gps.chksumErrorCounter = 0;
  gps.dgpsChecksumErrorCounter = 0;
  statMaxControlCycleTime = 0;
  statMowObstacles = 0;
  statMowBumperCounter = 0;
  statMowSonarCounter = 0;
  statMowLiftCounter = 0;
  statMowGPSMotionTimeoutCounter = 0;
  statGPSJumps = 0;
  cmdAnswer(s);
}

static bool bluetoothLoggingFlag = false;

static void cmdToggleBluetoothLoggingFlag()
{
   String s = F("Y2");
   cmdAnswer(s);
   bluetoothLoggingFlag = !bluetoothLoggingFlag;
   CONSOLE.print(F("=Bluetooth logging is "));
   CONSOLE.println(bluetoothLoggingFlag ? "enabled" : "disabled");
}

// process request
void processCmd(bool checkCrc, String cmd)
{
  cmdResponse = "";
  if (cmd.length() < 4) return;
  byte expectedCrc = 0;
  int idx = cmd.lastIndexOf(',');
  if (idx < 1)
  {
    if (checkCrc)
    {
      CONSOLE.println(F("CRC ERROR "));
      return;
    }
  } 
  else 
  {
    for (int i=0; i < idx; i++) expectedCrc += cmd[i];
    String s = cmd.substring(idx+1, idx+5);
    int crc = strtol(s.c_str(), NULL, 16);
    if (expectedCrc != crc)
    {
      if (checkCrc)
      {
        CONSOLE.print(F("CRC ERROR  received: 0x"));
        CONSOLE.print(crc,HEX);
        CONSOLE.print(F(", expected: 0x"));
        CONSOLE.print(expectedCrc,HEX);
        CONSOLE.println();
        return;
      }
    } 
    else 
    {
      // remove CRC
      cmd = cmd.substring(0, idx);
      //CONSOLE.println(cmd);
    }
  }
  //CONSOLE.print(F("ProcessCmd : "));
  //cONSOLE.println(cmd[3]);
  if (cmd[0] != 'A') return;
  if (cmd[1] != 'T') return;
  if (cmd[2] != '+') return;
  else if (cmd[3] == 'A') cmdSetGpsConfigFilter(cmd);
  else if (cmd[3] == 'C') cmdControl(cmd);
  else if (cmd[3] == 'D') cmdRtc(cmd);
  else if (cmd[3] == 'E') cmdMotorTest();
  else if (cmd[3] == 'F') cmdSensorTest();
  else if (cmd[3] == 'G') cmdToggleGPSSolution();   // for developers
  else if (cmd[3] == 'K') cmdKidnap();   // for developers
  else if (cmd[3] == 'L') cmdClearStats();
  else if (cmd[3] == 'M') cmdMotor(cmd);
  else if (cmd[3] == 'N') cmdWayCount(cmd);
  else if (cmd[3] == 'O') cmdObstacle();
  else if (cmd[3] == 'P') cmdPosMode(cmd);
  else if (cmd[3] == 'Q') cmdSwitchOffRobot();
  else if (cmd[3] == 'R') cmdReadMapFile(cmd);
  else if (cmd[3] == 'S') cmdSummary();
  else if (cmd[3] == 'T') cmdStats();
  else if (cmd[3] == 'U') cmdStartUploadMap(cmd);
  else if (cmd[3] == 'V') cmdVersion();
  else if (cmd[3] == 'W') cmdWaypoint(cmd);
  else if (cmd[3] == 'X') cmdExclusionCount(cmd);
  else if (cmd[3] == 'Z') cmdStressTest();   // for developers
  else if (cmd[3] == '#') cmdRemoteControl(cmd);  
  else if (cmd[3] == '$') FileSystemCmd(cmd);
  else if (cmd[3] == 'Y') 
  {
      if (cmd.length() <= 4)
      {
         cmdTriggerWatchdog();   // for developers
      } 
      else 
      {
         if (cmd[4] == '2') cmdGnssWarmRestart();   // for developers
         if (cmd[4] == '3') cmdSwitchOffRobot();   // for developers
         if (cmd[4] == '4') cmdTriggerRaspiShutdown();   // for developers
         if (cmd[4] == '5') cmdToggleBluetoothLoggingFlag();   // for developers
         if (cmd[4] == '6') cmdPing();
         if (cmd[4] == 'R') cmdGnssColdRestart();
         if (cmd[4] == 'D') cmdToggleUseGPSfloatForDeltaEstimationEstimation();
         if (cmd[4] == 'F') cmdToggleEnablePathFinder();
         //HB if (cmd[4] == 'G') cmdToggleGpsLogging();
         if (cmd[4] == 'G') cmdToggleUpHillDetectionFlag();
         if (cmd[4] == 'P') cmdToggleUseGPSfloatForPosEstimation();
         if (cmd[4] == 'S') cmdToggleSmoothCurves();
         if (cmd[4] == '6') cmdPing();
      }
  }
  else
  {
     CONSOLE.println(F("Illegal command"));
  }
}

// process console input
void processConsole(){
  char ch;
  if (CONSOLE.available()){
    battery.resetIdle();
    while ( CONSOLE.available() ){
      ch = CONSOLE.read();
      if ((ch == '\r') || (ch == '\n')) {
        CONSOLE.println(cmd);
        processCmd(false, cmd);
        if (cmdResponse.length() > 0) CONSOLE.print(cmdResponse);
        cmd = "";
      } else if (cmd.length() < 500){
        cmd += ch;
      }
    }
  }
}

// process Bluetooth input
void processBLE()
{
   if (simulationFlag) return;

   //static bool skip=true;
   //static int timeOut;
   char ch;
   if (BLE.available())
   {
       battery.resetIdle();
       while ( BLE.available() )
       {
           ch = BLE.read();
           if ((ch == '\r') || (ch == '\n'))
           {
               if (bluetoothLoggingFlag) CONSOLE.println(cmd);
               processCmd(true, cmd);
               if (cmdResponse.length() > 0) 
               {
                  if (bluetoothLoggingFlag) CONSOLE.print(F("BLE:")); // HB
                  if (bluetoothLoggingFlag) CONSOLE.print(cmdResponse); // HB
                  BLE.print(cmdResponse);
               }
               cmd = "";
               //skip=false;
               //timeOut=0;
               break;
           }
           else if (cmd.length() < 500)
           {
               cmd += ch;
           }
       }
   }
}

// process WIFI input
void processWifi()
{
  if (!wifiFound) return;
  if (!ENABLE_SERVER) return;
  // listen for incoming clients
  if (client != NULL){
    if (stopClientTime != 0) {
      if (millis() > stopClientTime){
        client.stop();
        stopClientTime = 0;
        client = NULL;
      }
      return;
    }
  }
  client = server.available();
  if (client != NULL) {                               // if you get a client,
    battery.resetIdle();
    //CONSOLE.println(F("New client"));             // print a message out the serial port
    buf.init();                               // initialize the circular buffer
    unsigned long timeout = millis() + 50;
    while ( (client.connected()) && (millis() < timeout) ) {              // loop while the client's connected
      if (client.available()) {               // if there's bytes to read from the client,
        char c = client.read();               // read a byte, then
        timeout = millis() + 50;
        buf.push(c);                          // push it to the ring buffer
        // you got two newline characters in a row
        // that's the end of the HTTP request, so send a response
        if (buf.endsWith("\r\n\r\n")) {
          cmd = "";
          while ((client.connected()) && (client.available()) && (millis() < timeout)) {
            char ch = client.read();
            timeout = millis() + 50;
            cmd = cmd + ch;
            gps.run();
          }
          CONSOLE.println(cmd);
          if (client.connected()) {
            processCmd(true, cmd);
            if (cmdResponse.length() > 0) 
            {
               client.print(
                 "HTTP/1.1 200 OK\r\n"
                 "Access-Control-Allow-Origin: *\r\n"
                 "Content-Type: text/html\r\n"
                 "Connection: close\r\n"  // the connection will be closed after completion of the response
                 // "Refresh: 1\r\n"        // refresh the page automatically every 20 sec
                 );
               client.print(F("Content-length: "));
               client.print(cmdResponse.length());
               client.print(F("\r\n\r\n"));
               client.print(cmdResponse);
            }
          }
          break;
        }
      }
      gps.run();
    }
    // give the web browser time to receive the data
    stopClientTime = millis() + 20;
    //delay(10);
    // close the connection
    //client.stop();
    //CONSOLE.println(F("Client disconnected"));
  }
}

void processUdp()
{
      const int SIZE = 255;
      static char packetBuf[SIZE];
      int len = udpSerial.readPacket(packetBuf, SIZE);
      if (len > 0)
      {
         //CONSOLE.print(F("Packet received: "));
         //CONSOLE.println(packetBuf);
         const bool USE_CHECKSUM = true;
         processCmd(USE_CHECKSUM, packetBuf);
         if (cmdResponse.length() > 0) CONSOLE.print(cmdResponse);
         battery.resetIdle();
      }
}

void processComm(){
  processConsole();
  processBLE();
  processWifi();
#if defined(ENABLE_UDP)
  processUdp();
#endif
  if (triggerWatchdog) {
    CONSOLE.println(F("=hang test - watchdog should trigger and perform a reset"));
    while (true){
      // do nothing, just hang
    }
  }
}


#if 0
// output summary on console
void outputConsole(){
  //return;
  if (millis() > nextInfoTime){
    bool started = (nextInfoTime == 0);
    nextInfoTime = millis() + 5000;
    unsigned long totalsecs = millis()/1000;
    unsigned long totalmins = totalsecs/60;
    unsigned long hour = totalmins/60;
    unsigned long min = totalmins % 60;
    unsigned long sec = totalsecs % 60;
    CONSOLE.print (hour);
    CONSOLE.print (":");
    CONSOLE.print (min);
    CONSOLE.print (":");
    CONSOLE.print (sec);
    CONSOLE.print (" ctlDur=");
    //if (!imuIsCalibrating){
    if (!started){
      if (controlLoops > 0){
        statControlCycleTime = 1.0 / (((float)controlLoops)/5.0);
      } else statControlCycleTime = 5;
      statMaxControlCycleTime = max(statMaxControlCycleTime, statControlCycleTime);
    }
    controlLoops=0;
    CONSOLE.print (statControlCycleTime);
    CONSOLE.print (" op=");
    CONSOLE.print (stateOp);
    CONSOLE.print (" freem=");
    CONSOLE.print (freeMemory ());
    uint32_t *spReg = (uint32_t*)__get_MSP();   // stack pointer
    CONSOLE.print (" sp=");
    CONSOLE.print (*spReg, HEX);
    CONSOLE.print(F(" volt="));
    CONSOLE.print(battery.batteryVoltage);
    CONSOLE.print(F(" chg="));
    CONSOLE.print(battery.chargingCurrent);
    CONSOLE.print(F(" tg="));
    CONSOLE.print(maps.targetPoint.x());
    CONSOLE.print(",");
    CONSOLE.print(maps.targetPoint.y());
    CONSOLE.print(F(" x="));
    CONSOLE.print(stateX);
    CONSOLE.print(F(" y="));
    CONSOLE.print(stateY);
    CONSOLE.print(F(" delta="));
    CONSOLE.print(stateDelta);
    CONSOLE.print(F(" tow="));
    CONSOLE.print(gps.iTOW);
    CONSOLE.print(F(" lon="));
    CONSOLE.print(gps.lon,8);
    CONSOLE.print(F(" lat="));
    CONSOLE.print(gps.lat,8);
    CONSOLE.print(F(" h="));
    //HB CONSOLE.print(gps.height,1);
    CONSOLE.print(gps.height,2);    //HB
    CONSOLE.print(F(" n="));
    CONSOLE.print(gps.relPosN);
    CONSOLE.print(F(" e="));
    CONSOLE.print(gps.relPosE);
    CONSOLE.print(F(" d="));
    CONSOLE.print(gps.relPosD);
    CONSOLE.print(F(" sol="));
    CONSOLE.print(gps.solution);
    CONSOLE.print(F(" age="));
    CONSOLE.print((millis()-gps.dgpsAge)/1000.0);

    //float leftCurrent, rightCurrent, mowCurrent;
    //motorDriver.getMotorCurrent(leftCurrent, rightCurrent, mowCurrent);
    CONSOLE.print(F(" Imot_mA="));    //HB
    CONSOLE.print(motor.motorLeftSenseLP*1000.,0);
    CONSOLE.print(",");
    CONSOLE.print(motor.motorRightSenseLP*1000.,0);
    CONSOLE.print(",");
    CONSOLE.print(motor.motorMowSenseLP*1000.,0);

    CONSOLE.println();
    //logCPUHealth();
  }
}
#else
#define PRINT(format, value) sprintf(buf, format, value); CONSOLE.print(buf);
// output summary on console

//static uint32_t timestampOffset_sec;

void outputConsoleInit()
{
   DateTime now;

   GetDateTime(now);
   //timestampOffset_sec = now.second + (now.minute + now.hour * 60) * 60 - millis()/1000;
   CONSOLE.print(F("Current datetime: "));
   CONSOLE.println(DateTime2String(now));
}

void outputConsole()
{
  char buf[40];
  static const float DEGREE = 180 / PI;

  if (millis() > nextInfoTime)
  {
    bool started = (nextInfoTime == 0);
    nextInfoTime = millis() + LOG_PERIOD_MS;  //(simulationFlag ? 1000: LOG_PERIOD_MS);

    //unsigned long totalsecs = millis()/1000 + timestampOffset_sec;
    //unsigned long totalmins = totalsecs/60;
    //unsigned long totalhours = totalmins/60;
    //unsigned long hour = totalhours % 24;
    //unsigned long min = totalmins % 60;
    //unsigned long sec = totalsecs % 60;
    static int headLineCnt = 0;
    if (headLineCnt == 0) CONSOLE.println(F("#Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy   Pitch    Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags  Map  WayPts "));
    headLineCnt = headLineCnt + 1 & 7;
    //PRINT(":%02d:", hour);
    //PRINT("%02d:", min);
    //PRINT("%02d", sec);
    GetTimeStamp(buf);
    CONSOLE.print(buf);
    if (!started){
      if (controlLoops > 0){
        //HB statControlCycleTime = 1.0 / (((float)controlLoops)/5.0);
         statControlCycleTime = (float) LOG_PERIOD_MS / (1000*controlLoops);
      } else statControlCycleTime = 5;
      statMaxControlCycleTime = max(statMaxControlCycleTime, statControlCycleTime);
    }
    controlLoops=0;
    PRINT("%4.2f", statControlCycleTime);
    
    if (stateOp == OP_IDLE)        CONSOLE.print(F("  IDLE "));
    else if (stateOp == OP_MOW)    CONSOLE.print(F("  MOW  "));
    else if (stateOp == OP_CHARGE) CONSOLE.print(F(" CHARGE"));
    else if (stateOp == OP_ERROR)  CONSOLE.print(F("  ERROR"));
    else if (stateOp == OP_DOCK)   CONSOLE.print(F("  DOCK "));
    else if (stateOp == OP_UNDOCK) CONSOLE.print(F(" UNDOCK"));
    else                           CONSOLE.print(F("  ???  "));


    //PRINT(" %6d", freeMemory());
    PRINT(" %4.1f", battery.batteryVoltage);
    PRINT(" %4.0f", battery.chargingCurrent*1000.);

#define MOWER_DUMMY_MOVEMENT  0
#if MOWER_DUMMY_MOVEMENT
    if (simulationFlag)
    {
       static float dummyTx = 10.0, dummyTy = -5.0;
       static float dummySx = 0.0, dummySy = -5.0, dummyStep = 1.;
       float dummyGx, dummyGy;
       static bool firstFlag = true;

       if (firstFlag)
       {
          firstFlag = false;
          randomSeed(analogRead(0));
       }

       dummySx += dummyStep;
       if (dummySx >= 10.)
       {
          dummyTx = -10.;
          dummyStep = -1.;
       }
       else if (dummySx <= -10.)
       {
          dummyTx = 10.;
          dummyStep = 1.;
       }
       dummyGx = dummySx + (float)random(-40, 40)*0.01;
       dummyGy = dummySy + (float)random(-40, 40)*0.01;

       PRINT(" %6.2f", dummyTx);
       PRINT(" %6.2f", dummyTy);
       PRINT(" %6.2f", dummySx);
       PRINT(" %6.2f", dummySy);
       PRINT(" %6.2f", stateDelta);
       PRINT(" %6.2f", dummyGx);
       PRINT(" %6.2f", dummyGy);
    }
    else
#endif
    {
       PRINT(" %6.2f", maps.targetPoint.x());
       PRINT(" %6.2f", maps.targetPoint.y());
       PRINT(" %6.2f", stateX);
       PRINT(" %6.2f", stateY);
       //PRINT(" %6.2f", stateDelta);
       PRINT(" %5.0f°", stateDelta*DEGREE);
       PRINT(" %6.2f", gps.relPosE);
       PRINT(" %6.2f", gps.relPosN);
    }
    //PRINT(" %5.0f°", gps.relPosD*DEGREE);
    float maxPitchDeg = maxPitch * 180.0 / PI;
    PRINT(" %5.0f°", maxPitchDeg);
    maxPitch = -PI;  // reset for next logging output

	 float gps_height = gps.height - 412;		// 412m ist ungefähr die minimale Höhe des Gartens
	 gps_height = min(gps_height, 99.99);
	 gps_height = max(gps_height,-99.99);
	 PRINT(" %6.2f", gps_height);
    
         if (gps.solution == UBLOX::SOL_INVALID) { CONSOLE.print(F(" INVAL")); }
	 else if (gps.solution == UBLOX::SOL_FLOAT)   { CONSOLE.print(F(" FLOAT")); }
	 else if (gps.solution == UBLOX::SOL_FIXED)   { CONSOLE.print(F(" FIX  ")); }
    else                                         { CONSOLE.print(F(" ???  ")); }

    float age = (millis() - gps.dgpsAge) / 1000.0;
    age = min(age, 999.00);
    age = max(age,   0.00);
    PRINT(" %5.1f", age);
    PRINT(" %-2d", gps.numSVdgps)
    PRINT("/%2d", gps.numSV)
    PRINT(" %4.0f", motor.motorLeftSenseLP*1000.);
    PRINT(" %4.0f", motor.motorRightSenseLP*1000.);
    PRINT(" %4.0f", motor.motorMowSenseLP*1000.);
    
    PRINT("%3.0f°C", stateTemp); 
    PRINT("%3.0f%%%", stateHumidity);

    PRINT(" %c", bluetoothLoggingFlag ? 'B' : 'b');
    PRINT("%c", maps.useGPSfloatForPosEstimation ? 'P' : 'p');
    PRINT("%c", maps.useGPSfloatForDeltaEstimation ? 'D' : 'd');
    //PRINT("%c", gps.verbose ? 'G' : 'g');
    PRINT("%c", upHillDetectionFlag ? 'K' : 'k');
    PRINT("%c", cfgSmoothCurves ? 'S' : 's');
    PRINT("%c", cfgEnablePathFinder ? 'F' : 'f');
    PRINT(" MAP%d", maps.mapID);
    PRINT(" %3d", maps.mowPointsIdx);
    PRINT("/%-3d", maps.mowPoints.numPoints);

    CONSOLE.println();

    // logging for Kippschutz debugging
    // CONSOLE.print(F("maxDeltaPitch="));
    // CONSOLE.print(maxDeltaPitch * 180.0 / PI);
    // CONSOLE.print(F("°, maxPitch="));
    // CONSOLE.print(maxPitchDeg);
    // CONSOLE.print("°, numKippSchutzEvents=");
    // CONSOLE.println(numKippSchutzEvents);
    // maxDeltaPitch = -PI;
    // maxDeltaPwm = -255;
    // numKippSchutzEvents = 0;

    // log additional info
    // PRINT(" posStep=%f ", sim.posStep);
    // PRINT(" deltaStep=%f ", sim.deltaStep);
    // CONSOLE.println();

    //logCPUHealth();
  }
}
#endif
