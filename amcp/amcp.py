# Importieren der Pygame-Bibliothek
import pygame
import math
import maps
import mapcfg
import plan
import udp
import mower
import heatmap
import param
from datetime import datetime
from version import versionString
import pygame_menu
#from msg import guiMessage
from udp import PrintGuiMessage, GetGuiMessage


def HideWindow():
   screen = pygame.display.set_mode((maps.screenX, maps.screenY), flags=pygame.HIDDEN)
   
def ShowWindow():
   screen = pygame.display.set_mode((maps.screenX, maps.screenY), flags=pygame.SHOWN)

LEFT = 1
RIGHT = 3

TEXT_LEFT = 30

r=3
iCurrentRefPoint = r
editMode = False

currentMapIndex = param.lastMapIndex
currentMapChecksum = 0
#currentWayPoints = []
showCurrentWayPoints = False
numMaps = 0

FONT_SIZE = 14
LINE_SPACING = FONT_SIZE + 1
FRAME_RATE = 20

aliveCounter=0

# Mower
B = 4
L = 8
MowerPolygon = [(-L,-B), (0,-B), (L,0), (0,B), (-L,B)]


def Rotate(poly, phi):
   cos_phi = math.cos(phi)
   sin_phi = math.sin(phi)
   length = len(poly)
   for i in range(length):
       (x,y) = poly[i]
       xn = x*cos_phi - y*sin_phi
       yn=  x*sin_phi + y*cos_phi
       poly[i] = (xn,yn)
   return


def DrawMower():
    (mowerPosX, mowerPosY) = maps.Map2ScreenXY(udp.stateX, udp.stateY)
    #(mowerPosX, mowerPosY) = maps.Map2ScreenXY(0, 0)
    #print((mowerPosX, mowerPosY))
    #mowerLocation = maps.Map2ScreenXY(udp.stateX, udp.stateY)
    pygame.draw.circle(screen, YELLOW, (mowerPosX, mowerPosY), 5, 1)
    delta = udp.stateDeltaDegree * math.pi / 180
    poly = MowerPolygon.copy()
    Rotate(poly, delta)
    length = len(poly)
    for i in range(length):
        (x,y) = poly[i]
        x =  (mowerPosX + x)
        y =  (mowerPosY - y)
        poly[i] = (x,y)
    fcol = GREEN
    #print(poly)
    pygame.draw.polygon(screen, fcol, poly)
    return


def KeepMowerAlive(aliveCounterThreshold):
   global aliveCounter
   aliveCounter += 1
   if aliveCounter >= aliveCounterThreshold:
      aliveCounter = 0
      mower.Ping()

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
    PrintGuiMessage("MAP" + str(currentMapIndex+1) + " selected")

def PrintMouseDistance():
   pos = pygame.mouse.get_pos()
   distance = "Distance mouse current edit point:     {0:7.2f} m".format(maps.Distance(maps.perimeters[currentMapIndex][r], pos))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((TEXT_LEFT, 50+0*LINE_SPACING))
   screen.blit(text, textRect)

def PrintRefPointDistance():
   if len(maps.perimeters[9]) == 0: 
        return
   pos = pygame.mouse.get_pos()
   distance = "Distance mouse/current reference point:{0:7.2f} m".format(maps.Distance(maps.perimeters[9][iCurrentRefPoint], pos))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((TEXT_LEFT, 50+1*LINE_SPACING))
   screen.blit(text, textRect)

def PrintDistance():
   distance = "Distance current/last edit point:      {0:7.2f} m".format(maps.Distance(maps.perimeters[currentMapIndex][r], lastPerimeter[r]))
   text = bigFont.render(distance, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((TEXT_LEFT, 50+2*LINE_SPACING))
   screen.blit(text, textRect)

def PrintMousePosition():
   pos = [ pygame.mouse.get_pos() ]
   maps.Screen2Map(pos)
   (x,y) = pos[0]
   if maps.IsInGarten(x, y): color = WHITE
   else: color = RED
   position = "{0:7.2f}{1:7.2f} m".format(x, y)
   text = bigFont.render(position, True, color, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((500, 50+0*LINE_SPACING))
   screen.blit(text, textRect)

def PrintCurrentPointPosition():
   pos = [ maps.perimeters[currentMapIndex][r] ]
   maps.Screen2Map(pos)
   (x,y) = pos[0]
   position = "{0:7.2f}{1:7.2f} m".format(x, y)
   text = bigFont.render(position, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((500, 50+1*LINE_SPACING))
   screen.blit(text, textRect)

def ShowGuiMessage():
   msg = udp.ReceiveMowerMessage()
   if msg != "":
      if msg[0] == ':': KeepMowerAlive(24)   # Mower sends a periodic log message every 5 sec --> ping every 2 minutes
   if GetGuiMessage() != "":
      text = bigFont.render(GetGuiMessage(), True, WHITE, BLACK)
      textRect = text.get_rect()
      textRect.topright = ((maps.screenX-20, maps.screenY-40))
      screen.blit(text, textRect)


def WriteTextBox(text, lineNum=-1):
   if lineNum < 0:
      WriteTextBox.line = WriteTextBox.line + 1
   else:
      WriteTextBox.line = lineNum
   text = bigFont.render(text, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((TEXT_LEFT, 100+LINE_SPACING*WriteTextBox.line))
   screen.blit(text, textRect)


def PrintHelpText():
   numWayPoints = len(maps.wayPoints[currentMapIndex])
   MapId = currentMapIndex + 1
   WriteTextBox(str.format("Current Map ID:        {:3d}   ", MapId), 0)
   WriteTextBox(str.format("Checksum:         {:8d}   ", currentMapChecksum))
   WriteTextBox(str.format("Number of waypoints:   {:3d}   ", numWayPoints))
   WriteTextBox("v   Print version number     ")
   WriteTextBox("m/i Start/stop mowing        ")
   WriteTextBox("M   Start mowing from wayp.  ")
   WriteTextBox("d/a Start docking/undocking  ")
   WriteTextBox("o   Switch ArduMower off     ")
   WriteTextBox("s   PrintStatistics          ")
   WriteTextBox("r   Read map from SD card    ")
   WriteTextBox("u   Upload current map       ")
   WriteTextBox("+   Duplicate point          ")
   WriteTextBox("BS  Remove point             ")
   WriteTextBox("^e  Toggle edit mode         ")
   WriteTextBox("^w  Show/hide waypoints      ")
   WriteTextBox("^u  Create U waypoints       ")
   WriteTextBox("^v  Create V waypoints       ")
   WriteTextBox("^o  Create O waypoints       ")
   WriteTextBox("^p  Make parallel            ")
   WriteTextBox("^r  Reorder rectangle        ")
   WriteTextBox("TAB Select next point        ")
   WriteTextBox("SPC Select previous point    ")
   WriteTextBox("ESC Show/hide menu           ")
   WriteTextBox("x   Select exclusion points  ")
   WriteTextBox("#   Select reference points  ")
   WriteTextBox("1..9   Select MAP1 to MAP9   ")
   WriteTextBox("0/^0   Select MAP10/MAP20    ")
   WriteTextBox("^1..^9 Select MAP11 to MAP19 ")
   WriteTextBox("^z/^y  Undo / Redo           ")


def PrintLogMsg():
   #if not hasattr(PrintLogMsg, "headline"):
   #    PrintLogMsg.headline = "Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy     Gd     Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags Map Info    "
   #    PrintLogMsg.oldMsg = " "
   #msg = udp.receive()
   #if msg != "":
   #   if msg[0] == ':':    PrintLogMsg.oldMsg = msg[1:len(msg)-2]
   #   elif msg[0] == '#':  PrintLogMsg.headline = msg[1:len(msg)-2]
   #   udp.WriteLog("[am] "+msg)
   #   KeepMowerAlive(24)   # Mower sends log message every 5 sec --> ping every 2 minutes
   # print headline
   text = bigFont.render(udp.logHeadline, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.topleft = ((10, 15-(LINE_SPACING-1)))
   screen.blit(text, textRect)
   # print logging text
   text = bigFont.render(udp.logMessage, True, WHITE, BLACK)
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
#pygame.display.set_caption("ArduMower Control Program")
pygame.display.set_caption(versionString)

gartenImg = pygame.image.load("garten-google-maps-zoom.png")

# Bildschirm Aktualisierungen einstellen
clock = pygame.time.Clock()

# Schleife Hauptprogramm
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

# solange die Variable True ist, soll das Spiel laufen
programActive = True

def ArdumowerControlProgram():
   global currentMapIndex
   global r
   global lastPerimeter
   global redoPerimeter
   global iCurrentRefPoint 
   global showCurrentWayPoints
   global numMaps
   global menu, config_menu
   global editMode
   global programActive

   #------------------------------------------------------------------------------------------------- 
   # Create Config Menu
   #------------------------------------------------------------------------------------------------- 
   theme_dark = pygame_menu.themes.THEME_DARK.copy()
   theme_dark.widget_font_size=18
   theme_dark.title_font_size=24
   config_menu = pygame_menu.Menu('Configuration Menu', 600, 800, theme=theme_dark)

   config_menu.add.button('Toggle Bluetooth Logging (b=off,B=on)', mower.ToggleBluetoothLogging)
   config_menu.add.button('Toggle UseGPSfloatForPosEstimation (p=off,P=on)', mower.ToggleUseGPSfloatForPosEstimation)
   config_menu.add.button('Toggle UseGPSfloatForDeltaEstimation (d=off,D=on)', mower.ToggleUseGPSfloatForDeltaEstimation)
   config_menu.add.button('Toggle Kippschutz (k=off,K=on)', mower.ToggleKippschutz)
   config_menu.add.button('Toggle SmoothCurves (s=off,S=on)', mower.ToggleSmoothCurves)
   config_menu.add.button('Toggle EnablePathFinder (f=off,F=on)', mower.ToggleEnablePathFinder)
   config_menu.add.button('GNSS Warm Reboot', mower.GnssWarmReboot)
   config_menu.add.button('Sensor Test', mower.SensorTest)
   config_menu.add.button('Sync RTC with current time', mower.SyncRtc)
   config_menu.add.button('ClearStatistics (c)', mower.ClearStatistics)
   config_menu.add.text_input('Maps File Name: ', textinput_id='ID_MAPS_FILE_NAME', default=param.mapFileName)
   config_menu.add.text_input('Export File Name: ', textinput_id='ID_EXPORT_FILE_NAME', default=param.exportFileName)
   config_menu.add.text_input('Linear speed in m/s: ', textinput_id='ID_LINEAR_SPEED', default=param.linearSpeed)
   config_menu.add.text_input('Angular speed in rad/s: ', textinput_id='ID_ANGULAR_SPEED', default=param.angularSpeed)
   config_menu.add.text_input('Fix Timeout in sec: ', textinput_id='ID_FIX_TIMEOUT', default=param.fixTimeout)
   config_menu.add.text_input('Set Waypoint: ', textinput_id='ID_WAYPOINT', default=param.waypoint)
   config_menu.add.text_input('Enable Bumper: ', textinput_id='ID_BUMPER_ENABLE', default=param.bumperEnable)
   config_menu.add.text_input('Front Wheel Drive: ', textinput_id='ID_FRONT_WHEEL_DRIVE', default=param.frontWheelDrive)
   config_menu.add.text_input('Moonlight Line Tracking: ', textinput_id='ID_ML_LINE_TRACKING', default=param.mlLineTracking)
   config_menu.add.text_input('Enable Tilt Detection: ', textinput_id='ID_ENABLE_TILT_DETECTION', default=param.enableTiltDetection)
   config_menu.add.text_input('GPS Config Filter: ', textinput_id='ID_GPS_CONFIG_FILTER', default=param.gpsConfigFilter)
   config_menu.add.button('Upload GPS Config Filter', CmdUploadGpsConfigFilter)
   config_menu.add.button('Return to Main Menu', pygame_menu.events.BACK)

   #------------------------------------------------------------------------------------------------- 
   # Create Main Menu
   #------------------------------------------------------------------------------------------------- 
   theme_dark = pygame_menu.themes.THEME_DARK.copy()
   theme_dark.widget_font_size=18  #20
   theme_dark.title_font_size=24  #30
   menu = pygame_menu.Menu('Main Menu', 600, 780, theme=theme_dark)

   menu.add.button('Show/Hide MainMenu (ESC)', CmdShowHideMainMenu)
   menu.add.button('Start mowing (m)', CmdStartMowing)
   menu.add.button('Start mowing from waypoint (M)', CmdStartMowingFromWaypoint)
   menu.add.button('Stop mowing (i)', mower.StopMowing)
   menu.add.button('Start docking (d)', mower.StartDocking)
   menu.add.button('Start undocking (a)', mower.StartUndocking)
   menu.add.button('Switch Off Robot (o)', mower.SwitchOffRobot)
   menu.add.button('Get Version Number (v)', mower.GetVersionNumber)
   menu.add.button('PrintStatistics (s)', mower.PrintStatistics)
   #menu.add.button('ClearStatistics (c)', mower.ClearStatistics)
   menu.add.button('Upload current map (u)', CmdUploadMap)
   menu.add.button('Read Map From SD Card (r)', CmdReadMapFromSdCard)
   menu.add.button('Save Maps', CmdStoreMaps)
   menu.add.button('Export Maps in SunrayApp format', CmdExportMaps)
   menu.add.button('Show/Hide Waypoints (^w)', CmdToggleShowWaypoints)
   menu.add.button('Create U Waypoints (^u)', CmdCreateUtypeWaypoints)
   menu.add.button('Create V Waypoints (^v)', CmdCreateVtypeWaypoints)
   menu.add.button('CmdReorder Rectangle (^r)', CmdReorderRectangle)
   menu.add.button('Convert Rectangle To Trapezoid (^p)', CmdConvertRectangleToTrapezoid)
   menu.add.button('Get Map Checksum From Mower', mower.ComputeMapChecksum)
   menu.add.button('Get RTC Date & Time', mower.GetRtcDateTime)
   menu.add.button('Mower Configuration', config_menu)
   #menu.add.button('Quit (q)', pygame_menu.events.EXIT)
   menu.add.button('Quit (q)', CmdQuit)

   # set key repeat 
   # delay_ms = 750
   # interval_ms = 100
   # pygame.key.set_repeat(delay_ms, interval_ms)
   
   # Init heatmap
   heatmap.CreateHeatMap()
   DrawHeatmapFlag = False
   
   while programActive:
      # Überprüfen, ob Nutzer eine Aktion durchgeführt hat
      events = pygame.event.get()
      for event in events:
         if event.type == pygame.QUIT:
               CmdQuit()  #programActive = False
         elif event.type == pygame.KEYDOWN:
               #PrintGuiMessage("")
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
                  elif event.key == pygame.K_1:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(10)
                     else: SetCurrentMapIndex(0)
                  elif event.key == pygame.K_2:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(11)
                     else: SetCurrentMapIndex(1)
                  elif event.key == pygame.K_3:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(12)
                     else: SetCurrentMapIndex(2)
                  elif event.key == pygame.K_4:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(13)
                     else: SetCurrentMapIndex(3)
                  elif event.key == pygame.K_5:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(14)
                     else: SetCurrentMapIndex(4)
                  elif event.key == pygame.K_6:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(15)
                     else: SetCurrentMapIndex(5)
                  elif event.key == pygame.K_7:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(16)
                     else: SetCurrentMapIndex(6)
                  elif event.key == pygame.K_8:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(17)
                     else: SetCurrentMapIndex(7)
                  elif event.key == pygame.K_9:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(18)
                     else: SetCurrentMapIndex(8)
                  elif event.key == pygame.K_0:
                     if event.mod & pygame.KMOD_CTRL:  SetCurrentMapIndex(19)
                     else: SetCurrentMapIndex(9)
                  elif event.key == pygame.K_a:
                     mower.StartUndocking()
                  elif event.key == pygame.K_b:
                     mower.ToggleBluetoothLogging()
                  elif event.key == pygame.K_c:
                        mower.ClearStatistics()
                  elif event.key == pygame.K_d:
                     mower.StartDocking()
                  elif event.key == pygame.K_e:
                     if event.mod & pygame.KMOD_CTRL:
                        editMode = not editMode
                        if editMode: PrintGuiMessage("Edit mode enabled")
                        else: PrintGuiMessage("Edit mode disabled")
                  elif event.key == pygame.K_h:
                     DrawHeatmapFlag =  not DrawHeatmapFlag
                  elif event.key == pygame.K_i:
                     mower.StopMowing()
                  elif event.key == pygame.K_m:
                     if event.mod & pygame.KMOD_SHIFT: CmdStartMowingFromWaypoint()
                     else: CmdStartMowing()
                  elif event.key == pygame.K_o:
                     if event.mod & pygame.KMOD_CTRL: CmdCreateOtypeWaypoints()
                     else: mower.SwitchOffRobot()
                  elif event.key == pygame.K_p:
                     if event.mod & pygame.KMOD_CTRL:
                        if editMode:
                           lastPerimeter=maps.perimeters[currentMapIndex].copy()
                           maps.MakeParallel(maps.perimeters[currentMapIndex], r)
                  elif event.key == pygame.K_q:
                     CmdQuit()   #programActive = False
                  elif event.key == pygame.K_r:
                     if event.mod & pygame.KMOD_CTRL:
                        if editMode: CmdReorderRectangle()
                     else: CmdReadMapFromSdCard()
                  elif event.key == pygame.K_s:
                     mower.PrintStatistics()
                  elif event.key == pygame.K_u:
                     if event.mod & pygame.KMOD_CTRL: CmdCreateUtypeWaypoints()
                     #   if editMode:
                     #      lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     #      maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
                     #      showCurrentWayPoints = True
                     else: CmdUploadMap()
                  elif event.key == pygame.K_w:
                     if event.mod & pygame.KMOD_CTRL:
                        CmdToggleShowWaypoints()
                  elif event.key == pygame.K_v:
                     if event.mod & pygame.KMOD_CTRL: CmdCreateVtypeWaypoints()
                     else: mower.GetVersionNumber()
                  elif event.key == pygame.K_x:       # exclusion points
                     SetCurrentMapIndex(maps.MAP_INDEX_PERIMETER_WITH_EXCLUSION)
                  elif event.key == pygame.K_y:
                     if event.mod & pygame.KMOD_CTRL:
                        maps.perimeters[currentMapIndex]=redoPerimeter.copy()
                        PrintDistance()
                  elif event.key == pygame.K_z:
                     if event.mod & pygame.KMOD_CTRL:
                        redoPerimeter=maps.perimeters[currentMapIndex].copy()
                        maps.perimeters[currentMapIndex]=lastPerimeter.copy()
                        PrintDistance()
                  elif event.key == pygame.K_HASH:    # references points
                     SetCurrentMapIndex(maps.MAP_INDEX_REFERENCE_POINTS)
                  elif event.key == pygame.K_SPACE and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     r -= 1
                     if r<0: r=len(maps.perimeters[currentMapIndex])-1
                  elif event.key == pygame.K_BACKSPACE and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     maps.perimeters[currentMapIndex].pop(r)
                     r -= 1
                     if r<0: r=len(maps.perimeters[currentMapIndex])-1
                  # add point
                  elif event.key == pygame.K_PLUS and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     maps.perimeters[currentMapIndex].append((0,0))
                     k=len(maps.perimeters[currentMapIndex])-1
                     while k>r:
                        maps.perimeters[currentMapIndex][k] = maps.perimeters[currentMapIndex][k-1]
                        k = k - 1
                     r = r + 1
                  elif event.key == pygame.K_TAB and editMode:
                     lastPerimeter=maps.perimeters[currentMapIndex].copy()
                     redoPerimeter=lastPerimeter
                     r += 1
                     if r>=len(maps.perimeters[currentMapIndex]): r=0
                  #elif event.key == pygame.K_F2:
                  #   CmdStoreMaps()
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
      pygame.draw.lines(screen, GREEN, True, maps.garten, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.haus, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.terrasse, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.schuppen, 3)
   
      # Nullpunkt
      DrawCross(WHITE, origin)
      
      # DockPoints zeichnen
      if len(maps.dockPoints) > 1: pygame.draw.lines(screen, WHITE,  False, maps.dockPoints, 3)
      
      # Messungen
      pygame.draw.circle(screen, RED, messungen[0], 2)
      pygame.draw.circle(screen, RED, messungen[1], 2)
      pygame.draw.circle(screen, RED, messungen[2], 2)
   
      # Show log message
      PrintLogMsg()
   
      # Draw maps.perimeters
      imax = min(maps.MAP_INDEX_PERIMETER_WITH_EXCLUSION+1, len(maps.perimeters))    # 11
      for i in range(imax):
         if len(maps.perimeters[i]) > 0:
            if i==maps.MAP_INDEX_PERIMETER_WITH_EXCLUSION: color = PURPLE
            else: color = ORANGE
            if i==currentMapIndex:
               if editMode: color = RED
               else: color = WHITE
            if i==maps.MAP_INDEX_PERIMETER_WITH_EXCLUSION: mapNum = "X"                 # exclusion points
            else: mapNum = "{0:d}".format(i+1)
            pygame.draw.lines(screen, color,  True, maps.perimeters[i], 1)
            text = font.render(mapNum, True, GREEN, BLUE)
            textRect = text.get_rect()
            # set the center of the rectangular object.
            (x0, y0) = maps.perimeters[i][0]
            textRect.center = ((x0-3, y0-3))
            # draw text
            screen.blit(text, textRect)
   
      # Draw reference points
      iRefPoints=maps.MAP_INDEX_REFERENCE_POINTS    # 11
      if len(maps.perimeters[iRefPoints]) > 0:
         for k in range(len(maps.perimeters[iRefPoints])):
            if currentMapIndex == iRefPoints:
               if editMode: color = RED
               else: color = WHITE
            else: color = ORANGE
            #if k == iCurrentRefPoint: color = ORANGE
            #pygame.draw.circle(screen, color, maps.perimeters[iRefPoints][k], 3)
            DrawCross(color, maps.perimeters[iRefPoints][k])      
      # Remember last reference point
      if currentMapIndex == iRefPoints: iCurrentRefPoint = r
      
      # Draw current and next edit point
      pygame.draw.circle(screen, WHITE, maps.perimeters[currentMapIndex][r], 3)
      if editMode:
         next = (r + 1) % 4
         pygame.draw.circle(screen, BLUE, maps.perimeters[currentMapIndex][next], 3)

      # Draw waypoints (if enabled)
      numWayPoints = len(maps.wayPoints[currentMapIndex])
      if showCurrentWayPoints and numWayPoints > 2: 
         pygame.draw.lines(screen, WHITE, False, maps.wayPoints[currentMapIndex], 1)
         pygame.draw.circle(screen, GREEN, maps.wayPoints[currentMapIndex][0], 5)
         pygame.draw.circle(screen, RED, maps.wayPoints[currentMapIndex][numWayPoints-1], 5)

      if DrawHeatmapFlag: heatmap.DrawHeatmap(screen)
      
      # Show mower location
      DrawMower()
      
      # Show mower GPS location
      gpsLocation = maps.Map2ScreenXY(udp.gpsX, udp.gpsY)
      pygame.draw.circle(screen, PURPLE, gpsLocation, 3)
      
      # Show target location
      targetLocation = maps.Map2ScreenXY(udp.targetX, udp.targetY)
      pygame.draw.circle(screen, GREEN, targetLocation, 5, 1)
      
      PrintDistance()
      PrintMouseDistance()
      PrintRefPointDistance()
      PrintMousePosition()
      PrintCurrentPointPosition()
      ShowGuiMessage()
      udp.ForwardRemoteControlMessage()
      
      # Draw menu
      if menu.is_enabled():
          menu.draw(screen)
          menu.update(events)
      
      # Fenster aktualisieren
      pygame.display.flip()
   
      # Refresh-Zeiten festlegen
      clock.tick(FRAME_RATE)

def CmdQuit():
    global programActive
    programActive = False

def CmdShowHideMainMenu():
   global editMode
   editMode = False
   menu.toggle()
   #data = menu.get_input_data()

   # set key repeat 
   #if menu.is_enabled(): 
   #   delay_ms = 750
   #   interval_ms = 75
   #   pygame.key.set_repeat(delay_ms, interval_ms)
   #else: pygame.key.set_repeat(0)

def CmdToggleShowWaypoints():
   global showCurrentWayPoints
   showCurrentWayPoints = not showCurrentWayPoints
   PrintGuiMessage("Show waypoints = " + str(showCurrentWayPoints))

def CmdReadMapFromSdCard():
   HideWindow();
   mapId = currentMapIndex + 1
   mower.ReadMapFromSdCard(mapId)
   ShowWindow();

def CmdStoreMaps():
   global config_menu
   data = config_menu.get_input_data()
   mapsFileName = data.get('ID_MAPS_FILE_NAME')
   maps.StoreMaps(mapsFileName)
   PrintGuiMessage("Maps successfully stored in file " + mapsFileName)

def CmdExportMaps():
   global config_menu
   data = config_menu.get_input_data()
   exportFileName = data.get('ID_EXPORT_FILE_NAME')
   maps.ExportMaps(exportFileName)
   PrintGuiMessage("Maps successfully exported to file " + exportFileName)


def CmdUploadGpsConfigFilter():
   global config_menu
   data = config_menu.get_input_data()
   gpsConfigFilter = data.get('ID_GPS_CONFIG_FILTER')
   mower.UploadGpsConfigFilter(gpsConfigFilter)


def CmdStartMowingOld(iWaypoint = -1):
   global config_menu
   data = config_menu.get_input_data()
   fixTimeout = int(data.get('ID_FIX_TIMEOUT'))
   linearSpeed = float(data.get('ID_LINEAR_SPEED'))
   angularSpeed = float(data.get('ID_ANGULAR_SPEED'))
   iBumperEnable = int(data.get('ID_BUMPER_ENABLE'))
   iFrontWheelDrive = int(data.get('ID_FRONT_WHEEL_DRIVE'))
   iMlLineTracking = int(data.get('ID_ML_LINE_TRACKING'))
   iEnableTiltDetetction = int(data.get('ID_ENABLE_TILT_DETECTION'))
   mower.StartMowing(linearSpeed, fixTimeout, iBumperEnable, iFrontWheelDrive, iMlLineTracking, iWaypoint, iEnableTiltDetetction, angularSpeed)


def CmdStartMowing(iWaypoint = -1):
   global config_menu
   data = config_menu.get_input_data()
   fixTimeout = int(data.get('ID_FIX_TIMEOUT'))
   angularSpeed = float(data.get('ID_ANGULAR_SPEED'))
   iEnableTiltDetetction = int(data.get('ID_ENABLE_TILT_DETECTION'))

   # check mapcfg
   iUseFloat = mapcfg.UseGpsFloatForPosEstimation(currentMapIndex)
   iObstacleMap = mapcfg.MapType(currentMapIndex)
   
   iBumperEnable = mapcfg.BumperEnable(currentMapIndex)
   if (iBumperEnable == -1): iBumperEnable = int(data.get('ID_BUMPER_ENABLE'))

   linearSpeed = mapcfg.LinearSpeed(currentMapIndex)
   if (linearSpeed == -1): linearSpeed = float(data.get('ID_LINEAR_SPEED'))

   iMlLineTracking = mapcfg.LineTracking(currentMapIndex)
   if (iMlLineTracking == -1): iMlLineTracking = int(data.get('ID_ML_LINE_TRACKING'))
   
   iFrontWheelDrive = mapcfg.FrontWheelDrive(currentMapIndex)
   if (iFrontWheelDrive == -1): iFrontWheelDrive = int(data.get('ID_FRONT_WHEEL_DRIVE'))
   
   mower.StartMowing(linearSpeed, fixTimeout, iBumperEnable, iFrontWheelDrive, iMlLineTracking, iWaypoint, iEnableTiltDetetction, angularSpeed, iUseFloat, iObstacleMap)

def CmdStartMowingFromWaypoint():
   global config_menu
   data = config_menu.get_input_data()
   iWaypoint = int(data.get('ID_WAYPOINT'))
   CmdStartMowing(iWaypoint)

def CmdUploadMap():
   HideWindow();
   mapId = currentMapIndex + 1
   mower.UploadMap(mapId)
   ShowWindow();

   
def CmdCreateUtypeWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

   
def CmdCreateVtypeWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateVmapWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

   
def CmdCreateOtypeWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateBumperWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

def CmdConvertRectangleToTrapezoid():
   global lastPerimeter
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.MakeParallel(maps.perimeters[currentMapIndex], r)

def CmdReorderRectangle():
   global r
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.ReorderRectangle(maps.perimeters[currentMapIndex], r)
   r = 0


ArdumowerControlProgram()
udp.close()
pygame.quit()

# save mower configuration
paramFile="param.py"
print(f"save mower parameters in file {paramFile}")
global config_menu
data = config_menu.get_input_data()
file = open(paramFile,"w")
file.write("mapFileName='"+data.get('ID_MAPS_FILE_NAME')+"'\n")
file.write("exportFileName='"+data.get('ID_EXPORT_FILE_NAME')+"'\n")
file.write("linearSpeed='"+data.get('ID_LINEAR_SPEED')+"'\n")
file.write("angularSpeed='"+data.get('ID_ANGULAR_SPEED')+"'\n")
file.write("fixTimeout='"+data.get('ID_FIX_TIMEOUT')+"'\n")
file.write("waypoint='"+data.get('ID_WAYPOINT')+"'\n")
file.write("bumperEnable='"+data.get('ID_BUMPER_ENABLE')+"'\n")
file.write("frontWheelDrive='"+data.get('ID_FRONT_WHEEL_DRIVE')+"'\n")
file.write("mlLineTracking='"+data.get('ID_ML_LINE_TRACKING')+"'\n")
file.write("enableTiltDetection='"+data.get('ID_ENABLE_TILT_DETECTION')+"'\n")
file.write("gpsConfigFilter='"+data.get('ID_GPS_CONFIG_FILTER')+"'\n")
file.write("lastMapIndex="+str(currentMapIndex)+"\n")

file.close() 
