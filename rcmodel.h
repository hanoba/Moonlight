// Ardumower Sunray 

// R/C model control

// use PCB pin 'mow' for R/C model control speed and PCB pin 'steering' for R/C model control steering, 
// also connect 5v and GND and activate model R/C control via PCB P20 start button for 3 sec.



#ifndef RCMODEL_H
#define RCMODEL_H



class RCModel 
{
    public:
      void begin();      
      void run();      
      void DoRemoteControl(String cmd);
    private:
      bool dataFlag = false;
      bool lastDataFlag = false;
      unsigned nextRcOutputTime = 0;
      int iLinear;
      int iAngular;
};


#endif

