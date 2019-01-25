# -*- coding: utf-8 -*-

#UserDialogs.py
from PyQt5.QtWidgets import QFileDialog
import pathlib

def chooseFolderByUser(message, input_folder=''):
     #let the user choose a folder for saving
     
#TODO: uncomment before commit to GIT     
#     if (input_folder != ''): 
#         #create a new folder for saving:
#         newfolder_name = (str(datetime.now())).replace(" ","_")[:-7].replace(":", ".") 
#         path_newFolder = input_folder + '/results_' + newfolder_name
#         pathlib.Path(str(path_newFolder)).mkdir(parents=True, exist_ok=True)
#         
#         #define starting path for UserDialog
#         path = str((pathlib.Path(path_newFolder)).resolve())
#         
#     else:
#         #define starting path for UserDialog
#         path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    if input_folder=='':
        path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    else:
        path = input_folder 
    chosen_folder = QFileDialog.getExistingDirectory(None, message, path, QFileDialog.ShowDirsOnly)

    return chosen_folder

def chooseFileByUser(message, input_folder=''):
    #choose a file
    if input_folder=='':
        path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    else:
        path = input_folder
    
    chosen_file = QFileDialog.getOpenFileName(None, message, path, "Video (*.avi *.mp4 *.mov)") #;;mp4 video (*.mp4);;mov vide (*.mov)
    return chosen_file
