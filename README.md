![OpenHeartWare-Logo](/icons/ohw-logo.png)

# OpenHeartWare (OHW)
Open source software for the optical determination of cardiomyocyte contractility
developed by Oliver Schneider & Carla Sailer at the Loskill Group, Fraunhofer Institute for Interfacial Engineering and Biotechnology (IGB)

https://github.com/loslab/ohw

### xx.xx.2021 new release v1.3.0

It took some time but we are finally releasing the next iteration of OHW. Check the update section on how to update to the recent version. Major improvements:
* allow the selection of regions of interest (rois)
* introduce the analysis of the integrated intensity in videos (useful e.g. for the analysis of Ca-signalling)
* restructure the gui
* introduce options to taylor the export of quiver videos
* resturcture the ohw class providing a more concise interface and separating pre-filtering and post-filtering parameters
* check out the doc section with an attempt to visualize the underlying class structure, a jupyter notebook displaying the class use and an API documentation made with pdoc

### 26.06.2019 new release v1.2.0

* allow saving of analysis as .pickle
* enable manual peak selection
* introduce checking for new releases
* restructure gui
* take care, the new changes are not implemented into the user guide yet

### Features 
Analyze your cardiomyocyte videos with OpenHeartWare! With our software, you can
* Load input videos as .mov/.avi/.mp4 or a series of tiff images
* Calculate motion vectors 
* Plot beating kinetics and detect peaks
* Create heatmap- and quiver-videos highlighting the tissue motion
* Create heatmaps of the time averaged motion
* Automatically analyze multiple videos via batch operation

### Install OpenHeartWare
##### For Python Beginners: 
OpenHeartWare offers an easy installation process for inexperienced Python users which have never worked with Python before. For detailed instructions, please read the provided user guide [User_Guide_to_OpenHeartWare.pdf]( User_Guide_to_OpenHeartWare.pdf). 
Briefly, you have to:
* Download and install Anaconda using the Python 3 version from https://www.anaconda.com/download/ 
* Download OpenHeartWare by the green "Clone or download" icon on the top right of this page and unpack the file in the folder of your choice
* Create a new Conda environment from the provided OHW.yml by
  * executing setup_OpenHeartWare.bat (with adjusting the filepath as mentioned in the user guide)
  OR
  * typing `conda env create -f OHW.yml` in the Anaconda prompt
* After successful installation, OpenHeartWare can be easily run by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat) (with adjusting the filepath as mentioned in the user guide). Running OpenHeartWare for the first time takes longer, as ffmpeg which is needed for exporting videos, is downloaded.

##### For experienced Python users:
* `git clone https://github.com/loslab/ohw.git`
* create new env from .yml or install the packages in the Python environment of your choice
* `python GUI_mainWindow.py`

#### Analyzing videos with OpenHeartWare:
OHW offers two modi for analyzing your videos:
* single mode: you can load one individual video and analyze it/ detect peaks/ export the graphs you want step by step.
* batch mode: you can create a list of inputvideos which will all be automatically processed the same way. However, you can still open your results (ohw_analysis.pickle) in single mode after analysis for further adjustments.
We provide exemplary input files in [sampleinput](sampleinput]). You can use the videofile and the tiff-series to check out the features of OpenHeartWare after the installation. 
Briefly, a video is analyzed in single mode as following:
* run OpenHeartWare by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat) and import the desired video.
* specify the framerate and video scale (Note: if you have many similar videos, you can adjust the standard values in the config.ini file)
* if you plan to export videos, you can adjust the brightness of your video for a better visual appearance
* a results folder is selected automatically, depending on the path of your videofile. However, you can also adjust the results folder to your own needs
* in the next tab you can adjust the parameter for motion analysis and start the analysis. In this tab you can also reload a previous analysis(ohw_analysis.pickle)
* when the analysis is done, the green bar indicates that the motion is calculated such that you can proceed to the next tabs. The analysis is now saved as ohw_analysis.pickle such that you can reload the analysis whenever you want without having to do the same calculation again 
* in the beating kinetics tab you see the 1D motion representation (avg. motion over time). You can manually add/ delete peaks by clicking into the graph or perform an automatic peak detection until all desired peaks are detected and export the graph and the obtained peakstatistics
* in the "Heatmaps and Quiverplots" tab you can investigate the detected motion frame by frame. You can save individual frames or export a whole video
* in the "Time averaged motion" tab you see and can save the averaged contractility as well as the contractility decomposed into x- and y-motion

### Update OpenHeartWare
With release v1.2.0 an automatic check for new releases during startup was introduced. Should a newer version be available, you will get notified by a popup-window. However, OpenHeartWare is not updated automatically. To replace your current version with the newest one you have to:
* Download OpenHeartWare by the green "Clone or download" icon on the top right of this page again and unpack the file in the folder of your choice (e.g. replacing the old folder)
* run update_OpenHeartWare.bat (with adjusting the filepath as mentioned in the user guide) to install possible new packages
* from now on, OpenHeartWare can be run again by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat) (with adjusting the filepath as mentioned in the user guide. You can of course replace it with the old run_OpenHeartWare.bat file where the path is already adjusted)

### Problems, questions, bugs, feedback and suggestions
We are happy about any feedback on OpenHeartWare. If you have problems setting up OpenHeartWare or can't analyze your data the way you want, don't hesitate to open an issue on github or contact us under oliver.schneider@igb.fraunhofer.de. The same goes for any bugs or additional features you would like to have implemented. We appreciate all input!

### License
Please cite [Schneider et al. 2019](https://www.liebertpub.com/doi/abs/10.1089/ten.TEA.2019.0002) if you use OHW in your publication.

This project is licensed under a BSD 3-Clause license. See the [LICENSE.md](licence.md) file for details.