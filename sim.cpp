#include "robot.h"
#include "helper.h"
#include <Arduino.h>

const float SAMPLE_PERIOD = CONTROL_PERIOD_MS/1000.;

extern float stateX;       // position-east (m)
extern float stateY;       // position-north (m)
extern float stateDelta;   // direction (rad)
extern float stateDeltaGPS;


Sim::Sim()
{
   activeFlag = false;
   posX =  4.0;
   posY = -3.0;
   delta = 0.0;
   deltaStep = 0.0;
   posStep = 0.0;
   nextGpsMsgTime = 0;
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
   if (millis() >= nextGpsMsgTime)
   {        
      nextGpsMsgTime = millis() + 1700;
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

      // simulate GPS logging
#ifdef MOONLIGHT_LOG_GPS_POSITION
      char buf[64];
      sprintf(buf,"x=%6.2f y=%6.2f SOL=%d\r\n", gps.relPosE, gps.relPosN, gps.solution);
      sdSerial.writeGpsLogSD(buf);
#endif
   }
   return true;
}

static bool IsInTriangle(double xp, double yp, double xa, double ya, double xb, double yb, double xc, double yc)
{
   // See https://prlbr.de/2014/liegt-der-punkt-im-dreieck/
   double ABC =  abs(xa*(yb-yc) + xb*(yc-ya) + xc*(ya-yb));
   double ABCP = abs(xa*(yb-yp) + xb*(yc-ya) + xc*(yp-yb) + xp*(ya-yc));
   double ABPC = abs(xa*(yb-yc) + xb*(yp-ya) + xp*(yc-yb) + xc*(ya-yp));
   double APBC = abs(xa*(yp-yc) + xp*(yb-ya) + xb*(yc-yp) + xc*(ya-yb));
   double dmax = max(ABCP, ABPC);
   dmax = max(APBC, dmax);
   return dmax <= ABC;
}

static bool IsInGarten(double xp, double yp)
{
   const double xa = -32.0785930264506;
   const double ya = -13.2325080556693;
   const double xb =   3.8013106740782;
   const double yb =  12.8357678835018;
   const double xc =  16.3663945990013;
   const double yc =  -8.0508496788145;
   const double xd = -28.2104329694310;
   const double yd = -20.0747984450987;
   if (IsInTriangle(xp, yp, xa, ya, xb, yb, xc, yc)) return true;
   if (IsInTriangle(xp, yp, xc, yc, xd, yd, xa, ya)) return true;
   return false;
}

bool Sim::Obstacle(bool& obstacleFlag)
{
   obstacleFlag = false; 
   if (!activeFlag) return false;
   //if (maps.mapID>=9) obstacleFlag = stateY > 0;
   obstacleFlag = !IsInGarten(stateX, stateY);
   return true;
}


bool Sim::RobotShouldMove(bool& shouldMoveFlag)
{
   if (!activeFlag) return false;
   shouldMoveFlag = fabs(deltaStep) > 0.001 || fabs(posStep) > 0.001;
   return true;
}