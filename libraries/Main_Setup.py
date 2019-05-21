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
from libraries.gui import tab_input, tab_motion, tab_TA, tab_quiver, tab_batch

class TableWidget(QWidget):
        def __init__(self, parent):   
            super(QWidget, self).__init__(parent)

            #read config file
            self.config = helpfunctions.read_config()
            self.current_ohw = OHW.OHW()
            
            self.layout = QGridLayout(self)
 
            # Initialize tab screen
            self.tabs = QTabWidget()
            # Add tabs to widget        
            self.layout.addWidget(self.tabs)
            self.setLayout(self.layout)
            #settings for tabs
            #place tabs at the left side of the GUI:
            #self.tabs.setTabPosition(QTabWidget.West)

            self.plotted_peaks = False
            
            self.tab_input = tab_input.TabInput(self)
            self.tab_motion = tab_motion.TabMotion(self)
            self.tab3 = QWidget()
            self.tab_quiver = tab_quiver.TabQuiver(self)
            self.tab_TA = tab_TA.TabTA(self)
            self.tab_batch = tab_batch.TabBatch(self)
            self.tabROIs = QWidget()
            self.tabs.resize(800,800)
             
            # Add tabs
            self.tabs.addTab(self.tab_input,"Video Input ")
            #self.tabs.addTab(self.tabROIs, "Manage ROIs")
            self.tabs.addTab(self.tab_motion,"Compute motion")
            self.tabs.addTab(self.tab3,"Beating kinetics")
            self.tabs.addTab(self.tab_quiver,"Heatmaps and Quiverplots")
            self.tabs.addTab(self.tab_TA,"Time averaged motion")
            self.tabs.addTab(self.tab_batch,"Batch analysis")
            
            self.tab_TA.init_ohw()
            
            color_for_info = QColor(198, 255, 26)
            self.pixmap_width = 250
            self.ROI_coordinates = []
            self.ROI_names = []
            self.ROI_OHWs = []
            
            curr_date = datetime.now().date()
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

########### fill the third tab ##################
            info_analysisBasic = QTextEdit()
            info_analysisBasic.setText('In this tab you can plot the motion as an EKG and calculate statistics based on the found peaks. Change the parameters manually to optimize the peak detection. You can save the graphs and export the peaks.')
            info_analysisBasic.setReadOnly(True)
            info_analysisBasic.setMaximumHeight(40)
            info_analysisBasic.setMaximumWidth(800)
            info_analysisBasic.setStyleSheet("background-color: LightSkyBlue")
            
            #create a label for choosing the ROI
            label_ekg_choose_ROI = QLabel('Choose the ROI to be displayed: ')
            label_ekg_choose_ROI.setFont(QFont("Times",weight=QFont.Bold))
            
            #create a drop-down menu for choosing the ROI to be displayed
            self.ekg_combobox = QComboBox()
            self.ekg_combobox.addItem('Full image')    
            #self.ekg_combobox.activated[str].connect(self.on_chooseROI)
            self.ekg_combobox.currentIndexChanged[int].connect(self.on_chooseROI)
            
            label_results = QLabel('Results: ')
            label_results.setFont(QFont("Times",weight=QFont.Bold))

            self.fig_kinetics, self.ax_kinetics = plt.subplots(1,1)
            self.fig_kinetics.set_size_inches(16,12)
            self.canvas_kinetics = FigureCanvas(self.fig_kinetics)           
            
            #spinboxes to choose for manual detection
            label_ratio = QLabel('Ratio of peaks: ')           
            self.spinbox_ratio = QDoubleSpinBox()
            self.spinbox_ratio.setRange(0.01, 0.90)
            self.spinbox_ratio.setSingleStep(0.01)
            self.spinbox_ratio.setValue(0.05)           
            
            label_neighbours = QLabel('Number of neighbouring values for evaluation:') 
            self.spinbox_neighbours = QSpinBox()    
            self.spinbox_neighbours.setRange(2,10)
            self.spinbox_neighbours.setSingleStep(2)
            self.spinbox_neighbours.setValue(4)
            
            #create labels for the statistics
            label_max_contraction = QLabel('Detected maximum contraction: ')
            label_max_relaxation = QLabel('Detected maximum relaxation: ')
            label_time_contraction = QLabel('Mean contraction interval: ')
            label_time_relaxation = QLabel('Mean relaxation interval: ')
            label_time_contr_relax = QLabel('Mean interval between contraction and relaxation: ')
            label_bpm = QLabel('Heart rate: ')
            
            self.label_max_contraction_result = QLabel('... needs to be calculated ...')            
            self.label_max_relaxation_result = QLabel('... needs to be calculated ...')
            self.label_time_contraction_result = QLabel('... needs to be calculated ...')
            self.label_time_relaxation_result = QLabel('... needs to be calculated ...')
            self.label_time_contr_relax_result = QLabel('... needs to be calculated ...')
            self.label_bpm_result = QLabel('... needs to be calculated ...')
            
            label_furtherAnalysis = QLabel('Further options:')
            label_furtherAnalysis.setFont(QFont("Times",weight=QFont.Bold))
            
            label_evaluate = QLabel('Start evaluation')
            label_evaluate.setFont(QFont("Times",weight=QFont.Bold))
            
            self.button_detectPeaks = QPushButton('Start peak detection')
            self.button_saveKinetics = QPushButton('Save current EKG graph as ...')
            self.button_export_peaks = QPushButton('Save raw and analyzed peaks ')
            self.button_export_ekg_csv = QPushButton('Save EKG as excel file (.xlsx)')
            self.button_export_statistics = QPushButton('Save statistical analysis ')
            
            self.button_detectPeaks.resize(self.button_detectPeaks.sizeHint())
            self.button_saveKinetics.resize(self.button_saveKinetics.sizeHint())
            self.button_export_peaks.resize(self.button_export_peaks.sizeHint())
            self.button_export_ekg_csv.resize(self.button_export_ekg_csv.sizeHint())
            self.button_export_statistics.resize(self.button_export_statistics.sizeHint())
            self.button_saveKinetics.setEnabled(False)
            self.button_export_peaks.setEnabled(False)
            self.button_export_ekg_csv.setEnabled(False)
            self.button_export_statistics.setEnabled(False)
            self.button_detectPeaks.setEnabled(False)
            
            self.button_detectPeaks.clicked.connect(self.on_detectPeaks)            
            self.button_saveKinetics.clicked.connect(self.on_saveKinetics)
            self.button_export_peaks.clicked.connect(self.on_exportPeaks)
            self.button_export_ekg_csv.clicked.connect(self.on_exportEKG_CSV)
            self.button_export_statistics.clicked.connect(self.on_exportStatistics)
                      
            self.tab3.layout = QGridLayout(self)
            self.tab3.layout.addWidget(info_analysisBasic,      0,0)
            self.tab3.layout.addWidget(label_ekg_choose_ROI,    1,0)
            self.tab3.layout.addWidget(self.ekg_combobox,       2,0)
            self.tab3.layout.addWidget(label_results,           3,0)
            self.tab3.layout.addWidget(label_ratio,             4,0)
            self.tab3.layout.addWidget(self.spinbox_ratio,      4,1)
            self.tab3.layout.addWidget(label_neighbours,        5,0)
            self.tab3.layout.addWidget(self.spinbox_neighbours, 5,1)
            self.tab3.layout.addWidget(self.button_detectPeaks, 6,0)
            self.tab3.layout.addWidget(self.canvas_kinetics,    7,0)
            self.tab3.layout.addWidget(label_max_contraction,   8,0)
            self.tab3.layout.addWidget(self.label_max_contraction_result, 8,1)
            self.tab3.layout.addWidget(label_max_relaxation,    9,0)
            self.tab3.layout.addWidget(self.label_max_relaxation_result, 9,1)
            self.tab3.layout.addWidget(label_time_contraction,  10,0)
            self.tab3.layout.addWidget(self.label_time_contraction_result, 10,1)
            self.tab3.layout.addWidget(label_time_relaxation,   11,0)            
            self.tab3.layout.addWidget(self.label_time_relaxation_result, 11,1)
            self.tab3.layout.addWidget(label_time_contr_relax,  12,0)
            self.tab3.layout.addWidget(self.label_time_contr_relax_result, 12,1)
            self.tab3.layout.addWidget(label_bpm,               13,0)
            self.tab3.layout.addWidget(self.label_bpm_result,   13,1)
            self.tab3.layout.addWidget(label_furtherAnalysis,   14,0)
            self.tab3.layout.addWidget(self.button_export_ekg_csv, 15,0)
            self.tab3.layout.addWidget(self.button_saveKinetics,16,0)
            self.tab3.layout.addWidget(self.button_export_peaks,17,0)
            self.tab3.layout.addWidget(self.button_export_statistics, 18,0)
            self.tab3.setLayout(self.tab3.layout)

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
                      
        def on_loadVideo(self):
            self.tab_input.progressbar_loadVideo.setValue(0)
            
            #choose a folder
            msg = 'Choose an input video: file of type .mp4, .avi, .mov or a .tif file in a folder containing a sequence of .tif-images'
            try:
                fileName  = UserDialogs.chooseFileByUser(message=msg, input_folder=self.config['LAST SESSION']['input_folder'])  
            except Exception:
                fileName  = UserDialogs.chooseFileByUser(message=msg)
            
            print(fileName)
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (fileName[0]  == ''):
                return
            try:
                inputpath = pathlib.Path(fileName[0])
                #save changes to config file
                self.config.set("LAST SESSION", "input_folder", str((inputpath / "..").resolve()))#easier with parent?
                helpfunctions.save_config(self.config)
                
                # create OHW object to work with motion vectors
                self.current_ohw = OHW.OHW()
                
                #read imagestack
                self.import_video_thread = self.current_ohw.import_video_thread(inputpath)
                self.import_video_thread.start()
                self.tab_input.progressbar_loadVideo.setRange(0,0)
                self.import_video_thread.finished.connect(self.finish_loadVideo)
            except Exception:
                pass 
                
        def finish_loadVideo(self):
            self.tab_input.progressbar_loadVideo.setRange(0,1)
            self.tab_input.progressbar_loadVideo.setValue(1)

            self.update_tab_input()  #update videoinfos with data from current_ohw
            self.tab_quiver.init_ohw()
            self.tab_TA.init_ohw()
            #self.button_selectROI.setEnabled(True) 
            
        def on_reloadVideo(self):
            """
                reloads video files into current_ohw
                e.g. when analysis file is opened
            """
            self.tab_input.progressbar_loadVideo.setValue(0)            
            self.reload_video_thread = self.current_ohw.reload_video_thread()
            self.reload_video_thread.start()
            self.tab_input.progressbar_loadVideo.setRange(0,0)
            self.reload_video_thread.finished.connect(self.finish_reloadVideo)
        
        def finish_reloadVideo(self):
            self.tab_input.progressbar_loadVideo.setRange(0,1)
            self.tab_input.progressbar_loadVideo.setValue(1)
            self.update_tab_input()
            self.current_ohw.set_analysisImageStack(px_longest = self.current_ohw.analysis_meta["px_longest"])
            self.tab_quiver.init_ohw()
            self.tab_TA.init_ohw()
            
        def on_changeResultsfolder(self):
            #choose a folder
            msg = 'Choose a new folder for saving your results'
            folderName = UserDialogs.chooseFolderByUser(msg, input_folder=self.current_ohw.analysis_meta['results_folder'])#, input_folder=self.config['LAST SESSION']['results_folder'])  
            
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (folderName == ''):
                return
            
            self.current_ohw.analysis_meta["results_folder"] = pathlib.Path(folderName)
            self.tab_input.label_results_folder.setText(folderName)
            # fix for batch and rois!
            '''
            if self.sender() == self.tab_input.btn_results_folder:
                #change the results folder of the OHW class
                self.current_ohw.results_folder = pathlib.Path(folderName)
                
                #change the results folder for all OHW
                if len(self.ROI_OHWs) is not 0:
                    for ROI_nr in range(0,len(self.ROI_OHWs)):
                        self.ROI_OHWs[ROI_nr].results_folder = pathlib.Path(folderName).joinpath(self.ROI_names[ROI_nr])
                #display
                current_folder = 'Current results folder: ' + str(pathlib.PureWindowsPath(self.current_ohw.results_folder))
                self.tab_input.label_results_folder.setText(current_folder)
                

            elif self.sender() == self.button_batch_resultsfolder:
                #change the batch results folder!
                self.results_folder_batch = pathlib.Path(folderName)
                
                #display new results folder
                current_folder = 'Current results folder: ' + str(pathlib.PureWindowsPath(self.results_folder_batch))
                self.tab_input.label_results_folder_batch.setText(current_folder)
            '''    
            print('New results folder: %s' %folderName)            
            
        def display_firstImage(self, image = None):
            self.tab_input.ax_firstIm.clear()
            self.tab_input.ax_firstIm.axis('off')
            # display first image and update controls
            if type(image) == np.ndarray:
                print(self.current_ohw.videometa["Blackval"], self.current_ohw.videometa["Whiteval"])
                self.imshow_firstImage = self.tab_input.ax_firstIm.imshow(image, cmap = 'gray', vmin = self.current_ohw.videometa["Blackval"], vmax = self.current_ohw.videometa["Whiteval"])
            else:
                self.tab_input.ax_firstIm.text(0.5, 0.5,'no video loaded yet',
                    size=14, ha='center', va='center', backgroundcolor='indianred', color='w')
            self.tab_input.canvas_firstImage.draw()
        
        def update_brightness(self):
            vmin, vmax = self.current_ohw.videometa["Blackval"], self.current_ohw.videometa["Whiteval"]
            self.imshow_firstImage.set_clim(vmin=vmin, vmax=vmax)
            self.tab_input.canvas_firstImage.draw()
            
            if (self.current_ohw.video_loaded and self.current_ohw.analysis_meta["has_MVs"]):
                self.tab_quiver.updateQuiverBrightness(vmin=vmin, vmax=vmax)
        
        def on_change_blackVal(self):          
            """
                change the white values for image display
                using a slider with 2 handles would be easiest option...
            """
         
            # save the new value to videometa
            self.current_ohw.videometa["Blackval"] = self.tab_input.slider_blackval.value()

            # set allowed whitevals and blackvals           
            self.tab_input.slider_whiteval.setMinimum(self.current_ohw.videometa["Blackval"])            
            self.update_brightness()

        def on_change_whiteVal(self):          
            """
                change the white values for image display
            """
            # save the new value to videometa
            self.current_ohw.videometa["Whiteval"] = self.tab_input.slider_whiteval.value()

            # set allowed whitevals and blackvals           
            self.tab_input.slider_blackval.setMaximum(self.current_ohw.videometa["Whiteval"])            
            self.update_brightness()

        def on_resetBrightness(self):
            """ resets the image display back to the original values
            """
            self.current_ohw.videometa["Blackval"] = self.current_ohw.raw_videometa["Blackval"]
            self.current_ohw.videometa["Whiteval"] = self.current_ohw.raw_videometa["Whiteval"]
            
            self.set_start_brightness()
            self.update_brightness()
            
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
          
        def on_detectPeaks(self):
            #detect peaks and draw them as EKG
            
            ratio = self.spinbox_ratio.value()
            number_of_neighbours = self.spinbox_neighbours.value()
            self.current_ohw.detect_peaks(ratio, number_of_neighbours)
            self.updatePeaks()

        def updatePeaks(self):
            """
                update detected peaks in graph
            """
            
            Peaks = self.current_ohw.get_peaks()     
            
            # clear old peaks first
            if self.plotted_peaks == True:
                self.highpeaks.remove()
                self.lowpeaks.remove()
                self.plotted_peaks = False
            
            if type(Peaks["t_peaks_low_sorted"]) == np.ndarray:
                # plot peaks, low peaks are marked as triangles , high peaks are marked as circles         
                self.highpeaks, = self.ax_kinetics.plot(Peaks["t_peaks_low_sorted"], Peaks["peaks_low_sorted"], marker='o', ls="", ms=5, color='r' )
                self.lowpeaks, = self.ax_kinetics.plot(Peaks["t_peaks_high_sorted"], Peaks["peaks_high_sorted"], marker='^', ls="", ms=5, color='r' )       
                self.plotted_peaks = True
                
            self.canvas_kinetics.draw()

            peakstatistics = self.current_ohw.get_peakstatistics()
            peaktime_intervals = self.current_ohw.get_peaktime_intervals()
            bpm = self.current_ohw.get_bpm()
            
            try:
                #display statistics
                text_contraction = str(peakstatistics["max_contraction"]) + ' +- '+ str(peakstatistics["max_contraction"]) +  u' \xb5m/sec'
                text_relaxation = str(peakstatistics["max_relaxation"]) + ' +- '+ str(peakstatistics["max_relaxation_std"]) +  u' \xb5m/sec'
                text_time_contraction = str(peaktime_intervals["contraction_interval_mean"]) + ' +- ' + str(peaktime_intervals["contraction_interval_std"]) + ' sec'
                text_time_relaxation = str(peaktime_intervals["relaxation_interval_mean"]) + ' +- ' + str(peaktime_intervals["relaxation_interval_std"]) + ' sec'
                text_time_contr_relax = str(peaktime_intervals["contr_relax_interval_mean"]) + ' +- ' + str(peaktime_intervals["contr_relax_interval_std"]) + ' sec'
                text_bpm = str(bpm["bpm_mean"]) + ' +- ' + str(bpm["bpm_std"]) + ' beats/min'
            
            except (NameError, AttributeError):
                return
            
            self.label_max_contraction_result.setText(text_contraction)
            self.label_max_relaxation_result.setText(text_relaxation)
            self.label_time_contraction_result.setText(text_time_contraction)
            self.label_time_relaxation_result.setText(text_time_relaxation)
            self.label_time_contr_relax_result.setText(text_time_contr_relax)
            self.label_bpm_result.setText(text_bpm)
            
            #enable saving of peaks and statistics
            self.button_export_peaks.setEnabled(True)
            self.button_export_ekg_csv.setEnabled(True)
            self.button_export_statistics.setEnabled(True)
            
        def on_exportPeaks(self):
            
            self.current_ohw.export_peaks()            
            helpfunctions.msgbox(self, 'Raw and analyzed peaks were successfully saved')
            
        def on_exportEKG_CSV(self):
            
            self.current_ohw.exportEKG_CSV()
            helpfunctions.msgbox(self, 'EKG values were successfully saved')
            
        def on_exportStatistics(self):
            
            self.current_ohw.exportStatistics()
            helpfunctions.msgbox(self, 'Statistics were successfully saved')
            
        def on_saveKinetics(self):
            
            mark_peaks = self.plotted_peaks
            
            #allowed file types:
            file_types = "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.tiff);;BMP(*.bmp);; Scalable Vector Graphics (*.svg)"
            #let the user choose a folder from the starting path
            path = str(pathlib.PureWindowsPath(self.current_ohw.analysis_meta["results_folder"] / 'beating_kinetics.PNG'))
            filename_save = QFileDialog.getSaveFileName(None, 'Choose a folder and enter a filename', path, file_types)

            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (filename_save == ('','')):
                return
            try:
                self.current_ohw.plot_beatingKinetics(mark_peaks, filename_save)
                mainWidget = self.findMainWindow()
                mainWidget.adjustSize()
                print('Graphs were saved successfully.')
                
            except (IndexError, NameError, AttributeError):
                pass
        
        def on_getMVs(self):
            #disable button to not cause interference between different calculations
            self.tab_motion.button_getMVs.setEnabled(False)
            
            #get current parameters entered by user
            blockwidth = self.tab_motion.spinbox_blockwidth.value()
            maxShift = self.tab_motion.spinbox_maxShift.value()
            delay = self.tab_motion.spinbox_delay.value()
            
            px_longest = None
            scaling_status = self.tab_motion.check_scaling.isChecked()
            print(scaling_status)
            if scaling_status == True:
                px_longest = 1024
            '''
            else:                
                #if at least one ROI was selected, use ROI ImageStack and also calculate the whole image
                if len(self.ROI_OHWs) is not 0:
                    for nr_ROI in range(0, len(self.ROI_OHWs)):
                        #calculate motion vectors for each ROI
                        self.ROI_OHWs[nr_ROI].scale_ImageStack(self.ROI_OHWs[nr_ROI].ROIImageStack.shape[1], 
                                                               self.ROI_OHWs[nr_ROI].ROIImageStack.shape[2])
    
                        cal_MVs_thread = self.ROI_OHWs[nr_ROI].calculate_MVs_thread(blockwidth = blockwidth, delay = delay, max_shift = maxShift)
                        cal_MVs_thread.start()
                        #self.ready = False
                        cal_MVs_thread.progressSignal.connect(self.updateMVProgressBar)
                        #initialize_calculatedMVs only for the full image, for the ROIs on-the-fly
                        #cal_MVs_thread.finished.connect(self.initialize_calculatedMVs)

#                #always calculate the full image
                self.current_ohw.scale_ImageStack(self.current_ohw.rawImageStack.shape[1], self.current_ohw.rawImageStack.shape[2])     
            '''
            
            self.current_ohw.set_analysisImageStack(px_longest = px_longest) # scale + set roi, , roi=[0,0,500,500]
            
            calculate_motion_thread = self.current_ohw.calculate_motion_thread(blockwidth = blockwidth, delay = delay, max_shift = maxShift)
            calculate_motion_thread.start()
            calculate_motion_thread.progressSignal.connect(self.updateMVProgressBar)
            calculate_motion_thread.finished.connect(self.initialize_motion)
              
        def updateMVProgressBar(self, value):
            self.tab_motion.progressbar_MVs.setValue(value*100)
                
        def updateProgressBar(self, value):
            self.progressbar_tab_motion.setValue(value*100)
        
        def initialize_motion(self):
            print('initializing motion')
            self.current_ohw.initialize_motion()
            
            # saves ohw_object when calculation is done and other general results
            self.current_ohw.exportEKG_CSV()
            self.current_ohw.save_ohw()
            self.current_ohw.plot_TimeAveragedMotions('.png')
            
            #set the succeed button to green:
            self.tab_motion.button_succeed_MVs.setStyleSheet("background-color: YellowGreen")
            self.tab_motion.button_succeed_MVs.setText("Motion available") # improve and move init to tab_motion!
                
            #enable other buttons for further actions
            self.tab_motion.button_save_MVs.setEnabled(True)
            self.button_detectPeaks.setEnabled(True)
            self.button_saveKinetics.setEnabled(True)
            self.button_export_ekg_csv.setEnabled(True)
            
            self.initialize_kinetics()
            
            # fill graphs with data from first frame
            # self.initialize_MV_graphs()
            self.tab_quiver.init_ohw()
    
            # initialize time averaged motion
            self.tab_TA.init_ohw()
            
            self.tab_motion.button_getMVs.setEnabled(True) #move to tab...
            
            #get the current video length and save it to the quiver settings
            #self.quiver_settings['video_length'] = str(1/self.current_ohw.videometa["fps"] * self.current_ohw.absMotions.shape[0])
            
        def initialize_kinetics(self):
            """
                initializes graph for beating kinetics "EKG"
            """
            print("initialize beating kinetics graphs")
            
            self.fig_kinetics, self.ax_kinetics = plotfunctions.plot_Kinetics(self.current_ohw.timeindex, self.current_ohw.mean_absMotions, Peaks=None, mark_peaks=False, file_name=None)#'test.png'           
            
            self.canvas_kinetics = FigureCanvas(self.fig_kinetics)  
            self.fig_kinetics.subplots_adjust(bottom = 0.2)            
            
            self.tab3.layout.addWidget(self.canvas_kinetics, 7,0)
            self.canvas_kinetics.draw()

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

        def on_saveMVs(self):
            """
                saves raw MVs to results folder
            """
            self.current_ohw.save_MVs()
            helpfunctions.msgbox(self, 'Motion vectors were successfully saved')
        
        def on_load_ohw(self):
            """
                loads already calculated motion and initializes gui
                ... how to optimize loading of rawImageStack?
            """
            msg = 'select .pickle-file of previous analysis'
            path = self.config['LAST SESSION']['input_folder']
            pickle_file = QFileDialog.getOpenFileName(None, msg, path, 
                "ohw_analysis (*.pickle)")[0]
                
            self.current_ohw = OHW.OHW()    # creates new instance here!
            self.current_ohw.load_ohw(pickle_file)
            self.initialize_motion()
            
            self.set_motion_param()
            self.update_tab_input()
            self.tab_input.btn_reloadVideo.setEnabled(True)
        
        def set_motion_param(self):
            """
                sets values in gui from loaded ohw-file
            """
            self.tab_motion.spinbox_blockwidth.setValue(self.current_ohw.analysis_meta["MV_parameters"]["blockwidth"])
            self.tab_motion.spinbox_delay.setValue(self.current_ohw.analysis_meta["MV_parameters"]["delay"])
            self.tab_motion.spinbox_maxShift.setValue(self.current_ohw.analysis_meta["MV_parameters"]["max_shift"])
        
        def set_start_brightness(self):
            """
                set brightness sliders to raw values
            """
            self.tab_input.slider_whiteval.blockSignals(True)# prevent calling on_change_whiteVal/blackVal
            self.tab_input.slider_blackval.blockSignals(True)
            self.tab_input.slider_whiteval.setMaximum(self.current_ohw.videometa["Whiteval"]*3)
            self.tab_input.slider_blackval.setMaximum(self.current_ohw.videometa["Whiteval"])      
            self.tab_input.slider_whiteval.setValue(self.current_ohw.videometa["Whiteval"])
            self.tab_input.slider_blackval.setValue(self.current_ohw.videometa["Blackval"])
            self.tab_input.slider_whiteval.setMinimum(self.current_ohw.videometa["Blackval"])
            self.tab_input.slider_whiteval.blockSignals(False)
            self.tab_input.slider_blackval.blockSignals(False)
        
        def update_tab_input(self):
            """
                updates info displayed in inputtab
                -> loading of new video or loading of analysis file
            """
            self.tab_input.edit_fps.setText(str(self.current_ohw.videometa['fps']))
            self.tab_input.edit_mpp.setText(str(self.current_ohw.videometa['microns_per_px']))            
            # disable input field if videoinfos.txt available? if self.current_ohw.videometa['infofile_exists'] == True: ....
            
            # check if video is loaded and update controls
            if self.current_ohw.video_loaded == True:
                self.display_firstImage(self.current_ohw.rawImageStack[0])
                self.tab_input.slider_blackval.setEnabled(True)
                self.tab_input.slider_whiteval.setEnabled(True)
                self.tab_input.btn_brightness.setEnabled(True)
                self.set_start_brightness()
                
                self.tab_motion.button_getMVs.setEnabled(True)
                #self.button_succeed_tab1.setStyleSheet("background-color: YellowGreen")
            else:
                self.display_firstImage()
                self.tab_input.slider_blackval.setEnabled(False)
                self.tab_input.slider_whiteval.setEnabled(False)
                self.tab_input.btn_brightness.setEnabled(False)
                
                self.tab_motion.button_getMVs.setEnabled(False)
                #self.button_succeed_tab1.setStyleSheet("background-color: IndianRed")
            
            inputpath = str(self.current_ohw.videometa['inputpath'])
            self.tab_input.label_input_path.setText(inputpath)
            
            results_folder = str(pathlib.PureWindowsPath(self.current_ohw.analysis_meta['results_folder']))
            self.tab_input.label_results_folder.setText(results_folder)
            self.tab_input.btn_results_folder.setEnabled(True)
        
        def findMainWindow(self): #-> typing.Union[QMainWindow, None]:
            # Global function to find the (open) QMainWindow in application
            #....why needed?
            app = QApplication.instance()
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    return widget
            return None
        
        def restartGUI(self):
            #restarts the application to work with new data
            python = sys.executable
            os.execl(python, python, *sys.argv)
        
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
            """
                receive the signals from quiver settings changed by user
            """
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