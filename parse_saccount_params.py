#!/usr/bin/env python3

import os
import platform
import re
import datetime as dt

def get_wait_time(stream):
   #Average the wait times for each project
   #Calculate wait times in hours
   hours = 0.0
   output = stream.readlines()
   #Trim the first two lines
   output = output[2:]
   n = len(output)
   for line in output:
      if "-" in line:
         wait_time = [line.split("-")[0]]
         wait_time.extend(line.split("-")[1].split(":"))
         hours += float(wait_time[0])*24.0 + float(wait_time[1]) + float(wait_time[2])/60.0 + float(wait_time[3])/3600.0
      else:
         wait_time = line.split(":")
         hours += float(wait_time[0]) + float(wait_time[1])/60.0 + float(wait_time[2])/3600.0

   if(n != 0):
      return ('{0:.4f}'.format(hours / float(n)))
   else:
      return "N/A"

def GetWindfallTime(account,start):
   windfall_cmd = "sacct -a -X -q windfall -o 'CPUTimeRAW' -A " + account + " -S " + start
   stream = os.popen(windfall_cmd)
   hours = 0.0
   for line in stream.readlines()[2:]:
      hours += float(line) / 3600.0

   return hours

hostname = (platform.node())
#Run jobs to calculate usage statistics
start_sacct = (dt.date.today() + dt.timedelta(days=-30)).strftime("%m%d%y")
sacct_cmd = "sacct -X -a -o Reserved -S " + start_sacct + " -A "
accounts = ["nesdis-rdo1", "nesdis-rdo2"]
if "Orion" not in hostname:
   sap_stream = os.popen('saccount_params -L -a nesdis-rdo1,nesdis-rdo2')
else:
   sap_stream = os.popen('saccount_params -L -a nesdis-rdo1,nesdis-rdo2,dras-aida')
   accounts.append("dras-aida")

sa_batch_streams = [os.popen(sacct_cmd + account + " -q batch") for account in accounts]
sa_wind_streams = [os.popen(sacct_cmd + account + " -q windfall") for account in accounts]
sa_all_streams = [os.popen(sacct_cmd + account) for account in accounts]

wind_hours = [GetWindfallTime(account,start_sacct) for account in accounts]

project_wait = []
batch_wait = []
wind_wait = []

for stream in sa_all_streams:
   project_wait.append(get_wait_time(stream))

for stream in sa_batch_streams:
   batch_wait.append(get_wait_time(stream))

for stream in sa_wind_streams:
   wind_wait.append(get_wait_time(stream))

output = sap_stream.readlines()
lines = [line.strip() for line in output]

projectInfo=[]
#Parse the output of saccount_params and also calculate the mean queue time for each project
for line in lines:
   if "Project:" in line:
      project=line.split(": ")[1]
      if project == "nesdis-rdo1":
         ndx = 0
      elif project == "nesdis-rdo2":
         ndx = 1
      elif project == "dras-aida":
         ndx = 2

      wait = '{0:.2f}'.format(float(project_wait[ndx]))
      windq = '{0:.2f}'.format(float(wind_wait[ndx]))
      batchq = '{0:.2f}'.format(float(batch_wait[ndx]))
      wind_use = '{0:.1f}'.format(float(wind_hours[ndx]))

   if "fairshare=" in line.lower():
      (fairShareInfo,allocInfo) = line.split("\t")
      fairShare = re.split('=| ', fairShareInfo)[1]
      (allocUsed, allocGiven) = re.split('=|, ', allocInfo)[1:4:2]
   if "Directory:" in line:
      (dmy, folder, dmy3, usage, unit, dmy5, quota, dmy6, dmy7, files, dmy8, fileQuota)=re.split(' |, |=', line)
      if unit=="KB" or unit=="MB":
         usage = "0"
      else:
         usage = '{0:.1f}'.format(float(usage) / 1000.0)

      quota = '{0:.1f}'.format(float(quota) / 1000.0)

      #If on orion, determine the directory clearly
      if "Orion" in hostname:
         if "work2" in folder:
            folder = "/work2:"
         else:
            folder = "/work:"
      else:
         #For other machines, we have only one allocation per project
         folder = ""

      projectInfo.append((project + ',' + fairShare + ',' + allocUsed + ',' + allocGiven +
         ',' + folder + usage + ',' + quota + "," + wait +
         "," + batchq + "," + windq + "," + wind_use))


print("Project information on " + hostname + ":")
with open("Orion_usage.csv", "w") as f:
   header = "Project,FairShare,CoreHoursUsed,Allocated,DiskUsageUsed,Allocated,MeanQueueTimeAll,Batch,Windfall,WindfallCoreHours"
   print(header)
   f.write(header + "\n")
   for proj in projectInfo:
      print(proj)
      f.write(proj + "\n")
