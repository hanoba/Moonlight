#include "LineTracker.h"
#include "robot.h"
//#include "StateEstimator.h"
#include "helper.h"
#include "pid.h"


//PID pidLine(0.2, 0.01, 0); // not used
//PID pidAngle(2, 0.1, 0);  // not used
Polygon circle(8);


float setSpeed = 0.1; // linear speed (m/s)
bool rotateLeft = false;
bool rotateRight = false;
bool angleToTargetFits = false;
bool targetReached = false;
float trackerDiffDelta = 0;
bool stateKidnapped = false;
bool printmotoroverload = false;
bool trackerDiffDelta_positive = false;

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
void trackLine(){  
  Point target = maps.targetPoint;
  Point lastTarget = maps.lastTargetPoint;
  float linear = 1.0;  
  bool mow = true;
  if (stateOp == OP_DOCK) mow = false;
  float angular = 0;      
  float targetDelta = pointsAngle(stateX, stateY, target.x(), target.y());      
  if (maps.trackReverse) targetDelta = scalePI(targetDelta + PI);
  targetDelta = scalePIangles(targetDelta, stateDelta);
  float diffDelta = distancePI(stateDelta, targetDelta);                         
  float lateralError = distanceLineInfinite(stateX, stateY, lastTarget.x(), lastTarget.y(), target.x(), target.y());        
  float distToPath = distanceLine(stateX, stateY, lastTarget.x(), lastTarget.y(), target.x(), target.y());        
  float targetDist = maps.distanceToTargetPoint(stateX, stateY);
  
  float lastTargetDist = maps.distanceToLastTargetPoint(stateX, stateY);  
  if (SMOOTH_CURVES)
    targetReached = (targetDist < 0.2);    
  else 
    targetReached = (targetDist < 0.05);    
  
  
  if ( (motor.motorLeftOverload) || (motor.motorRightOverload) || (motor.motorMowOverload) ){
    linear = 0.1;  
  }   
  
  if (KIDNAP_DETECT){
    if (fabs(distToPath) > 1.0){ // actually, this should not happen (except something strange is going on...)
      CONSOLE.println("kidnapped!");
      stateSensor = SENS_KIDNAPPED;
      setOperation(OP_ERROR);
      buzzer.sound(SND_ERROR, true);        
      return;
   }
  }
          
  // allow rotations only near last or next waypoint or if too far away from path
  if ( (targetDist < 0.5) || (lastTargetDist < 0.5) ||  (fabs(distToPath) > 0.5) ) {
    if (SMOOTH_CURVES)
      angleToTargetFits = (fabs(diffDelta)/PI*180.0 < 120);          
    else     
      angleToTargetFits = (fabs(diffDelta)/PI*180.0 < 20);   
  } else angleToTargetFits = true;

               
  if (!angleToTargetFits){
    // angular control (if angle to far away, rotate to next waypoint)
    linear = 0;
    angular = 0.5;               
    if ((!rotateLeft) && (!rotateRight)){ // decide for one rotation direction (and keep it)
      if (diffDelta < 0) rotateLeft = true;
        else rotateRight = true;
    }        
    if (rotateLeft) angular *= -1;            
    if (fabs(diffDelta)/PI*180.0 < 90){
      rotateLeft = false;  // reset rotate direction
      rotateRight = false;
    }
  } 
  else {
    // line control (stanley)
    bool straight = maps.nextPointIsStraight();
    if (maps.trackSlow) {
      // planner forces slow tracking (e.g. docking etc)
      linear = 0.1;           
    } else if (     ((setSpeed > 0.2) && (maps.distanceToTargetPoint(stateX, stateY) < 0.5) && (!straight))   // approaching
          || ((linearMotionStartTime != 0) && (millis() < linearMotionStartTime + 3000))                      // leaving  
       ) 
    {
      linear = 0.1; // reduce speed when approaching/leaving waypoints          
    } 
    else {
      if (gps.solution == UBLOX::SOL_FLOAT)        
         //HB linear = min(setSpeed, 0.1); // reduce speed for float solution
         linear = max(setSpeed/2, 0.2); // reduce speed for float solution
      else
        linear = setSpeed;         // desired speed
      if (sonar.nearObstacle()) linear = 0.1; // slow down near obstacles
      if (upHillFlag) linear = 0.1;   //HB vermeiden, dass Mower kippt bei grossen Steigungen
    }      
    //angular = 3.0 * diffDelta + 3.0 * lateralError;       // correct for path errors 
    float k = STANLEY_CONTROL_K_NORMAL;
    if (maps.trackSlow) k = STANLEY_CONTROL_K_SLOW;   
    angular = diffDelta + atan2(k * lateralError, (0.001 + fabs(motor.linearSpeedSet)));       // correct for path errors           
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
    if (!SMOOTH_CURVES) angular = max(-PI/16, min(PI/16, angular)); // restrict steering angle for stanley
    //if (SMOOTH_CURVES) angular = max(-PI/8, min(PI/8, angular)); // restrict steering angle for stanley
    //else  angular = max(-PI/16, min(PI/16, angular));
  }
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
    if (linear > 0.06) {
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

  motor.setLinearAngularSpeed(linear, angular);      
  motor.setMowState(mow);
   
  if (targetReached){
    if (maps.wayMode == WAY_MOW){
      maps.clearObstacles(); // clear obstacles if target reached
    }
    bool straight = maps.nextPointIsStraight();
    if (!maps.nextPoint(false)){
      // finish        
      if (stateOp == OP_DOCK){
        CONSOLE.println("docking finished!");
        setOperation(OP_IDLE); 
      } else {
        CONSOLE.println("mowing finished!");
        if (!finishAndRestart){             
          if (DOCKING_STATION){
            setOperation(OP_DOCK);               
          } else {
            setOperation(OP_IDLE); 
          }
        }                   
      }
    } else {      
      // next waypoint          
      //if (!straight) angleToTargetFits = false;      
    }
  }  
}

