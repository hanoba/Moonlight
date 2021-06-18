from datetime import datetime

# datetime object containing current date and time
now = datetime.now()
 
print("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("AT+D,%y,%-m,%d,%H,%M,%S,%w")
print("date and time =", dt_string)	