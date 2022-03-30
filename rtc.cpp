#include <Wire.h>
#include <SD.h>
#include "rtc.h"

// I²C Address for the RTC module
#define DS1307_ADDRESS  0x68
#define AT24C32_ADDRESS 0x50


/**
 * Converts a decimal (Base-10) integer to BCD (Binary-coded decimal)
 */
static int decToBcd(int value)
{
   return ((value/10*16) + (value%10));
}

/**
 * Converts a BCD (Binary-coded decimal) to decimal (Base-10) integer
 */
static int bcdToDec(int value)
{
   return ((value/16*10) + (value%16));
}

/**
 * Sets date/time of the RTC module via the serial monitor
 */
void SetDateTime(DateTime& dateTime)
{
   Wire.beginTransmission(DS1307_ADDRESS);
   Wire.write(byte(0));
   Wire.write(decToBcd(dateTime.second));
   Wire.write(decToBcd(dateTime.minute));
   Wire.write(decToBcd(dateTime.hour));
   Wire.write(decToBcd(dateTime.weekday));
   Wire.write(decToBcd(dateTime.monthday));
   Wire.write(decToBcd(dateTime.month));
   Wire.write(decToBcd(dateTime.year));
   Wire.write(byte(0));
   Wire.endTransmission();
}


/**
 * Read the current date/time from the RTC module
 */
void GetDateTime(DateTime& dateTime)
{
   Wire.beginTransmission(DS1307_ADDRESS);
   Wire.write(0x00);
   Wire.endTransmission();
   Wire.requestFrom(DS1307_ADDRESS, 7);
 
   dateTime.second = bcdToDec(Wire.read());
   dateTime.minute = bcdToDec(Wire.read());
   dateTime.hour = bcdToDec(Wire.read() & 0b111111);
   dateTime.weekday = bcdToDec(Wire.read());
   dateTime.monthday = bcdToDec(Wire.read());
   dateTime.month = bcdToDec(Wire.read());
   dateTime.year = bcdToDec(Wire.read());
}

String DateTime2String(DateTime& dateTime)
{
   char data[20] = "";
   sprintf(data, "20%02d-%02d-%02d %02d:%02d:%02d", 
      dateTime.year, 
      dateTime.month, 
      dateTime.monthday, 
      dateTime.hour, 
      dateTime.minute, 
      dateTime.second);
   return (String) data;
}


//bb add to read byte into the Tiny RTC memory
byte ReadAT24C32(unsigned int address) 
{
   byte b = 0;
   int r = 0;
   Wire.beginTransmission(AT24C32_ADDRESS);
   if (Wire.endTransmission() == 0) 
   {
      Wire.beginTransmission(AT24C32_ADDRESS);
      Wire.write(address >> 8);
      Wire.write(address & 0xFF);
      if (Wire.endTransmission() == 0) 
      {
         Wire.requestFrom(AT24C32_ADDRESS, 1);
         while (Wire.available() > 0 && r < 1) 
         {
            b = (byte)Wire.read();
            r++;
         }
      }
   }
   return b;
}

//bb add to write byte into the Tiny RTC memory
//bb1
void WriteAT24C32(unsigned int address,byte data) 
{
   //unsigned int address = 1021;
   Wire.beginTransmission(AT24C32_ADDRESS);
   if (Wire.endTransmission() == 0) 
   {
      Wire.beginTransmission(AT24C32_ADDRESS);
      Wire.write(address >> 8);
      Wire.write(address & 0xFF);
      Wire.write(data);
      Wire.endTransmission();
      delay(5);
   }
}

// after your rtc is set up and working you code just needs:

static void SdCardDateTime(uint16_t* date, uint16_t* time)
{
   DateTime now;

   GetDateTime(now);

   // return date using FAT_DATE macro to format fields
   *date = FAT_DATE(2000+now.year, now.month, now.monthday);
 
   // return time using FAT_TIME macro to format fields
   *time = FAT_TIME(now.hour, now.minute, now.second);
}

void SdCardDateTimeInit()
{
   SdFile::dateTimeCallback(SdCardDateTime);
}


void GetTimeStamp(char *buf)
{
   static uint32_t timestampOffset_sec;
   static bool firstFlag = true;
   if (firstFlag)
   {
      firstFlag = false;
      DateTime now;
      GetDateTime(now);
      timestampOffset_sec = now.second + (now.minute + now.hour * 60) * 60 - millis()/1000;
   }

   unsigned long totalsecs = millis()/1000 + timestampOffset_sec;
   unsigned long totalmins = totalsecs/60;
   unsigned long totalhours = totalmins/60;
   unsigned long hour = totalhours % 24;
   unsigned long min = totalmins % 60;
   unsigned long sec = totalsecs % 60;
   sprintf(buf, ":%02d:%02d:%02d ", hour, min, sec);
}