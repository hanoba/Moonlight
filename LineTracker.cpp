// Ardumower Sunray 
// Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH
// Licensed GPLv3 for open source use
// or Grau GmbH Commercial License for commercial use (http://grauonline.de/cms2/?page_id=153)


#include "LineTracker.h"
#include "robot.h"
//#include "StateEstimator.h"
#include "helper.h"
#include "pid.h"


//PID pidLine(0.2, 0.01, 0); // not used
//PID pidAngle(2, 0.1, 0);  // not used
Polygon circle(8);

float stanleyTrackingNormalK = STANLEY_CONTROL_K_NORMAL;
float stanleyTrackingNormalP = STANLEY_CONTROL_P_NORMAL;    
float stanleyTrackingSlowK = STANLEY_CONTROL_K_SLOW;
float stanleyTrackingSlowP = STANLEY_CONTROL_P_SLOW;    

float setSpeed = 0.1; // linear speed (m/s)
Point last_rotation_target;
bool rotateLeft = false;
bool rotateRight = false;
bool angleToTargetFits = false;
bool langleToTargetFits = false;
bool targetReached = false;
float trackerDiffDelta = 0;
bool stateKidnapped = false;
bool printmotoroverload = false;
bool trackerDiffDelta_positive = false;

float lateralError = 0; // lateral error

int get_turn_direction_preference() {
  Point target = maps.targetPoint;
  float targetDelta = pointsAngle(stateX, stateY, target.x(), target.y());
  float center_x = stateX;
  float center_y = stateY;
  float r = 0.3;

  // create circle / octagon around center angle 0 - "360"
  circle.points[0].setXY(center_x + cos(deg2rad(0)) * r, center_y + sin(deg2rad(0)) * r);
  circle.points[1].setXY(center_x + cos(deg2rad(45)) * r, center_y + sin(deg2rad(45)) * r);
  circle.points[2].setXY(center_x + cos(deg2rad(90)) * r, center_y + sin(deg2rad(90)) * r);
  circle.points[3].setXY(center_x + cos(deg2rad(135)) * r, center_y + sin(deg2rad(135)) * r);
  circle.points[4].setXY(center_x + cos(deg2rad(180)) * r, center_y + sin(deg2rad(180)) * r);
  circle.points[5].setXY(center_x + cos(deg2rad(225)) * r, center_y + sin(deg2rad(225)) * r);
  circle.points[6].setXY(center_x + cos(deg2rad(270)) * r, center_y + sin(deg2rad(270)) * r);
  circle.points[7].setXY(center_x + cos(deg2rad(315)) * r, center_y + sin(deg2rad(315)) * r);

  // CONSOLE.print("get_turn_direction_preference: ");
  // CONSOLE.print(" pos: ");
  // CONSOLE.print(stateX);
  // CONSOLE.print("/");
  // CONSOLE.print(stateY);
  // CONSOLE.print(" stateDelta: ");
  // CONSOLE.print(stateDelta);
  // CONSOLE.print(" targetDelta: ");
  // CONSOLE.println(targetDelta);
  int right = 0;
  int left = 0;
  for(int i = 0; i < circle.numPoints; ++i) {
    float angle = pointsAngle(stateX, stateY, circle.points[i].x(), circle.points[i].y());
    // CONSOLE.print(angle);
    // CONSOLE.print(" ");
    // CONSOLE.print(i);
    // CONSOLE.print(": ");
    // CONSOLE.print(circle.points[i].x());
    // CONSOLE.print("/");
    // CONSOLE.println(circle.points[i].y());
    if (maps.checkpoint(circle.points[i].x(), circle.points[i].y())) {

            // skip points in front of us
            if (fabs(angle-stateDelta) < 0.05) {
                    continue;
            }

            if (stateDelta < targetDelta) {
                if (angle >= stateDelta && angle <= targetDelta) {
                    left++;
                } else {
                    right++;
                }
            } else {
                   if (angle <= stateDelta && angle >= targetDelta) {
                    right++;
                } else {
                    left++;
                }
            }
    }
  }
  // CONSOLE.print("left/right: ");
  // CONSOLE.print(left);
  // CONSOLE.print("/");
  // CONSOLE.println(right);

  if (right == left) {
          return 0;
  }

  if (right < left) {
          return 1;
  }

  return -1;
}

// control robot velocity (linear,angular) to track line to next waypoint (target)
// uses a stanley controller for line tracking
// https://medium.com/@dingyan7361/three-methods-of-vehicle-lateral-control-pure-pursuit-stanley-and-mpc-db8cc1d32081
void trackLine()
{  
  Point target = maps.targetPoint;
  Point lastTarget = maps.lastTargetPoint;
  float linear = 1.0;  
  bool mow = true;
  if (stateOp == OP_DOCK) mow = false;
  float angular = 0;      
  float targetDelta = pointsAngle(stateX, stateY, target.x(), target.y());      
  if (maps.trackReverse) targetDelta = scalePI(targetDelta + PI);
  targetDelta = scalePIangles(targetDelta, stateDelta);
  trackerDiffDelta = distancePI(stateDelta, targetDelta);                         
  lateralError = distanceLineInfinite(stateX, stateY, lastTarget.x(), lastTarget.y(), target.x(), target.y());        
  float distToPath = distanceLine(stateX, stateY, lastTarget.x(), lastTarget.y(), target.x(), target.y());        
  float targetDist = maps.distanceToTargetPoint(stateX, stateY);
  
  float lastTargetDist = maps.distanceToLastTargetPoint(stateX, stateY);  
  // MAP11..14 are "bumper maps". Mow until bumper hits for odd mow points
  if (maps.isObstacleMowPoint()) targetReached = maps.obstacleTargetReached;
  else if (cfgSmoothCurves)
     targetReached = (targetDist < 0.2);    
  else 
     targetReached = (targetDist < 0.05);    
  
  if ( (last_rotation_target.x() != target.x() || last_rotation_target.y() != target.y()) &&
        (rotateLeft || rotateRight ) ) {
    // CONSOLE.println("reset left / right rot (target point changed)");
    rotateLeft = false;
    rotateRight = false;
  }
          
  // allow rotations only near last or next waypoint or if too far away from path
  // it might race between rotating mower and targetDist check below
  // if we race we still have rotateLeft or rotateRight true
  if ( (targetDist < 0.5) || (lastTargetDist < 0.5) || (fabs(distToPath) > 0.5) ||
       rotateLeft || rotateRight ) {
    if (cfgSmoothCurves)
      angleToTargetFits = (fabs(trackerDiffDelta)/PI*180.0 < 120);    //HB (cfgMoonlightLineTracking ? 40 : 120));
    else     
      angleToTargetFits = (fabs(trackerDiffDelta)/PI*180.0 < 20);
  } else {
     angleToTargetFits = true;
  }
               
  if (!angleToTargetFits){
    // angular control (if angle to far away, rotate to next waypoint)
    linear = 0;
    angular = cfgAngularSpeed;      //HB was 0.5;               
    if ((!rotateLeft) && (!rotateRight)) // decide for one rotation direction (and keep it)
    {
       if (cfgMoonlightLineTracking)
       {
          rotateRight = trackerDiffDelta < 0;
          rotateLeft = !rotateRight;
       }         
       else   
       {
          int r = 0;
          // no idea but don't work in reverse mode...
          if (!maps.trackReverse) {
            r = get_turn_direction_preference();
          }        
          
          if (r == 1) {
            //CONSOLE.println("force turn right");
            rotateLeft = false;
            rotateRight = true;
          }
          else if (r == -1) {
            //CONSOLE.println("force turn left");
            rotateLeft = true;
            rotateRight = false;
          }
          else if (trackerDiffDelta < 0) {
            rotateRight = true;
          } else {
            rotateLeft = true;
          }
       }
       // store last_rotation_target point
       last_rotation_target.setXY(target.x(), target.y());
       trackerDiffDelta_positive = (trackerDiffDelta >= 0);
    }        
    if (trackerDiffDelta_positive != (trackerDiffDelta >= 0)) {
      CONSOLE.println("reset left / right rotation - DiffDelta overflow");
      rotateLeft = false;
      rotateRight = false;
      // reverse rotation (*-1) - slowly rotate back
      angular = 10.0 / 180.0 * PI * -1; //  10 degree/s (0.19 rad/s);               
    }
    if (rotateRight) angular *= -1;
  } 
  else {
    // line control (stanley)
    bool straight = maps.nextPointIsStraight();
    bool trackslow_allowed = true;

    rotateLeft = false;
    rotateRight = false;
    if (maps.trackSlow && trackslow_allowed) {
      // planner forces slow tracking (e.g. docking etc)
      linear = 0.1;           
    } else if (     ((setSpeed > 0.2) && (maps.distanceToTargetPoint(stateX, stateY) < 0.5) && (!straight))   // approaching
          || ((linearMotionStartTime != 0) && (millis() < linearMotionStartTime + 3000))                      // leaving  
       ) 
    {
      linear = maps.isObstacleMap ? min(cfgSlowSpeedObstacleMap, setSpeed) : 0.1; // reduce speed when approaching/leaving waypoints          
    } 
    else {
      //if (gps.solution == UBLOX::SOL_FLOAT)        
      //  linear = max(setSpeed/2, 0.2); // reduce speed for float solution
      //else
        linear = setSpeed;         // desired speed
      if (sonar.nearObstacle()) linear = 0.1; // slow down near obstacles
      if (upHillFlag) linear = 0.1;   //HB vermeiden, dass Mower kippt bei grossen Steigungen
    }      
    // slow down speed in case of overload and overwrite all prior speed 
    if ( (motor.motorLeftOverload) || (motor.motorRightOverload) || (motor.motorMowOverload) ){
      if (!printmotoroverload) {
          CONSOLE.println("motor overload detected: reduce linear speed");
      }
      printmotoroverload = true;
      linear = maps.isObstacleMap ? min(cfgSlowSpeedObstacleMap, setSpeed) : 0.1;  
    } else {
      printmotoroverload = false;
    }   
          
    //angular                                   r = 3.0 * trackerDiffDelta + 3.0 * lateralError;       // correct for path errors 
    float k = stanleyTrackingNormalK; // STANLEY_CONTROL_K_NORMAL;
    float p = stanleyTrackingNormalP; // STANLEY_CONTROL_P_NORMAL;    
    if (maps.trackSlow && trackslow_allowed) {
      k = stanleyTrackingSlowK; //STANLEY_CONTROL_K_SLOW;   
      p = stanleyTrackingSlowP; //STANLEY_CONTROL_P_SLOW;          
    }
    angular =  p * trackerDiffDelta + atan2(k * lateralError, (0.001 + fabs(motor.linearSpeedSet)));       // correct for path errors           
    /*pidLine.w = 0;              
    pidLine.x = lateralError;
    pidLine.max_output = PI;
    pidLine.y_min = -PI;
    pidLine.y_max = PI;
    pidLine.compute();
    angular = -pidLine.y;   */
    //CONSOLE.print(lateralError);        
    //CONSOLE.print(",");        
    //CONSOLE.println(angular/PI*180.0);            
    if (maps.trackReverse) linear *= -1;   // reverse line tracking needs negative speed
    if (!cfgSmoothCurves) angular = max(-PI/16, min(PI/16, angular)); // restrict steering angle for stanley
    //if (cfgSmoothCurves) angular = max(-PI/8, min(PI/8, angular)); // restrict steering angle for stanley
    //else  angular = max(-PI/16, min(PI/16, angular));
  }
  // check some pre-conditions that can make linear+angular speed zero
  if (fixTimeout != 0){
    if (millis() > lastFixTime + fixTimeout * 1000.0){
      // stop on fix solution timeout (fixme: optionally: turn on place if fix-timeout)
      linear = 0;
      angular = 0;
      mow = false; 
      stateSensor = SENS_GPS_FIX_TIMEOUT;
      //angular = 0.2;
    } else {
      if (stateSensor == SENS_GPS_FIX_TIMEOUT) stateSensor = SENS_NONE; // clear fix timeout
    }       
  }     
  
  if ((gps.solution == UBLOX::SOL_FIXED) || (gps.solution == UBLOX::SOL_FLOAT)){        
    if (abs(linear) > 0.06) {
      if ((millis() > linearMotionStartTime + 5000) && (stateGroundSpeed < 0.03)){
        // if in linear motion and not enough ground speed => obstacle
        if (GPS_SPEED_DETECTION){
          CONSOLE.println("gps no speed => obstacle!");
          triggerObstacle();
          return;
        }
      }
    }  
  } else {
    // no gps solution
    if (REQUIRE_VALID_GPS){
      if (!maps.isUndocking()) { 
        //CONSOLE.println("no gps solution!");
        stateSensor = SENS_GPS_INVALID;
        //setOperation(OP_ERROR);
        //buzzer.sound(SND_STUCK, true);          
        linear = 0;
        angular = 0;      
        mow = false;
      } 
    }
  }
   
  if (mow)  {  // wait until mowing motor is running
    if (millis() < motor.motorMowSpinUpTime + 5000){
      if (!buzzer.isPlaying()) buzzer.sound(SND_WARNING, true);
      linear = 0;
      angular = 0;   
    }
  }

  if (abs(linear) < 0.01){
    resetLinearMotionMeasurement();
  }
  if (angleToTargetFits != langleToTargetFits) {
      //CONSOLE.print("angleToTargetFits: ");
      //CONSOLE.print(angleToTargetFits);
      //CONSOLE.print(" trackerDiffDelta: ");
      //CONSOLE.println(trackerDiffDelta);
      langleToTargetFits = angleToTargetFits;
  }

  //HB moved down: motor.setLinearAngularSpeed(linear, angular);      
  // if (detectLift()) mow = false; // in any case, turn off mower motor if lifted 
  motor.setMowState(mow);
   
  if (targetReached)
  {
     CONSOLE.println(F(" Target reached!"));
     linear = 0;
     angular = 0;
     if (maps.isObstacleMowPoint() && maps.obstacleTargetReached) 
     {
        //HB motorDriver.reverseDrive = true;
        maps.obstacleTargetReached = false;
     }
     //HB else motorDriver.reverseDrive = false;
     rotateLeft = false;
     rotateRight = false;
     if (maps.wayMode == WAY_MOW){
       maps.clearObstacles(); // clear obstacles if target reached
     }
     bool straight = maps.nextPointIsStraight();
     if (!maps.nextPoint(false)){
       // finish        
       if (stateOp == OP_DOCK){
         CONSOLE.println(F("=docking finished!"));
         setOperation(OP_IDLE); 
       } else {
         CONSOLE.println(F("=mowing finished!"));
         if (!finishAndRestart){             
           if (DOCKING_STATION){
             setOperation(OP_DOCK);               
           } else {
             setOperation(OP_IDLE); 
           }
         }                   
       }
     } 
     // else {      
     //   next waypoint          
     //  if (!straight) angleToTargetFits = false;      
     //}
     motorDriver.reverseDrive = maps.isObstacleMowPoint();
  }  
  motor.setLinearAngularSpeed(linear, angular);

}

