#pragma once
class Sim
{
   float posX, posY;    // simulated mower position
   float posStep;
   float delta;         // simulated mower direction
   float deltaStep;
   float speed;
public:
   bool activeFlag = false;
   bool SetLinearAngularSpeed(float lin, float ang);
   bool ComputeRobotState();
   Sim();
};

extern Sim sim;
#define simulationFlag sim.activeFlag