# constant configuration parameters that cannot be changed via the amcp GUI
sonarEnable=0   

# Pitch detection
pitchThresholdDeg = 40.0    # motor stops immediately if pitch is higher than this value

# Obstacle map configuration
oMapOutsideFenceDist = 1.5                         # distance from fence to odd waypoints in m
oMapSlowSpeed = 0.25                               # slow speed close to fence for obstacle maps
oMapDistThreshold = oMapOutsideFenceDist + 0.4     # slow speed distance threshold in m for obstacle maps

# 0 means that mow motor is temporarily disabled for tests
enableMowMotor = 1

# Durchmesser der neuen Messer: 25 cm
# Durchmesser der alten Messer: 21.5 cm
dmMesser = 0.25      # in meter
uLaneOverlap = 0.09  # in meter
vLaneOverlap = 0.03  # in meter

