import math

# Gartenplan - x-Achse parallel zum oberen Zaun
gartenPlan = [(0,0),(44.70,0),(44.70,-24.00),(0,-4.12)]

#square([7.23,4.67]);

# GPS-RTK Nullpunkt
x0 = 44.7 - 10.3
y0 = 0.5 + 4.7 + 2.45
phi = 38 / 180 * math.pi

# 
cos_phi = math.cos(phi)
sin_phi = math.sin(phi)


def Plan2Map(poly):
    res = []
    #length = len(poly)
    for (x,y) in poly:
        #(x,y) = xy;
        x=(x-x0)
        y=(y+y0)
        # Drehung
        xn = x*cos_phi - y*sin_phi
        yn=  y*cos_phi + x*sin_phi
        res.append((x,y))
    return res


t = (1, 2)
(x,y) = t
print(x)
print(y)
print(y)
print(math.floor(-1.5))

print(gartenPlan)
gartenMap = Plan2Map(gartenPlan)
print(gartenMap)
