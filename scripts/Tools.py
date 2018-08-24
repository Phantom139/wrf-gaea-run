#!/usr/bin/python
# Tools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains micro classes and methods used to help the program

import sys
import os
import os.path
import ApplicationSettings
import subprocess

#CD: Current Directory management, see https://stackoverflow.com/a/13197763/7537290 for implementation. This is used to maintain the overall OS CWD while allowing embedded changes.
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
		
#popen: A wrapped call to the subprocess.popen method to test for the debugging flag.
class popen:
	def __init__(self, settings, command):
		if(settings.fetch("debugmode") == '1'):
			print("D: " + command)
		else:
			runCmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			runCmd.wait()
			self.stored = runCmd.stdout
			
	def fetch(self):
		return self.stored
		
#loggedPrint: A class that prints output to console and then writes it to a log file
class loggedPrint:
	def __init__(self, logFile):
		self.f = open(logFile, "w")
	
	def write(self, out):
		self.f.write(out + '\n')
		print(out)
	
	def close(self):
		self.f.close()