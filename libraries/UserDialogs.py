# -*- coding: utf-8 -*-

#UserDialogs.py
from PyQt5.QtWidgets import QFileDialog
import pathlib

def chooseFolderByUser(message, input_folder=''):
    #let the user choose a folder for saving 
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
