# OpenHeartWare (OHW)
Open source software for the optical determination of cardiomyocyte contractility
developed at Loskill Group, Fraunhofer Institute for Interfacial Engineering and Biotechnology (IGB)

https://github.com/loslab/ohw


### Features 
Analyze your cardiomyocyte videos with OpenHeartWare! With our software, you can
* Load input data as series of tiff images or videofile (.mov/.avi)  
* Calculate motion vectors 
* Plot beating kinetics and detect peaks
* Create heatmap and quiver videos
* Create heatmaps of time averaged motion
* Analyze one video at a time or multiple videos via batch import

### Getting Started
#### Install OpenHeartWare
##### For Python Beginners: 
OpenHeartWare offers an easy installation process, also for inexperienced Python and Anaconda users. For detailed instructions, please read the provided user guide [User_Guide_to_OpenHeartWare.pdf]( User_Guide_to_OpenHeartWare.pdf). 
##### For experienced Python users:
* Download and install Anaconda using the Python 3 version from https://www.anaconda.com/download/ 
* Open the Anaconda prompt and create a new environment from OHW.yml file with 
    ```
    conda env create -f OHW.YML
    ```
For detailed instructions, please also read the provided user guide [User_Guide_to_OpenHeartWare.pdf]( User_Guide_to_OpenHeartWare.pdf)
After the successful installation, OpenHeartWare can be easily run by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat).
#### Test OpenHeartWare with Example Input
We provide exemplary input files in [sampleinput](sampleinput]). You can use the videofile and the tiff-series to check out the features of OpenHeartWare after the installation. Run OpenHeartWare by double-clicking on [run_OpenHeartWare.bat](run_OpenHeartWare.bat) and choose the videofile as input file.

### License
This project is licensed under a BSD 3-Clause license. See the [LICENSE.md](licence.md) file for details.
