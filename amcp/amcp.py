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
   WriteTextBox(str.format("Current Map ID:      {:8d}   ", MapId), 0)
   WriteTextBox(str.format("Checksum:            {:8d}   ", currentMapChecksum))
   WriteTextBox(str.format("Number of waypoints: {:8d}   ", numWayPoints))
   WriteTextBox("<v>   Print version number      ")
  #WriteTextBox("<b>   ToggleBluetoothLogging    ")
   WriteTextBox("<m>   Start mowing              ")
   WriteTextBox("<d>   Start docking             ")
   WriteTextBox("<a>   Start undocking           ")
   WriteTextBox("<o>   SwitchOffRobot            ")
  #WriteTextBox("<p>   ToggleUseGPSfloatForPosEst")
  #WriteTextBox("<d>   ToggleUseGPSfloatForDeltaE")
   WriteTextBox("<s>   PrintStatistics           ")
   WriteTextBox("<u>   Upload current map        ")
   WriteTextBox("<i>   Stop mowing               ")
  #WriteTextBox("<DEL> ClearStatistics           ")
   WriteTextBox("<+>   Add point                 ")
   WriteTextBox("<BS>  Remove point              ")
   WriteTextBox("<x>   Exclusion points          ")
   WriteTextBox("<#>   Select reference points   ")
   WriteTextBox("<1> to <9> Select MAP1 to MAP9  ")
   WriteTextBox("<0>   Select MAP10              ")
  #WriteTextBox("<F2>  Save maps to file maps.jso")
   WriteTextBox("<F4>  Toggle edit mode          ")
   WriteTextBox("<F5>  Show/hide waypoints       ")
   WriteTextBox("<F6>  Create waypoints          ")
   WriteTextBox("<F7>  Make parallel             ")
   WriteTextBox("<^y>  Redo                      ")
   WriteTextBox("<^z>  Undo                      ")
   WriteTextBox("<TAB> Select next point         ")
   WriteTextBox("<SPC> Select previous point     ")
   WriteTextBox("<ESC> Main Menu                 ")


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

   #------------------------------------------------------------------------------------------------- 
   # Create Config Menu
   #------------------------------------------------------------------------------------------------- 
   theme_dark = pygame_menu.themes.THEME_DARK.copy()
   theme_dark.widget_font_size=20
   theme_dark.title_font_size=30
   config_menu = pygame_menu.Menu('Configuration Menu', 600, 500, theme=theme_dark)

   config_menu.add.button('Toggle Bluetooth Logging (b=off,B=on)', mower.ToggleBluetoothLogging)
   config_menu.add.button('Toggle UseGPSfloatForPosEstimation (p=off,P=on)', mower.ToggleUseGPSfloatForPosEstimation)
   config_menu.add.button('Toggle UseGPSfloatForDeltaEstimation (d=off,D=on)', mower.ToggleUseGPSfloatForDeltaEstimation)
   config_menu.add.button('Toggle GPS Logging (g=off,G=on)', mower.ToggleGpsLogging)
   config_menu.add.button('Toggle SmoothCurves (s=off,S=on)', mower.ToggleSmoothCurves)
   config_menu.add.button('Toggle EnablePathFinder (f=off,F=on)', mower.ToggleEnablePathFinder)
   config_menu.add.button('GNSS Reboot', mower.GnssReboot)
   config_menu.add.button('GNSS Hardware Reset', mower.GnssHardwareReset)
   config_menu.add.button('Sync RTC with current time', mower.SyncRtc)
   config_menu.add.text_input('Maps File Name: ', textinput_id='ID_MAPS_FILE_NAME', default='maps.json')
   config_menu.add.text_input('Export File Name: ', textinput_id='ID_EXPORT_FILE_NAME', default='export.json')
   config_menu.add.button('Return to Main Menu', pygame_menu.events.BACK)

   #------------------------------------------------------------------------------------------------- 
   # Create Main Menu
   #------------------------------------------------------------------------------------------------- 
   theme_dark = pygame_menu.themes.THEME_DARK.copy()
   theme_dark.widget_font_size=20
   theme_dark.title_font_size=30
   menu = pygame_menu.Menu('Main Menu', 600, 800, theme=theme_dark)

   menu.add.button('Show/Hide MainMenu (ESC)', CmdShowHideMainMenu)
   menu.add.button('Upload current map (u)', CmdUploadMap)
   menu.add.button('Start mowing (m)', mower.StartMowing)
   menu.add.button('Stop mowing (i)', mower.StopMowing)
   menu.add.button('Start docking (d)', mower.StartDocking)
   menu.add.button('Start undocking', mower.StartUndocking)
   menu.add.button('Switch Off Robot (o)', mower.SwitchOffRobot)
   menu.add.button('Get Version Number (v)', mower.GetVersionNumber)
   menu.add.button('PrintStatistics (s)', mower.PrintStatistics)
   menu.add.button('ClearStatistics (c)', mower.ClearStatistics)
   menu.add.button('Store Maps', CmdStoreMaps)
   menu.add.button('Export Maps in SunrayApp format', CmdExportMaps)
   menu.add.button('Show/Hide Waypoints (F5)', CmdToggleShowWaypoints)
   menu.add.button('Create Waypoints (F6)', CmdCreateWaypoints)
   menu.add.button('Create Bumper Waypoints', CmdCreateBumperWaypoints)
   menu.add.button('Convert Rectangle To Trapezoid (F7)', CmdConvertRectangleToTrapezoid)
   menu.add.button('Read Map From SD Card (r)', CmdReadMapFromSdCard)
   menu.add.button('Get Map Checksum From Mower', mower.ComputeMapChecksum)
   menu.add.button('Get RTC Date & Time', mower.GetRtcDateTime)
   menu.add.button('Mower Configuration', config_menu)
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
               PrintGuiMessage("")
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
                  elif event.key == pygame.K_0:
                     SetCurrentMapIndex(9)
                  elif event.key == pygame.K_x:       # exclusion points
                     SetCurrentMapIndex(10)
                  elif event.key == pygame.K_HASH:    # references points
                     SetCurrentMapIndex(11)
                  elif event.key == pygame.K_b:
                     mower.ToggleBluetoothLogging()
                  elif event.key == pygame.K_c:
                     mower.ClearStatistics()
                  #elif event.key == pygame.K_d:
                  #   mower.ToggleUseGPSfloatForDeltaEstimation()
                  elif event.key == pygame.K_d:
                     mower.StartDocking()
                  elif event.key == pygame.K_a:
                     mower.StartUndocking()
                  elif event.key == pygame.K_i:
                     mower.StopMowing()
                  elif event.key == pygame.K_m:
                     mower.StartMowing()
                  elif event.key == pygame.K_o:
                     mower.SwitchOffRobot()
                  #elif event.key == pygame.K_p:
                  #   mower.ToggleUseGPSfloatForPosEstimation()
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
                  elif event.key == pygame.K_F4:
                     editMode = not editMode
                     if editMode: PrintGuiMessage("Edit mode enabled")
                     else: PrintGuiMessage("Edit mode disabled")
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
      pygame.draw.lines(screen, GREEN, True, maps.garten, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.haus, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.terrasse, 3)
      pygame.draw.lines(screen, BLUE,  True, maps.schuppen, 3)
   
      # Nullpunkt
      # pygame.draw.circle(screen, WHITE, origin, 6)
      DrawCross(WHITE, origin)
      
      # DockPoints zeichnen
      if len(maps.dockPoints) > 1: pygame.draw.lines(screen, PURPLE,  True, maps.dockPoints, 3)
      
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
      
      # draw maps.perimeters[currentMapIndex]
      # pygame.draw.lines(screen, BLUE,  True, maps.perimeters[currentMapIndex], 1)
      pygame.draw.circle(screen, WHITE, maps.perimeters[currentMapIndex][r], 3)
      if showCurrentWayPoints and len(maps.wayPoints[currentMapIndex]) > 2: 
         pygame.draw.lines(screen, WHITE, False, maps.wayPoints[currentMapIndex], 1)
         pygame.draw.circle(screen, RED, maps.wayPoints[currentMapIndex][0], 3)
      
      PrintDistance()
      PrintMouseDistance()
      PrintRefPointDistance()
      PrintMousePosition()
      PrintCurrentPointPosition()
      ShowGuiMessage()
      
      # Draw menu
      if menu.is_enabled():
          menu.draw(screen)
          menu.update(events)
      
      # Fenster aktualisieren
      pygame.display.flip()
   
      # Refresh-Zeiten festlegen
      clock.tick(60)


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

def CmdReadMapFromSdCard():
   mapId = currentMapIndex + 1
   mower.ReadMapFromSdCard(mapId)

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


def CmdUploadMap():
   mapId = currentMapIndex + 1
   mower.UploadMap(mapId)

   
def CmdCreateWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

   
def CmdCreateBumperWaypoints():
   global lastPerimeter
   global showCurrentWayPoints
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.wayPoints[currentMapIndex] = maps.CreateBumperWaypoints(maps.perimeters[currentMapIndex], r)
   showCurrentWayPoints = True

def CmdConvertRectangleToTrapezoid():
   global lastPerimeter
   lastPerimeter=maps.perimeters[currentMapIndex].copy()
   maps.MakeParallel(maps.perimeters[currentMapIndex], r)

ArdumowerControlProgram()
udp.close()
pygame.quit()
