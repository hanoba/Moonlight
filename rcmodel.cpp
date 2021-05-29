// Ardumower Sunray 


#include "config.h"
#include "rcmodel.h"
#include "robot.h"


volatile unsigned long PPM_start_lin = 0;
volatile unsigned long PPM_end_lin = 0;                
volatile unsigned long PPM_start_ang = 0;
volatile unsigned long PPM_end_ang = 0 ;        
      

void get_lin_PPM()                                                        // Interrupt Service Routine
{
  if (digitalRead(pinRemoteMow)==HIGH) PPM_start_lin = micros();  
  else                                   PPM_end_lin = micros();    
}

void get_ang_PPM()                                                        // Interrupt Service Routine
{
  if (digitalRead(pinRemoteSteer)==HIGH) PPM_start_ang = micros();  
  else                                   PPM_end_ang = micros();  
}

void RCModel::begin(){  
  lin_PPM = 0;                                            
  linearPPM = 0;                                         
  ang_PPM = 0;                                            
  angularPPM = 0;                                         
  buttontimer = 0;                                          
  RC_Mode = false; 
  nextControlTime = 0;
  // R/C
  pinMode(pinRemoteSteer, INPUT);
  pinMode(pinRemoteMow, INPUT); 
#ifdef RC_DEBUG
  nextOutputTime = millis() + 1000;
#endif
  if (RCMODEL_ENABLE){
    //attachInterrupt(digitalPinToInterrupt(pinRemoteMow), get_lin_PPM, CHANGE);// Interrupt aktivieren
    //attachInterrupt(digitalPinToInterrupt(pinRemoteSteer), get_ang_PPM, CHANGE);// Interrupt aktivieren 
  }
} 

void RCModel::run(){
  unsigned long t = millis();
  if (!RCMODEL_ENABLE) return;
  if (t < nextControlTime) return;
  nextControlTime = t + 100;                                       // save CPU resources by running at 10 Hz
  
  if ((digitalRead(pinButton)== LOW) && (buttontimer <= 30)) {               // Taster abfragen
    buttontimer ++;                                                       // Timer 3sec.
    if (buttontimer == 30)    {                                        // 3sec. erreicht
      RC_Mode = !RC_Mode;                                                   // R/C-Mode toggle
      if (RC_Mode)  {                                                       // R/C-Mode ist aktiv
        buzzer.sound(SND_ERROR, true);                                      // 3x Piep für R/C aktiv        
        attachInterrupt(digitalPinToInterrupt(pinRemoteMow), get_lin_PPM, CHANGE);// Interrupt aktivieren
        attachInterrupt(digitalPinToInterrupt(pinRemoteSteer), get_ang_PPM, CHANGE);// Interrupt aktivieren 
      }
      if (!RC_Mode) {                                                       // R/C-Mode inaktiv
        buzzer.sound(SND_WARNING, true);                          // 2x Piiiiiiiep für R/C aus
        motor.setLinearAngularSpeed(0, 0);                                 
        detachInterrupt(digitalPinToInterrupt(pinRemoteMow));             // Interrupt deaktivieren
        detachInterrupt(digitalPinToInterrupt(pinRemoteSteer));             // Interrupt deaktivieren
      }
    }
  }
  if (digitalRead(pinButton)== HIGH) buttontimer = 0;                        // Taste los gelasseb = freigeben
  
  if (RC_Mode)    {       
    lin_PPM = 0;
    if (PPM_start_lin < PPM_end_lin) lin_PPM = PPM_end_lin - PPM_start_lin; 
    if (lin_PPM < 2000 && lin_PPM > 1000)   {                               // Wert innerhalb 1100 bis 1900µsec
      float value_l = (lin_PPM - 1500) / 1500;                                // PPM auf Bereich +0.30 bis -0.30
      if ((value_l < 0.05) && (value_l > -0.05)) value_l = 0;                 // NullLage vergrössern         
      linearPPM = value_l;                                                    // Weitergabe an Debug
    }

    ang_PPM = 0;
    if (PPM_start_ang < PPM_end_ang) ang_PPM = PPM_end_ang - PPM_start_ang; 
    if (ang_PPM < 2000 && ang_PPM > 1000)   {                               // Wert innerhalb 1100 bis 1900µsec
      float value_a = (ang_PPM - 1500) / 950;                                 // PPM auf Bereich +0.50 bis -0.50
      if ((value_a < 0.05) && (value_a > -0.05)) value_a = 0;                 // NullLage vergrössern         
      angularPPM = value_a;                                                   // Weitergabe an Debug
    }

#ifdef RC_DEBUG
    if (t >= nextOutputTime) {
      nextOutputTime = t + 1000;

      CONSOLE.print("RC: linearPPM= ");
      CONSOLE.print(linearPPM);
      CONSOLE.print("  angularPPM= ");
      CONSOLE.println(angularPPM);
    }
#endif
    motor.setLinearAngularSpeed(linearPPM, angularPPM, false);                     // R/C Signale an Motor leiten
  }
}
