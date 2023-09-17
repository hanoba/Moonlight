iMapId = 0
iMapType = 1
iDrive = 2
iPos = 3
iBumper = 4
iTracking = 5
iSpeed = 6

PosFloat = 1
PosFix = 0

ObstacleMap = 1
NormalMap = 0

BackWheelDrive = 0
FrontWheelDrive = 1

BumperDisabled = 0
BumperEnabled = 1
BumperDefault = -1

SunrayTracking = 0
MoonlightTracking = 1
DefaultTracking = -1

Speed = 0.5
DefaultSpeed = -1
FastSpeed = 0.50
SlowSpeed = 0.25

mapCfg = [
   [  1, NormalMap,   BackWheelDrive,  PosFix,   BumperDefault, SunrayTracking,    DefaultSpeed ],        # Einfahrt   
   [  2, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Grigelat kurz
   [  3, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Brunner lang
   [  4, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Grigelat/Brunner unten
   [  5, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Grigelat lang
   [  6, NormalMap,   BackWheelDrive,  PosFix,   BumperDefault, SunrayTracking,    DefaultSpeed ],        # Schuppen/Wald
   [  7, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Tischtennis
   [  8, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Schuppen/Hang
   [  9, NormalMap,   BackWheelDrive,  PosFix,   BumperDefault, SunrayTracking,    DefaultSpeed ],        # Hinterm Haus
   [ 10, NormalMap,   BackWheelDrive,  PosFloat, BumperDefault, SunrayTracking,    DefaultSpeed ],        # Teststrecke
   [ 11, ObstacleMap, FrontWheelDrive, PosFloat, BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Grigelat vorne
   [ 12, ObstacleMap, FrontWheelDrive, PosFloat, BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Terrassenmauer
   [ 13, ObstacleMap, FrontWheelDrive, PosFloat, BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Wald/Schuppen
   [ 14, ObstacleMap, FrontWheelDrive, PosFloat, BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Grigelat hinten  
]

def MapId(i):
   return mapCfg[i][iMapId]

def MapType(i):
   return mapCfg[i][iMapType]

def FrontWheelDrive(i):
   return mapCfg[i][iDrive]

def UseGpsFloatForPosEstimation(i):
   return mapCfg[i][iPos]

def BumperEnable(i):
   return mapCfg[i][iBumper]

def LineTracking(i):
   return mapCfg[i][iTracking]

def LinearSpeed(i):
   return mapCfg[i][iSpeed]


def main():
   for x in mapCfg:
      print(x)

if __name__ == '__main__':
    main()

