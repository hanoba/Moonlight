# Importieren der Pygame-Bibliothek
import pygame
import math
import maps
import plan
import udp
import mower
from datetime import datetime
import pygame_menu
#from msg import guiMessage
from msg import PrintGuiMessage, GetGuiMessage

#guiMessage=""

LEFT = 1
RIGHT = 3

r=3
iCurrentRefPoint = r
editMode = False
   

currentMapIndex = 3
currentMapChecksum = 0
#currentWayPoints = []
showCurrentWayPoints = False
numMaps = 0

#CMD_PrintVersionNumber = "AT+V"
#CMD_PrintStatistics = "AT+T"
#CMD_ClearStatistics = "AT+L"
#CMD_MotorTest = "AT+E"
#CMD_TriggerObstacle = "AT+O"
#CMD_SensorTest = "AT+F"
#CMD_ToggleGpsSolution = "AT+G"
#CMD_KidnappingTest = "AT+K"
#CMD_StopMowing = "AT+C,-1,0,-1,-1,-1,-1,-1,-1"
#CMD_StressTest = "AT+Z"
#CMD_TriggerWatchdogTest = "AT+Y"
#CMD_SwitchOffRobot = "AT+Y3"
#CMD_TriggerRaspiShutdown = "AT+Y4"
#CMD_ToggleBluetoothLogging = "AT+Y2"
#CMD_ToggleUseGPSfloatForPosEstimation = "AT+YP"
#CMD_ToggleUseGPSfloatForDeltaEstimation = "AT+YD"
#CMD_ToggleGPSLogging = "AT+YV"
FONT_SIZE = 14
LINE_SPACING = FONT_SIZE + 1



def SetCurrentMapIndex(index):
    global currentMapIndex, currentMapChecksum
    global r
    global lastPerimeter
    global redoPerimeter
    currentMapIndex = index
    if len(maps.perimeters[currentMapIndex])==0:
        #wpoly = [ (797, 173), (922, 89), (1099, 373), (974, 431)]
        #w = 50
        #originX = maps.originX
        #originY = maps.originY
        #wpoly = [ (originX-w, originY-w), (originX-w, originY+w), (originX+w, originY+w),(originX+w, originY-w)] 
        maps.perimeters[currentMapIndex] = maps.NewMap().copy()  # wpoly.copy()
    lastPerimeter=maps.perimeters[currentMapIndex].copy()
    redoPerimeter=lastPerimeter
    showCurrentWayPoints = False
    currentMapChecksum = maps.ComputeMapChecksum(currentMapIndex)
    r = 0

def PrintMouseDistance():
   pos = pygame.mouse.get_pos()
   distance = "Distance mouse current edit point:     {0:7.2f} m".format(maps.Distance(maps.perimeters[currentMapIndex][r], pos))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((50, 50+0*LINE_SPACING))
   screen.blit(text, textRect)


def PrintRefPointDistance():
   if len(maps.perimeters[9]) == 0: 
        return
   pos = pygame.mouse.get_pos()
   distance = "Distance mouse/current reference point:{0:7.2f} m".format(maps.Distance(maps.perimeters[9][iCurrentRefPoint], pos))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((50, 50+1*LINE_SPACING))
   screen.blit(text, textRect)


def PrintDistance():
   distance = "Distance current/last edit point:      {0:7.2f} m".format(maps.Distance(maps.perimeters[currentMapIndex][r], lastPerimeter[r]))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((50, 50+2*LINE_SPACING))
   screen.blit(text, textRect)

def PrintVersionNumber():
   if GetGuiMessage() != "":
      text = bigFont.render(GetGuiMessage(), True, WHITE, BLACK)
      textRect = text.get_rect()
      textRect.topright = ((maps.screenX-20, maps.screenY-80))
      screen.blit(text, textRect)


def WriteTextBox(text, lineNum=-1):
   if lineNum < 0:
      WriteTextBox.line = WriteTextBox.line + 1
   else:
      WriteTextBox.line = lineNum
   text = bigFont.render(text, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((50, 100+LINE_SPACING*WriteTextBox.line))
   screen.blit(text, textRect)


def PrintHelpText():
   numWayPoints = len(maps.wayPoints[currentMapIndex])
   MapId = currentMapIndex + 1
   WriteTextBox(str.format("Current Map ID:      {:8d}             ", MapId), 0)
   WriteTextBox(str.format("Checksum:            {:8d}             ", currentMapChecksum))
   WriteTextBox(str.format("Number of waypoints: {:8d}             ", numWayPoints))
   WriteTextBox("<v>   PrintVersionNumber                  ")
   #WriteTextBox("<b>   ToggleBluetoothLogging              ")
   WriteTextBox("<m>   Start mowing                        ")
   WriteTextBox("<o>   SwitchOffRobot                      ")
   #WriteTextBox("<p>   ToggleUseGPSfloatForPosEstimation   ")
   #WriteTextBox("<d>   ToggleUseGPSfloatForDeltaEstimation ")
   WriteTextBox("<s>   PrintStatistics                     ")
   WriteTextBox("<u>   Upload current map                  ")
   WriteTextBox("<i>   Stop mowing                         ")
   #WriteTextBox("<DEL> ClearStatistics                     ")
   WriteTextBox("<0>   Select reference points             ")
   WriteTextBox("<1> to <9> Select perimeter 1 to 9        ")
   WriteTextBox("<F2>  Save maps to file maps2.json        ")
   WriteTextBox("<F4>  Toggle edit mode                    ")
   WriteTextBox("<F5>  Show/hide waypoints                 ")
   WriteTextBox("<F6>  Create waypoints                    ")
   WriteTextBox("<F7>  Make parallel                       ")
   WriteTextBox("<^y>  Redo                                ")
   WriteTextBox("<^z>  Undo                                ")
   WriteTextBox("<TAB> Select next perimeter point         ")
   WriteTextBox("<SPC> Select previous perimeter point     ")
   WriteTextBox("<ESC> Main Menu                           ")


def PrintLogMsg():
   if not hasattr(PrintLogMsg, "headline"):
       PrintLogMsg.headline = "Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy     Gd     Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags Map Info    "
       PrintLogMsg.oldMsg = " "
   msg = udp.receive()
   if msg != "":
      if msg[0] == ':':    PrintLogMsg.oldMsg = msg[1:len(msg)-2]
      elif msg[0] == '#':  PrintLogMsg.headline = msg[1:len(msg)-2]
      print(msg, end='', flush=True)
   # print headline
   text = bigFont.render(PrintLogMsg.headline, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((10, 15-(LINE_SPACING-1)))
   screen.blit(text, textRect)
   # print logging text
   text = bigFont.render(PrintLogMsg.oldMsg, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((10, 15))
   screen.blit(text, textRect)

def DrawCross(color, point):
   (x,y) = point
   s = 5
   w = 1
   pygame.draw.line(screen, color, (x-s, y), (x+s, y), w)
   pygame.draw.line(screen, color, (x, y-s), (x, y+s), w)


# initialisieren von pygame
pygame.init()

# genutzte Farbe
ORANGE  = ( 255, 140, 0)
RED     = ( 255, 0, 0)
GREEN   = ( 0, 255, 0)
BLUE    = ( 0, 0, 255)
BLACK = ( 0, 0, 0)
WHITE   = ( 255, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (102, 0, 102)

# Fenster öffnen
screen = pygame.display.set_mode((maps.screenX, maps.screenY))

# Titel für Fensterkopf
pygame.display.set_caption("ArduMower Control Program")

gartenImg = pygame.image.load("garten-google-maps-zoom.png")

# Bildschirm Aktualisierungen einstellen
clock = pygame.time.Clock()

# Schleife Hauptprogramm
garten_old = plan.Garten_old()
maps.Plan2Map(garten_old)
maps.Map2Screen(garten_old)

garten = plan.Garten()
maps.Plan2Map(garten)
maps.Map2Screen(garten)

rx = maps.cos_phi
ry = maps.sin_phi

hx = -maps.sin_phi
hy =  maps.cos_phi

#Messungen
mh=1.17*1
mr=0.10*1
sh=0.16
sr=-3.57
messungen = [(-3.15+rx*mr+hx*mh, -5.62+ry*mr+hy*mh),(-17.76+rx*sr+hx*sh,-9.68+ry*sr+hy*sh), (-21.77, -13.99)]
maps.Map2Screen(messungen)

haus = plan.Gartenhaus()
maps.Plan2Map(haus)
maps.Map2Screen(haus)

terrasse = plan.Terrasse()
maps.Plan2Map(terrasse)
maps.Map2Screen(terrasse)

# Schuppen
schuppen = plan.Schuppen()
maps.Plan2Map(schuppen)
maps.Map2Screen(schuppen)

# waypoints
maps.LoadMaps()

# Origin
origin = [(0,0)]
maps.Map2Screen(origin)
origin = origin[0]
wl=3

# create a font object.
# 1st parameter is the font file
# which is present in pygame.
# 2nd parameter is size of the font
font = pygame.font.Font('freesansbold.ttf', 10)
bigFont = pygame.font.SysFont('Courier New', FONT_SIZE)
 



y=50
dy=1
#rectangle=[ (797, 173), (922, 89), (1099, 373), (974, 431)]

SetCurrentMapIndex(currentMapIndex)
r=0

theme_dark = pygame_menu.themes.THEME_DARK.copy()
theme_dark.widget_font_size=20
theme_dark.title_font_size=30
menu = pygame_menu.Menu('Main Menu', 600, 800, theme=theme_dark)


def ArdumowerControlProgram():
   global currentMapIndex
   global r
   global lastPerimeter
   global redoPerimeter
   global iCurrentRefPoint 
   global showCurrentWayPoints
   global numMaps
   global menu
   global editMode
   
   menu.add.button('Show/Hide MainMenu (ESC)', CmdShowHideMainMenu)
   menu.add.button('Upload current map (u)', CmdUploadMap)
   menu.add.button('Start mowing (m)', mower.StartMowing)
   menu.add.button('Stop mowing (i)', mower.StopMowing)
   menu.add.button('Switch Off Robot (o)', mower.SwitchOffRobot)
   menu.add.button('Get Version Number (v)', mower.GetVersionNumber)
   menu.add.button('Toggle Bluetooth Logging (b)', mower.ToggleBluetoothLogging)
   menu.add.button('Toggle UseGPSfloatForPosEstimation (p)', mower.ToggleUseGPSfloatForPosEstimation)
   menu.add.button('Toggle UseGPSfloatForDeltaEstimation (d)', mower.ToggleUseGPSfloatForDeltaEstimation)
   menu.add.button('PrintStatistics (s)', mower.PrintStatistics)
   menu.add.button('ClearStatistics (c)', mower.ClearStatistics)
   menu.add.button('Store Maps (F2)', CmdStoreMaps)
   menu.add.button('Show/Hide Waypoints (F5)', CmdToggleShowWaypoints)
   menu.add.button('Create Waypoints (F6)', CmdCreateWaypoints)
   menu.add.button('Make Square Parallel (F7)', CmdMakeSquareParallel)
   menu.add.button('Read Map From SD Card (r)', CmdReadMapFromSdCard)
   menu.add.button('Get Map Checksum From Mower', mower.ComputeMapChecksum)
   menu.add.button('Get RTC Date & Time', mower.GetRtcDateTime)
   menu.add.button('Sync RTC with current time', mower.SyncRtc)
   menu.add.text_input('Maps File Name: ', textinput_id='ID_MAPS_FILE_NAME', default='maps2.json')
   menu.add.button('Quit (q)', pygame_menu.events.EXIT)

   # solange die Variable True ist, soll das Spiel laufen
   programActive = True
   
   while programActive:
      # Überprüfen, ob Nutzer eine Aktion durchgeführt hat
      events = pygame.event.get()
      for event in events:
         if event.type == pygame.QUIT:
               programActive = False
         elif event.type == pygame.KEYDOWN:
               if event.key == pygame.K_ESCAPE:
                  CmdShowHideMainMenu()
               elif not menu.is_enabled():
                  if event.key == pygame.K_RIGHT and editMode:
                     (x,y) = maps.perimeters[currentMapIndex][r]
                     maps.perimeters[currentMapIndex][r] = (x+1,y)
                     PrintDistance()
                  elif event.key == pygame.K_LEFT and editMode:
                     (x,y) = maps.perimeters[currentMapIndex][r]
                     maps.perimeters[currentMapIndex][r] = (x-1,y)
                     PrintDistance()
                  elif event.key == pygame.K_UP and editMode:
                     (x,y) = maps.perimeters[currentMapIndex][r]
                     maps.perimeters[currentMapIndex][r] = (x,y-1)
                     PrintDistance()
                  elif event.key == pygame.K_DOWN and editMode:
                     (x,y) = maps.perimeters[currentMapIndex][r]
                     maps.perimeters[currentMapIndex][r] = (x,y+1)
                     PrintDistance()
                  elif event.key == pygame.K_0:
                     SetCurrentMapIndex(9)
                  elif event.key == pygame.K_1:
                     SetCurrentMapIndex(0)
                  elif event.key == pygame.K_2:
                     SetCurrentMapIndex(1)
                  elif event.key == pygame.K_3:
                     SetCurrentMapIndex(2)
                  elif event.key == pygame.K_4:
                     SetCurrentMapIndex(3)
                  elif event.key == pygame.K_5:
                     SetCurrentMapIndex(4)
                  elif event.key == pygame.K_6:
                     SetCurrentMapIndex(5)
                  elif event.key == pygame.K_7:
                     SetCurrentMapIndex(6)
                  elif event.key == pygame.K_8:
                     SetCurrentMapIndex(7)
                  elif event.key == pygame.K_9:
                     SetCurrentMapIndex(8)
                  elif event.key == pygame.K_b:
                     mower.ToggleBluetoothLogging()
                  elif event.key == pygame.K_c:
                     mower.ClearStatistics()
                  elif event.key == pygame.K_d:
                     mower.ToggleUseGPSfloatForDeltaEstimation()
                  elif event.key == pygame.K_i:
                     mower.StopMowing()
                  elif event.key == pygame.K_m:
                     mower.StartMowing()
                  elif event.key == pygame.K_o:
                     mower.SwitchOffRobot()
                  elif event.key == pygame.K_p:
                     mower.ToggleUseGPSfloatForPosEstimation()
                  elif event.key == pygame.K_q:
                     programActive = False
                  elif event.key == pygame.K_r:
                     CmdReadMapFromSdCard()
                  elif event.key == pygame.K_s:
                     mower.PrintStatistics()
                  elif event.key == pygame.K_u:
                     CmdUploadMap()
                  elif event.key == pygame.K_v:
                     mower.GetVersionNumber()
                  elif event.key == pygame.K_y:
                     if event.mod & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL):
                        maps.perimeters[currentMapIndex]=redoPerimeter.copy()
                        PrintDistance()
                  elif event.key == pygame.K_z:
                     if event.mod & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL):
                        redoPerimeter=maps.perimeters[currentMapIndex].copy()
                        maps.perimeters[currentMapIndex]=lastPerimeter.copy()
                        PrintDistance()
                  elif event.key == pygame.K_SPACE and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     r -= 1
                     if r<0: r=len(maps.perimeters[currentMapIndex])-1
                  elif event.key == pygame.K_TAB and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     r += 1
                     if r>=len(maps.perimeters[currentMapIndex]): r=0
                  elif event.key == pygame.K_F2:
                     CmdStoreMaps()
                  elif event.key == pygame.K_F4:
                     editMode = not editMode
                  elif event.key == pygame.K_F5:
                     CmdToggleShowWaypoints()
                  elif event.key == pygame.K_F6 and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
                     showCurrentWayPoints = True
                  elif event.key == pygame.K_F7 and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     maps.MakeParallel(maps.perimeters[currentMapIndex], r)
         elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT and editMode:
               #lastPerimeter=maps.perimeters[currentMapIndex].copy()
               pos = pygame.mouse.get_pos()
               maps.perimeters[currentMapIndex][r] = pos
               PrintDistance()
         elif event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT and editMode:
               #lastPerimeter=maps.perimeters[currentMapIndex].copy()
               pos = pygame.mouse.get_pos()
               maps.MoveRectangle(maps.perimeters[currentMapIndex], r, pos)
               PrintDistance()
      
      # Google Maps image vom Garten als Hintergrund
      screen.blit(gartenImg, (0,0))
   
      PrintHelpText()
      
      # Garten und Gebäude zeichnen
      # pygame.draw.lines(screen, WHITE, True, garten_old, 3)
      pygame.draw.lines(screen, GREEN, True, garten, 3)
      pygame.draw.lines(screen, BLUE,  True, haus, 3)
      pygame.draw.lines(screen, BLUE,  True, terrasse, 3)
      pygame.draw.lines(screen, BLUE,  True, schuppen, 3)
   
      # Nullpunkt
      # pygame.draw.circle(screen, WHITE, origin, 6)
      DrawCross(WHITE, origin)
      
      # Messungen
      pygame.draw.circle(screen, RED, messungen[0], 2)
      pygame.draw.circle(screen, RED, messungen[1], 2)
      pygame.draw.circle(screen, RED, messungen[2], 2)
      
      # Show mower location
      mowerLocation = maps.Map2ScreenXY(udp.stateX, udp.stateY)
      pygame.draw.circle(screen, YELLOW, mowerLocation, 5, 1)
      
      # Show mower GPS location
      gpsLocation = maps.Map2ScreenXY(udp.gpsX, udp.gpsY)
      pygame.draw.circle(screen, PURPLE, gpsLocation, 3)
      
      # Show target location
      targetLocation = maps.Map2ScreenXY(udp.targetX, udp.targetY)
      pygame.draw.circle(screen, GREEN, targetLocation, 5, 1)
   
      # Show log message
      PrintLogMsg()
   
      # Draw maps.perimeters
      imax = min(9, len(maps.perimeters))
      for i in range(imax):
         if len(maps.perimeters[i]) > 0:
            color = ORANGE
            if i==currentMapIndex:
               if editMode: color = RED
               else: color = WHITE
            pygame.draw.lines(screen, color,  True, maps.perimeters[i], 1)
            #text = font.render(chr(48+i+1), True, GREEN, BLUE)
            mapNum = "{0:d}".format(i+1)
            text = font.render(mapNum, True, GREEN, BLUE)
            textRect = text.get_rect()
            # set the center of the rectangular object.
            (x0, y0) = maps.perimeters[i][0]
            textRect.center = ((x0-3, y0-3))
            # draw text
            screen.blit(text, textRect)
   
      # Draw reference points
      iRefPoints=9
      if len(maps.perimeters[iRefPoints]) > 0:
         for k in range(len(maps.perimeters[iRefPoints])):
            color = WHITE
            if k == iCurrentRefPoint: color = ORANGE
            #pygame.draw.circle(screen, color, maps.perimeters[iRefPoints][k], 3)
            DrawCross(color, maps.perimeters[iRefPoints][k])
      
      # draw maps.perimeters[currentMapIndex]
      # pygame.draw.lines(screen, BLUE,  True, maps.perimeters[currentMapIndex], 1)
      pygame.draw.circle(screen, WHITE, maps.perimeters[currentMapIndex][r], 3)
      if showCurrentWayPoints and len(maps.wayPoints[currentMapIndex]) > 2: 
         pygame.draw.lines(screen, WHITE, False, maps.wayPoints[currentMapIndex], 1)
         pygame.draw.circle(screen, RED, maps.wayPoints[currentMapIndex][0], 3)
      
      # Remember last reference point
      if currentMapIndex == 9: iCurrentRefPoint = r
      
      PrintDistance()
      PrintMouseDistance()
      PrintRefPointDistance()
      PrintVersionNumber()
      
      # Draw menu
      if menu.is_enabled():
          menu.draw(screen)
          menu.update(events)
      
      # Fenster aktualisieren
      pygame.display.flip()
   
      # Refresh-Zeiten festlegen
      clock.tick(60)


## Return values of AT+S (summary) command
##  0 = F("S,");
##  1 = battery.batteryVoltage;
##  2 = stateX;
##  3 = stateY;
##  4 = stateDelta;
##  5 = gps.solution;
##  6 = stateOp;
##  7 = maps.mowPointsIdx;
##  8 = (millis() - gps.dgpsAge)/1000.0;
##  9 = stateSensor;
## 10 = maps.targetPoint.x();
## 11 = maps.targetPoint.y();
## 12 = gps.accuracy;
## 13 = gps.numSV;
## 14 = charge current or motor current
## 15 = gps.numSVdgps;
## 16 = maps.mapCRC;
#def GetSummary():
#   answer = udp.ExecCmd("AT+S")
#   if answer=="": return
#   fields = answer.split(",")
#   checkSum = int(fields[16])
#   print("BatteryVoltage =", float(fields[1]))
#   print("MowPoint.Index =", int(fields[7]))
#   print("MapCRC =", checkSum)
#   return checkSum
#
#def PrintGuiMessage(msg):
#   global guiMessage
#   guiMessage = msg
#   print("[GuiMessage] " + msg)
#
#def CmdSyncRtc():
#   now = datetime.now()
#   cmd = now.strftime("AT+D,%y,%m,%d,%H,%M,%S,%w")
#   answer = udp.ExecCmd(cmd)
#   if answer=="": return
#   PrintGuiMessage(answer);
#
#def CmdGetRtcDateTime():
#   answer = udp.ExecCmd("AT+D")
#   if answer=="": return
#   answer = answer[2:len(answer)-7]
#   PrintGuiMessage(answer);
#   
#def CmdComputeMapChecksum():
#   #checksum = maps.ComputeMapChecksum(currentMapIndex)
#   #print("[amcp] Map checksum:", checksum)
#   PrintGuiMessage("Checksum computed by mower: {}".format(GetSummary()))

def CmdShowHideMainMenu():
   global editMode
   editMode = False
   menu.toggle()
   data = menu.get_input_data()
   if menu.is_enabled(): PrintGuiMessage("")
   #mapsFileName = data.get('ID_MAPS_FILE_NAME')
   #print("Maps File Name: " + mapsFileName)

def CmdToggleShowWaypoints():
   global showCurrentWayPoints
   showCurrentWayPoints = not showCurrentWayPoints

#def CmdGetVersionNumber():
#   result = udp.ExecCmd(CMD_PrintVersionNumber)
#   if result != "": 
#      PrintGuiMessage(result[2:len(result)-7])
#
#def CmdToggleBluetoothLogging():
#   udp.send(CMD_ToggleBluetoothLogging)
#
#def CmdToggleUseGPSfloatForDeltaEstimation():
#   udp.send(CMD_ToggleUseGPSfloatForDeltaEstimation)
#
def CmdReadMapFromSdCard():
   mapId = currentMapIndex + 1
   mower.ReadMapFromSdCard(mapId)

#def CmdStartMowing():
#   # AT+C,-1,1,0.39,0,0,-1,-1,0,0x8
#   #bEnableMowMotor = -1          # off
#   #iOperationType = 1            # 1=OP_MOW
#   fSpeed = 0.25                 # m/s
#   #iFixTimeout = 0               # 0 = no fix timeout
#   #bFinishAndRestart = 0         # disabled
#   #fMowingPointPercent = -1      # 
#   #bSkipNextMowingPoint = -1     # disabled
#   #bEnableSonar = 0              # disabled
#   cmd = str.format('AT+C,-1,1,{:.2f},0,0,-1,-1,0', fSpeed)
#   #if SendCmd(cmd)==ERROR: print("[CmdStartMowing] ERROR")
#   udp.send(cmd)

def CmdStoreMaps():
   global menu
   data = menu.get_input_data()
   mapsFileName = data.get('ID_MAPS_FILE_NAME')
   maps.StoreMaps(mapsFileName)
   PrintGuiMessage("Maps successfully stored in file " + mapsFileName)

   
#def CmdToggleUseGPSfloatForPosEstimation():
#   udp.send(CMD_ToggleUseGPSfloatForPosEstimation)
#
#def CmdSwitchOffRobot():
#   udp.send(CMD_SwitchOffRobot)

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
#def CmdPrintStatistics():
#   answer = udp.ExecCmd(CMD_PrintStatistics)
#   if answer=="": return
#   fields = answer.split(",")
#   i=1
#   print("statIdleDuration               :", fields[i+0])
#   print("statChargeDuration             :", fields[i+1])
#   print("statMowDuration                :", fields[i+2])
#   print("statMowDurationFloat           :", fields[i+3])
#   print("statMowDurationFix             :", fields[i+4])
#   print("statMowFloatToFixRecoveries    :", fields[i+5])
#   print("statMowDistanceTraveled        :", fields[i+6])
#   print("statMowMaxDgpsAge              :", fields[i+7])
#   print("statImuRecoveries              :", fields[i+8])
#   print("statTempMin                    :", fields[i+9])
#   print("statTempMax                    :", fields[i+10])
#   print("gps.chksumErrorCounter         :", fields[i+11])
#   print("gps.dgpsChecksumErrorCounter   :", fields[i+12]) 
#   print("statMaxControlCycleTime        :", fields[i+13])
#   print("SERIAL_BUFFER_SIZE             :", fields[i+14])
#   print("statMowDurationInvalid         :", fields[i+15])
#   print("statMowInvalidRecoveries       :", fields[i+16])
#   print("statMowObstacles               :", fields[i+17])
#   print("freeMemory()                   :", fields[i+18])
#   print("getResetCause()                :", fields[i+19])
#   print("statGPSJumps                   :", fields[i+20])
#   print("statMowSonarCounter            :", fields[i+21])
#   print("statMowBumperCounter           :", fields[i+22])
#   print("statMowGPSMotionTimeoutCounter :", fields[i+23])
#
#def CmdClearStatistics():
#   udp.send(CMD_ClearStatistics)
#
def CmdUploadMap():
   mapId = currentMapIndex + 1
   mower.UploadMap(mapId)

#def CmdUploadMap():
#   PrintGuiMessage("Uploading map started...");
#   if maps.UploadMap(currentMapIndex)==maps.ERROR:
#      print("[CmdUploadMap] ERROR during map upload")
#   else:
#      checksum = maps.ComputeMapChecksum(currentMapIndex)
#      print("[maps.ComputeMapChecksum] Checksum = ", checksum)
#      reportedChecksum = GetSummary()
#      if reportedChecksum == checksum:
#         PrintGuiMessage("Map upload completed successfully")
#      else:
#         PrintGuiMessage("Map upload checksum error")
#
#def CmdStopMowing():
#   udp.send(CMD_StopMowing)
   
def CmdCreateWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

def CmdMakeSquareParallel():
   global lastPerimeter
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.MakeParallel(maps.perimeters[currentMapIndex], r)

ArdumowerControlProgram()
udp.close()
pygame.quit()
