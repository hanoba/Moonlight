guiMessage=""

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   print("[GuiMessage] " + guiMessage)
