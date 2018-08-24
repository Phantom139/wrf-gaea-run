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
	def __init__(self, logFile):
		self.f = open(logFile, "w")
	
	def write(self, out):
		self.f.write(out + '\n')
		print(out)
	
	def close(self):
		self.f.close()