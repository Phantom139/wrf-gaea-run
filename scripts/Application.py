#!/usr/bin/python
# Application.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# The primary script file used by this process, handles the "fork" calls to the other classes and methods

import sys
import os
from ApplicationSettings import *
from ModelData import *
from Cleanup import *
from Template import *
from Jobs import *
from Tools import *

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		print("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		print(" 1. Loading program settings, Performing pre-run directory creations")
		settings = ApplicationSettings.AppSettings()
		modelParms = ModelData.ModelDataParameters(settings, settings.fetch("modeldata"))
		if not modelParms.validModel():
			sys.exit("Program failed at step 1, model data source: " + settings.fetch("modeldata") + ", is not defined in the program.")
		print(" - Settings loaded, model data source " + settings.fetch("modeldata") + " applied to the program.")
		prc = Cleanup.PostRunCleanup(settings)
		prc.performClean()
		mParms = modelParms.fetch()
		Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8])
		Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8] + "/output")		
		print(" 1. Done.")
		#Step 2: Download Data Files
		print(" 2. Downloading Model Data Files")
		modelData = ModelData.ModelData(settings, modelParms)
		modelData.fetchFiles()
		print(" 2. Done")
		#Step 3: Generate run files
		print(" 3. Generating run files from templates")
		tWrite = Template.Template_Writer(settings)
		for ext in mParms["FileExtentions"]:
			tWrite.generateTemplatedFile("../templates/namelist.wps.template", "namelist.wps." + ext, extraKeys = {"[ungrib_prefix]": ext, "[fg_name]": mParms["FGExt"]})
		tWrite.generateTemplatedFile("../templates/namelist.input.template", "namelist.input")
		tWrite.generateTemplatedFile("../templates/geogrid.job.template", "geogrid.job")
		tWrite.generateTemplatedFile("../templates/metgrid.job.template", "metgrid.job")
		tWrite.generateTemplatedFile("../templates/real.job.template", "real.job")
		tWrite.generateTemplatedFile("../templates/wrf.job.template", "wrf.job")
		print(" 3. Done")
		#Step 4: Run the WRF steps
		print(" 4. Run WRF Steps")
		jobs = Jobs.JobSteps(settings, modelParms)
		print("  4.a. Checking for geogrid flag...")
		if(settings.fetch("run_geogrid") == '1'):
			print("  4.a. Geogrid flag is set, preparing geogrid job.")
			jobs.run_geogrid()
			print("  4.a. Geogrid job Done")
		else:
			print("  4.a. Geogrid flag is not set, skipping step")
		print("  4.a. Done")
		print("  4.b. Running pre-processing executables")
		jobs.run_ungrib()
		if(jobs.run_metgrid() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True, cleanModelData = False)
			sys.exit("   4.b. ERROR: Metgrid.exe process failed to complete, check error file.")
		print("  4.b. Done")
		print("  4.c. Running WRF executables")
		if(jobs.run_real() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True, cleanModelData = False)
			sys.exit("   4.c. ERROR: real.exe process failed to complete, check error file.")	
		if(jobs.run_wrf() == False):
			#prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = False, cleanInFiles = True, cleanWRFOut = True, cleanModelData = False)
			sys.exit("   4.c. ERROR: wrf.exe process failed to complete, check error file.")	
		print("  4.c. Done")
		print(" 4. Done")
		#Step 5: Run postprocessing steps
		if(settings.fetch("run_postprocessing") == '1'):
			print(" 5. Running post-processing")
			post = Jobs.Postprocessing_Steps(settings, modelParms)
			print(" 5. Done")
		else:
			print(" 5. Post-processing flag disabled, skipping step")
		#Step 6: Cleanup
		print(" 6. Cleaning Temporary Files")
		prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = False, cleanModelData = True)
		print(" 6. Done")		
		#Done.
		print("All Steps Completed.")
		print("Program execution complete.")

# Run the program.
if __name__ == "__main__":
	pInst = Application()