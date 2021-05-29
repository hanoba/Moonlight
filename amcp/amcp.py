# Importieren der Pygame-Bibliothek
import pygame
import math
import maps
import plan
import udp

LEFT = 1
RIGHT = 3

r=3
iCurrentRefPoint = r

currentMapIndex = 3
#currentWayPoints = []
showCurrentWayPoints = False
numMaps = 0

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
CMD_SwitchOffRobot = "AT+Y3"
CMD_TriggerRaspiShutdown = "AT+Y4"
CMD_ToggleBluetoothLogging = "AT+Y2"
CMD_ToggleUseGPSfloatForPosEstimation = "AT+YP"
CMD_ToggleUseGPSfloatForDeltaEstimation = "AT+YD"
CMD_ToggleGPSLogging = "AT+YV"

FONT_SIZE = 14
LINE_SPACING = FONT_SIZE + 1



def SetCurrentMapIndex(index):
    global currentMapIndex
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
   WriteTextBox(str.format("Current map index:   {:3d}                  ", currentMapIndex+1), 0)
   WriteTextBox(str.format("Number of waypoints: {:3d}                  ", numWayPoints))
   WriteTextBox("<v>   PrintVersionNumber                  ")
   WriteTextBox("<b>   ToggleBluetoothLogging              ")
   WriteTextBox("<m>   Upload current map & start mowing   ")
   WriteTextBox("<q>   SwitchOffRobot                      ")
   WriteTextBox("<p>   ToggleUseGPSfloatForPosEstimation   ")
   WriteTextBox("<d>   ToggleUseGPSfloatForDeltaEstimation ")
   WriteTextBox("<s>   PrintStatistics                     ")
   WriteTextBox("<u>   Upload current map                  ")
   WriteTextBox("<x>   Stop mowing                         ")
   WriteTextBox("<DEL> ClearStatistics                     ")
   WriteTextBox("<0>   Select reference points             ")
   WriteTextBox("<1> to <9> Select perimeter 1 to 9        ")
   WriteTextBox("<F2>  Save maps to file maps2.txt         ")
   WriteTextBox("<F5>  Show/hide waypoints                 ")
   WriteTextBox("<F6>  Create waypoints                    ")
   WriteTextBox("<F7>  Make parallel                       ")
   WriteTextBox("<^y>  Redo                                ")
   WriteTextBox("<^z>  Undo                                ")
   WriteTextBox("<TAB> Select next perimeter point         ")
   WriteTextBox("<SPC> Select previous perimeter point     ")
   WriteTextBox("<ESC> Quit program                        ")


def PrintLogMsg():
   if not hasattr(PrintLogMsg, "headline"):
       PrintLogMsg.headline = "         Tctl State   freem Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy     Gd     Gz  SOL   Age   Il   Ir   Im   Temp Hum Flags"
       PrintLogMsg.oldMsg = " "
   msg = udp.receive()
   if msg != "":
      if msg[0] == ':':    PrintLogMsg.oldMsg = msg[1:len(msg)-2]
      elif msg[0] == '#':  PrintLogMsg.headline = msg[1:len(msg)-2]
      print(msg, end='', flush=True)
   # print headline
   text = bigFont.render(PrintLogMsg.headline, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.center = ((maps.screenX/2, 25-(LINE_SPACING-1)))
   screen.blit(text, textRect)
   # print logging text
   text = bigFont.render(PrintLogMsg.oldMsg, True, WHITE, BLACK)
   textRect = text.get_rect()
   textRect.center = ((maps.screenX/2, 25))
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

# solange die Variable True ist, soll das Spiel laufen
spielaktiv = True

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

while spielaktiv:
    # Überprüfen, ob Nutzer eine Aktion durchgeführt hat
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            spielaktiv = False
            print("Spieler hat Quit-Button angeklickt")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                (x,y) = maps.perimeters[currentMapIndex][r]
                maps.perimeters[currentMapIndex][r] = (x+1,y)
                PrintDistance()
            elif event.key == pygame.K_LEFT:
                (x,y) = maps.perimeters[currentMapIndex][r]
                maps.perimeters[currentMapIndex][r] = (x-1,y)
                PrintDistance()
            elif event.key == pygame.K_UP:
                (x,y) = maps.perimeters[currentMapIndex][r]
                maps.perimeters[currentMapIndex][r] = (x,y-1)
                PrintDistance()
            elif event.key == pygame.K_DOWN:
                (x,y) = maps.perimeters[currentMapIndex][r]
                maps.perimeters[currentMapIndex][r] = (x,y+1)
                #print(maps.Distance(maps.perimeters[currentMapIndex][r], lastPerimeter[r]), "m");
                PrintDistance()
            elif event.key == pygame.K_ESCAPE:
                print("Bye bye.")
                spielaktiv = False
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
                udp.send(CMD_ToggleBluetoothLogging)
            elif event.key == pygame.K_d:
                udp.send(CMD_ToggleUseGPSfloatForDeltaEstimation)
            elif event.key == pygame.K_m:
                START_MOWING = True
                maps.UploadMap(currentMapIndex, START_MOWING)
            elif event.key == pygame.K_p:
                udp.send(CMD_ToggleUseGPSfloatForPosEstimation)
            elif event.key == pygame.K_q:
                udp.send(CMD_SwitchOffRobot)
            elif event.key == pygame.K_s:
                udp.send(CMD_PrintStatistics)
            elif event.key == pygame.K_u:
                DO_NOT_START_MOWING = False
                maps.UploadMap(currentMapIndex, DO_NOT_START_MOWING)
            elif event.key == pygame.K_v:
                udp.send(CMD_PrintVersionNumber);
            elif event.key == pygame.K_x:
                udp.send(CMD_StopMowing);
            elif event.key == pygame.K_y:
                if event.mod & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL):
                   maps.perimeters[currentMapIndex]=redoPerimeter.copy()
                   PrintDistance()
            elif event.key == pygame.K_z:
                if event.mod & (pygame.KMOD_LCTRL | pygame.KMOD_RCTRL):
                   redoPerimeter=maps.perimeters[currentMapIndex].copy()
                   maps.perimeters[currentMapIndex]=lastPerimeter.copy()
                   PrintDistance()
            elif event.key == pygame.K_SPACE:
                lastPerimeter=maps.perimeters[currentMapIndex].copy()
                redoPerimeter=lastPerimeter
                r -= 1
                if r<0: r=len(maps.perimeters[currentMapIndex])-1
            elif event.key == pygame.K_TAB:
                lastPerimeter=maps.perimeters[currentMapIndex].copy()
                redoPerimeter=lastPerimeter
                r += 1
                if r>=len(maps.perimeters[currentMapIndex]): r=0
            elif event.key == pygame.K_F2:
                maps.StoreMaps()
            elif event.key == pygame.K_F5:
                showCurrentWayPoints = not showCurrentWayPoints
            elif event.key == pygame.K_F6:
                lastPerimeter=maps.perimeters[currentMapIndex].copy()
                maps.wayPoints[currentMapIndex] = maps.CreateWaypoints(maps.perimeters[currentMapIndex], r)
                showCurrentWayPoints = True
            elif event.key == pygame.K_F7:
                lastPerimeter=maps.perimeters[currentMapIndex].copy()
                maps.MakeParallel(maps.perimeters[currentMapIndex], r)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            #lastPerimeter=maps.perimeters[currentMapIndex].copy()
            pos = pygame.mouse.get_pos()
            maps.perimeters[currentMapIndex][r] = pos
            PrintDistance()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT:
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
            if i==currentMapIndex: color = RED
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
    #pygame.draw.lines(screen, ORANGE,  True, perimeter0, 1)

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
    
    # Fenster aktualisieren
    pygame.display.flip()

    # Refresh-Zeiten festlegen
    clock.tick(60)

udp.close()
pygame.quit()
#print(maps[1])
