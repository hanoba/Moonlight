import math
import json
import math
import numpy as np
import os
from time import sleep
from datetime import datetime
import udp
import plan


# Return values
ERROR = True
SUCCESS = False

# indices for special perimeters
#MAP_INDEX_EXCLUSION_POINTS = 10
MAP_INDEX_PERIMETER_WITH_EXCLUSION = 14
MAP_INDEX_REFERENCE_POINTS = 15

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
        x = round(x,2)
        y = round(y,2)
        poly[i] = (x,y)


def NewMap():
    m = [(0,-5),(0,0),(5,0),(5,-5)]
    Plan2Map(m)
    Map2Screen(m)
    return m

# Garten
garten = plan.Garten()
Plan2Map(garten)
gmap = garten.copy()
#print(gmap)
Map2Screen(garten)

# Gartenhaus
haus = plan.Gartenhaus()
Plan2Map(haus)
Map2Screen(haus)

# DockPoints
#dockPoints = [(3,-3),(3.36,-1.50),(3.03,-1.08),(2.70,-0.65),(2.46,-0.34)]
dockPoints = [(3,-3),(3.36,-1.50),(3.03,-1.08),(2.70,-0.65),(2.33,-0.18)]

Map2Screen(dockPoints)

# Terrasse
terrasse = plan.Terrasse()
Plan2Map(terrasse)
Map2Screen(terrasse)

# Schuppen
schuppen = plan.Schuppen()
Plan2Map(schuppen)
Map2Screen(schuppen)

def IsInTriangleOld(xp, yp, triangle):
   #print(triangle)
   (xa, ya) = triangle[0]
   (xb, yb) = triangle[1]
   (xc, yc) = triangle[2]
   a = (yb-yp)*(xa-xp) - (ya-yp)*(xb-xp)
   b = (yc-yp)*(xa-xp) - (ya-yp)*(xc-xp)
   if a*b > 0: return True
   a = (ya-yp)*(xb-xp) - (yb-yp)*(xa-xp)
   b = (yc-yp)*(xb-xp) - (yb-yp)*(xc-xp)
   if a*b > 0: return True
   return False

def IsInTriangle(xp, yp, xa, ya, xb, yb, xc, yc):
   #print(triangle)
   #(xa, ya) = triangle[0]
   #(xb, yb) = triangle[1]
   #(xc, yc) = triangle[2]
   ABC =  abs(xa*(yb-yc) + xb*(yc-ya) + xc*(ya-yb))
   ABCP = abs(xa*(yb-yp) + xb*(yc-ya) + xc*(yp-yb) + xp*(ya-yc))
   ABPC = abs(xa*(yb-yc) + xb*(yp-ya) + xp*(yc-yb) + xc*(ya-yp))
   APBC = abs(xa*(yp-yc) + xp*(yb-ya) + xb*(yc-yp) + xc*(ya-yb))
   return max([ABCP, ABPC, APBC]) <= ABC

def IsInGarten(xp, yp):
   xa = -32.0785930264506
   ya = -13.2325080556693
   xb =   3.8013106740782
   yb =  12.8357678835018
   xc =  16.3663945990013
   yc =  -8.0508496788145
   xd = -28.2104329694310
   yd = -20.0747984450987
   #t1 = [gmap[0], gmap[1], gmap[2]]
   #t2 = [gmap[2], gmap[3], gmap[0]]
   if IsInTriangle(xp, yp, xa, ya, xb, yb, xc, yc): return True
   if IsInTriangle(xp, yp, xc, yc, xd, yd, xa, ya): return True
   return False

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

def CreateBumperWaypoints(rectangle, n):
    waypoints = []
    if len(rectangle) != 4:
        print("Error: CreateWaypoints needs a rectangle as input")
        return waypoints
    # Durchmesser der neuen Messer: 25 cm
    # Durchmesser der alten Messer: 21.5 cm
    #maxLaneDistance = 0.16*scalingFactor
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
            #Vnext = np.add(Vb, VlaneTop*(i+1))
            #if i < numLanes-1: waypoints.append((Vnext[0],Vnext[1]))
        else:
            Vnext = np.add(Va, VlaneBottom*i)
            waypoints.append((Vnext[0],Vnext[1]))
            #Vnext = np.add(Va, VlaneBottom*(i+1))
            #if i < numLanes-1: waypoints.append((Vnext[0],Vnext[1]))
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
    with open('maps.json') as json_file:
        maps_json = json.load(json_file)
    numMaps = len(maps_json)
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
    udp.WriteLog("[maps.LoadMaps] " + str(numMaps) + " maps loaded")

def StoreMaps(fileName):
    #for m in range(1,10):
    for m in range(0,MAP_INDEX_REFERENCE_POINTS+1):
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
    os.system("python -m json.tool tmp.json >"+fileName)

# export maps in Ardumower App format
def ExportMaps(fileName):
    # use garten as perimeter
    #perimeter = garten.copy()
    # MAP10 is perimeter with all exclusions
    perimeter = perimeters[MAP_INDEX_PERIMETER_WITH_EXCLUSION].copy()
    Screen2Map(perimeter)
    p = []
    for i in range(len(perimeter)):
        (x,y) = perimeter[i]
        timestamp = '2021-04-20T15:19:37.433Z'
        p.append({'X': x, 'Y': y, 'delta': 0.01, 'timestamp': timestamp})
        
    # use MapId=11 as exclusion point
    #perimeter = perimeters[10].copy()
    #Screen2Map(perimeter)
    #e1 = []
    #for i in range(len(perimeter)):
    #    (x,y) = perimeter[i]
    #    timestamp = '2021-04-20T15:19:37.433Z'
    #    e1.append({'X': x, 'Y': y, 'delta': 0.01, 'timestamp': timestamp})
    #e = [ e1 ]
        
    for m in range(0,10):
        if len(perimeters[m]) > 2:
            #process perimeter
            ##perimeter = perimeters[m].copy()
            ##Screen2Map(perimeter)
            ##p = []
            ##for i in range(len(perimeter)):
            ##    (x,y) = perimeter[i]
            ##    timestamp = '2021-04-20T15:19:37.433Z'
            ##    p.append({'X': x, 'Y': y, 'delta': 0.01, 'timestamp': timestamp})
            # process waypoints
            waypoints = wayPoints[m].copy()
            Screen2Map(waypoints)
            w = []
            for i in range(len(waypoints)):
                (x,y) = waypoints[i]
                w.append({'X': x, 'Y': y})
            #maps_json[m] = {'perimeter': p, 'exclusions': e, 'waypoints': w, 'dockpoints': []}
            maps_json[m] = {'perimeter': p, 'exclusions': [], 'waypoints': w, 'dockpoints': []}
        else:
            maps_json[m] = { }
    with open('tmp.json', 'w') as outfile:
        json.dump(maps_json, outfile)
    os.system("python -m json.tool tmp.json >"+fileName)


def UploadMap(m):
   errorFlag = True
   #if len(perimeters[m]) >= 4:
   cmd = str.format('AT+U,{:d}',m+1)
   if udp.ExecCmd(cmd)=="": return ERROR
   # process perimeter + exclusionPoints + waypoints
   #plen = len(garten)
   #xlen = len(perimeters[MAP_INDEX_EXCLUSION_POINTS])
   #wlen = len(wayPoints[m])
   #allPoints = garten.copy()
   #allPoints.extend(perimeters[MAP_INDEX_EXCLUSION_POINTS])
   #allPoints.extend(wayPoints[m])
   plen = len(perimeters[MAP_INDEX_PERIMETER_WITH_EXCLUSION])
   xlen = 0
   dlen = len(dockPoints)
   wlen = len(wayPoints[m])
   allPoints = perimeters[MAP_INDEX_PERIMETER_WITH_EXCLUSION].copy()
   #allPoints.extend(perimeters[MAP_INDEX_EXCLUSION_POINTS])
   allPoints.extend(dockPoints)
   allPoints.extend(wayPoints[m])
   Screen2Map(allPoints)
   aLen = len(allPoints)
   print("Total points in map:", aLen)
   i = 0
   j = 0
   while True:
       if i >=aLen: break
       (x1,y1) = allPoints[i]
       i = i + 1
       if i<aLen:
           (x2,y2) = allPoints[i]
           cmd = str.format('AT+W,{:d},{:.2f},{:.2f},{:.2f},{:.2f}',j,x1,y1,x2,y2)
           i = i + 1
           j = j + 2
       else:
           cmd = str.format('AT+W,{:d},{:.2f},{:.2f}',j,x1,y1)
           j = j + 1
           #break
       if udp.ExecCmd(cmd)=="": return ERROR
   # AT+N, iWayPerimeter, iWayExclusion, iWayDock, iWayMow, iWayFree
   cmd = str.format('AT+N,{:d},{:d},{:d},{:d},0',plen,xlen,dlen,wlen)
   if udp.ExecCmd(cmd)=="": return ERROR
   sleep(1)
   # AT+X,0,iExclusionLength0 [,1,iExclusionLength0,...]
   #cmd = str.format('AT+X,0,{:d}',xlen)
   #if udp.ExecCmd(cmd)=="": return ERROR
   return SUCCESS


def ComputeMapChecksum(m):
   checkSum = int(0)
   #allPoints = garten.copy()
   #
   allPoints = perimeters[MAP_INDEX_PERIMETER_WITH_EXCLUSION].copy()
   allPoints.extend(dockPoints)
   allPoints.extend(wayPoints[m])
   Screen2Map(allPoints)
   for point in allPoints:
      (x1,y1) = point
      checkSum += int(math.floor(x1*100+0.5)) + int(math.floor(y1*100+0.5))
   return checkSum


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
