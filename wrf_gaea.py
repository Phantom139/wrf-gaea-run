#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys, os, datetime, multiprocessing

# Singleton: Wrapper instance for a single-ly defined class
class Singleton:
	__instance = None
	
	@staticmethod
	def instance():
		if Singleton.__instance == None:
			Singleton()
		else:
			return Singleton.__instance
	
	def __init__(self):
		if(Singleton.__instance != None):
			printf("Singleton: Error, attempting to init a singleton that already exists")
		else:
			Singleton.__instance = self

# Application: Class responsible for running the program steps.
class Application(Singleton):
	# Storage dictionary for program settings
	settings = {}
	
	def loadSettings():
		with open("control.txt") as f: 
			for line in f: 
				tokenized = line.split()
				if(tokenized[0][0] == '#'):
					#Comment line, ignore
				else:
					self.settings[tokenized[0]] = tokenized[1]
		#Test for program critical settings
		if(not self.settings):
			printf("Program critical variables missing, check for existence of control.txt, abort.")
			return False
		else:
			return True
			
	def __init__(self):
		super().__init__()
		printf("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		printf(" 1. Loading program settings")
		if(loadSettings() == False):
			sys.exit("Failed at step 1, program critical variables not defined.")
		printf(" 1. Done.")
		#Step 2: Download CSFV2 Files
		printf(" 2. Downloading CSFV2 Files")
		downloads = CSFV2_Fetch()
		printf(" 2. Done")
		#Step 3: Generate WRF Namelist File
		printf(" 3. Generating namelist files")
		namelistGenerate = Namelist_Writer()
		printf(" 3. Done")
		#Step 4: Generate GAEA Job Files
		printf(" 4. Generating GAEA Job Files")
		
		printf(" 4. Done")		
		#Step 5: Run the preprocessing steps
		printf(" 5. Run WRF Pre-Processing Steps")
		preprocessing = Preprocessing_Steps()
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
class CFSV2_Fetch():
	
	startTime = ""
	cfsDir = ""
	runDays = 1
	runHours = 1

	def __init__(self):
		self.cfsDir = Application.instance().settings["cfsDir"]
		self.startTime = datetime.datetime.strptime(Application.instance().settings["startTime"], "%Y%m%d%H")
		self.runDays = Application.instance().settings["runDays"]
		self.runHours = Application.instance().settings["runHours"]
		
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
	
	def __init__(self):
		self.startTime = datetime.datetime.strptime(Application.instance().settings["startTime"], "%Y%m%d%H")
		self.runDays = Application.instance().settings["runDays"]
		self.runHours = Application.instance().settings["runHours"]
		
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

	def __init__(self):
		self.cfsDir = Application.instance().settings["cfsDir"]
		self.wrfDir = Application.instance().settings["wrfDir"]
		self.startTime = Application.instance().settings["startTime"]
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