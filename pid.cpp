/*  
   How to find out P,I,D:
    1. Increase P until system starts to oscillate
    2. Set I =0.6 * P and D = 0.125 * P 
   
*/

#include "pid.h"


PID::PID()
{
}
    
PID::PID(float Kp, float Ki, float Kd){
  this->Kp = Kp;
  this->Ki = Ki;
  this->Kd = Kd;
}


void PID::reset(void) {
  this->eold = 0;
  this->esum = 0;
}

float PID::compute() {
  unsigned long now = millis();
  Ta = ((float)(now - lastControlTime)) / 1000.0;
  //printf("%.3f\n", Ta);
  lastControlTime = now;
  if (Ta > 1.0) Ta = 1.0;   // should only happen for the very first call

  // compute error
  float e = (w - x);
  // integrate error
  esum += e;
  // anti wind-up
  if (esum < -max_output)  esum = -max_output;
  if (esum > max_output)  esum = max_output;
  y = Kp * e
      + Ki * Ta * esum
      + Kd/Ta * (e - eold);
  eold = e;
  // restrict output to min/max
  if (y > y_max) y = y_max;
  if (y < y_min) y = y_min;

  return y;
}


// ---------------------------------

VelocityPID::VelocityPID()
{
}
    
VelocityPID::VelocityPID(float Kp, float Ki, float Kd){
  this->Kp = Kp;
  this->Ki = Ki;
  this->Kd = Kd;
}


float VelocityPID::compute()
{   
  unsigned long now = micros();
  Ta = ((now - lastControlTime) / 1000000.0);
  lastControlTime = now;
  if (Ta > 1.0) Ta = 1.0;   // should only happen for the very first call

  // compute error
  float e = (w - x);

  // compute max/min output
  if (w < 0) { y_min = -max_output; y_max = 0; }
  if (w > 0) { y_min = 0; y_max = max_output; }     

  y = yold
      + Kp * (e - eold1)
      + Ki * Ta * e
      + Kd/Ta * (e - 2* eold1 + eold2);
     
  // restrict output to min/max 
  if (y > y_max) y = y_max;
  if (y < y_min) y = y_min; 

  // save variable for next time
  eold2 = eold1;
  eold1 = e;
  yold = y ;  
  
  return y;
}

