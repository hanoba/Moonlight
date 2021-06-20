import math
import maps

def Garten_old():
    # Gartenplan - x-Achse parallel zum oberen Zaun
    gx1=44.70
    gx2=gx1-1.4
    garten_old = [(0,0),(gx1,0),(gx2,-24.00),(0,-7.56)]
    return garten_old

def Garten():
    # Messwerte Bosch Laserentfernungsmesser
    a0 = 18.73
    b0 = 15.16
    c0 =  7.86 
    m1 = 30.54
    b2 = 44.35
    c2 = 24.25
    b3 =  0.47
    
    # Dreieck D0
    wa0 = math.acos((b0*b0 + c0*c0 - a0*a0)/(2*b0*c0))
    #print("wa0 =", wa0/math.pi*180)
    
    # Dreieck D1
    wa1 = wa0
    b1 = b0 + m1
    c1 = c0
    a1 = math.sqrt(b1*b1 + c1*c1 - 2*b1*c1*math.cos(wa1))
    #print("a1 =", a1)
    wc1 = math.acos((a1*a1 + b1*b1 - c1*c1)/(2*a1*b1))
    #print("wc1 =", wc1/math.pi*180)
    
    # Dreieck D2
    a2 = a1
    wa2 = math.acos((b2*b2 + c2*c2 - a2*a2)/(2*b2*c2))
    #print("wa2 =", wa2/math.pi*180)
    wb2 = math.acos((a2*a2 + c2*c2 - b2*b2)/(2*a2*c2))
    #print("wb2 =", wb2/math.pi*180)
    
    # Dreieck D3
    c3 = c2
    wa3 = math.pi - wc1 - wb2
    a3 = math.sqrt(b3*b3 + c3*c3 - 2*b3*c3*math.cos(wa3))
    #print("a3 =", a3)
    wb3 = math.acos((a3*a3 + c3*c3 - b3*b3)/(2*a3*c3))
    #print("wb3 =", wb3/math.pi*180)
    
    # Viereck
    wpb = wa2 + wb3
    #print("wpb =", wpb/math.pi*180)
    wpa = 2*math.pi - wa0 - wpb - (math.pi - wa3 - wb3)
    #print("wpa =", wpa/math.pi*180)
    
    
    xo = 0.3
    PA=(xo,0)
    PB=(xo+b2,0)
    
    wb = wpb - math.pi/2
    PC=(xo+b2+a3*math.sin(wb), -a3*math.cos(wb))
    
    wa = wpa - math.pi/2
    PD=(xo-c0*math.sin(wa), -c0*math.cos(wa))

    check=math.sqrt((PD[0]-PC[0])**2+(PD[1]-PC[1])**2)
    #print(check, b1+b3)

    garten=[PA, PB, PC, PD]
    return garten

def Gartenhaus():
    haus = [(0,0),(7.23,0),(7.23,4.67),(0,4.67)]
    mx = 44.70 - 10.30 - 7.23 # 5.10 + 4.00 + 16.60
    my = -4.76-0.5
    maps.Move(haus,mx,my)
    return haus

def Terrasse():
    xx = 7.23-6.08
    #yy = 4.67
    mx = 44.70 - 10.30 - 7.23 # 5.10 + 4.00 + 16.60
    my = -4.76-0.5
    terrasse = [(xx,0),(xx+6.08,0),(xx+6.08,-4.45),(xx,-4.45)]
    maps.Move(terrasse,mx,my)
    return terrasse
    
def Schuppen():
    schuppen = [(0,0),(4.00,0),(4.00,4.50),(0,4.50)]
    mx = 5.10 + 1.6 - 0.5
    my = -4.50-0.50 - 0.3
    maps.Move(schuppen,mx,my)
    return schuppen
