#!/usr/bin/python
# Jobs.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Script file containing classes and methods pertaining to the various jobs in the WRF processes

import sys
import os
import os.path
import datetime
import time
from multiprocessing.pool import ThreadPool
from ApplicationSettings import *
from ModelData import *
from Tools import *
from Wait import *

# JobSteps: Class responsible for handling the steps that involve job submission and checkup
class JobSteps:
	aSet = None
	modelParms = None
	startTime = ""
	dataDir = ""
	wrfDir = ""

	def __init__(self, settings, modelParms):
		self.aSet = settings
		self.modelParms = modelParms
		self.dataDir = settings.fetch("datadir") + '/' + settings.fetch("modeldata")
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		#Copy important files to the directory
		Tools.popen(self.aSet, "cp ../run_files/* " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		#Move the generated files to the run directory		
		Tools.popen(self.aSet, "mv namelist.input " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		Tools.popen(self.aSet, "mv geogrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv metgrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv real.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv wrf.job " + self.wrfDir + '/' + self.startTime[0:8])
	
	def run_geogrid(self):
		#
		return None
	
	def run_ungrib(self):	
		#ungrib.exe needs to run in the data directory
		Tools.popen(self.aSet, "cp ../vtables/Vtable." + self.aSet.fetch("modeldata") + "* " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv namelist.wps* " + self.wrfDir + '/' + self.startTime[0:8])
		mParms = self.modelParms.fetch()
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			with open("ungrib.csh", 'w') as target_file:
				target_file.write("module add " + self.aSet.fetch("wrfmodule") + '\n')
				target_file.write("cd " + self.wrfDir + '/' + self.startTime[0:8] + '\n')
				target_file.write("link_grib.csh " + self.dataDir + '/' + self.startTime + '/' + '\n')
				i = 0
				for ext in mParms["FileExtentions"]:
					target_file.write("cp " + mParms["VTable"][i] + " Vtable" + '\n')
					target_file.write("cp namelist.wps." + ext + " namelist.wps" + '\n')
					target_file.write("ungrib.exe" + '\n')
					i += 1
			Tools.popen(self.aSet, "chmod +x ungrib.csh")
			Tools.popen(self.aSet, "./ungrib.csh")
		
	def run_metgrid(self):
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):	
			Tools.popen(self.aSet, "qsub metgrid.job")
			if(self.aSet.fetch("debugmode") == '1'):
				print("Debug mode is active, skipping")
				return True
			else:
				#Submit a wait condition for the file to appear
				try:
					firstWait = [{"waitCommand": "(ls metgrid.log* && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
					wait1 = Wait.Wait(firstWait, timeDelay = 25)
					wait1.hold()
				except Wait.TimeExpiredException:
					sys.exit("metgrid.exe job not completed, abort.")
				#Now wait for the output file to be completed
				try:
					secondWait = [{"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "Successful completion of program metgrid.exe", "retCode": 1},
								  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "fatal", "retCode": 2},
								  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "runtime", "retCode": 2},
								  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "error", "retCode": 2},]
					wait2 = Wait.Wait(secondWait, timeDelay = 25)
					wRC = wait2.hold()
					if wRC == 1:
						return True
					elif wRC == 2:
						return False
				except Wait.TimeExpiredException:
					sys.exit("metgrid.exe job not completed, abort.")
		print("run_metgrid(): Failed to enter run directory")
		return False
		
	def run_real(self):
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			Tools.popen(self.aSet, "qsub real.job")
			if(self.aSet.fetch("debugmode") == '1'):
				print("Debug mode is active, skipping")
				return True
			else:			
				#Submit a wait condition for the file to appear
				try:
					firstWait = [{"waitCommand": "(ls output/rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
					wait1 = Wait.Wait(firstWait, timeDelay = 25)
					wait1.hold()			
				except Wait.TimeExpiredException:
					sys.exit("real.exe job not completed, abort.")
				#Now wait for the output file to be completed
				try:
					secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS", "retCode": 1},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
					wait2 = Wait.Wait(secondWait, timeDelay = 60)
					wRC = wait2.hold()
					if wRC == 2:
						return False
					else:
						#Validate the presense of the two files.
						file1 = os.popen("(ls output/wrfinput_d01 && echo \"yes\") || echo \"no\"").read()
						file2 = os.popen("(ls output/wrfbdy_d01 && echo \"yes\") || echo \"no\"").read()
						if("yes" in file1 and "yes" in file2):
							return True
						return False					
				except Wait.TimeExpiredException:
					sys.exit("real.exe job not completed, abort.")		
		print("run_real(): Failed to enter run directory")
		return False			
		
	def run_wrf(self):
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			# Remove the old log files as these are no longer needed
			Tools.popen(self.aSet, "rm output/rsl.out.*")
			Tools.popen(self.aSet, "rm output/rsl.error.*")	
			Tools.popen(self.aSet, "qsub wrf.job")
			if(self.aSet.fetch("debugmode") == '1'):
				print("Debug mode is active, skipping")
				return True
			else:			
				#Submit a wait condition for the file to appear
				try:
					firstWait = [{"waitCommand": "(ls output/rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
					wait1 = Wait.Wait(firstWait, timeDelay = 25)
					wait1.hold()			
				except Wait.TimeExpiredException:
					sys.exit("wrf.exe job not completed, abort.")
				#Now wait for the output file to be completed (Note: Allow 7 days from the output file first appearing to run)
				#Now wait for the output file to be completed
				try:
					secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS COMPLETE WRF", "retCode": 1},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
								  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
					# Note: I have the script checking the files once every three minutes so we don't stack five calls rapidly, this can be modified later if needed.
					wait2 = Wait.Wait(secondWait, timeDelay = 180)
					wRC = wait2.hold()
					if wRC == 2:
						return False
					else:
						return True				
				except Wait.TimeExpiredException:
					sys.exit("wrf.exe job not completed, abort.")				
		print("run_wrf(): Failed to enter run directory")
		return False			

class Postprocessing_Steps:
	aSet = None
	modelParms = None
	startTime = ""
	wrfDir = ""

	def __init__(self, settings, modelParms):
		self.aSet = settings
		self.modelParms = modelParms
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		
		self.prepare_postprocessing()
		
	def prepare_postprocessing(self):
		if(self.aSet.fetch("post_run_unipost") == '1'):
			pass