#include <SD.h>
#include "sdserial.h"
#include "file_cmds.h"
#include "config.h"


SDFile root;
const char *SOF_MARK = "$$$SOF$$$";
const char *EOF_MARK = "$$$EOF$$$";

static bool match(char *fileName, String pattern)
{
   int len = pattern.length();

   for (int i = 0; i < len; i++)
   {
      if (pattern[i] == '*') return true;
      if (fileName[i] == 0) return false;
      if (fileName[i] != pattern[i]) return false;
   }
   return true;
}

static void FileSystemCmd_ls(String pattern)
{
   root = SD.open("/");
   root.rewindDirectory();

   while (true)
   {
      SDFile entry = root.openNextFile();
      if (!entry)
      {
         break;
      }
      if (match(entry.name(), pattern))
      {
         CONSOLE.print(entry.name());
         if (!entry.isDirectory())
         {
            CONSOLE.print("\t\t");
            CONSOLE.println(entry.size(), DEC);
         }
         else
         {
            CONSOLE.println("\t\t[DIR]");
         }

      }
      entry.close();
   }

   root.close();
}


static void FileSystemCmd_rm(String pattern)
{
   if (pattern.length() == 0) return;

   root = SD.open("/");
   root.rewindDirectory();

   while (true)
   {
      SDFile entry = root.openNextFile();
      if (!entry)
      {
         break;
      }
      if (match(entry.name(), pattern))
      {
         if (!entry.isDirectory())
         {
            CONSOLE.print(entry.name());
            if (SD.remove(entry.name()))
            {
               CONSOLE.println(" removed");
            }
            else
            {
               CONSOLE.println(" cannot be removed");
            }
         }

      }
      entry.close();
   }

   root.close();
}


static void FileSystemCmd_cat(String fileName)
{
   //const int BUF_SIZE = 100;
   //char buf[BUF_SIZE + 1];

   //SDFile dataFile = SD.open("LOG1048.TXT");
   SDFile dataFile = SD.open(fileName);

   // if the file is available, read it:
   if (dataFile)
   {
      const int LINE_SIZE = 256;
      char line[LINE_SIZE];
      int i = 0;
      while (dataFile.available())
      {
         char ch = dataFile.read();
         //CONSOLE.write(ch);
         if (ch != 10)
         {
            if (ch == 13 || i == LINE_SIZE - 1)
            {
               line[i] = 0;
               CONSOLE.println(line);
               i = 0;
               watchdogReset();
            }
            else
            {
               line[i++] = ch;
            }
         }
      }
      if (i)
      {
         line[i] = 0;
         CONSOLE.print(line);
      }
   }
   else 
   {
      CONSOLE.println("error opening file" + fileName);
   }
   dataFile.close();
}


void FileSystemCmd(String cmd)
{
   udpSerial.DisableLogging();
   CONSOLE.println(SOF_MARK);
   String fileName = cmd.substring(6);
        if (cmd[4] == 'L') FileSystemCmd_ls(fileName);
   else if (cmd[4] == 'C') FileSystemCmd_cat(fileName);
   else if (cmd[4] == 'R') FileSystemCmd_rm(fileName);
   CONSOLE.println(EOF_MARK);
   udpSerial.EnableLogging();
}