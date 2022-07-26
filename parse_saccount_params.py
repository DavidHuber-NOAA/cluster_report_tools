#!/usr/bin/env python3

import os
import platform
import re

hostname = (platform.node())
if "Orion" not in hostname:
   stream = os.popen('saccount_params -L -a nesdis-rdo1,nesdis-rdo2')
else:
   stream = os.popen('saccount_params -L -a nesdis-rdo1,nesdis-rdo2,dras-aida')

output = stream.readlines()
lines = [line.strip() for line in output]

projectInfo=[]
for line in lines:
   if "Project:" in line:
      project=line.split(": ")[1]
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
            folder = "/work2 "
         else:
            folder = "/work "
      else:
         #For other machines, we have only one allocation per project
         folder = ""

      projectInfo.append((project, 'fs: ' + fairShare, 'alloc: ' + allocUsed + '/' + allocGiven,
         'usage: ' + folder + usage + '/' + quota))

print("Project information on " + hostname + ":")
for proj in projectInfo:
   print(proj)
