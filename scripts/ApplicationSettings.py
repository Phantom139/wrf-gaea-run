#!/usr/bin/python
# ApplicationSettings.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains the class responsible for managing settings for the application

import datetime
import time

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
		with open("../control.txt") as f: 
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
		self.replacementKeys["[wrf_module]"] = self.fetch("wrfmodule")
		self.replacementKeys["[geog_path]"] = self.fetch("geogdir")
		self.replacementKeys["[table_path]"] = self.fetch("tabledir")
		self.replacementKeys["[run_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8]
		self.replacementKeys["[out_geogrid_path]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[data_dir]"] = self.fetch("datadir") + '/' + self.fetch("modeldata") + '/' + self.fetch("starttime")
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