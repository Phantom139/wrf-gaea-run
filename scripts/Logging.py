#!/usr/bin/python
# Logging.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# File for managing logs

import sys
import os
import os.path
import datetime
import Tools
		
#loggedPrint: A class that prints output to console and then writes it to a log file
@Singleton
class loggedPrint:
	f = None
	filePath = None
	
	def __init__(self):
		curTime = datetime.date.today().strftime("%B%d%Y-%H%M%S")
		curDir = os.path.dirname(os.path.abspath(__file__)) 	
		logName = "wrf_gaea_run_" + str(curTime) + ".log"	
		logFile = curDir + '/' + logName
		self.filePath = logFile
	
	def write(self, out):
		self.f = open(self.filePath, "a")
		self.f.write(out + '\n')
		self.f.close()
		print(out)
	
	def close(self):
		self.f.close()