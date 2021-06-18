import json

def GetWayPoints():
    with open('maps.json') as json_file:
        data = json.load(json_file)
        length = len(data)
        #print(length)
        map1 = data[1]
        waypoints = map1["waypoints"]
        #print(waypoints)
        #print(len(waypoints))
        wpoly = []
        for point in waypoints:
            wpoly.append((point["X"], point["Y"]))
    return wpoly

wayPoints = GetWayPoints()
print(wayPoints)
