#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys, os, datetime, multiprocessing

# Application: Class responsible for running the program steps.
class Application:

	#startTime: The time the model initializes (YYYYMMDDHH)
	startTime = "2016030100"
	#runDays: The amount of days the model will run
	runDays = 0
	#runHours: The amount of hours the model will run (This is in addition to runDays (IE: Total = (runDays *24) + runHours))
	runHours = 0
	#headDir: The primary directory
	headDir = ""
	#cfsDir: The directory where the CFS files will be stored
	cfsDir = ""
	#wrfDir: The directory where WRF files need to be stored
	wrfDir = ""

	def loadSettings():
		with open("control.txt") as f: 
			for line in f: 
				tokenized = line.split()
				if(tokenized[0][0] == '#'):
					#Comment line, ignore
				elif(tokenized[0].lower() == "starttime"):
					self.startTime = tokenized[1]
				elif(tokenized[0].lower() == "rundays"):
					self.runDays = tokenized[1]
				elif(tokenized[0].lower() == "runhours"):
					self.runHours = tokenized[1]
				elif(tokenized[0].lower() == "headdir"):
					self.headDir = tokenized[1]					
				elif(tokenized[0].lower() == "cfsdir"):
					self.cfsDir = tokenized[1]					
				elif(tokenized[0].lower() == "wrfdir"):
					self.wrfDir = tokenized[1]
				else:
					printf("Unknown file setting found in control.txt: " + str(tokenized[0]) + " => " str(tokenized[1]))
		#Test for program critical settings
		if((not self.startTime) or (not self.runDays) or (not self.runHours) or not (self.headDir) or (not self.cfsDir) or (not self.writeDir)):
			printf("Program critical variable missing, check for existence of control.txt, abort.")
			return False
		else:
			return True
			
	def __init__(self):
		printf("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		printf(" 1. Loading program settings")
		if(loadSettings() == False):
			sys.exit("Failed at step 1, program critical variables not defined.")
		printf(" 1. Done.")
		#Step 2: Download CSFV2 Files
		printf(" 2. Downloading CSFV2 Files")
		downloads = CSFV2_Fetch(self.cfsDir, self.startTime, self.runDays, self.runHours)
		printf(" 2. Done")
		#Step 3: Generate WRF Namelist File
		printf(" 3. Generating namelist files")
		namelistGenerate = Namelist_Writer(self.startTime, self.runDays, self.runHours)
		printf(" 3. Done")
		#Step 4: Generate GAEA Job Files
		printf(" 4. Generating GAEA Job Files")
		
		printf(" 4. Done")		
		#Step 5: Run the preprocessing steps
		printf(" 5. Run WRF Pre-Processing Steps")
		preprocessing = Preprocessing_Steps(self.cfsDir, self.wrfDir, self.startTime)
		printf(" 5. Done")
		#Step 6: Run WRF
		printf(" 6. Running WRF")
		
		printf(" 6. Done")
		#Step 7: Run postprocessing steps
		printf(" 7. Running post-processing")
		
		printf(" 7. Done")
		#Step 8: Cleanup
		printf(" 8. Cleaning Temporary Files")
		
		printf(" 8. Done")		
		#Done.
		printf("All Steps Completed.")
		printf("Program execution complete.")

#CFSV2_Fetch: Class responsible for downloading and storing the CSFV2 Data
class CFSV2_Fetch:
	
	startTime = ""
	cfsDir = ""
	runDays = 1
	runHours = 1

	def __init__(self, cfsDir, startTime, runDays, runHours):
		self.cfsDir = cfsDir
		self.startTime = datetime.datetime.strptime(startTime, "%Y%m%d%H")
		self.runDays = runDays
		self.runHours = runHours
		
		fetchFiles()
		
	def fetchFiles():
		os.system("mkdir " + self.cfsDir + '/' + str(self.strftime('%Y%m%d%H')))
	
		enddate = self.startTime + datetime.timedelta(days=self.runDays, hours=self.runHours)
		dates = []
		current = self.startTime
		while current <= enddate:
			dates.append(current)
			current += datetime.timedelta(hours=6)	
	
		pool = multiprocessing.Pool(processes = 6)
		r2 = pool.map(self.pooled_download, dates)
		pool.close()
		pool.join()
	
	def pooled_download(timeObject):
		prs_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_pgbf/"
		flx_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_flxf/"
		
		strTime = str(self.startTime)
		
		pgrb2link = prs_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' strTime + "/pgbf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		sgrb2link = flx_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' strTime + "/flxf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		pgrb2writ = self.cfsDir + '/' + strTime[0:8] + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		sgrb2writ = self.cfsDir + '/' + strTime[0:8] + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		
		os.system("wget " + pgrb2link + " -O " + pgrb2writ)
		os.system("wget " + sgrb2link + " -O " + sgrb2writ)		
		
# Namelist_Writer: Class responsible for writing the namelist files for WRF
class Namelist_Writer:

	startTime = ""
	endTime = ""
	runDays = 0
	runHours = 0
	
	def __init__(self, startTime, runDays, runHours):
		self.startTime = datetime.datetime.strptime(startTime, "%Y%m%d%H")
		self.runDays = runDays
		self.runHours = runHours
		
		self.endTime = self.startTime + datetime.timedelta(days=self.runDays, hours=self.runHours)
		
		generateNamelistInput()
		
	def generateNamelistInput():
		with open("namelist.input", 'w') as target_file:
			with open("namelist.input.template", 'r') as source_file:
				for line in source_file:
					newLine = line
					newLine = newLine.replace("[run_days]", str(self.runDays))
					newLine = newLine.replace("[run_hours]", str(self.runHours))
					newLine = newLine.replace("[start_year]", str(self.startTime.year))
					newLine = newLine.replace("[start_month]", str(self.startTime.month))
					newLine = newLine.replace("[start_day]", str(self.startTime.day))
					newLine = newLine.replace("[start_hour]", str(self.startTime.hour))
					newLine = newLine.replace("[end_year]", str(self.endTime.year))
					newLine = newLine.replace("[end_month]", str(self.endTime.month))
					newLine = newLine.replace("[end_day]", str(self.endTime.day))
					newLine = newLine.replace("[end_hour]", str(self.endTime.hour))					
					target_file.write(newLine)
	
# Preprocessing_Steps: Class responsible for running the steps prior to the WRF model
class Preprocessing_Steps:

	startTime = ""
	cfsDir = ""
	wrfDir = ""

	def __init__(self, cfsDir, wrfDir, startTime):
		self.cfsDir = cfsDir
		self.wrfDir = wrfDir
		self.startTime = startTime
		os.system("module add wrf-3.9.1")
		os.system("mkdir " + self.wrfDir + '/' + self.startTime[0:8])
	
	def run_ungrib():
		#Start by symlinking out files from the run folder 
		os.system("ln -s " + cfsDir + '/' + strTime[0:8] + "/* " + wrfDir + '/' + strTime[0:8])
		#ungrib.exe needs to run in the data directory
		os.system("cd " + wrfDir + '/' + self.startTime[0:8])

class Run_WRF:

class Postprocessing_Steps:

# Run the program.
pInst = Application()