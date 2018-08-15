#!/usr/bin/python
# run_wrf.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Python script to execute the wrf_gaea.py script with options

import scripts.Tools as Tools
import sys
import os
import datetime

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		#NOTE: If you're looking to automate (CRON) jobs, use this portion of the code to update control.txt
		
		#Run the script
		curTime = datetime.date.today().strftime("%B%d%Y-%H%M%S")
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		with Tools.cd(curDir + "/scripts/"):
			os.system("nohup Application.py > wrf_gaea_run_" + str(curTime) + ".log")
			mv("wrf_gaea_run_" + str(curTime) + ".log ../logs/")

if __name__ == "__main__":
	pInst = Application()