#!/usr/bin/python
# Logging.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# File for managing logs

import sys
import os
import os.path
		
#loggedPrint: A class that prints output to console and then writes it to a log file
class loggedPrint:
	f = None
	filePath = None
	
	def __init__(self, logFile):
		self.filePath = logFile
	
	def write(self, out):
		self.f = open(self.filePath, "a")
		self.f.write(out + '\n')
		self.f.close()
		print(out)
	
	def close(self):
		self.f.close()