# WRF on Gaea @ NIU #
## Dpt. Geographic & Atmospheric Sciences ##
## By: Robert C. Fritzen ##

### Introduction ###
This python script package automates the entire WRF process for use on cluster based computers, such as the Gaea computer provided for use by the Computer Science department at Northern Illinois University. This is a fully self-contained script package that handles the tasks of obtaining the data, running the pre-processing executables, the WRF process, and forking the task to post-processing scripts for visualization.

### Contents ###
This git repository contains the following:
  * wrf_gaea.py: The primary script file containing the various methods used by the program
  * run_wrf.py: The primary run process which runs wrf_gaea.py in the background so execution via PuTTy can continue even after a session is disconnected
  * control.txt: A newline terminated text file that sets various parameters on the script (See below section on control.txt)
  * Vtable.CFSv2.*: The Vtable files needed by WRF for specific model data, in this case, the CFSv2 forecast system
  * Job Templates: The job template files which are used and written on by the script file, for the most part, these should be left alone unless specific clusters require different command calls or paramters
  * README.md: You're reading it!
  
Additionally, you will need to define a directory inside the repository directory called run_files, and place the following inside:
  * The WRF executables (wrf.exe, real.exe, tc.exe)
  * The WRF Run Files and Tables located in the /run/ folder of your WRF installation
  
### Control.txt ###
control.txt is a newline terminated text file which contains important parameters needed to run this script. The control.txt file MUST be located in the same directory as the wrf_gaea.py script file in order for the script to run. The format of this file is simple:

Each command line is split into two breaks:

**variable value**

EX: myvar 12

Would store the value of 12 in a parameter named myvar for the file. Any line that begins with a pound sign (#) is treated as a comment line. These variables are all defined in the AppSettings() class, but for simplicity, here is a list of the parameters accepted by control.txt

  * starttime: The initialization time for the first forecast hour, the format is YYYYMMDDHH
  * rundays: The number of days to run the model after initialization
  * runhours: The number of hours to run in addition to rundays (IE: total = 24*rundays + runhours)
  * geogdir: The path to the wrf_geog/ folder stored on your machine
  * tabledir: The path to your shared WRF tables folder stored on your machine
  * datadir: The path to where you want GRIB data to be stored, the full path is: datadir/model source/YYYYMMDDHH/
  * wrfdir: The path to where you want model runs to occur on your machine
  * wrfmodule: The name of the WRF module on your cluster (Added via module add wrfmodule)
  * modeldata: The data source used in this run (*See the section below on adding model sources if you want to use something other than CFSv2*)
  * run_geogrid: A 1/0 flag used to designate if the geogrid process needs to be run, if you are using the same grid space, run geogrid once and copy the resulting geo_em file to the run_files/ folder, then set the parameter to 0, otherwise geogrid will run.
  * num_geogrid_nodes: The number of CPU nodes to use in the geogrid process
  * num_geogrid_processors: The number of CPU processors to use in the geogrid process
  * geogrid_walltime: The maximum wall time to be required by the geogrid process
  * num_metgrid_nodes: The number of CPU nodes to use in the metgrid process
  * num_metgrid_processors: The number of CPU processors to use in the metgrid process
  * metgrid_walltime: The maximum wall time to be required by the metgrid process
  * num_real_nodes: The number of CPU nodes to use in the real.exe process
  * num_real_processors: The number of CPU processors to use in the real.exe process
  * real_walltime: The maximum wall time to be required by the real.exe process
  * num_wrf_nodes: The number of CPU nodes to use in the WRF process
  * num_wrf_processors: The number of CPU processors to use in the WRF process
  * wrf_walltime: The maximum wall time to be required by the WRF process  
  
### Adding Model Sources ###
This script package was writted for the CFSv2 forecast system as an input for the WRF model, however the script package is dynamic enough to allow for quick additions of other model sources.

First, you will need to obtain the VTable files for your specific model data source and include these in the directory.

Second, you'll need to add some basic model information to the *ModelDataParameters* class instance, located near the top of the wrf_gaea.py file. A dictionary is contained in this class with the following format:
```python
			"CFSv2": {
				"VTable": ["Vtable.CFSv2.3D", "Vtable.CFSv2.FLX"],
				"FileExtentions": ["3D", "FLX"],
				"FGExt": "\'3D\', \'FLX\'",
				"HourDelta": 6,
			},
```
The name of the dictionary instance should ideally be the model data source. *VTable* is a list instance containing all VTable files contained in the head folder used by this model data source. *FileExtentions* is a list of all file extensions used by the incoming GRIB data, for specific models (IE: CFSv2), multiple files are needed, hence this allows it. *FGExt* is a parameter applied by namelist.wps for the extensions of the ungribbed files used by the metgrid process, make this similar to the GRIB files. Finally *HourDelta* is the amount of hours separating each incoming GRIB file.

Next, scroll down to the *ModelData* class and find the pooled_download section. You will need to incorporate an additional if/elif clause for your new model that downloads the model data, here is a sample:

```python
		if(model == "CFSv2"):
			prs_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_pgbf/"
			flx_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_flxf/"
			strTime = str(self.startTime.strftime('%Y%m%d%H'))
			
			pgrb2link = prs_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/pgbf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
			sgrb2link = flx_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/flxf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
			pgrb2writ = self.dataDir + '/' + strTime + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
			sgrb2writ = self.dataDir + '/' + strTime + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
			if not os.path.isfile(pgrb2writ):
				os.system("wget " + pgrb2link + " -O " + pgrb2writ)
			if not os.path.isfile(sgrb2writ):
				os.system("wget " + sgrb2link + " -O " + sgrb2writ)	
```

Finally, change the modeldata parameter in control.txt to match your model source.
				
### Contact Info ###
Any questions regarding the script package can be sent to Robert C. Fritzen (rfritzen1@niu.edu). In-person questions can be done from my office in Davis Hall, room 202.