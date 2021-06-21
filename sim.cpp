#include "robot.h"
#include "helper.h"

const float SAMPLE_PERIOD = CONTROL_PERIOD_MS/1000.;

extern float stateX;       // position-east (m)
extern float stateY;       // position-north (m)
extern float stateDelta;   // direction (rad)
extern float stateDeltaGPS;


Sim::Sim()
{
   activeFlag = false;
   posX = -6.0;
   posY = -3.0;
   delta = 0.0;
   deltaStep = 0.0;
   posStep = 0.0;
}

bool Sim::SetLinearAngularSpeed(float linear, float angular)
{
   if (!activeFlag) return false;

   speed = linear;
   deltaStep = angular*SAMPLE_PERIOD;
   posStep = linear*SAMPLE_PERIOD;
   return true;
}

bool Sim::ComputeRobotState()
{
   if (!activeFlag) return false;

   posX += cos(delta)*posStep;
   posY += sin(delta)*posStep;
   delta = scalePI(delta + deltaStep);
   stateX = posX;
   stateY = posY;
   stateDelta = delta;
   stateDeltaGPS = delta;
   gps.solutionAvail = true;
   gps.solution = UBLOX::SOL_FIXED;
   gps.numSV = 30;
   gps.numSVdgps = 28;
   gps.groundSpeed = speed;
   gps.relPosD = delta;
   gps.relPosE = posX;
   gps.relPosN = posY;
   gps.height = 415;
   gps.dgpsAge = millis();
   return true;
}