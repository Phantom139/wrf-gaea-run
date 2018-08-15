#!/usr/bin/python
# Jobs.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Script file containing classes and methods pertaining to the various jobs in the WRF processes

import sys
import os
import os.path
import datetime
import glob
import time
from multiprocessing.pool import ThreadPool
import ApplicationSettings
import ModelData
import Tools
import Wait
import Template

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
		self.postDir = self.wrfDir + '/' + self.startTime[0:8] + "/postprd/"
		
	# This method is mainly used for UPP post-processing as it requires some links to be established prior to running a Unipost.exe job. Python is skipped
	def prepare_postprocessing(self):
		if(self.aSet.fetch("post_run_unipost") == '1'):
			print("  5.a. UPP Flagged Active")
			curDir = os.path.dirname(os.path.abspath(__file__)) 
			uppDir = curDir[:curDir.rfind('/')] + "/post/UPP/"
			if(self.aSet.fetch("unipost_out") == "grib"):
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/wrf_cntrl.parm " + self.postDir + "wrf_cntrl.parm")
			elif(self.aSet.fetch("unipost_out") == "grib2"):
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/postcntrl.xml " + self.postDir + "postcntrl.xml")
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/post_avblflds.xml " + self.postDir + "post_avblflds.xml")
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/params_grib2_tbl_new " + self.postDir + "params_grib2_tbl_new")
			else:
				print("  5.a. Error: Neither GRIB or GRIB2 is defined for UPP output processing, please modify control.txt, aborting")
				return False
			
			Tools.popen(self.aSet, "ln -sf " + uppDir + "scripts/cbar.gs " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/nam_micro_lookup.dat " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/hires_micro_lookup.dat " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "includes/* " + self.postDir)
			print("  5.a. Done")
			return True
		elif(self.aSet.fetch("post_run_python") == '1'):
			print("  5.a. Python Flagged Active")
			print("  5.a. Done")
			return True
		else:
			print("  5. Error: No post-processing methods selected, please make changes to control.txt, aborting")
			return False
			
	def run_postprocessing(self):
		if(self.aSet.fetch("post_run_unipost") == '1'):
			# We run unipost in a single job by assembling all of out wrfout files and writing the UPP steps into one file for each
			tWrite = Template.Template_Writer(self.aSet)
			curDir = os.path.dirname(os.path.abspath(__file__)) 
			temDir = curDir[:curDir.rfind('/')] + "/templates/"			
			uppNodes = self.aSet.fetch("num_upp_nodes")
			uppProcs = self.aSet.fetch("num_upp_processors")
			total = int(uppNodes) * int(uppProcs)
			fList = glob.glob(self.wrfDir + '/' + self.startTime[0:8] + "/output/wrfout*")
			print("  5.b. Running UPP on " + str(len(fList)) + " wrfout files")
			with Tools.cd(self.postDir):
				upp_job_contents = ""
				for iFile in fList:
					dNum = iFile[-23:3]
					year = iFile[-19:4]
					month = iFile[-14:2]
					day = iFile[-11:2]
					hour = iFile[-8:2]
					minute = iFile[-5:2]
					second = iFile[-2:]
					logName = "unipost_log_" + dNum + "_" + year + "_" + month + "_" + day + "_" + hour + ":" + minute + ":" + second + ".log"
					catCMD = ""
					if(self.aSet.fetch("unipost_out") == "grib"):
						catCMD = "cat > itag <<EOF\n" + iFile + '\n' + "netcdf\n" + str(year) + "-" + str(month) + "-" + str(day) + "_" + str(hour) + ":" + str(minute) + ":" + str(second) + '\n' + "NCAR\0"
					elif(self.aSet.fetch("unipost_out") == "grib2"):
						catCMD = "cat > itag <<EOF\n" + iFile + '\n' + "netcdf\n" + "grib2\n" + str(year) + "-" + str(month) + "-" + str(day) + "_"  + str(hour) + ":" + str(minute) + ":" + str(second) + '\n' + "NCAR\0"					
					else:
						#You should never end up here...
						sys.exit("  5.b. Error: grib/grib2 not defined in control.txt")
					upp_job_contents += catCMD
					upp_job_contents += "\n" + "mpirun -np " + str(total) + " unipost.exe > " + logName
					# Create the job file, then submit it.
					tWrite.generateTemplatedFile(temDir + "upp.job.template", "upp.job", extraKeys = {"[upp_job_contents]": upp_job_contents})
				# Once the file has been written, submit the job.
				Tools.popen(self.aSet, "qsub upp.job")
				# Wait for testing...
				return True
		elif(self.aSet.fetch("post_run_python") == '1'):
			return True
		else:
			sys.exit("Error: run_postprocessing() called without a mode flagged, abort.")
			return False
		