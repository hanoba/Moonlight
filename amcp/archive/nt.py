import json
import numpy as np

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
    print(A)
    print(Va)
    Va = np.rint(np.add(Vb,Vdc*x[0])).astype(int)
    print(Va)
    rectangle[n] = (Va[0], Va[1])
    print(rectangle)

r=0
rectangle=[ (797, 173), (922, 89), (1099, 373), (974, 431)]

MakeParallel(rectangle, 1)
