# OpenHeartWare (OHW)
Open source software for the optical determination of cardiomyocyte contractility
developed by Oliver Schneider & Carla Sailer at the Loskill Group, Fraunhofer Institute for Interfacial Engineering and Biotechnology (IGB)

https://github.com/loslab/ohw


### Features 
Analyze your cardiomyocyte videos with OpenHeartWare! With our software, you can
* Load input videos as .mov/.avi or a series of tiff images
* Calculate motion vectors 
* Plot beating kinetics and detect peaks
* Create heatmap- and quiver-videos highlighting the tissue motion
* Create heatmaps of the time averaged motion
* Automatically analyze multiple videos via the batch option

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

#### Test OpenHeartWare with Example Input
We provide exemplary input files in [sampleinput](sampleinput]). You can use the videofile and the tiff-series to check out the features of OpenHeartWare after the installation. Run OpenHeartWare by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat) and import the desired video.

### License
Please cite [Schneider et al. 2019](https://www.liebertpub.com/doi/abs/10.1089/ten.TEA.2019.0002) if you use OHW in your publication.

This project is licensed under a BSD 3-Clause license. See the [LICENSE.md](licence.md) file for details.