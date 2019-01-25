@echo off
REM SET VARIABLES
SET anaconda_folder=C:\ProgramData\Anaconda3\Scripts\activate.bat

REM START THE APPLICATION
windir%\System32\cmd.exe "/K" 
@echo on
call "%anaconda_folder%"
call activate OHW
call python GUI_mainWindow.py
pause