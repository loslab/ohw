# -*- coding: utf-8 -*-

import os, sys
import time
import pathlib
import glob
import cv2
import configparser
import copy
from datetime import datetime, timedelta
from matplotlib.lines import Line2D
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QMainWindow, QHeaderView, QCheckBox, QHBoxLayout, QLineEdit, QTableWidget, \
    QTableWidgetItem, QDoubleSpinBox, QStyle, QSlider, QSizePolicy, QAction, QTextEdit, QMessageBox, \
    QComboBox, QProgressBar, QSpinBox, QFileDialog, QTabWidget, QWidget, QLabel, QVBoxLayout, QGridLayout, \
    QPushButton, QApplication, QDesktopWidget, QDialogButtonBox, QListWidget, QAbstractItemView
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QImage
from PyQt5.QtCore import Qt, pyqtSignal
#from PyQt5 import QtGui
 
from ohw import MultipleFoldersByUser, UserDialogs, Filters, helpfunctions, QuiverExportOptions, plotfunctions, OHW
from ohw.gui import tab_analysis, tab_TA, tab_quiver, tab_batch, tab_kinetics

class TabWidgetMain(QWidget):
    def __init__(self, parent):   
        super(TabWidgetMain, self).__init__(parent)

        #read config file
        self.config = helpfunctions.read_config()
        self.cohw = OHW.create_analysis()
        
        self.layout = QGridLayout(self)
 
        self.tabs = QTabWidget() 
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        #self.plotted_peaks = False
        #self.tab_input = tab_input.TabInput(self)
        #self.tab_motion = tab_motion.TabMotion(self)
        self.tab_analysis = tab_analysis.TabAnalysis(self, self)
        self.tab_kinetics = tab_kinetics.TabKinetics(self, self) # TODO: rework, first self is parent, 2nd is controller
        self.tab_quiver = tab_quiver.TabQuiver(self, self)
        self.tab_TA = tab_TA.TabTA(self, self)
        self.tab_batch = tab_batch.TabBatch(self, self)
        
        #self.tabs.resize(800,800)
         
        self.tabs.currentChanged.connect(self.on_tabselection)
        
        # Add tabs
        self.tabs.addTab(self.tab_analysis,"Video analysis")
        self.tabs.addTab(self.tab_kinetics,"Beating kinetics")
        self.tabs.addTab(self.tab_quiver,"Heatmaps and Quiverplots")
        self.tabs.addTab(self.tab_TA,"Time averaged motion")
        self.tabs.addTab(self.tab_batch,"Batch analysis")
        
        #self.update_tabs() #not needed, init_ohw() called in each tab at initialization
        
        curr_date = datetime.now().date()   # move updatecheck into function
        last_check = datetime.strptime(self.config['UPDATE']['last_check'],"%Y-%m-%d").date()
        if curr_date > last_check + timedelta(days=1): #older than a day
            helpfunctions.check_update(self, self.config['UPDATE']['version'])# self needed for msgbox... get rid at some point?
            self.config['UPDATE']['last_check'] = str(curr_date)
            helpfunctions.save_config(self.config) # save curr_date back into config

        # default values for quiver export
        # self.config.getboolean(section='DEFAULT QUIVER SETTINGS', option='one_view')
        self.quiver_settings = {}# self.config['DEFAULT QUIVER SETTINGS']
        for item in ['one_view', 'three_views', 'show_scalebar']:
            self.quiver_settings[item] = self.config.getboolean(section='QUIVER OPTIONS', option=item)
         
        for item in ['quiver_density']:
            self.quiver_settings[item] = self.config.getint(section='QUIVER OPTIONS', option=item)
    
        for item in ['video_length']:
            self.quiver_settings[item] = self.config.getfloat(section='QUIVER OPTIONS', option=item)

    def close_Window(self):
        ''' 
            called by closing event
            save analysis on exit (MVs should be already automatically saved,
            peaks might have changed)
        '''
        self.cohw.save_ohw()

    def update_tabs(self):
        ''' sets update flags = True on tabs to update when clicked the next time'''
        for tab in [self.tab_analysis, self.tab_kinetics, self.tab_quiver, self.tab_TA]:
            tab.update = True
        
        #update current tab as user won't click it automatically
        idx = self.tabs.currentIndex()
        self.tabs.widget(idx).init_ohw()
        
    def on_tabselection(self, selection):
        ''' calls init_ohw on clicked tab -> inits depending on update flag '''
        self.tabs.widget(selection).init_ohw() 
        # todo: perhaps rename to update() as it does not have to be related to changes in cohw...