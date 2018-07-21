#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys
import os
import os.path
import datetime
import time
from multiprocessing.pool import ThreadPool

# AppSettings: Class responsible for obtaining information from the control file and parsing it to classes that need the information
class AppSettings():
	startTime = ""
	endTime = ""
	runDays = 0
	runHours = 0
	settings = {}
	replacementKeys = {}
	myUserID = None

	def loadSettings(self):
		with open("control.txt") as f: 
			for line in f: 
				#To-Do: This can be simplified to a single if block, but for the time being, I'm going to leave it as is
				if not line.split():
					#Comment
					print("Ignored empty line")
				else:
					tokenized = line.split()
					if(tokenized[0][0] == '#'):
						#Comment line, ignore
						print("Comment line: " + line)
					else:
						self.settings[tokenized[0]] = tokenized[1]
						print("Applying setting (" + tokenized[0] +"): " + tokenized[1])
		#Test for program critical settings
		if(not self.settings):
			print("Program critical variables missing, check for existence of control.txt, abort.")
			return False
		else:
			return True
        
	def fetch(self, key):
		try:
			return self.settings[key]
		except KeyError:
			print("Key does not exist")
			return None    
			
	def assembleKeys(self):	
		# DFI
		dfi_back = self.startTime - datetime.timedelta(hours=1)
		dfi_fwd = self.startTime + datetime.timedelta(minutes=30)
		# Construct the replacement dictionary from the settings
		self.replacementKeys["[run_days]"] = str(self.runDays)
		self.replacementKeys["[run_hours]"] = str(self.runHours)
		self.replacementKeys["[start_date]"] = str(self.startTime.strftime('%Y-%m-%d_%H:%M:%S'))
		self.replacementKeys["[end_date]"] = str(self.endTime.strftime('%Y-%m-%d_%H:%M:%S'))
		self.replacementKeys["[start_year]"] = str(self.startTime.year)
		self.replacementKeys["[start_month]"] = str(self.startTime.month)
		self.replacementKeys["[start_day]"] = str(self.startTime.day)
		self.replacementKeys["[start_hour]"] = str(self.startTime.hour)
		self.replacementKeys["[end_year]"] = str(self.endTime.year)
		self.replacementKeys["[end_month]"] = str(self.endTime.month)
		self.replacementKeys["[end_day]"] = str(self.endTime.day)
		self.replacementKeys["[end_hour]"] = str(self.endTime.hour)
		self.replacementKeys["[geog_path]"] = self.fetch("geogdir")
		self.replacementKeys["[table_path]"] = self.fetch("tabledir")
		self.replacementKeys["[run_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8]
		self.replacementKeys["[out_geogrid_path]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[data_dir]"] = self.fetch("cfsdir") + '/' + self.fetch("starttime")
		self.replacementKeys["[num_geogrid_nodes]"] = self.fetch("num_geogrid_nodes")
		self.replacementKeys["[num_geogrid_processors]"] = self.fetch("num_geogrid_processors")
		self.replacementKeys["[geogrid_walltime]"] = self.fetch("geogrid_walltime")
		self.replacementKeys["[mpi_geogrid_total]"] = str(int(self.fetch("num_geogrid_nodes")) * int(self.fetch("num_geogrid_processors")))
		self.replacementKeys["[num_metgrid_nodes]"] = self.fetch("num_metgrid_nodes")
		self.replacementKeys["[num_metgrid_processors]"] = self.fetch("num_metgrid_processors")
		self.replacementKeys["[metgrid_walltime]"] = self.fetch("metgrid_walltime")
		self.replacementKeys["[mpi_metgrid_total]"] = str(int(self.fetch("num_metgrid_nodes")) * int(self.fetch("num_metgrid_processors")))
		self.replacementKeys["[num_real_nodes]"] = self.fetch("num_real_nodes")
		self.replacementKeys["[num_real_processors]"] = self.fetch("num_real_processors")
		self.replacementKeys["[real_walltime]"] = self.fetch("real_walltime")
		self.replacementKeys["[mpi_real_total]"] = str(int(self.fetch("num_real_nodes")) * int(self.fetch("num_real_processors")))	
		self.replacementKeys["[num_wrf_nodes]"] = self.fetch("num_wrf_nodes")
		self.replacementKeys["[num_wrf_processors]"] = self.fetch("num_wrf_processors")
		self.replacementKeys["[wrf_walltime]"] = self.fetch("wrf_walltime")
		self.replacementKeys["[mpi_wrf_total]"] = str(int(self.fetch("num_wrf_nodes")) * int(self.fetch("num_wrf_processors")))
		self.replacementKeys["[dfi_back_year]"] = str(dfi_back.year)		
		self.replacementKeys["[dfi_back_month]"] = str(dfi_back.month)
		self.replacementKeys["[dfi_back_day]"] = str(dfi_back.day)
		self.replacementKeys["[dfi_back_hour]"] = str(dfi_back.hour)
		self.replacementKeys["[dfi_back_minute]"] = str(dfi_back.minute)
		self.replacementKeys["[dfi_fwd_year]"] = str(dfi_fwd.year)		
		self.replacementKeys["[dfi_fwd_month]"] = str(dfi_fwd.month)
		self.replacementKeys["[dfi_fwd_day]"] = str(dfi_fwd.day)
		self.replacementKeys["[dfi_fwd_hour]"] = str(dfi_fwd.hour)
		self.replacementKeys["[dfi_fwd_minute]"] = str(dfi_fwd.minute)		
	 
	def replace(self, str):
		if not str:
			#print("AppSettings::replace(): Error, no string sent)
			return str
		fStr = str
		for key, value in self.replacementKeys.items():
			fStr = fStr.replace(key, value)
		return fStr
		
	def whoami(self):
		return self.myUserID
     
	def __init__(self):
		if(self.loadSettings() == False):
			sys.exit("Failed to load settings, please check for control.txt")
        
		self.myUserID = os.popen("whoami").read()
		
		self.startTime = datetime.datetime.strptime(self.fetch("starttime"), "%Y%m%d%H")
		self.runDays = self.fetch("rundays")
		self.runHours = self.fetch("runhours")

		self.endTime = self.startTime + datetime.timedelta(days=int(self.runDays), hours=int(self.runHours))

		self.assembleKeys()
		
# Template_Writer: Class responsible for taking the template files and saving the use files with parameters set
class Template_Writer:
	aSet = None
	
	def __init__(self, settings):
		self.aSet = settings
					
	def generateTemplatedFile(self, inFile, outFile):
		outContents = ""
		with open(outFile, 'w') as target_file:
			with open(inFile, 'r') as source_file:
				for line in source_file:
					newLine = line
					newLine = self.aSet.replace(newLine) + '\n'
					outContents += newLine
			target_file.write(outContents)	

#TimeExpiredException: Custom exception that is thrown when the Wait() command expires
class TimeExpiredException(Exception):
	pass
					
# Wait: Class instance designed to establish a hold condition until execution has been completed
class Wait:
	holds = []
	currentTime = ""
	abortTime = ""
	timeDelay = ""
	
	def __init__(self, holdList, abortTime = None, timeDelay=10):
		self.holds = holdList
		self.currentTime = datetime.datetime.utcnow()
		self.abortTime = self.currentTime + datetime.timedelta(days=int(999))
		self.timeDelay = timeDelay
		if(abortTime != None):
			self.abortTime = self.currentTime + datetime.timedelta(seconds=int(abortTime))
	
	def hold(self):
		cTime = datetime.datetime.utcnow()
		if(cTime > self.abortTime):
			raise TimeExpiredException
			return None
		
		for indHold in self.holds:
			command = indHold["waitCommand"]
			retCode = indHold["retCode"]
			cResult = os.popen(command).read()
			if 'splitFirst' in indHold:
				cResult = cResult.split()[0]
			if 'contains' in indHold:
				contains = indHold["contains"]
				if(contains in cResult):
					return retCode
			elif 'isValue' in indHold:
				isValue = indHold["isValue"]
				if(cResult == isValue):
					return retCode
			elif 'isNotValue' in indHold:
				isValue = indHold["isNotValue"]
				if(cResult != isValue):
					return retCode
			else:
				return cResult	
		time.sleep(self.timeDelay)
		return self.hold()

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
		
#CFSV2_Fetch: Class responsible for downloading and storing the CSFV2 Data
class CFSV2_Fetch():
	
	startTime = ""
	cfsDir = ""
	runDays = 1
	runHours = 1

	def __init__(self, settings):
		self.cfsDir = settings.fetch("cfsdir")
		self.startTime = datetime.datetime.strptime(settings.fetch("starttime"), "%Y%m%d%H")
		self.runDays = settings.fetch("rundays")
		self.runHours = settings.fetch("runhours")
		
		self.fetchFiles()
		
	def fetchFiles(self):
		dirPath = self.cfsDir + '/' + str(self.startTime.strftime('%Y%m%d%H'))
		if not os.path.isdir(dirPath):
			os.system("mkdir " + dirPath)
	
		enddate = self.startTime + datetime.timedelta(days=int(self.runDays), hours=int(self.runHours))
		dates = []
		current = self.startTime
		while current <= enddate:
			dates.append(current)
			current += datetime.timedelta(hours=6)	
			
		t = ThreadPool(processes=6)
		rs = t.map(self.pooled_download, dates)
		t.close()
	
	def pooled_download(self, timeObject):
		prs_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_pgbf/"
		flx_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_flxf/"
		
		strTime = str(self.startTime.strftime('%Y%m%d%H'))
		
		pgrb2link = prs_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/pgbf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		sgrb2link = flx_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/flxf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		pgrb2writ = self.cfsDir + '/' + strTime + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		sgrb2writ = self.cfsDir + '/' + strTime + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		if not os.path.isfile(pgrb2writ):
			os.system("wget " + pgrb2link + " -O " + pgrb2writ)
		if not os.path.isfile(sgrb2writ):
			os.system("wget " + sgrb2link + " -O " + sgrb2writ)	
	
# JobSteps: Class responsible for handling the steps that involve job submission and checkup
class JobSteps:
	aSet = None
	startTime = ""
	cfsDir = ""
	wrfDir = ""

	def __init__(self, settings):
		self.aSet = settings
		self.cfsDir = settings.fetch("cfsdir")
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		os.system("mkdir " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mkdir " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		#Copy important files to the directory
		os.system("cp Vtable.CFSR_press_pgbh06 " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("cp Vtable.CFSR_sfc_flxf06 " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("cp geo_em.d01.nc " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		os.system("cp run_files/* " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		#Move the generated files to the run directory		
		os.system("mv namelist.input " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		os.system("mv namelist.wps.3D " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv namelist.wps.FLX " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv geogrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv metgrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv real.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv wrf.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv ungrib.csh " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("chmod +x " + self.wrfDir + '/' + self.startTime[0:8] + "/ungrib.csh")
	
	def run_geogrid(self):
		#
		return None
	
	def run_ungrib(self):	
		#ungrib.exe needs to run in the data directory
		with cd(self.wrfDir + '/' + self.startTime[0:8]):
			os.system("./ungrib.csh")		
		
	### BIG TO-DO: Need to update the Wait class to be able to test multiple conditions at once with return code for each if triggered
	###  The likely best bet choice here is some kind of a list which stores a dictionary {command:Blah,condition:Blah,return:0} for instance
	def run_metgrid(self):
		with cd(self.wrfDir + '/' + self.startTime[0:8]):	
			os.system("qsub metgrid.job")
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls metgrid.log* && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait(firstWait, timeDelay = 25)
				wait1.hold()
			except TimeExpiredException:
				sys.exit("metgrid.exe job not completed, abort.")
			#Now wait for the output file to be completed
			try:
				secondWait = [{"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "Successful completion of program metgrid.exe", "retCode": 1},
#								{"waitCommand": "du -h METGRID.e*", "splitFirst": 1, "isNotValue": "0", "retCode": 2}, #7/15: WARN messages that don't affect results can trigger this condition
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "error", "retCode": 2},]
				wait2 = Wait(secondWait, timeDelay = 25)
				wRC = wait2.hold()
				if wRC == 1:
					return True
				elif wRC == 2:
					return False
			except TimeExpiredException:
				sys.exit("metgrid.exe job not completed, abort.")
		print("run_metgrid(): Failed to enter run directory")
		return False
		
	def run_real(self):
		with cd(self.wrfDir + '/' + self.startTime[0:8]):
			os.system("qsub real.job")
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls output/rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait(firstWait, timeDelay = 25)
				wait1.hold()			
			except TimeExpiredException:
				sys.exit("real.exe job not completed, abort.")
			#Now wait for the output file to be completed
			try:
				secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS", "retCode": 1},
#								{"waitCommand": "du -h REAL.e*", "splitFirst": 1, "isNotValue": "0", "retCode": 2}, #See Above
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
				wait2 = Wait(secondWait, timeDelay = 60)
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
			except TimeExpiredException:
				sys.exit("real.exe job not completed, abort.")		
		print("run_real(): Failed to enter run directory")
		return False			
		
	def run_wrf(self):
		with cd(self.wrfDir + '/' + self.startTime[0:8]):
			# Remove the old log files as these are no longer needed
			os.system("rm output/rsl.out.*")
			os.system("rm output/rsl.error.*")	
			os.system("qsub wrf.job")
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait(firstWait, timeDelay = 25)
				wait1.hold()			
			except TimeExpiredException:
				sys.exit("wrf.exe job not completed, abort.")
			#Now wait for the output file to be completed (Note: Allow 7 days from the output file first appearing to run)
			#Now wait for the output file to be completed
			try:
				secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS", "retCode": 1},
#								{"waitCommand": "du -h WRF.e*", "splitFirst": 1, "isNotValue": "0", "retCode": 2}, #See Above
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
				# Note: I have the script checking the files once every three minutes so we don't stack five calls rapidly, this can be modified later if needed.
				wait2 = Wait(secondWait, timeDelay = 180)
				wRC = wait2.hold()
				if wRC == 2:
					return False
				else:
					return True				
			except TimeExpiredException:
				sys.exit("wrf.exe job not completed, abort.")				
		print("run_wrf(): Failed to enter run directory")
		return False			

#class Postprocessing_Steps:

class PostRunCleanup():
	sObj = None
	
	def __init__(self, settings):
		self.sObj = settings
		
	def performClean(self, cleanAll = True, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = True):
		sTime = self.sObj.fetch("starttime")
		wrfDir = self.sObj.fetch("wrfdir") + '/' + sTime[0:8]
		outDir = wrfDir + "/output"
		if(cleanAll == True):
			cleanOutFiles = True
			cleanErrorFiles = True
			cleanInFiles = True
			cleanWRFOut = True
		if(cleanOutFiles == True):
			os.system("rm " + wrfDir + "/geogrid.log.*")
			os.system("rm " + outDir + "/metgrid.log.*")
			os.system("rm " + outDir + "/ungrib.log*")
			os.system("rm " + outDir + "/rsl.out.*")
			os.system("rm " + wrfDir + "/GEOGRID.o*")
			os.system("rm " + wrfDir + "/METGRID.o*")
			os.system("rm " + wrfDir + "/UNGRIB.o*") #This shouldn't be needed, but in the event we use a job for ungrib.
			os.system("rm " + outDir + "/REAL.o*")
			os.system("rm " + outDir + "/WRF.o*")
		if(cleanErrorFiles == True):
			os.system("rm " + outDir + "/rsl.error.*")
			os.system("rm " + wrfDir + "/GEOGRID.e*")
			os.system("rm " + wrfDir + "/METGRID.e*")
			os.system("rm " + wrfDir + "/UNGRIB.e*") #This shouldn't be needed, but in the event we use a job for ungrib.
			os.system("rm " + outDir + "/REAL.e*")
			os.system("rm " + outDir + "/WRF.e*")	
		if(cleanInFiles == True):
			os.system("rm " + wrfDir + "/GRIBFILE.*")
			os.system("rm " + wrfDir + "/3D:*")
			os.system("rm " + wrfDir + "/FLX:*")
			os.system("rm " + outDir + "/FILE:*")
			os.system("rm " + outDir + "/met_em*")
			os.system("rm " + outDir + "/wrfinput*")
			os.system("rm " + outDir + "/wrfbdy*")
			os.system("rm " + outDir + "/geo_em.d01.nc")
			os.system("rm " + outDir + "/aero*")
			os.system("rm " + outDir + "/bulk*")
			os.system("rm " + outDir + "/CAM*")
			os.system("rm " + outDir + "/capacity.asc")
			os.system("rm " + outDir + "/CCN*")
			os.system("rm " + outDir + "/CLM*")
			os.system("rm " + outDir + "/co2_trans")
			os.system("rm " + outDir + "/coeff*")
			os.system("rm " + outDir + "/constants.asc")
			os.system("rm " + outDir + "/create_p3_lookupTable_1.f90")
			os.system("rm " + outDir + "/ETA*")
			os.system("rm " + outDir + "/GEN*")
			os.system("rm " + outDir + "/grib*")
			os.system("rm " + outDir + "/kernels*")
			os.system("rm " + outDir + "/LANDUSE.TBL")
			os.system("rm " + outDir + "/masses.asc")
			os.system("rm " + outDir + "/MPTABLE.TBL")
			os.system("rm " + outDir + "/ozone*")
			os.system("rm " + outDir + "/p3_lookup_table_1.dat")
			os.system("rm " + outDir + "/RRTM*")
			os.system("rm " + outDir + "/RRTMG*")
			os.system("rm " + outDir + "/SOILPARM.TBL")
			os.system("rm " + outDir + "/termvels.asc")
			os.system("rm " + outDir + "/tr*")
			os.system("rm " + outDir + "/URB*")
			os.system("rm " + outDir + "/VEG*")
			os.system("rm " + outDir + "/wind-turbine-1.tbl")
			os.system("rm " + outDir + "/real.exe")
			os.system("rm " + outDir + "/tc.exe")
			os.system("rm " + outDir + "/wrf.exe")
		if(cleanWRFOut == True):
			os.system("rm " + outDir + "/wrfout*")
			os.system("rm " + outDir + "/wrfrst*")
		return None

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		print("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		print(" 1. Loading program settings")
		settings = AppSettings()
		prc = PostRunCleanup(settings)
		prc.performClean()
		print(" 1. Done.")
		#Step 2: Download CSFV2 Files
		print(" 2. Downloading CSFV2 Files")
		downloads = CFSV2_Fetch(settings)
		print(" 2. Done")
		#Step 3: Generate run files
		print(" 3. Generating run files from templates")
		tWrite = Template_Writer(settings)
		tWrite.generateTemplatedFile("namelist.input.template", "namelist.input")
		tWrite.generateTemplatedFile("namelist.wps.3D.template", "namelist.wps.3D")
		tWrite.generateTemplatedFile("namelist.wps.FLX.template", "namelist.wps.FLX")
		tWrite.generateTemplatedFile("geogrid.job.template", "geogrid.job")
		tWrite.generateTemplatedFile("metgrid.job.template", "metgrid.job")
		tWrite.generateTemplatedFile("real.job.template", "real.job")
		tWrite.generateTemplatedFile("wrf.job.template", "wrf.job")
		tWrite.generateTemplatedFile("ungrib.csh.template", "ungrib.csh")
		print(" 3. Done")
		#Step 4: Run the WRF steps
		print(" 4. Run WRF Steps")
		jobs = JobSteps(settings)
		print("  4.a Checking for geogrid flag...")
		if(settings.fetch("run_geogrid") == '1'):
			print("  4.a Geogrid flag is set, preparing geogrid job.")
			jobs.run_geogrid()
			print("  4.a Geogrid job Done")
		else:
			print("  4.a Geogrid flag is not set, skipping step")
		print("  4.a. Done")
		print("  4.b. Running pre-processing executables")
		time.sleep(10)
		jobs.run_ungrib()
		time.sleep(10)
		if(jobs.run_metgrid() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True)
			sys.exit("   4.b. ERROR: Metgrid.exe process failed to complete, check error file.")
		print("  4.b. Done")
		print("  4.c. Running WRF executables")
		time.sleep(10)
		if(jobs.run_real() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True)
			sys.exit("   4.c. ERROR: real.exe process failed to complete, check error file.")	
		time.sleep(10)
		if(jobs.run_wrf() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True)
			sys.exit("   4.c. ERROR: wrf.exe process failed to complete, check error file.")	
		print("  4.c. Done")
		print(" 4. Done")
		#Step 5: Run postprocessing steps
		print(" 5. Running post-processing")
		
		print(" 5. Done")
		#Step 6: Cleanup
		print(" 6. Cleaning Temporary Files")
		#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = False)
		print(" 6. Done")		
		#Done.
		print("All Steps Completed.")
		print("Program execution complete.")

# Run the program.
if __name__ == "__main__":
	pInst = Application()