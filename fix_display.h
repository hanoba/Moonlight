#pragma once
#include <Servo.h>

class FixDisplay
{
public:
   void begin();            
   void run();	  
private:
   Servo servo; 
   unsigned long nextDisplayTime = 0;
   int state = 0;
};