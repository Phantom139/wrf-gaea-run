#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys, os, datetime
from multiprocessing.pool import ThreadPool

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

		self.assembleKeys()
		
# Template_Writer: Class responsible for taking the template files and saving the use files with parameters set
class Template_Writer:
	aSet = None
	
	def __init__(self, settings):
		self.aSet = settings
					
	def generateTemplatedFile(self, inFile, outFile):
		with open(outFile, 'w') as target_file:
			with open(inFile, 'r') as source_file:
				for line in source_file:
					newLine = line
					newLine = self.aSet.replace(newLine)				
					target_file.write(newLine)	

# Wait: Class instance designed to establish a hold condition until execution has been completed
class Wait:
	waitCommand = ""
	currentTime = ""
	abortTime = ""
	condition = ""
	timeDelay = ""
	
	def __init__(self, waitCommand, condition, abortTime = None, timeDelay=60):
		self.waitCommand = waitCommand
		self.condition = condition
		self.currentTime = datetime.datetime.utcnow()
		self.abortTime = self.currentTime + datetime.timedelta(days=int(999))
		self.timeDelay = timeDelay
		if(abortTime != None):
			self.abortTime = self.currentTime + datetime.timedelta(seconds=int(abortTime))
		
		self.hold()
	
	def hold():
		cTime = datetime.datetime.utcnow()
		if(cTime > self.abortTime):
			print("Wait(): Abort time elapsed, breaking wait")
			return False
		cResult = os.popen(self.waitCommand).read()
		if(condition in cResult):
			return True
		time.sleep(self.timeDelay)
		return self.hold()

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
		#os.system("mkdir " + self.cfsDir + '/' + str(self.startTime.strftime('%Y%m%d%H')))
		print("mkdir " + self.cfsDir + '/' + str(self.startTime.strftime('%Y%m%d%H')))
	
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
		
		#os.system("wget " + pgrb2link + " -O " + pgrb2writ)
		#os.system("wget " + sgrb2link + " -O " + sgrb2writ)	
		print("wget " + pgrb2link + " -O " + pgrb2writ)
		print("wget " + sgrb2link + " -O " + sgrb2writ)
	
# Preprocessing_Steps: Class responsible for running the steps prior to the WRF model
class Preprocessing_Steps:
	aSet = None
	startTime = ""
	cfsDir = ""
	wrfDir = ""

	def __init__(self, settings):
		self.aSet = settings
		self.cfsDir = settings.fetch("cfsdir")
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		#os.system("module add wrf-3.9.1")
		#os.system("mkdir " + self.wrfDir + '/' + self.startTime[0:8])
		print("module add wrf-3.9.1")
		print("mkdir " + self.wrfDir + '/' + self.startTime[0:8])
	
	def run_geogrid(self):
		#
		return None
	
	def run_ungrib(self):
		#Start by symlinking out files from the run folder 
		#os.system("ln -s " + cfsDir + '/' + strTime[0:8] + "/* " + wrfDir + '/' + strTime[0:8])
		#ungrib.exe needs to run in the data directory
		#os.system("cd " + wrfDir + '/' + self.startTime[0:8])
		print("test")
		
	def run_metgrid(self):
		return None

#class Run_WRF:

#class Postprocessing_Steps:

# Application: Class responsible for running the program steps.
class Application():
	# Storage dictionary for program settings
	settings = None
			
	def __init__(self):
		print("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		print(" 1. Loading program settings")
		settings = AppSettings()
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
		print(" 3. Done")
		#Step 4: Run the preprocessing steps
		print(" 4. Run WRF Pre-Processing Steps")
		preprocessing = Preprocessing_Steps(settings)
		print(" 4.a Checking for geogrid flag...")
		if(settings.fetch("run_geogrid") == '1'):
			print(" 4.a Geogrid flag is set, preparing geogrid job.")
			
			print(" 4.a Done")
		else:
			print(" 4.a Geogrid flag is not set, skipping step")
		print(" 4.b. Running pre-processing executables")
		
		print(" 4.b. Done")
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

# Run the program.
if __name__ == "__main__":
	pInst = Application()