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

### Adding Model Sources ###
This script package was writted for the CFSv2 forecast system as an input for the WRF model, however the script package is dynamic enough to allow for quick additions of other model sources.



### Contact Info ###
Any questions regarding the script package can be sent to Robert C. Fritzen (rfritzen1@niu.edu). In-person questions can be done from my office in Davis Hall, room 202.