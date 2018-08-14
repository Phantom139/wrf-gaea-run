#!/usr/bin/python
# Template.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains methods used to modify and save the templated files

from ApplicationSettings import *

# Template_Writer: Class responsible for taking the template files and saving the use files with parameters set
class Template_Writer:
	aSet = None
	
	def __init__(self, settings):
		self.aSet = settings
					
	def generateTemplatedFile(self, inFile, outFile, extraKeys = None):
		outContents = ""
		with open(outFile, 'w') as target_file:
			with open(inFile, 'r') as source_file:
				for line in source_file:
					newLine = line
					newLine = self.aSet.replace(newLine)
					if(extraKeys != None):
						for key, value in extraKeys.items():
							newLine = newLine.replace(key, value)
					newLine += '\n'
					outContents += newLine
			target_file.write(outContents)	