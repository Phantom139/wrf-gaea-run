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
	#writeDir: The directory where output files need to be written
	writeDir = ""

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
				elif(tokenized[0].lower() == "writedir"):
					self.writeDir = tokenized[1]
				else:
					printf("Unknown file setting found in control.txt: " + str(tokenized[0]) + " => " str(tokenized[1]))
		#Test for program critical settings
		if((not self.startTime) or (not self.runDays) or (not self.runHours) or (not self.writeDir)):
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
		downloads = CSFV2_Fetch(self.writeDir, self.startTime, self.runDays, self.runHours)
		printf(" 2. Done")
		#Step 3: Generate WRF Namelist File
		printf(" 3. Generating namelist.input file")
		namelistGenerate = Namelist_Writer(self.startTime, self.runDays, self.runHours)
		printf(" 3. Done")
		#Step 4: Run the preprocessing steps
		printf(" 4. Run WRF Pre-Processing Steps")
		
		printf(" 4. Done")
		#Step 5: Run WRF
		printf(" 5. Running WRF")
		
		printf(" 5. Done")
		#Step 6: Run postprocessing steps
		printf(" 6. Running post-processing")
		
		printf(" 6. Done")
		#Done.
		printf("Program execution complete.")

#CFSV2_Fetch: Class responsible for downloading and storing the CSFV2 Data
class CFSV2_Fetch:
	
	startTime = ""
	writeDir = ""
	runDays = 1
	runHours = 1

	def __init__(self, writeDir, startTime, runDays, runHours):
		self.writeDir = writeDir
		self.startTime = datetime.datetime.strptime(startTime, "%Y%m%d%H")
		self.runDays = runDays
		self.runHours = runHours
		
		fetchFiles()
		
	def fetchFiles():
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
		pgrb2writ = self.writeDir + '/' + strTime[0:8] + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		sgrb2writ = self.writeDir + '/' + strTime[0:8] + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		
		os.system("wget " + pgrb2link + " -O " + pgrb2writ)
		os.system("wget " + sgrb2link + " -O " + sgrb2writ)		
		
# Namelist_Writer: Class responsible for writing the namelist file for WRF
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
		
		generateNamelist()
		
	def generateNamelist():
		with open("namelist.input", 'w') as target_file:
			with open("namelist.template", 'r') as source_file:
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
	
class Preprocessing_Steps:

class Run_WRF:

class Postprocessing_Steps:

# Run the program.
pInst = Application()