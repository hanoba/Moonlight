import version
from udp import WriteLog

guiMessage = version.versionString

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   if msg != "": WriteLog("[GuiMessage] " + guiMessage)
