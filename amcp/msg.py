guiMessage="amcp - Version 1.0, 2022-04-26"

def GetGuiMessage():
   return guiMessage

def PrintGuiMessage(msg):
   global guiMessage
   guiMessage = msg
   if msg != "": print("[GuiMessage] " + guiMessage)
