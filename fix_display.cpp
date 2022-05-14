/*
Arduino Servo Test sketch
*/
#include "config.h"
#include "fix_display.h"

void FixDisplay::begin()
{
   servo.attach(pinFixServo); // servo on digital pin
}

void FixDisplay::run()
{
    if (millis() < nextDisplayTime) return;
    nextDisplayTime = millis() + 1000;

   servo.write(state); // change Servo by 45 degrees
   state += 45;
   if (state > 180) state=0;
}