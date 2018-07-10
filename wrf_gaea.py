#!/usr/bin/python
# wrf_gaea.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Performs tasks related to obtaining CFS data and running WRF on gaea in a single process

import sys
import os
import os.path
import datetime
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
	
	def __init__(self, waitCommand, condition, abortTime = None, timeDelay=10):
		self.waitCommand = waitCommand
		self.condition = condition
		self.currentTime = datetime.datetime.utcnow()
		self.abortTime = self.currentTime + datetime.timedelta(days=int(999))
		self.timeDelay = timeDelay
		if(abortTime != None):
			self.abortTime = self.currentTime + datetime.timedelta(seconds=int(abortTime))
	
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
		#Move the generated files to the run directory		
		os.system("mv namelist.input " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		os.system("mv namelist.wps.3D " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv namelist.wps.FLX " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv geogrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv metgrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv real.job " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("mv wrf.job " + self.wrfDir + '/' + self.startTime[0:8])
	
	def run_geogrid(self):
		#
		return None
	
	def run_ungrib(self):	
		#ungrib.exe needs to run in the data directory
		os.system("cd " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("module add wrf-3.9.1")
		os.system("link_grib.csh " + self.cfsDir + '/' + self.startTime + '/')
		os.system("cp Vtable.CFSR_press_pgbh06 Vtable")
		os.system("cp namelist.wps.3D namelist.wps")
		os.system("ungrib.exe")
		os.system("cp Vtable.CFSR_sfc_flxf06 Vtable")
		os.system("cp namelist.wps.FLX namelist.wps")
		os.system("ungrib.exe")		
		
	def run_metgrid(self):
		os.system("cd " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("module add wrf-3.9.1")	
		os.system("qsub metgrid.job")
		#Submit a wait condition for the file to appear
		wait1 = Wait("(ls METGRID.o* && echo \"yes\") || echo \"no\"", "yes", timeDelay = 25)
		wait1.hold()
		#Now wait for the output file to be completed
		wait2 = Wait("tail -n 1 METGRID.o*", "*** Successful completion of program metgrid.exe ***", abortTime = 1, timeDelay = 30)
		if(wait2.hold() == False):
			return False
		#Check for errors
		if(os.popen("du -h METGRID.e*").read().split()[0] != "0"):
			return False
		return True
		
	def run_real(self):
		os.system("cd " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("module add wrf-3.9.1")	
		os.system("qsub real.job")
		#Submit a wait condition for the file to appear
		wait1 = Wait("(ls REAL.o* && echo \"yes\") || echo \"no\"", "yes", timeDelay = 25)
		wait1.hold()
		#Now wait for the output file to be completed
		wait2 = Wait("tail -n 1 rsl.out.*", "SUCCESS", abortTime = 1, timeDelay = 30)
		if(wait2.hold() == False):
			return False
		#Check for errors
		if(os.popen("du -h REAL.e*").read().split()[0] != "0"):
			return False			
		#Validate the presense of the two files.
		file1 = os.popen("(ls wrfinput_d01 && echo \"yes\") || echo \"no\"", "yes").read()
		file2 = os.popen("(ls wrfbdy_d01 && echo \"yes\") || echo \"no\"", "yes").read()
		if("yes" in file1 and "yes" in file2):
			return True
		return False
		
	def run_wrf(self):
		os.system("cd " + self.wrfDir + '/' + self.startTime[0:8])
		os.system("module add wrf-3.9.1")	
		os.system("qsub wrf.job")
		#Submit a wait condition for the file to appear
		wait1 = Wait("(ls WRF.o* && echo \"yes\") || echo \"no\"", "yes", timeDelay = 25)
		wait1.hold()
		#Now wait for the output file to be completed (Note: Allow 7 days from the output file first appearing to run)
		wait2 = Wait("tail -n 1 rsl.out.*", "SUCCESS", abortTime = 7, timeDelay = 30)
		if(wait2.hold() == False):
			return False
		#Check for errors
		if(os.popen("du -h WRF.e*").read().split()[0] != "0"):
			return False			
		return True

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
			os.system("rm " + outDir + "/FILE:*")
			os.system("rm " + outDir + "/met_em*")
			os.system("rm " + outDir + "/wrfinput*")
			os.system("rm " + outDir + "/wrfbdy*")
		if(cleanWRFOut == True):
			os.system("rm " + outDir + "/wrfout*")
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
		jobs.run_ungrib()
		if(jobs.run_metgrid() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True)
			sys.exit("   4.b. ERROR: Metgrid.exe process failed to complete, check error file.")
		print("  4.b. Done")
		print("  4.c. Running WRF executables")
		if(jobs.run_real() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True)
			sys.exit("   4.c. ERROR: real.exe process failed to complete, check error file.")		
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