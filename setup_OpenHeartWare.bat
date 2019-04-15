@echo off
REM SET VARIABLES
SET anaconda_folder=C:\ProgramData\Anaconda3\Scripts\activate.bat

REM START THE SETUP
@echo on
call %anaconda_folder%
call conda env create -f OHW.yml
pause