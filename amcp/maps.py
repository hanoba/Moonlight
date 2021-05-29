import math
import json
import math
import numpy as np
import os
from time import sleep
from datetime import datetime
import udp

# Return values

ERROR = True
SUCCESS = False

# GPS-RTK Nullpunkt
x0 = 44.7 - 10.3 - 0.67 + 0.3
y0 = -(0.5 + 4.7 + 2.45) - 0.5
phi = (38-3+1) / 180 * math.pi

screenX = 1273 # 1064  # 640
screenY =  878 # 572  # 480

scalingFactor = screenX / 56 # 58 #55  # 53
invScalingFactor = 1/scalingFactor

# Nullpunkt in pixels
originX = 0.6 * screenX + 836 - 827 + 831 - 767 + 7 #+ 762 - 637
originY = 0.4 * screenY + 355 - 385 + 328 - 293 + 10      #+ 180 - 228

# Drehung
cos_phi = math.cos(phi)
sin_phi = math.sin(phi)

# ArduMower Maps
maps_json = []
perimeters = []
wayPoints = []


def Distance(new, old):
    (xn,yn) = new
    (xo,yo) = old
    return invScalingFactor*math.sqrt((xn-xo)**2 + (yn-yo)**2)


def Plan2Map(poly):
    length = len(poly)
    for i in range(length):
        (x,y) = poly[i]
        x=(x-x0)
        y=(y-y0)
        # Drehung
        xn = x*cos_phi - y*sin_phi
        yn=  x*sin_phi + y*cos_phi
        poly[i] = (xn,yn)
    return


def Map2Screen(poly):
    length = len(poly)
    for i in range(length):
        (x,y) = poly[i]
        #x = math.floor(0.5 + x*scalingFactor + originX)
        #y = math.floor(0.5 - y*scalingFactor + originY)
        x =  x*scalingFactor + originX
        y = -y*scalingFactor + originY
        poly[i] = (x,y)
    return


def Map2ScreenXY(x,y):
    x =  x*scalingFactor + originX
    y = -y*scalingFactor + originY
    return (x,y)


def Screen2Map(poly):
    length = len(poly)
    for i in range(length):
        (x,y) = poly[i]
        x =  (x - originX)*invScalingFactor
        y = -(y - originY)*invScalingFactor
        poly[i] = (x,y)


def NewMap():
    m = [(0,-5),(0,0),(5,0),(5,-5)]
    Plan2Map(m)
    Map2Screen(m)
    return m


def Move(poly, mx, my):
    length = len(poly)
    for i in range(length):
        (x,y) = poly[i]
        poly[i] = (x+mx,y+my)
    return


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

def CreateWaypoints(rectangle, n):
    waypoints = []
    if len(rectangle) != 4:
        print("Error: CreateWaypoints needs a rectangle as input")
        return waypoints
    # Durchmesser der neuen Messer: 25 cm
    # Durchmesser der alten Messer: 21.5 cm
    maxLaneDistance = 0.16*scalingFactor
    Va = np.array(rectangle[n])
    Vb = np.array(rectangle[(n + 1) & 3])
    Vc = np.array(rectangle[(n + 2) & 3])
    Vd = np.array(rectangle[(n + 3) & 3])
    Vba = np.subtract(Vb,Va)
    Vcb = np.subtract(Vc,Vb)
    Vda = np.subtract(Vd,Va)
    Vortho = np.array((-Vba[1], Vba[0]))
    Vortho = Vortho/np.linalg.norm(Vortho)
    
    Lcb = np.linalg.norm(Vcb)
    Vcb_n = Vcb/Lcb
    alpha = math.acos(np.dot(Vortho,Vcb_n))
    print(Vortho)
    print(Vcb_n)
    print("alpha=", alpha)
    perimeterDistance = Lcb*math.cos(alpha)
    numLanes = 1 + math.floor(perimeterDistance/maxLaneDistance+1)
    print("NumLanes=", numLanes)
    laneDistance = perimeterDistance / (numLanes - 1)
    VlaneTop = Vcb_n * laneDistance / math.cos(alpha)

    Lda = np.linalg.norm(Vda)
    Vda_n = Vda/Lda
    beta = math.acos(np.dot(Vortho,Vda_n))
    VlaneBottom = Vda_n * laneDistance / math.cos(beta)

    topFlag = True
    waypoints.append((Va[0],Va[1]))
    for i in range(numLanes):
        if topFlag:
            Vnext = np.add(Vb, VlaneTop*i)
            waypoints.append((Vnext[0],Vnext[1]))
            Vnext = np.add(Vb, VlaneTop*(i+1))
            if i < numLanes-1: waypoints.append((Vnext[0],Vnext[1]))
        else:
            Vnext = np.add(Va, VlaneBottom*i)
            waypoints.append((Vnext[0],Vnext[1]))
            Vnext = np.add(Va, VlaneBottom*(i+1))
            if i < numLanes-1: waypoints.append((Vnext[0],Vnext[1]))
        topFlag = not topFlag
    return waypoints


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

def LoadMaps():
    global maps_json
    global numMaps
    with open('maps2.json') as json_file:
        maps_json = json.load(json_file)
    numMaps = len(maps_json)
    print(numMaps)
    for i in range(numMaps):
        # load perimeter
        wpoly = []
        if len(maps_json[i]) > 0:
            points = maps_json[i]["perimeter"]
            for point in points:
                wpoly.append((point["X"], point["Y"]))
            Map2Screen(wpoly)
        perimeters.append(wpoly)
        # load waypoints
        wpoly = []
        if len(maps_json[i]) > 0:
            points = maps_json[i]["waypoints"]
            for point in points:
                wpoly.append((point["X"], point["Y"]))
            Map2Screen(wpoly)
        wayPoints.append(wpoly)
            
def StoreMaps():
    for m in range(1,10):
        if len(perimeters[m]) > 2:
            #process perimeter
            perimeter = perimeters[m].copy()
            Screen2Map(perimeter)
            p = []
            for i in range(len(perimeter)):
                (x,y) = perimeter[i]
                timestamp = '2021-04-20T15:19:37.433Z'
                p.append({'X': x, 'Y': y, 'delta': 0.01, 'timestamp': timestamp})
            # process waypoints
            waypoints = wayPoints[m].copy()
            Screen2Map(waypoints)
            w = []
            for i in range(len(waypoints)):
                (x,y) = waypoints[i]
                w.append({'X': x, 'Y': y})
            maps_json[m] = {'perimeter': p, 'exclusions': [], 'waypoints': w, 'dockpoints': []}
        else:
            maps_json[m] = { }
    with open('tmp.json', 'w') as outfile:
        json.dump(maps_json, outfile)
    print("Storing maps in maps2.json")
    os.system("python -m json.tool tmp.json >maps2.json")


def SendCmd(cmd):
   sleep(0.1)
   for transmission in range(3):
      print("[maps.SendCmd] " + cmd)
      udp.send(cmd)
      
      print("[maps.SendCmd] Wait for answer: " + cmd[3])
      timeOutCounter = 5
      # longer timeout for N and C commands
      if cmd[3]=="N" or cmd[3]=="C": timeOutCounter = 20
      while True:
         answer = udp.receive()
         if answer != "":
            print(answer, end='')
            if answer[0] == cmd[3]: return SUCCESS
         sleep(0.1)
         timeOutCounter = timeOutCounter - 1
         if timeOutCounter == 0: break;
      print("[maps.SendCmd] TIMEOUT ERROR - Transmission #", transmission);
   return ERROR



def UploadMap(m, startMowingFlag):
   errorFlag = True
   if len(perimeters[m]) >= 4:
       cmd = str.format('AT+U,{:d}',m+1)
       if SendCmd(cmd): return True
       #process perimeter
       perimeter = perimeters[m].copy()
       Screen2Map(perimeter)
       plen = len(perimeter)
       i = 0
       j = 0
       while True:
           if i >=plen: break
           (x1,y1) = perimeter[i]
           i = i + 1
           if i<plen:
               (x2,y2) = perimeter[j]
               cmd = str.format('AT+W,{:d},{:.2f},{:.2f},{:.2f},{:.2f}',j,x1,y1,x2,y2)
               i = i + 1
               j = j + 2
           else:
               cmd = str.format('AT+W,{:d},{:.2f},{:.2f}',j,x1,y1)
               j = j + 1
               break
           if SendCmd(cmd)==ERROR: return ERROR
   if len(wayPoints[m]) >= 2:
       # process waypoints
       waypoints = wayPoints[m].copy()
       Screen2Map(waypoints)
       wlen = len(waypoints)
       i = 0
       while True:
           if i >=wlen: break
           (x1,y1) = waypoints[i]
           i = i + 1
           if i<wlen:
               (x2,y2) = waypoints[i]
               cmd = str.format('AT+W,{:d},{:.2f},{:.2f},{:.2f},{:.2f}',j,x1,y1,x2,y2)
               i = i + 1
               j = j + 2
           else:
               cmd = str.format('AT+W,{:d},{:.2f},{:.2f}',j,x1,y1)
               j = j + 1
               break
           if SendCmd(cmd)==ERROR: return ERROR
       # AT+N, iWayPerimeter, iWayExclusion, iWayDock, iWayMow, iWayFree
       cmd = str.format('AT+N,{:d},0,0,{:d},0',plen,wlen)
       if SendCmd(cmd)==ERROR: return ERROR
       if startMowingFlag:
           sleep(1)
           # AT+C,-1,1,0.39,0,0,-1,-1,0,0x8
           #bEnableMowMotor = -1          # off
           #iOperationType = 1            # 1=OP_MOW
           fSpeed = 0.39                 # m/s
           #iFixTimeout = 0               # 0 = no fix timeout
           #bFinishAndRestart = 0         # disabled
           #fMowingPointPercent = -1      # 
           #bSkipNextMowingPoint = -1     # disabled
           #bEnableSonar = 0              # disabled
           cmd = str.format('AT+C,-1,1,{:.2f},0,0,-1,-1,0', fSpeed)
           if SendCmd(cmd)==ERROR: return ERROR
   return SUCCESS



def main():
    # Gartenplan - x-Achse parallel zum oberen Zaun
    garten = [(0,0),(44.70,0),(44.70,-24.00),(0,-7.80)]
    print(garten)
    Plan2Map(garten)
    print(garten)
    Map2Screen(garten)
    print(garten)

if __name__ == '__main__':
    main()
