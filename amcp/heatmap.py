import pygame
import math
import numpy as np
import maps

N = 4  # points per meter
heatMapColorPalette = [(233,62,58),(237,104,60),(243,144,63),(253,199,12),(255,243,59)]
numColors = len(heatMapColorPalette)
print(numColors)

#   0        1     2     3      4     5     6       7      8      9     10     11     12     13  14
# #Time     Tctl State  Volt   Ic    Tx     Ty     Sx     Sy     Sd     Gx     Gy     Gd     Gz  SOL     Age  Sat.   Il   Ir   Im Temp Hum Flags  Map  WayPts 
iSX=7
iSY=8
iSOL=14
txt = ":14:13:20 0.02  MOW   27.1   56 -20.74  -8.21 -13.27  -3.18  -178° -13.23  -3.18   123°   5.41 FIX     0.2 30/35   86  105   18 39°C 32% bpdgSF MAP6  27/54 "

xmin = -34;
xmax =  18;
ymin = -21;
ymax =  15;

DX = (xmax - xmin)*N
DY = (ymax - ymin)*N

total = np.zeros((DX, DY))
numFix =  np.zeros((DX, DY))


def CreateHeatMap():
    # Using readlines()
    file1 = open('mow.txt', 'r')
    Lines = file1.readlines()
    
    # process each line of logfile
    for line in Lines:
        x = line.split()
        sol = x[iSOL]
        # fix inconsistent position (logs are are from two different Moonlight versions)
        if sol=="FIX" or sol=="FLOAT" or sol=="INVAL":
            sx = float(x[iSX])
            sy = float(x[iSY])
        else:
            sol = x[iSOL+1]
            sx = float(x[iSX+1])
            sy = float(x[iSY+1])
        nx = math.floor((sx - xmin)*N)
        ny = math.floor((sy - ymin)*N)
        #print(sol, sx, sy, nx, ny)
        total[nx,ny] += 1
        if sol == "FIX": numFix[nx,ny] += 1


def PrintHeatmap():
    for iy in range(DY-1,-1,-1):
        for ix in range(DX):
            if total[ix,iy] > 0: heat = int(numFix[ix,iy] / total[ix,iy] * numColors + 1)
            else: heat = 0;
            print("{:1d}".format(heat), end="")
        print(" ")


def DrawHeatmap(surface):
    width = maps.scalingFactor/N
    height = maps.scalingFactor/N
    for iy in range(DY-1,-1,-1):
        my = iy/N + ymin;
        for ix in range(DX):
            if total[ix,iy] > 1: 
                heat = int(numFix[ix,iy] / total[ix,iy] * numColors)
                if heat == numColors: heat = numColors - 1
                color = heatMapColorPalette[heat]
                mx = ix/N + xmin
                (left,bottom) = maps.Map2ScreenXY(mx,my)
                top = bottom - height
                rect = pygame.Rect(left, top, width, height)
                pygame.draw.rect(surface, color, rect)
    
    
def main():
    CreateHeatMap()
    PrintHeatmap()


if __name__ == '__main__':
    main()
