guiMessage=""

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   if msg != "": print("[GuiMessage] " + guiMessage)
