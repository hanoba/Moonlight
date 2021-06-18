# Importieren der Pygame-Bibliothek
import pygame
import transform
import json
import math
import numpy as np
from datetime import datetime

# pretty json: python -m json.tool data.json >data2.json

print(datetime.now())

LEFT = 1
RIGHT = 3

def MoveRectangle(rectangle, n, newPos):
    (xNew, yNew) = newPos
    (x,y) = rectangle[n]
    dx = xNew - x
    dy = yNew - y
    length = len(rectangle)
    for i in range(length):
        (x,y) = rectangle[i]
        rectangle[i] = (x+dx,y+dy)

def MakeParallel(rectangle, n):
    na = n;
    nb = (n + 1) & 3
    nc = (n + 2) & 3
    nd = (n + 3) & 3
    Va = np.array(rectangle[na])
    Vb = np.array(rectangle[nb])
    Vc = np.array(rectangle[nc])
    Vd = np.array(rectangle[nd])
    Vdc = np.subtract(Vd,Vc)
    Vda = np.subtract(Vd,Va)
    Vdb = np.subtract(Vd,Vb)
    A = np.column_stack((Vdc, Vda))
    x = np.linalg.solve(A, Vdb)
    Va = np.rint(np.add(Vb,Vdc*x[0])).astype(int)
    rectangle[n] = (Va[0], Va[1])

def WriteRectangle(rectangle):
    f=open('perimeter.txt','w')
    for ele in rectangle:
        f.write(str(ele[0])+" ")
        f.write(str(ele[1])+'\n')
    f.close()
    print("Save to file");

def ReadRectangle():
    with open('perimeter.txt') as f:
        array = []
        for line in f: # read rest of lines
            array.append([int(x) for x in line.split()])
    print("Load from file")
    print(array)
    return array

def GetWayPoints(mapType, mapNum):
    with open('maps.json') as json_file:
        data = json.load(json_file)
        length = len(data)
        #print(length)
        map = data[mapNum]
        waypoints = map[mapType]
        print(mapType)
        print(waypoints)
        #print(len(waypoints))
        wpoly = []
        for point in waypoints:
            wpoly.append((point["X"], point["Y"]))
        transform.Map2Screen(wpoly)
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile)
    return wpoly

# initialisieren von pygame
pygame.init()

# genutzte Farbe
ORANGE  = ( 255, 140, 0)
RED     = ( 255, 0, 0)
GREEN   = ( 0, 255, 0)
BLUE    = ( 0, 0, 255)
BLACK = ( 0, 0, 0)
WHITE   = ( 255, 255, 255)

# Fenster öffnen
screen = pygame.display.set_mode((transform.screenX, transform.screenY))

# Titel für Fensterkopf
pygame.display.set_caption("ArduMower Control Program")

# solange die Variable True ist, soll das Spiel laufen
spielaktiv = True

gartenImg = pygame.image.load("garten-google-maps-zoom.png")

# Bildschirm Aktualisierungen einstellen
clock = pygame.time.Clock()

# Schleife Hauptprogramm

# Gartenplan - x-Achse parallel zum oberen Zaun
gx1=44.70
gx2=gx1-1.4
garten = [(0,0),(gx1,0),(gx2,-24.00),(0,-7.56)]
transform.Plan2Map(garten)
transform.Map2Screen(garten)
x = math.sqrt((gx2-0)**2+(24.00-7.56)**2)
print("soll=46.30 ist=", x)

# Gartenhaus
haus = [(0,0),(7.23,0),(7.23,4.67),(0,4.67)]
mx = 44.70 - 10.30 - 7.23 # 5.10 + 4.00 + 16.60
my = -4.76-0.5
transform.Move(haus,mx,my)
transform.Plan2Map(haus)
transform.Map2Screen(haus)

# Schuppen
schuppen = [(0,0),(4.00,0),(4.00,4.50),(0,4.50)]
mx = 5.10
my = -4.50-0.90
transform.Move(schuppen,mx,my)
transform.Plan2Map(schuppen)
transform.Map2Screen(schuppen)

# MAP1
map1=[(1.81,-8.47), (2.34,-11.47), (15.77,-7.75), (13.64,-4.72)]
transform.Map2Screen(map1)

# waypoints
wayPoints = GetWayPoints("waypoints",1)
print(wayPoints)
print(wayPoints[1:2])
WLEN=len(wayPoints)

# perimeter
perimeter0 = GetWayPoints("perimeter",0)
perimeter1 = GetWayPoints("perimeter",1)

# Origin
origin = [(0,0)]
transform.Map2Screen(origin)
origin = origin[0]
wl=3

# create a font object.
# 1st parameter is the font file
# which is present in pygame.
# 2nd parameter is size of the font
font = pygame.font.Font('freesansbold.ttf', 10)
 
# create a text suface object,
# on which text is drawn on it.
text = font.render('0', True, GREEN, BLUE)
 
# create a rectangular object for the
# text surface object
textRect = text.get_rect()
 
# set the center of the rectangular object.
textRect.center = (perimeter0[0])



y=50
dy=1
r=0
rectangle=[ (797, 173), (922, 89), (1099, 373), (974, 431)]
lastRectangle=rectangle.copy()

while spielaktiv:
    # Überprüfen, ob Nutzer eine Aktion durchgeführt hat
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            spielaktiv = False
            print("Spieler hat Quit-Button angeklickt")
        elif event.type == pygame.KEYDOWN:
            #print("Spieler hat Taste gedrückt")

            # 
            if event.key == pygame.K_RIGHT:
                lastRectangle=rectangle.copy()
                (x,y) = rectangle[r]
                rectangle[r] = (x+1,y)
            elif event.key == pygame.K_LEFT:
                lastRectangle=rectangle.copy()
                (x,y) = rectangle[r]
                rectangle[r] = (x-1,y)
            elif event.key == pygame.K_UP:
                lastRectangle=rectangle.copy()
                (x,y) = rectangle[r]
                rectangle[r] = (x,y-1)
            elif event.key == pygame.K_DOWN:
                lastRectangle=rectangle.copy()
                (x,y) = rectangle[r]
                rectangle[r] = (x,y+1)

            # Taste für Spieler 2
            elif event.key == pygame.K_ESCAPE:
                print("Bye bye.")
                spielaktiv = False
            elif event.key == pygame.K_m:
                lastRectangle=rectangle.copy()
                MakeParallel(rectangle, r)
            elif event.key == pygame.K_w:
                WriteRectangle(rectangle)
            elif event.key == pygame.K_r:
                rectangle = ReadRectangle()
            elif event.key == pygame.K_SPACE:
                r -= 1
                if r<0: r=3
            elif event.key == pygame.K_TAB:
                r += 1
                if r>3: r=0
            elif event.key == pygame.K_z:
                tmp=rectangle.copy()
                rectangle=lastRectangle.copy()
                lastRectangle=tmp.copy()

        #elif event.type == pygame.KEYUP:
        #    print("Spieler hat Taste losgelassen")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            #print("Spieler hat die Maus angeklickt")
            lastRectangle=rectangle.copy()
            pos = pygame.mouse.get_pos()
            #print(pos)
            rectangle[r] = pos
            #posMap = transform.Screen2Map(pos)
            #print(posMap)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT:
            lastRectangle=rectangle.copy()
            pos = pygame.mouse.get_pos()
            MoveRectangle(rectangle, r, pos)
            

    # Spiellogik hier integrieren

    # Spielfeld löschen
    # screen.fill(WHITE)
    screen.blit(gartenImg, (0,0))

    # Spielfeld/figuren zeichnen
    #pygame.draw.rect(screen, RED, (100,y,100,50), 1)
    #y=y+dy
    #if y >= 200:
    #    dy = -1
    #elif y <= 50:
    #    dy = 1
    # polygon([[0,0],[44.70,0],[44.70,-24.00],[0,-4.12]]);
    #pygame.draw.lines(screen, GREEN, True, [(0,0), (447,0), (447,240), (0, 41)], 1)
    pygame.draw.lines(screen, GREEN, True, garten, 1)
    pygame.draw.lines(screen, RED,   True, haus, 1)
    pygame.draw.lines(screen, RED,   True, schuppen, 1)
    #pygame.draw.lines(screen, BLUE,  True, map1, 1)
    #pygame.draw.lines(screen, ORANGE,  False, wayPoints[0:wl], 1)
    pygame.draw.lines(screen, ORANGE,  True, perimeter0, 1)
    pygame.draw.lines(screen, ORANGE,  True, perimeter1, 1)
    
    pygame.draw.circle(screen, WHITE, origin, 6)
    
    # draw rectangle
    pygame.draw.lines(screen, BLUE,  True, rectangle, 1)
    pygame.draw.circle(screen, WHITE, rectangle[r], 3)
    
    # draw text
    screen.blit(text, textRect)
    
    # Fenster aktualisieren
    pygame.display.flip()

    # Refresh-Zeiten festlegen
    clock.tick(60)

pygame.quit()
