# FILE:  mower.py
# DESCRIPTION: This file conatins the following functions
#  - ClearStatistics
#  - ComputeMapChecksum
#  - GetRtcDateTime
#  - GetSummary
#  - GetVersionNumber
#  - Ping
#  - PrintStatistics
#  - ReadMapFromSdCard
#  - StartMowing
#  - StopMowing
#  - SwitchOffRobot
#  - SyncRtc
#  - ToggleBluetoothLogging
#  - ToggleGpsLogging
#  - ToggleSmoothCurves
#  - ToggleUseGPSfloatForDeltaEstimation
#  - ToggleUseGPSfloatForPosEstimation
#  - UploadMap
# 
import math
import maps
import udp
from udp import PrintGuiMessage
from datetime import datetime
from time import sleep

currentMapChecksum = 0
#currentWayPoints = []
showCurrentWayPoints = False
numMaps = 0

CMD_Ping = "AT+Y6"
CMD_UploadGpsConfigFilter = "AT+A"
CMD_PrintVersionNumber = "AT+V"
CMD_PrintStatistics = "AT+T"
CMD_ClearStatistics = "AT+L"
CMD_MotorTest = "AT+E"
CMD_TriggerObstacle = "AT+O"
CMD_SensorTest = "AT+F"
CMD_ToggleGpsSolution = "AT+G"
CMD_KidnappingTest = "AT+K"
CMD_StopMowing = "AT+C,-1,0,-1,-1,-1,-1,-1,-1"
CMD_StressTest = "AT+Z"
CMD_TriggerWatchdogTest = "AT+Y"
CMD_GnssReboot = "AT+Y2"
CMD_GnssHardwareReset = "AT+YR"
CMD_SwitchOffRobot = "AT+Y3"
CMD_TriggerRaspiShutdown = "AT+Y4"
CMD_ToggleBluetoothLogging = "AT+Y5"
CMD_ToggleUseGPSfloatForPosEstimation = "AT+YP"
CMD_ToggleUseGPSfloatForDeltaEstimation = "AT+YD"
CMD_ToggleSmoothCurves = "AT+YS"
CMD_ToggleEnablePathFinder = "AT+YF"
CMD_ToggleGpsLogging = "AT+YG"
CMD_GetSummary = "AT+S"
CMD_GetRtcDateTime = "AT+D"


# Return values of AT+S (summary) command
#  0 = F("S,");
#  1 = battery.batteryVoltage;
#  2 = stateX;
#  3 = stateY;
#  4 = stateDelta;
#  5 = gps.solution;
#  6 = stateOp;
#  7 = maps.mowPointsIdx;
#  8 = (millis() - gps.dgpsAge)/1000.0;
#  9 = stateSensor;
# 10 = maps.targetPoint.x();
# 11 = maps.targetPoint.y();
# 12 = gps.accuracy;
# 13 = gps.numSV;
# 14 = charge current or motor current
# 15 = gps.numSVdgps;
# 16 = maps.mapCRC;
def GetSummary():
   answer = udp.ExecCmd(CMD_GetSummary)
   if answer=="": return
   fields = answer.split(",")
   
   checkSum = int(fields[16])
   stateDelta = round(float(fields[4])*180/math.pi,0);
   
   textStateOp = ["IDLE", "MOW", "CHARGE", "ERROR", "DOCK", "???"]
   stateOp = int(fields[ 6])
   if stateOp < 0 or stateOp > 5: stateOp=5
   
   textGpsSolution = ["INVALID", "FLOAT", "FIX", "???"]
   gpsSolution = int(fields[5])
   if gpsSolution < 0 or gpsSolution > 3: gpsSolution=3
   
   textSensor = [ "NONE", "BAT_UNDERVOLTAGE", "OBSTACLE", "GPS_FIX_TIMEOUT", "IMU_TIMEOUT", "IMU_TILT", "KIDNAPPED", "OVERLOAD", "MOTOR_ERROR",  
               "GPS_INVALID", "ODOMETRY_ERROR", "MAP_NO_ROUTE", "MEM_OVERFLOW", "BUMPER", "SONAR", "LIFT", "RAIN", "STOP_BUTTON", "???" ]
   stateSensor = int(fields[9])
   if stateSensor < 0 or stateSensor >= len(textSensor): stateSensor = len(textSensor) - 1

#   print("Battery Voltage:        ", fields[ 1], "V")
#   print("StateX:                 ", fields[ 2], "m")
#   print("StateY:                 ", fields[ 3], "m")
#   print("StateDelta:             ", stateDelta, "°")
#   print("GPS solution:           ", textGpsSolution[gpsSolution])
#   print("Operating State:        ", textStateOp[stateOp])
#   print("Mow Point Index:        ", fields[ 7])
#   print("GPS Age:                ", fields[ 8], "sec")
#   print("Last triggered sensor:  ", textSensor[stateSensor])
#   print("TargetPointX:           ", fields[10], "m")
#   print("TargetPointY:           ", fields[11], "m")
#   print("GPS Accuracy;           ", fields[12], "m")
#   print("Num Satellites          ", fields[13])
#   print("Charge/motor current:   ", fields[14], "A")
#   print("Num DGPS Satellites:    ", fields[15])
#   print("Map Checksum:           ", checkSum)

   udp.WriteLog("[mower.GetSummary] Battery Voltage:        " + fields[ 1] + "V")
   udp.WriteLog("[mower.GetSummary] StateX:                 " + fields[ 2] + "m")
   udp.WriteLog("[mower.GetSummary] StateY:                 " + fields[ 3] + "m")
   udp.WriteLog("[mower.GetSummary] StateDelta:             " + str(stateDelta) + "°")
   udp.WriteLog("[mower.GetSummary] GPS solution:           " + textGpsSolution[gpsSolution])
   udp.WriteLog("[mower.GetSummary] Operating State:        " + textStateOp[stateOp])
   udp.WriteLog("[mower.GetSummary] Mow Point Index:        " + fields[ 7])
   udp.WriteLog("[mower.GetSummary] GPS Age:                " + fields[ 8] + "sec")
   udp.WriteLog("[mower.GetSummary] Last triggered sensor:  " + textSensor[stateSensor])
   udp.WriteLog("[mower.GetSummary] TargetPointX:           " + fields[10] + "m")
   udp.WriteLog("[mower.GetSummary] TargetPointY:           " + fields[11] + "m")
   udp.WriteLog("[mower.GetSummary] GPS Accuracy;           " + fields[12] + "m")
   udp.WriteLog("[mower.GetSummary] Num Satellites          " + fields[13])
   udp.WriteLog("[mower.GetSummary] Charge/motor current:   " + fields[14] + "A")
   udp.WriteLog("[mower.GetSummary] Num DGPS Satellites:    " + fields[15])
   udp.WriteLog("[mower.GetSummary] Map Checksum:           " + str(checkSum))
   return checkSum

def SyncRtc():
   now = datetime.now()
   cmd = now.strftime("AT+D,%y,%m,%d,%H,%M,%S,%w")
   answer = udp.ExecCmd(cmd)
   if answer=="": return
   PrintGuiMessage(answer);

def GetRtcDateTime():
   answer = udp.ExecCmd(CMD_GetRtcDateTime)
   if answer=="": return
   answer = answer[2:len(answer)-7]
   PrintGuiMessage(answer);
   
def ComputeMapChecksum():
   #checksum = maps.ComputeMapChecksum(currentMapIndex)
   #print("[amcp] Map checksum:", checksum)
   PrintGuiMessage("Checksum computed by mower: {}".format(GetSummary()))

def GetVersionNumber():
   result = udp.ExecCmd(CMD_PrintVersionNumber)
   if result != "": 
      PrintGuiMessage(result[2:len(result)-7])

def GnssReboot():
   udp.ExecCmd(CMD_GnssReboot)

def GnssHardwareReset():
   udp.ExecCmd(CMD_GnssHardwareReset)

def ToggleBluetoothLogging():
   udp.ExecCmd(CMD_ToggleBluetoothLogging)

def ToggleUseGPSfloatForDeltaEstimation():
   udp.ExecCmd(CMD_ToggleUseGPSfloatForDeltaEstimation)

def ToggleUseGPSfloatForPosEstimation():
   udp.ExecCmd(CMD_ToggleUseGPSfloatForPosEstimation)

def ToggleSmoothCurves():
   udp.ExecCmd(CMD_ToggleSmoothCurves)

def ToggleEnablePathFinder():
   udp.ExecCmd(CMD_ToggleEnablePathFinder)

def ToggleGpsLogging():
   udp.ExecCmd(CMD_ToggleGpsLogging)

def Ping():
   udp.ExecCmd(CMD_Ping)
   
def ReadMapFromSdCard(mapId):
   udp.send(str.format('AT+R,{:d}', mapId))
   mapIndex = mapId - 1
   expectedCheckSum = maps.ComputeMapChecksum(mapIndex)
   mowerChecksum = GetSummary()
   sleep(0.5)
   print("Expected Checksum:", expectedCheckSum)
   if expectedCheckSum == mowerChecksum: PrintGuiMessage("Map successfully loaded from SD Card")
   else: PrintGuiMessage("Maps not synchronized")
   #udp.ExecCmd(str.format('AT+R,{:d}', mapId))

def StartMowing(fSpeed=0.25, iFixTimeout=0):
   # AT+C,1,1,0.39,0,0,-1,-1,0,0x8  # -1 means no change, keep current value
   #bEnableMowMotor = 1           # on
   #iOperationType = 1            # 1=OP_MOW
   #fSpeed = 0.25                  # m/s
   #iFixTimeout = 0               # 0 = no fix timeout
   #bFinishAndRestart = 0         # disabled
   #fMowingPointPercent = -1      # 
   #bSkipNextMowingPoint = -1     #
   #bEnableSonar = 0              # disabled
   #cmd = str.format('AT+C,-1,1,{:.2f},0,0,-1,-1,0', fSpeed)
   cmd = str.format('AT+C,1,1,{:.2f},{:d},0,-1,-1,0', fSpeed, iFixTimeout)     #HB enable mow motor + add iFixTimeout
   udp.ExecCmd(cmd)

def StartDocking():
   # AT+C,-1,1,0.39,0,0,-1,-1,0,0x8
   #bEnableMowMotor = 0           # off
   #iOperationType = 4            # 4=OP_DOCK
   fSpeed = 0.3                   # m/s
   #iFixTimeout = 0               # 0 = no fix timeout
   #bFinishAndRestart = 0         # disabled
   #fMowingPointPercent = -1      # 
   #bSkipNextMowingPoint = -1     # disabled
   #bEnableSonar = 0              # disabled
   cmd = str.format('AT+C,0,4,{:.2f},0,0,-1,-1,0', fSpeed)
   udp.ExecCmd(cmd)

def StartUndocking():
   # AT+C,-1,1,0.39,0,0,-1,-1,0,0x8
   #bEnableMowMotor = 0           # off
   #iOperationType = 5            # 5=OP_UNDOCK
   fSpeed = 0.1                   # m/s
   #iFixTimeout = 0               # 0 = no fix timeout
   #bFinishAndRestart = 0         # disabled
   #fMowingPointPercent = -1      # 
   #bSkipNextMowingPoint = -1     # disabled
   #bEnableSonar = 0              # disabled
   cmd = str.format('AT+C,0,5,{:.2f},0,0,-1,-1,0', fSpeed)
   udp.ExecCmd(cmd)

def SwitchOffRobot():
   udp.ExecCmd(CMD_SwitchOffRobot)

# statIdleDuration;
# statChargeDuration;
# statMowDuration;
# statMowDurationFloat;
# statMowDurationFix;
# statMowFloatToFixRecoveries;
# statMowDistanceTraveled;
# statMowMaxDgpsAge;
# statImuRecoveries;
# statTempMin;
# statTempMax;
# gps.chksumErrorCounter;
# gps.dgpsChecksumErrorCounter;
# statMaxControlCycleTime;
# SERIAL_BUFFER_SIZE;
# statMowDurationInvalid;
# statMowInvalidRecoveries;
# statMowObstacles;
# freeMemory();
# getResetCause();
# statGPSJumps;
# statMowSonarCounter;
# statMowBumperCounter;
# statMowGPSMotionTimeoutCounter;
def PrintStatistics():
   answer = udp.ExecCmd(CMD_PrintStatistics)
   if answer=="": return
   fields = answer.split(",")
   i=1
   udp.WriteLog("[mower.PrintStatistics] statIdleDuration               :" + fields[i+0])
   udp.WriteLog("[mower.PrintStatistics] statChargeDuration             :" + fields[i+1])
   udp.WriteLog("[mower.PrintStatistics] statMowDuration                :" + fields[i+2])
   udp.WriteLog("[mower.PrintStatistics] statMowDurationFloat           :" + fields[i+3])
   udp.WriteLog("[mower.PrintStatistics] statMowDurationFix             :" + fields[i+4])
   udp.WriteLog("[mower.PrintStatistics] statMowFloatToFixRecoveries    :" + fields[i+5])
   udp.WriteLog("[mower.PrintStatistics] statMowDistanceTraveled        :" + fields[i+6])
   udp.WriteLog("[mower.PrintStatistics] statMowMaxDgpsAge              :" + fields[i+7])
   udp.WriteLog("[mower.PrintStatistics] statImuRecoveries              :" + fields[i+8])
   udp.WriteLog("[mower.PrintStatistics] statTempMin                    :" + fields[i+9])
   udp.WriteLog("[mower.PrintStatistics] statTempMax                    :" + fields[i+10])
   udp.WriteLog("[mower.PrintStatistics] gps.chksumErrorCounter         :" + fields[i+11])
   udp.WriteLog("[mower.PrintStatistics] gps.dgpsChecksumErrorCounter   :" + fields[i+12]) 
   udp.WriteLog("[mower.PrintStatistics] statMaxControlCycleTime        :" + fields[i+13])
   udp.WriteLog("[mower.PrintStatistics] SERIAL_BUFFER_SIZE             :" + fields[i+14])
   udp.WriteLog("[mower.PrintStatistics] statMowDurationInvalid         :" + fields[i+15])
   udp.WriteLog("[mower.PrintStatistics] statMowInvalidRecoveries       :" + fields[i+16])
   udp.WriteLog("[mower.PrintStatistics] statMowObstacles               :" + fields[i+17])
   udp.WriteLog("[mower.PrintStatistics] freeMemory()                   :" + fields[i+18])
   udp.WriteLog("[mower.PrintStatistics] getResetCause()                :" + fields[i+19])
   udp.WriteLog("[mower.PrintStatistics] statGPSJumps                   :" + fields[i+20])
   udp.WriteLog("[mower.PrintStatistics] statMowSonarCounter            :" + fields[i+21])
   udp.WriteLog("[mower.PrintStatistics] statMowBumperCounter           :" + fields[i+22])
   udp.WriteLog("[mower.PrintStatistics] statMowGPSMotionTimeoutCounter :" + fields[i+23])

def ClearStatistics():
   udp.ExecCmd(CMD_ClearStatistics)

def UploadMap(mapId):
   if mapId < 1 or mapId > 15:
      print("ERROR: Valid range for MapId is 1 to 15");
      return
   mapIndex = mapId - 1
   PrintGuiMessage("Uploading map started...");
   if maps.UploadMap(mapIndex)==maps.ERROR:
      print("[CmdUploadMap] ERROR during map upload")
      PrintGuiMessage("ERROR during map upload")
   else:
      checksum = maps.ComputeMapChecksum(mapIndex)
      print("[maps.ComputeMapChecksum] Checksum = ", checksum)
      reportedChecksum = GetSummary()
      if reportedChecksum == checksum:
         PrintGuiMessage("Map upload completed successfully")
      else:
         PrintGuiMessage("Map upload checksum error")

def StopMowing():
   udp.ExecCmd(CMD_StopMowing)

def UploadGpsConfigFilter(gpsConfigFilter):
   udp.ExecCmd(CMD_UploadGpsConfigFilter + "," + gpsConfigFilter)

