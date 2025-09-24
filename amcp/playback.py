import pygame
import sys
from enum import Enum

class PlaybackState(Enum):
    Idle = 0
    NextMsg = 1
    PrevMsg = 2
    NextPeriodicLogMsg = 3
    PrevPeriodicLogMsg = 4
    NextErrorMsg = 5
    PrevErrorMsg = 6
    NextLoadingMapMsg = 7
    PrevLoadingMapMsg = 8
    NextStateChange = 9
    PrevStateChange = 10
    FirstMsg = 11
    LastMsg = 12
    Off = 13


# Define a class
class Playback:
    # Constructor (initializer)
    def __init__(self):
        argc = len(sys.argv)
        
        if argc != 2:
            self.state = PlaybackState.Off
            return

        fileName = sys.argv[1] 
        self.lines = []
        with open(fileName, "r", encoding="latin-1") as file:
            for line in file:
                # fix problem with blanks in satellite display. Convert "0 /30" into "0/30" and "0 / 0" to "0/0"
                line = line.replace(" /", "/")
                line = line.replace("/ ", "/")

                # remove "[am] " prefix used in amcp log files
                line = line.replace("[am] ", "")
                
                # store only lines from mower (skip other lines)
                if line[9] != "[": self.lines.append(line[9:])
                    
        self.lastLineNum = len(self.lines) - 1
        print(f"Playback mode is active! {self.lastLineNum+1} lines read from logfile {fileName}")
        self.PrintHelpText()
        self.lineNum = -1   # lineNum indicates the last line read from logfile
        self.state = PlaybackState.Idle
        return

    def PlaybackMode(self):
        return self.state != PlaybackState.Off
        
    def ReadLine(self):
        if self.state == PlaybackState.Off: 
            return ""

        if self.state == PlaybackState.Idle:
            return ""
            
        elif self.state == PlaybackState.NextMsg:
            self.state = PlaybackState.Idle
            if self.lineNum >= self.lastLineNum: 
                print("Last message reached")
                return "" 
            self.lineNum += 1
            return self.lines[self.lineNum]
            
        elif self.state == PlaybackState.PrevMsg:
            self.state = PlaybackState.Idle
            if self.lineNum <= 0: 
                print("First message reached")
                return "" 
            self.lineNum -= 1
            return self.lines[self.lineNum]
            
        elif self.state == PlaybackState.NextPeriodicLogMsg:
            if self.lineNum >= self.lastLineNum: 
                self.state = PlaybackState.Idle
                print("Last message reached")
                return "" 
            self.lineNum += 1
            if self.lines[self.lineNum][0]==":":
                self.state = PlaybackState.Idle
            return self.lines[self.lineNum]

        elif self.state == PlaybackState.PrevPeriodicLogMsg:
            if self.lineNum <= 0: 
                self.state = PlaybackState.Idle
                print("First message reached")
                return "" 
            self.lineNum -= 1
            if self.lines[self.lineNum][0]==":": 
                self.state = PlaybackState.Idle
            return self.lines[self.lineNum]

        elif self.state == PlaybackState.NextErrorMsg:
            if self.lineNum >= self.lastLineNum: 
                self.state = PlaybackState.Idle
                print("Last message reached")
                return "" 
            self.lineNum += 1
            if "error" in self.lines[self.lineNum].lower() or "=BumperFreeWheel" in self.lines[self.lineNum]:      
                self.state = PlaybackState.Idle
            return self.lines[self.lineNum]
        
        elif self.state == PlaybackState.PrevErrorMsg:
            if self.lineNum <= 0: 
                self.state = PlaybackState.Idle
                print("First message reached")
                return "" 
            self.lineNum -= 1
            if "error" in self.lines[self.lineNum].lower() or "=BumperFreeWheel" in self.lines[self.lineNum]:      
                self.state = PlaybackState.Idle
            return self.lines[self.lineNum]

        elif self.state == PlaybackState.NextLoadingMapMsg:
            if self.lineNum >= self.lastLineNum: 
                self.state = PlaybackState.Idle
                print("Last message reached")
                return "" 
            self.lineNum += 1
            for i in range(self.lineNum + 1, self.lastLineNum):
                if "loading map" in self.lines[i]:      
                    self.lineNum = i
                    break
            self.state = PlaybackState.Idle
            return self.lines[self.lineNum]
        
        elif self.state == PlaybackState.PrevLoadingMapMsg:
            self.state = PlaybackState.Idle
            if self.lineNum <= 0: 
                print("First message reached")
                return "" 
            i = self.lineNum - 1
            while i >= 0:
                if "loading map" in self.lines[i]:      
                    self.lineNum = i
                    return self.lines[self.lineNum]
                i -= 1
            self.lineNum = 0
            return self.lines[self.lineNum]

        elif self.state == PlaybackState.NextStateChange:
            if self.lineNum >= self.lastLineNum: 
                self.state = PlaybackState.Idle
                print("Last message reached")
                return "" 
            
            oldState = ""
            for i in range(self.lineNum, self.lastLineNum):
                if self.lines[i][0] != ":":
                    continue
                elif oldState == "":
                    oldState = self.lines[i][15:21]
                elif self.lines[i][15:21] != oldState:      
                    self.lineNum = i
                    break
            self.state = PlaybackState.Idle
            return self.lines[self.lineNum]
        
        elif self.state == PlaybackState.PrevStateChange:
            self.state = PlaybackState.Idle
            if self.lineNum <= 0: 
                print("First message reached")
                return "" 
            i = self.lineNum
            oldState = ""
            while i >= 0:
                if self.lines[i][0] == ":":
                    if oldState == "":
                        oldState = self.lines[i][15:21]
                    elif self.lines[i][15:21] != oldState:      
                        self.lineNum = i
                        return self.lines[self.lineNum]
                i -= 1
            self.lineNum = 0
            return self.lines[self.lineNum]
        
        elif self.state == PlaybackState.FirstMsg:
            self.state = PlaybackState.Idle
            self.lineNum = 0
            return self.lines[self.lineNum]
        
        elif self.state == PlaybackState.LastMsg:
            self.state = PlaybackState.Idle
            self.lineNum = self.lastLineNum
            return self.lines[self.lineNum]
            
        return ""
        
    def HandleKey(self, key):
        if not self.PlaybackMode(): return False
        elif key == pygame.K_F1:   self.state = PlaybackState.NextMsg
        elif key == pygame.K_F2:   self.state = PlaybackState.PrevMsg
        elif key == pygame.K_F3:   self.state = PlaybackState.NextPeriodicLogMsg
        elif key == pygame.K_F4:   self.state = PlaybackState.PrevPeriodicLogMsg
        elif key == pygame.K_F5:   self.state = PlaybackState.NextErrorMsg
        elif key == pygame.K_F6:   self.state = PlaybackState.PrevErrorMsg
        elif key == pygame.K_F7:   self.state = PlaybackState.NextLoadingMapMsg
        elif key == pygame.K_F8:   self.state = PlaybackState.PrevLoadingMapMsg
        elif key == pygame.K_F9:   self.state = PlaybackState.NextStateChange
        elif key == pygame.K_F10:  self.state = PlaybackState.PrevStateChange
        elif key == pygame.K_HOME: self.state = PlaybackState.FirstMsg
        elif key == pygame.K_END:  self.state = PlaybackState.LastMsg
        elif key == pygame.K_h:    self.PrintHelpText()
        else: return False
        return True

    def PrintHelpText(self):
        print("\n Playback Commands")
        print("F1:   Step to next message")
        print("F2:   Step to previous message")
        print("F3:   Step to next periodic log message")
        print("F4:   Step to previous periodic log message")
        print("F5:   Step to next error message")
        print("F6:   Step to previous error message")
        print("F7:   Goto to next loading map message")
        print("F8:   Goto to previous loading map message")
        print("F9:   Goto to next state change")
        print("F10:  Goto to previous state change")
        print("HOME: Goto to first message")
        print("END:  Goto to last message")
        print("h:    Print this help text")
        print("")
    
# Create playback object       
playback = Playback()

def PlaybackMode():
    return playback.PlaybackMode()
    
def PlaybackHandleKey(key):
    return playback.HandleKey(key)
    
def PlaybackReadLine():
    return playback.ReadLine()
    