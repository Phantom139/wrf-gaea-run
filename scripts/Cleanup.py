#!/usr/bin/python
# Cleanup.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains classes used to handle post script run cleaning

import sys
import os
from ApplicationSettings import *

class PostRunCleanup():
	sObj = None
	
	def __init__(self, settings):
		self.sObj = settings
		
	def performClean(self, cleanAll = True, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = True, cleanModelData = True):
		sTime = self.sObj.fetch("starttime")
		dataDir = self.sObj.fetch("datadir") + '/' + self.sObj.fetch("modeldata") + sTime
		wrfDir = self.sObj.fetch("wrfdir") + '/' + sTime[0:8]
		outDir = wrfDir + "/output"
		if(cleanAll == True):
			cleanOutFiles = True
			cleanErrorFiles = True
			cleanInFiles = True
			cleanWRFOut = True
			cleanModelData = True
		if(cleanOutFiles == True):
			os.system("rm " + wrfDir + "/geogrid.log.*")
			os.system("rm " + wrfDir + "/metgrid.log.*")
			os.system("rm " + wrfDir + "/ungrib.log*")
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
			os.system("rm " + wrfDir + "/GRIBFILE.*")
			os.system("rm " + wrfDir + "/3D:*")
			os.system("rm " + wrfDir + "/FLX:*")
			os.system("rm " + outDir + "/FILE:*")
			os.system("rm " + outDir + "/met_em*")
			os.system("rm " + outDir + "/wrfinput*")
			os.system("rm " + outDir + "/wrfbdy*")
			os.system("rm " + outDir + "/geo_em.d01.nc")
			os.system("rm " + outDir + "/aero*")
			os.system("rm " + outDir + "/bulk*")
			os.system("rm " + outDir + "/CAM*")
			os.system("rm " + outDir + "/capacity.asc")
			os.system("rm " + outDir + "/CCN*")
			os.system("rm " + outDir + "/CLM*")
			os.system("rm " + outDir + "/co2_trans")
			os.system("rm " + outDir + "/coeff*")
			os.system("rm " + outDir + "/constants.asc")
			os.system("rm " + outDir + "/create_p3_lookupTable_1.f90")
			os.system("rm " + outDir + "/ETA*")
			os.system("rm " + outDir + "/GEN*")
			os.system("rm " + outDir + "/grib*")
			os.system("rm " + outDir + "/kernels*")
			os.system("rm " + outDir + "/LANDUSE.TBL")
			os.system("rm " + outDir + "/masses.asc")
			os.system("rm " + outDir + "/MPTABLE.TBL")
			os.system("rm " + outDir + "/ozone*")
			os.system("rm " + outDir + "/p3_lookup_table_1.dat")
			os.system("rm " + outDir + "/RRTM*")
			os.system("rm " + outDir + "/RRTMG*")
			os.system("rm " + outDir + "/SOILPARM.TBL")
			os.system("rm " + outDir + "/termvels.asc")
			os.system("rm " + outDir + "/tr*")
			os.system("rm " + outDir + "/URB*")
			os.system("rm " + outDir + "/VEG*")
			os.system("rm " + outDir + "/wind-turbine-1.tbl")
			os.system("rm " + outDir + "/real.exe")
			os.system("rm " + outDir + "/tc.exe")
			os.system("rm " + outDir + "/wrf.exe")
		if(cleanWRFOut == True):
			os.system("rm " + outDir + "/wrfout*")
			os.system("rm " + outDir + "/wrfrst*")
		if(cleanModelData == True):
			os.system("rm -r " + dataDir)
		return None