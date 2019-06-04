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
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QMainWindow, QHeaderView, QCheckBox, QHBoxLayout, QLineEdit, QTableWidget, \
    QTableWidgetItem, QDoubleSpinBox, QStyle, QSlider, QSizePolicy, QAction, QTextEdit, QMessageBox, \
    QComboBox, QProgressBar, QSpinBox, QFileDialog, QTabWidget, QWidget, QLabel, QVBoxLayout, QGridLayout, \
    QPushButton, QApplication, QDesktopWidget, QDialogButtonBox, QListWidget, QAbstractItemView
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QImage
from PyQt5.QtCore import Qt, pyqtSignal
#from PyQt5 import QtGui
 
from libraries import MultipleFoldersByUser, UserDialogs, Filters, helpfunctions, QuiverExportOptions, plotfunctions, OHW
from libraries.gui import tab_input, tab_motion, tab_TA, tab_quiver, tab_batch, tab_kinetics

class TableWidget(QWidget):
        def __init__(self, parent):   
            super(QWidget, self).__init__(parent)

            #read config file
            self.config = helpfunctions.read_config()
            self.current_ohw = OHW.OHW()
            
            self.layout = QGridLayout(self)
 
            self.tabs = QTabWidget() 
            self.layout.addWidget(self.tabs)
            self.setLayout(self.layout)

            self.plotted_peaks = False
            
            self.tab_input = tab_input.TabInput(self)
            self.tab_motion = tab_motion.TabMotion(self)
            self.tab_kinetics = tab_kinetics.TabKinetics(self)
            self.tab_quiver = tab_quiver.TabQuiver(self)
            self.tab_TA = tab_TA.TabTA(self)
            self.tab_batch = tab_batch.TabBatch(self)
            self.tabROIs = QWidget()
            self.tabs.resize(800,800)
             
            # Add tabs
            self.tabs.addTab(self.tab_input,"Video Input ")
            #self.tabs.addTab(self.tabROIs, "Manage ROIs")
            self.tabs.addTab(self.tab_motion,"Compute motion")
            self.tabs.addTab(self.tab_kinetics,"Beating kinetics")
            self.tabs.addTab(self.tab_quiver,"Heatmaps and Quiverplots")
            self.tabs.addTab(self.tab_TA,"Time averaged motion")
            self.tabs.addTab(self.tab_batch,"Batch analysis")
            
            # replace with own init_ohw function which calls other init_ohws
            self.tab_motion.init_ohw()
            self.tab_kinetics.init_ohw()
            self.tab_quiver.init_ohw()
            self.tab_TA.init_ohw()
            
            #self.ROI_coordinates = []
            #self.ROI_names = []
            #self.ROI_OHWs = []
            
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
                self.quiver_settings[item] = self.config.getboolean(section='DEFAULT QUIVER SETTINGS', option=item)
             
            for item in ['quiver_density']:
                self.quiver_settings[item] = self.config.getint(section='DEFAULT QUIVER SETTINGS', option=item)
        
            for item in ['video_length']:
                self.quiver_settings[item] = self.config.getfloat(section='DEFAULT QUIVER SETTINGS', option=item)
            """
########### fill the ROI selection tab ###########
            info_ROI = QTextEdit()
            info_ROI.setText('In this tab you can add, edit and choose Regions of Interest.')
            info_ROI.setReadOnly(True)
            info_ROI.setMaximumHeight(40)
            info_ROI.setMaximumWidth(800)
            info_ROI.setStyleSheet("background-color: LightSkyBlue")
            
            #Button for ROI selection
            self.button_selectROI = QPushButton('Add a Region of Interest (ROI)')
            self.button_selectROI.resize(self.button_selectROI.sizeHint())
            self.button_selectROI.clicked.connect(self.on_selectROI)
            self.button_selectROI.setEnabled(False)

#            #add a table to display ROIs and corresponding names
#            self.ROI_tableWidget = QTableWidget()
#            self.ROI_tableWidget.setRowCount(2)
#            self.ROI_tableWidget.setColumnCount(2)
#            #titles
#            header = self.ROI_tableWidget.horizontalHeader()
#            header.setSectionResizeMode(QHeaderView.ResizeToContents)       
#            header.setSectionResizeMode(0, QHeaderView.Stretch)
#            
#            header_vert = self.ROI_tableWidget.verticalHeader()
#            header_vert.setSectionResizeMode(QHeaderView.ResizeToContents)
#            header_vert.setSectionResizeMode(0, QHeaderView.Stretch)
#            header_vert.setSectionResizeMode(1, QHeaderView.Stretch)
#            
             #set exemplary item 
            self.ROI = QLabel()
            self.ROI.setPixmap(QPixmap('icons/dummy_image.png').scaledToWidth(self.pixmap_width))
#            self.ROI_tableWidget.setItem(0,0,
#                                         QTableWidgetItem(QIcon(QPixmap('icons/dummy_image.png')), 'meee'))#.scaledToWidth(self.pixmap_width)),
#                                                   #       'meeee')           
            self.fig_ROI, self.ax_ROI = plt.subplots(1,1)
            self.ax_ROI.axis('off')
            self.canvas_ROI = FigureCanvas(self.fig_ROI)            
            
            #dict for ROIs 
            #save ROI names and corresponding OHWs!
            self.ROI_Management = {}
            self.ROIManagement_title = QLabel('Currently available ROIs:')
            self.ROIManagement_title.setFont(QFont("Times",weight=QFont.Bold))
        
            self.tabROIs.layout = QGridLayout(self)
            self.tabROIs.layout.setSpacing(25)
            self.tabROIs.layout.addWidget(info_ROI,                     0,0)
            self.tabROIs.layout.addWidget(self.button_selectROI,        1,0)
            self.tabROIs.layout.addWidget(self.ROIManagement_title,     2,0)
            self.tabROIs.layout.addWidget(QLineEdit('Example ROI'),     3,0)
            self.tabROIs.layout.addWidget(self.ROI,                     3,1)
            self.tabROIs.setLayout(self.tabROIs.layout)
            """

###############################################################################
        def change_ROI_names(self, ROI_nr):
            """ 
                emitted when name of one of the ROIs is changed by the user in one of the lineedits
                Parameters: 
                ROI_nr      index of the ROI
            """
            #get the new name from the LineEdit which send the signal
            new_name = self.sender().text()
            self.ROI_names[ROI_nr] = new_name
            
            #change the resultsfolder name in the corresponding ROI_OHW
            self.ROI_OHWs[ROI_nr].results_folder = self.current_ohw.results_folder.joinpath(self.ROI_names[ROI_nr])
            
            #change the items in all the comboboxes, first item is the full image 
            self.ekg_combobox.setItemText(ROI_nr+1,         new_name)
            self.advanced_combobox.setItemText(ROI_nr+1,    new_name)
            self.timeavg_combobox.setItemText(ROI_nr+1,     new_name)
            
        def on_chooseROI(self, current_index):
            """ choose a ROI for displaying and analyzing results in beating_kinetics, heatmaps and quiverplots
            """
            if current_index == 0:
                self.current_ohw = self.current_ohw
            #self.current_ROI is specified as ROI_nr, index in self.ROI_OHWs!
            else:
                self.current_ROI_idx = current_index-1
                self.current_ohw = self.ROI_OHWs[self.current_ROI_idx]
                print(self.ROI_names[self.current_ROI_idx])
            
            if self.sender() == self.ekg_combobox:
                self.current_ohw.initialize_calculatedMVs()
                self.initialize_kinetics()
            
            elif self.sender() == self.advanced_combobox:
                self.initialize_MV_graphs()
                self.button_succeed_heatmaps.setStyleSheet("background-color: IndianRed")
                self.button_succeed_quivers.setStyleSheet("background-color: IndianRed")
                self.progressbar_heatmaps.setValue(0)
                self.progressbar_quivers.setValue(0)
            
            #elif self.sender() == self.timeavg_combobox:
            #    self.init_TAMotion()
                
        def on_selectROI(self):
            """ select a ROI from the first image of the rawImageStack, calculation of MVs will be performed on ROI only after this 
            """
            widget_height = self.frameSize().height()
            
            #take the first image of rawImageStack and scale to fit on display
            img = cv2.cvtColor(self.current_ohw.rawImageStack[0], cv2.COLOR_GRAY2RGB)      
            hpercent = (widget_height / float(img.shape[1]))
            wsize = int((float(img.shape[0]) * float(hpercent)))
            image_scaled = cv2.resize(img, (wsize, widget_height))
            
            #convert to uint8 if needed
            if img.dtype != 'uint8':
                image_norm = image_scaled
                image_norm = cv2.normalize(image_scaled, image_norm, 0, 1, cv2.NORM_MINMAX)*255
                image_scaled = image_norm.astype(np.uint8)
                   
            #open the ROI selection
            r = cv2.selectROI('Press Enter to save the currently selected ROI:', image_scaled, fromCenter=False)
            
            #transform the coordinates back to match the image of original size
            r_transf = [r[idx]/hpercent for idx in range(0,len(r))]
            
            #add the new ROI to the OHWs, the ROI_names
            new_nr = len(self.ROI_names) + 1 
            new_name = 'ROI_{}'.format(new_nr)
            self.ROI_names.append(new_name)
            self.ekg_combobox.addItem(new_name)
            self.advanced_combobox.addItem(new_name) 
            self.timeavg_combobox.addItem(new_name)
            
            #create new OHW
            self.manageROIs(r_transf)
            cv2.destroyAllWindows()
            
            self.check_scaling.setEnabled(False)
            self.scaling_status = False
            self.check_scaling.setEnabled(False)
            self.scaling_status = False
        
        def manageROIs(self, r):
            """
            Parameters:     
                r       coordinates returned by cv2.selectROI
            """
            self.ROI_coordinates.append(r)
          
            self.ROI_OHWs = []
            for nr_ROI in range(0, len(self.ROI_coordinates)):
                #create new OHW object for each ROI
                current_ROI_OHW = copy.deepcopy(self.current_ohw)
                #create new subfolder for storing ROI analysis
                current_ROI_OHW.results_folder = self.current_ohw.results_folder.joinpath(self.ROI_names[nr_ROI])
                #mark as ROI_OHW
                current_ROI_OHW.isROI_OHW = True
                current_ROI_OHW.createROIImageStack(self.ROI_coordinates[nr_ROI])
                                
                #display ROI in tab
                current_row = 3 + nr_ROI#len(self.ROI_coordinates)
                self.display_ROI(current_ROI_OHW.ROIImageStack[0], nr_ROI, current_row)
            
                #add OHW to list of all ROI OHWs
                self.ROI_OHWs.append(current_ROI_OHW)
 
        def perform_batchAnalysis(self, progressSignal=None):
             #number of signals to be emitted  
            self.maxNumberSignals = self.getMaximumSignals_batch()
            
            #internal counter of current batch signals
            self.count_batch_signals = 0               

            print('Current folders for batch analysis:')
            print(self.batch_folders)
            
            for folder in self.batch_folders:
               
                print('Start Analysis for folder %s:' %folder)
            #### perform analysis for one folder:
                current_ohw = OHW.OHW()
                
                # create a subfolder for the results 
               # save_subfolder = self.results_folder_batch / folder.split('/')[-1]
                save_subfolder = str(pathlib.PureWindowsPath(self.results_folder_batch)) + '/' + folder.split('/')[-1] #+ '/results'
                if not os.path.exists(str(save_subfolder)):
                    os.makedirs(str(save_subfolder))
                current_ohw.results_folder = save_subfolder

                # read data
                current_ohw.read_imagestack(folder)
                print('    ... finished reading data.')
                #progress signal for finishing reading data
                if progressSignal != None:
                    self.count_batch_signals += 1
                    progressSignal.emit(self.count_batch_signals/self.maxNumberSignals)
                    
                # scale data if desired
                if self.batch_scaling_status == True:
                    current_ohw.scale_ImageStack()
                else:
                  #  current_ohw.scale_ImageStack(current_ohw.rawImageStack.shape[0][1])   # too hacky, refactor...
                    if current_ohw.ROIImageStack is not None:
                        current_ohw.scale_ImageStack(current_ohw.ROIImageStack.shape[1], current_ohw.ROIImageStack[2])
                    else: 
                        current_ohw.scale_ImageStack(current_ohw.rawImageStack.shape[1], current_ohw.rawImageStack[2])     
                # calculate MVs
                current_ohw.calculate_MVs(blockwidth=self.blockwidth_batch, delay=self.delay_batch, max_shift=self.maxShift_batch)
                print('    ... finished calculating motion vectors.')
                #progress signal for finishing calc MVs
                if progressSignal != None:
                    self.count_batch_signals += 1
                    progressSignal.emit(self.count_batch_signals/self.maxNumberSignals)
             
                # plot beating kinetics
                current_filename = str(save_subfolder) +'/' + 'beating_kinetics.png'
                current_ohw.plot_beatingKinetics(filename=current_filename, keyword='batch')
                print('    ... finished plotting beating kinetics.')
                
                # create heatmap video if chosen by user
                if self.batch_heatmap_status == True:
                    current_ohw.save_heatmap(subfolder=pathlib.Path(save_subfolder), keyword='batch')
                    print('    ... finished saving heatmaps.')
                #progress signal for finishing heatmap data
                    if progressSignal != None:
                        self.count_batch_signals += 1
                        progressSignal.emit(self.count_batch_signals/self.maxNumberSignals)

                # create quiver video if chosen by user
                if self.batch_quiver_status == True:
                    current_ohw.save_quiver(subfolder=pathlib.Path(save_subfolder), keyword='batch')
                    print('    ... finished saving quivers.')
                    #progress signal for finishing quiver data
                    if progressSignal != None:
                        self.count_batch_signals += 1
                        progressSignal.emit(self.count_batch_signals/self.maxNumberSignals)
                    
        def display_ROI(self, ROI, ROI_nr, row):
            fig_ROI, ax_ROI = plt.subplots(1,1)
            ax_ROI.axis('off')
            canvas_ROI = FigureCanvas(fig_ROI)   
            
            #create frame
            frame = patches.Rectangle((0,0),ROI.shape[1],ROI.shape[0],linewidth=2,edgecolor='k',facecolor='none')
            # Add the patch to the Axes
            ax_ROI.add_patch(frame)
            
            # canvas_ROI.drawRectangle([0,0, ROI.shape[1], ROI.shape[0]])
            imshow_ROI = ax_ROI.imshow(ROI, cmap = 'gray', vmin = self.current_ohw.videometa["Blackval"], vmax = self.current_ohw.videometa["Whiteval"])

#            #adapt size
#            fig_size = plt.rcParams["figure.figsize"]
#            ratio = fig_size[1]/fig_size[0]
#            #change height
#            fig_size[1] = 4
#            fig_size[0] = fig_size[1] * ratio
    
            canvas_ROI.draw()           
            current_lineedit = QLineEdit()
            current_lineedit.setText(self.ROI_names[ROI_nr])
            #if text is changed by user, save it to ROI_names:
            current_lineedit.textEdited.connect(lambda: self.change_ROI_names(ROI_nr=ROI_nr))
            self.tabROIs.layout.addWidget(current_lineedit, row, 0)
            self.tabROIs.layout.addWidget(canvas_ROI,row,1) 
            
        def init_ohw(self):
            ''' init tabs to changed ohw '''
            
            self.tab_input.init_ohw()
            self.tab_motion.init_ohw()
            self.tab_kinetics.init_ohw()
            self.tab_TA.init_ohw()
            self.tab_quiver.init_ohw()

        def init_quivers(self):
            pass
            '''
            if not self.current_ohw.isROI_OHW:
                if self.quiver_settings['show_scalebar']:
                    #only draw scalebar if it is the full image and if specified in the quiver settings
                    self.current_ohw.plot_scalebar()  
                else:
                    #remove scalebar by recalculating the scaled imagestack
                    self.current_ohw.scale_ImageStack(self.current_ohw.rawImageStack.shape[1], self.current_ohw.rawImageStack.shape[2])
            '''
        
        def on_change_quiverSettings(self):
            #calculate maximum video length
          #  del self.quiver_settings['video_length']
            self.quiver_settings['video_length'] = str(
                1/self.current_ohw.videometa["fps"] * self.current_ohw.absMotions.shape[0])

            # open new window and let user change export settings
            self.settingsWindow = QuiverExportOptions.QuiverExportOptions(prevSettings = self.quiver_settings)
            self.settingsWindow.table_widget.got_settings.connect(self.save_quiver_settings)
            self.settingsWindow.show()
            
        def save_quiver_settings(self, settings):
            ''' receive the signals from quiver settings changed by user '''
            self.quiver_settings = settings
            
            #save quiver settings to config.ini:
            #convert to string suitable for configparser
            for item in ['one_view', 'three_views', 'show_scalebar']:
                self.config.set("DEFAULT QUIVER SETTINGS", option=item, value=str(self.quiver_settings[item]).lower())
            for item in ['quiver_density', 'video_length']:
                self.config.set("DEFAULT QUIVER SETTINGS", option=item, value=str(self.quiver_settings[item]))
            
            helpfunctions.save_config(self.config)
            
            self.settingsWindow.close()       
            #initialize MV_graphs again
            #self.initialize_MV_graphs()