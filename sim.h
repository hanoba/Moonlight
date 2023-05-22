#pragma once
class Sim
{
   float posX, posY;    // simulated mower position
   float delta;         // simulated mower direction
   float speed;
   unsigned long nextGpsMsgTime;    // for GPS logging
public:
   float posStep;
   float deltaStep;
   bool activeFlag = false;
   bool homeFlag = true;
   bool SetLinearAngularSpeed(float lin, float ang);
   bool ComputeRobotState();
   bool Obstacle(bool& obstacleFlag);
   bool RobotShouldMove(bool& shouldMoveFlag);
   Sim();
};

extern Sim sim;
#define simulationFlag sim.activeFlag