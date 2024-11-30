iMapId = 0
iMapType = 1
iDrive = 2
iPos = 3
iBumper = 4
iTracking = 5
iSpeed = 6

PosFloat = 1
PosFix = 0

#MT_NORMAL_U=0, MT_NORMAL_V=1, MT_OBSTACLE=2, MT_OBSTACLE_IGNORE_GPS=3
DistIgnoreGps=100   # cm
NormalMapU = 0
NormalMapV = 1
ObstacleMap = 2
ObstacleMapIG = 3 + 4*DistIgnoreGps

BackWheelDrive = 0
FrontWheelDrive = 1
DefaultDrive = -1

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
   [  1, NormalMapV,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Einfahrt alt
   [  2, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Grigelat kurz
   [  3, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Brunner lang
   [  4, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Grigelat/Brunner unten
   [  5, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Grigelat lang
   [  6, NormalMapV,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Schuppen/Wald
   [  7, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Tischtennis
   [  8, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Schuppen/Hang
   [  9, NormalMapV,    FrontWheelDrive, PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Hinterm Haus
   [ 10, NormalMapU,    DefaultDrive,    PosFix,   BumperDefault, MoonlightTracking, DefaultSpeed ],        # Teststrecke
   [ 11, ObstacleMap,   BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Grigelat vorne
   [ 12, ObstacleMap,   BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Terrassenmauer
   [ 13, ObstacleMapIG, BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Wald/Schuppen
   [ 14, ObstacleMap,   BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Grigelat hinten  
   [ 15, ObstacleMap,   BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Brunner oben
   [ 16, NormalMapV,    FrontWheelDrive, PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Bassin
   [ 17, ObstacleMap,   BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Hinterm Haus/Wald
   [ 18, NormalMapV,    FrontWheelDrive, PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Rhododendron Brunner
   [ 19, ObstacleMapIG, BackWheelDrive,  PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ],        # Zaun Brunner unten
   [ 20, NormalMapV,    FrontWheelDrive, PosFix,   BumperEnabled, MoonlightTracking, DefaultSpeed ]         # Einfahrt neu
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

