# -*- coding: utf-8 -*-

#UserDialogs.py
from PyQt5.QtWidgets import QFileDialog
import pathlib

def chooseFolderByUser(message, input_folder=None):
    #let the user choose a folder for saving 
    if input_folder==None:
        path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    else:
        path = str(input_folder)
    chosen_folder = QFileDialog.getExistingDirectory(None, message, path, QFileDialog.ShowDirsOnly)

    return chosen_folder

def chooseFileByUser(message, input_folder=None):
    #choose a file
    if input_folder==None:
        path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    else:
        path = str(input_folder)
    
    chosen_file = QFileDialog.getOpenFileName(None, message, path, "Video (*.avi *.mp4 *.mov *.tif)") #;;mp4 video (*.mp4);;mov vide (*.mov)
    return chosen_file

def chooseFilesByUser(message, input_folder=None):
    #choose multiple fileS
    if input_folder==None:
        path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    else:
        path = str(input_folder)
    
    chosen_files = QFileDialog.getOpenFileNames(None, message, path, "Video (*.avi *.mp4 *.mov *.tif)") #;;mp4 video (*.mp4);;mov vide (*.mov)
    return chosen_files