// --------- serial monitor output (CONSOLE) ------------------------
// which Arduino Due USB port do you want to your for serial monitor output (CONSOLE)?
// Arduino Due native USB port  => choose SerialUSB
// Arduino Due programming port => choose Serial
//
// This include file is used in
//  - config.h
//  - sdserial.h
//  - udpserial.h

#if defined(_SAM3XA_)
  //#define CONSOLE SerialUSB   // Arduino Due: do not change (used for Due native USB serial console)
  #define CONSOLE Serial
#else
  #define CONSOLE Serial      // Adafruit Grand Central M4
#endif