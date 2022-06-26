import version

guiMessage = version.versionString

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   if msg != "": print("[GuiMessage] " + guiMessage)
