#!/usr/bin/python
# Tools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains micro classes and methods used to help the program

import sys
import os
import os.path
import ApplicationSettings

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
		
#popen: A wrapped call to the os.popen method to test for the debugging flag.
class popen:
	def __init__(self, settings, command, returnOutput = False):
		self.aSet = settings
		self.command = command
		self.returnOutput = returnOutput
		
	def __enter__(self):
		if(self.aSet.fetch("debugmode") == '1'):
			print("D: " + self.command)
		else:
			command = os.popen(self.command)
			stored = command.read()
			self.stored = None
			if(self.returnOutput == True):
				self.stored = stored
			
	def __exit(self, etype, value, traceback):
		return isinstance(value, TypeError)