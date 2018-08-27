#!/usr/bin/python
# Application.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# The primary script file used by this process, handles the "fork" calls to the other classes and methods

import sys
import os
import datetime
import ApplicationSettings
import ModelData
import Cleanup
import Template
import Jobs
import Tools
import Logging

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		logger = Logging.loggedPrint.instance()
	
		logger.write("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		logger.write(" 1. Loading program settings, Performing pre-run directory creations")
		settings = ApplicationSettings.AppSettings()
		modelParms = ModelData.ModelDataParameters(settings.fetch("modeldata"))
		if not modelParms.validModel():
			sys.exit("Program failed at step 1, model data source: " + settings.fetch("modeldata") + ", is not defined in the program.")
		logger.write(" - Settings loaded, model data source " + settings.fetch("modeldata") + " applied to the program.")
		prc = Cleanup.PostRunCleanup(settings)
		prc.performClean()
		mParms = modelParms.fetch()
		Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8])
		Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8] + "/output")		
		Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8] + "/postprd")	
		logger.write(" 1. Done.")
		#Step 2: Download Data Files
		logger.write(" 2. Downloading Model Data Files")
		modelData = ModelData.ModelData(settings, modelParms)
		modelData.fetchFiles()
		logger.write(" 2. Done")
		#Step 3: Generate run files
		logger.write(" 3. Generating run files from templates")
		tWrite = Template.Template_Writer(settings)
		for ext in mParms["FileExtentions"]:
			tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/namelist.wps.template", "namelist.wps." + ext, extraKeys = {"[ungrib_prefix]": ext, "[fg_name]": mParms["FGExt"]})
		tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/namelist.input.template", "namelist.input")
		tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/geogrid.job.template", "geogrid.job")
		tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/metgrid.job.template", "metgrid.job")
		tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/real.job.template", "real.job")
		tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/wrf.job.template", "wrf.job")
		logger.write(" 3. Done")
		#Step 4: Run the WRF steps
		logger.write(" 4. Run WRF Steps")
		jobs = Jobs.JobSteps(settings, modelParms)
		logger.write("  4.a. Checking for geogrid flag...")
		if(settings.fetch("run_geogrid") == '1'):
			logger.write("  4.a. Geogrid flag is set, preparing geogrid job.")
			jobs.run_geogrid()
			logger.write("  4.a. Geogrid job Done")
		else:
			logger.write("  4.a. Geogrid flag is not set, skipping step")
		logger.write("  4.a. Done")
		logger.write("  4.b. Running pre-processing executables")
		jobs.run_ungrib()
		if(jobs.run_metgrid() == False):
			logger.write("   4.b. Error at Metgrid.exe")
			logger.close()		
			sys.exit("   4.b. ERROR: Metgrid.exe process failed to complete, check error file.")
		logger.write("  4.b. Done")
		logger.write("  4.c. Running WRF executables")
		if(jobs.run_real() == False):
			logger.write("   4.c. Error at Real.exe")
			logger.close()		
			sys.exit("   4.c. ERROR: real.exe process failed to complete, check error file.")				
		if(jobs.run_wrf() == False):
			logger.write("   4.c. Error at WRF.exe")
			logger.close()		
			sys.exit("   4.c. ERROR: wrf.exe process failed to complete, check error file.")				
		logger.write("  4.c. Done")
		logger.write(" 4. Done")
		#Step 5: Run postprocessing steps
		if(settings.fetch("run_postprocessing") == '1'):
			logger.write(" 5. Running post-processing")
			post = Jobs.Postprocessing_Steps(settings, modelParms)
			if(post.prepare_postprocessing() == False):
				logger.write("   5. Error initializing unipost")
				logger.close()			
				sys.exit("   5. ERROR: unipost.exe process failed to initialize, check error file.")				
			if(post.run_postprocessing() == False):
				logger.write("   5. Error running unipost")
				logger.close()				
				sys.exit("   5. ERROR: unipost.exe process failed to complete, check error file.")			
			logger.write(" 5. Done")
		else:
			logger.write(" 5. Post-processing flag disabled, skipping step")
		#Step 6: Cleanup
		logger.write(" 6. Cleaning Temporary Files")
		prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = False, cleanModelData = True)
		logger.write(" 6. Done")		
		#Done.
		logger.write("All Steps Completed.")
		logger.write("Program execution complete.")
		logger.close()

# Run the program.
if __name__ == "__main__":
	pInst = Application()