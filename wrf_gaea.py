#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys, os, datetime, multiprocessing

# AppSettings: Class responsible for obtaining information from the control file and parsing it to classes that need the information
class AppSettings():
	startTime = ""
	endTime = ""
	runDays = 0
	runHours = 0
	settings = {}
	replacementKeys = {}

	def loadSettings(self):
		with open("control.txt") as f: 
			for line in f: 
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
		# Construct the replacement dictionary from the settings
		replacementKeys["[run_days]"] = str(self.runDays)
		replacementKeys["[run_hours]"] = str(self.runHours)
		replacementKeys["[start_date]"] = str(self.startTime.strftime('%y-%m-%d_%H:%M:%S'))
		replacementKeys["[end_date]"] = str(self.endTime.strftime('%y-%m-%d_%H:%M:%S'))
		replacementKeys["[start_year]"] = str(self.startTime.year)
		replacementKeys["[start_month]"] = str(self.startTime.month)
		replacementKeys["[start_day]"] = str(self.startTime.day)
		replacementKeys["[start_hour]"] = str(self.startTime.hour)
		replacementKeys["[end_year]"] = str(self.endTime.year)
		replacementKeys["[end_month]"] = str(self.endTime.month)
		replacementKeys["[end_day]"] = str(self.endTime.day)
		replacementKeys["[end_hour]"] = str(self.endTime.hour)
		replacementKeys["[geog_path]"] = self.fetch("geogdir")
		replacementKeys["[table_path]"] = self.fetch("tabledir")
		replacementKeys["[run_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime").startTime[0:8]
		replacementKeys["[out_geogrid_path]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime").startTime[0:8] + "/output"
		replacementKeys["[run_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime").startTime[0:8] + "/output"
	 
	def replace(self, str):
		if not str:
			#print("AppSettings::replace(): Error, no string sent)
			return str
		fStr = str
		for key, value in self.replacementKeys.items():
			fStr = fStr.replace(key, value)
		return fStr
     
	def __init__(self):
		if(self.loadSettings() == False):
			sys.exit("Failed to load settings, please check for control.txt")
        
		self.startTime = datetime.datetime.strptime(self.fetch("starttime"), "%Y%m%d%H")
		self.runDays = self.fetch("rundays")
		self.runHours = self.fetch("runhours")

		self.endTime = self.startTime + datetime.timedelta(days=int(self.runDays), hours=int(self.runHours))

		self.assemblyKeys()

# Application: Class responsible for running the program steps.
class Application():
	# Storage dictionary for program settings
	settings = {}
			
	def __init__(self):
		print("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		print(" 1. Loading program settings")
		settings = AppSettings()
		print(" 1. Done.")
		#Step 2: Download CSFV2 Files
		print(" 2. Downloading CSFV2 Files")
		downloads = CSFV2_Fetch(settings)
		print(" 2. Done")
		#Step 3: Generate run files
		print(" 3. Generating run files from templates")
		tWrite = Template_Writer(settings)
		tWrite.generateTemplatedFile("namelist.input.template", "namelist.input")
		print(" 3. Done")
		#Step 4: Run the preprocessing steps
		print(" 4. Run WRF Pre-Processing Steps")
		preprocessing = Preprocessing_Steps(settings)
		print(" 4. Done")
		#Step 5: Run WRF
		print(" 5. Running WRF")
		
		print(" 5. Done")
		#Step 6: Run postprocessing steps
		print(" 6. Running post-processing")
		
		print(" 6. Done")
		#Step 7: Cleanup
		print(" 7. Cleaning Temporary Files")
		
		print(" 7. Done")		
		#Done.
		print("All Steps Completed.")
		print("Program execution complete.")

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
		os.system("mkdir " + self.cfsDir + '/' + str(self.startTime.strftime('%Y%m%d%H')))
	
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
	
	def pooled_download(self, timeObject):
		prs_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_pgbf/"
		flx_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_flxf/"
		
		strTime = str(self.startTime)
		
		pgrb2link = prs_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' strTime + "/pgbf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		sgrb2link = flx_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' strTime + "/flxf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
		pgrb2writ = self.cfsDir + '/' + strTime[0:8] + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		sgrb2writ = self.cfsDir + '/' + strTime[0:8] + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
		
		os.system("wget " + pgrb2link + " -O " + pgrb2writ)
		os.system("wget " + sgrb2link + " -O " + sgrb2writ)		
		
# Template_Writer: Class responsible for taking the template files and saving the use files with parameters set
class Template_Writer:
	aSet = None
	startTime = ""
	endTime = ""
	runDays = 0
	runHours = 0
	
	def __init__(self, settings):
		self.aSet = settings
		self.startTime = datetime.datetime.strptime(settings.fetch("starttime"), "%Y%m%d%H")
		self.runDays = settings.fetch("rundays")
		self.runHours = settings.fetch("runhours")
		
		self.endTime = self.startTime + datetime.timedelta(days=self.runDays, hours=self.runHours)
					
	def generateTemplatedFile(self, inFile, outFile):
		with open(outFile, 'w') as target_file:
			with open(inFile, 'r') as source_file:
				for line in source_file:
					newLine = aSet.replace(line)				
					target_file.write(newLine)	
	
# Preprocessing_Steps: Class responsible for running the steps prior to the WRF model
class Preprocessing_Steps:

	startTime = ""
	cfsDir = ""
	wrfDir = ""

	def __init__(self, settings):
		self.cfsDir = settings.fetch("cfsdir")
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		os.system("module add wrf-3.9.1")
		os.system("mkdir " + self.wrfDir + '/' + self.startTime[0:8])
	
	def run_ungrib(self):
		#Start by symlinking out files from the run folder 
		os.system("ln -s " + cfsDir + '/' + strTime[0:8] + "/* " + wrfDir + '/' + strTime[0:8])
		#ungrib.exe needs to run in the data directory
		os.system("cd " + wrfDir + '/' + self.startTime[0:8])

class Run_WRF:

class Postprocessing_Steps:

# Run the program.
pInst = Application()