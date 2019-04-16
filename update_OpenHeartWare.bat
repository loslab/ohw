@echo off
REM SET VARIABLES
SET anaconda_folder=C:\ProgramData\Anaconda3\Scripts\activate.bat

REM UPDATE THE APPLICATION
windir%\System32\cmd.exe "/K" 
@echo on
call "%anaconda_folder%"
call conda env update -f=ohw.yml
pause