import os

def check_ping(hostname):
    response = os.system("ping -n 1 " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"
    return pingstatus
    
#print(check_ping("192.168.178.71"))
#print(check_ping("192.168.20.100"))

if os.environ['COMPUTERNAME']=="HBA004":
   print("192.168.178.71")
else:
   print("192.168.20.100")
