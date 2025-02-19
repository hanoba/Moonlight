# constant configuration parameters that cannot be changed via the amcp GUI
sonarEnable=0   #HB was 1
sonarObstacleDist=0  #20
sonarNearDist=0  #35
#sonarNearSpeed=0.1     #HB parameter removed

# Kippschutz: Factor to convert from pitch (in rad) to duty cycle (255=100%)
pitchPwmFactor = 16*255  / (3.1415/2)

# temporarily disable mow motor for tests
enableMowMotor = 0

# Durchmesser der neuen Messer: 25 cm
# Durchmesser der alten Messer: 21.5 cm
dmMesser = 0.25      # in meter
uLaneOverlap = 0.09  # in meter
vLaneOverlap = 0.03  # in meter

