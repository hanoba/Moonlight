
struct DateTime
{
   byte second;
   byte minute;
   byte hour;
   byte weekday;
   byte monthday;
   byte month;
   byte year;
};

void SetDateTime(DateTime& dateTime);
void GetDateTime(DateTime& dateTime);
String DateTime2String(DateTime& dateTime);
void SdCardDateTimeInit();

void WriteAT24C32(unsigned int address, byte data);
byte ReadAT24C32(unsigned int address);

void GetTimeStamp(char *buf);