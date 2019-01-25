# -*- coding: utf-8 -*-

import os
import cv2
import time

import numpy as np
from PyQt5.QtWidgets import QMainWindow, QCheckBox, QHBoxLayout, QLineEdit, QDoubleSpinBox, QStyle, QSlider, QSizePolicy, QAction, QTextEdit, QMessageBox, QComboBox, QProgressBar, QSpinBox, QFileDialog, QTabWidget, QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton, QApplication, QDesktopWidget 
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QImage
from PyQt5.QtCore import QDir, Qt, QUrl, QThread, QThreadPool
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
import PyQt5.QtCore as Core
import pathlib
#from pathlib import Path
import moviepy.editor as mpy
import matplotlib.pyplot as plt
from skimage import exposure
#import tifffile
import glob
from moviepy.video.io.bindings import mplfig_to_npimage
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from libraries import MultipleFoldersByUser, UserDialogs, Filters#, Measurement
from libraries import OHW   #move and change to .Functions

class TableWidget(QWidget):
        def __init__(self, parent):   
            super(QWidget, self).__init__(parent)
            self.layout = QGridLayout(self)
 
            # create OHW object to work with motion vectors
            self.OHW = OHW.OHW()
 
            # Initialize tab screen
            self.tabs = QTabWidget()
            # Add tabs to widget        
            self.layout.addWidget(self.tabs)
            self.setLayout(self.layout)
            #settings for tabs
            #place tabs at the left side of the GUI:
            #self.tabs.setTabPosition(QTabWidget.West)

            self.plotted_peaks = False
            
            self.tab1 = QWidget()	
            self.tab2 = QWidget()
            self.tab3 = QWidget()
            self.tab4 = QWidget()
            self.tab5 = QWidget()
            self.tab6 = QWidget()
            self.tabs.resize(800,800)
             
            # Add tabs
            self.tabs.addTab(self.tab1,"Input folder ")
            self.tabs.addTab(self.tab2,"Compute motion vectors ")
            self.tabs.addTab(self.tab3,"Analysis (Basic) ")
            self.tabs.addTab(self.tab4,"Analysis: Heatmaps and Quiverplots (Advanced) ")
            self.tabs.addTab(self.tab5,"Analysis: Time averaged motion (Advanced)")
            self.tabs.addTab(self.tab6,"Automated analysis of multiple folders (Advanced)")
            
            color_for_info = QColor(198, 255, 26)
            self.pixmap_width = 250
           
 ########### fill the first tab ##################
            info_loadFile = QTextEdit()
            info_loadFile.setText('In this tab you choose the input folder. If a videoinfos.txt file is found, the information is processed automatically. Otherwise, please enter the framerate and pixel per microns.')
            info_loadFile.setReadOnly(True)
            info_loadFile.setMaximumHeight(40)
            info_loadFile.setMaximumWidth(800)
            info_loadFile.setTextBackgroundColor(color_for_info)
            info_loadFile.setStyleSheet("background-color: LightSkyBlue")
            
            label_loadFile = QLabel('Load file(s): ')
            self.label_fps = QLabel('Enter the framerate [frames/sec]: ')
            self.label_px_per_micron = QLabel('Enter the number of micrometer per pixel: ')
            label_display = QLabel('Display image: ')
            label_loadFile.setFont(QFont("Times",weight=QFont.Bold))
            label_display.setFont(QFont("Times",weight=QFont.Bold))


            self.line_fps = QLineEdit()
            self.line_px_perMicron = QLineEdit()

            self.line_px_perMicron.setText('1.5374')
            self.line_fps.setText('17.49105135069209')
            self.line_px_perMicron.textChanged.connect(self.changePxPerMicron)
            self.line_fps.textChanged.connect(self.changeFPS)            
            
            """
            #call changeFPS and changeDPI for the first time to get initial values
            # not necessary anymore, as values directly read in from file
            self.fps = self.changeFPS()
            self.px_per_micron = self.changePxPerMicron()
            """
            
            #display image
            source = 'Chosen image: '
            self.label_chosen_image = QLabel(str(source + ' - '))
            self.image = QLabel()
            self.image.setPixmap(QPixmap('icons/dummy_image.png').scaledToWidth(self.pixmap_width))
        
           # Bild mit Matplotlib Canvas ersetzt for later 
            self.fig_firstIm, self.ax_firstIm = plt.subplots(1,1)
#            self.fig_firstIm.set_size_inches(16,12)
            self.ax_firstIm.axis('off')
            
            self.canvas_firstImage = FigureCanvas(self.fig_firstIm)
            
            #load-folder button
            self.button_loadFolder = QPushButton('Choose folder')
            self.button_loadFolder.resize(self.button_loadFolder.sizeHint())
            self.button_loadFolder.clicked.connect(self.on_loadFolder)
            
            #load-file button
            self.button_loadFile = QPushButton('Choose file')
            self.button_loadFile.resize(self.button_loadFile.sizeHint())
            self.button_loadFile.clicked.connect(self.on_loadFile)      
            
            #label to display current results folder
            self.label_resultsfolder = QLabel('Current results folder: ')
          
            #button for changing the results folder
            self.button_change_resultsfolder = QPushButton('Change results folder ')
            self.button_change_resultsfolder.resize(self.button_change_resultsfolder.sizeHint())
            self.button_change_resultsfolder.clicked.connect(self.on_change_resultsfolder)
            self.button_change_resultsfolder.setEnabled(False)
            
            #succed-button
            self.button_succeed_tab1 = QPushButton('Move on to the next tab if this button is green!')
            self.button_succeed_tab1.setStyleSheet("background-color: IndianRed")
            
            #reset-button
            self.button_reset = QPushButton('Restart with new data')
            self.button_reset.resize(self.button_reset.sizeHint())
            self.button_reset.clicked.connect(self.restartGUI)      
            
            #progressbar in tab1  
            #rename progressbars in future?
            self.progressbar_tab1 = QProgressBar(self)
            self.progressbar_tab1.setMaximum(1)  
            self.progressbar_tab1.setValue(0)
            
            self.tab1.layout = QGridLayout(self)
            self.tab1.layout.setSpacing(25)
            self.tab1.layout.addWidget(self.button_reset,           1,  1)
            self.tab1.layout.addWidget(info_loadFile,               1,  0)
            self.tab1.layout.addWidget(label_loadFile,              2,  0)            
            self.tab1.layout.addWidget(self.label_fps,              4,  0)
            self.tab1.layout.addWidget(self.line_fps,               4,  1)
            self.tab1.layout.addWidget(self.label_px_per_micron,    5,  0)
            self.tab1.layout.addWidget(self.line_px_perMicron,      5,  1)
            self.tab1.layout.addWidget(self.button_loadFolder,      6,  0)
            self.tab1.layout.addWidget(self.button_loadFile,        7,  0)
            self.tab1.layout.addWidget(self.progressbar_tab1,       8,  0)
            self.tab1.layout.addWidget(self.button_succeed_tab1,    9,  0)
            self.tab1.layout.addWidget(label_display,               10, 0)
            self.tab1.layout.addWidget(self.label_chosen_image,     11, 0)
            self.tab1.layout.addWidget(self.image,                  12, 0)
            self.tab1.layout.addWidget(self.label_resultsfolder,    13, 0)
            self.tab1.layout.addWidget(self.button_change_resultsfolder, 14,0)
            
            self.tab1.setLayout(self.tab1.layout)
            
########### fill the second tab ##################
            info_measurement = QTextEdit()
            info_measurement.setText('In this tab you set the settings for the block-matching algorithm and perform the calculation of the motion vectors. You can also export the motion vectors.')
            info_measurement.setReadOnly(True)
            info_measurement.setMaximumHeight(40)
            info_measurement.setMaximumWidth(800)
            info_measurement.setStyleSheet("background-color: LightSkyBlue")
            
            label_measure = QLabel('Measure velocity (block-matching): ')
            label_settings = QLabel('Settings: ')
            label_measure.setFont(QFont("Times",weight=QFont.Bold))
            label_settings.setFont(QFont("Times",weight=QFont.Bold))
            label_addOptions = QLabel('Additional options: ')
            label_addOptions.setFont(QFont("Times",weight=QFont.Bold))
            
            #user settings  
            label_blockwidth =  QLabel('Blockwidth (in pixels):')
            label_delay =       QLabel('Delay (in frames): ')
            label_maxShift =    QLabel('Maximum shift p (in pixels): ')
            self.spinbox_blockwidth = QSpinBox()
            self.spinbox_delay = QSpinBox()
            self.spinbox_maxShift = QSpinBox()
            
            #settings for the spinboxes
            self.spinbox_blockwidth.setRange(2,128)
            self.spinbox_blockwidth.setSingleStep(2)
            self.spinbox_blockwidth.setSuffix(' pixels')
            self.spinbox_blockwidth.setValue(16)
            self.spinbox_delay.setRange(2,10)
            self.spinbox_delay.setSuffix(' frames')
            self.spinbox_delay.setSingleStep(1)
            self.spinbox_delay.setValue(2)
            self.spinbox_maxShift.setSuffix(' pixels')
            self.spinbox_maxShift.setValue(7)

            #if value of box is changed
            self.spinbox_blockwidth.valueChanged.connect(self.changeBlockwidth)
            self.spinbox_delay.valueChanged.connect(self.changeDelay)
            self.spinbox_maxShift.valueChanged.connect(self.changeMaxShift)
            
            self.check_scaling = QCheckBox('Scale the image to 1024 x 1024 pixels during calculation')
            #default values:
            self.scaling_status = True
            self.factor_scaling = 1024
            self.check_scaling.setChecked(self.scaling_status)
            self.check_scaling.stateChanged.connect(self.changeStatus)
            
            #enable/disable filtering
            self.check_filter = QCheckBox("Filter motion vectors during calculation")
            #create a variable for the filter status
            self.filter_status = True
            
            self.check_filter.setChecked(self.filter_status)
            self.check_filter.stateChanged.connect(self.changeStatus)
            
            self.button_getMVs = QPushButton('Get motion vectors')
            self.button_getMVs.resize(self.button_getMVs.sizeHint())
            self.button_getMVs.clicked.connect(self.on_getMVs)
            self.button_getMVs.setEnabled(False)
            
            self.button_save_motionVectors = QPushButton('Save motion vectors')
            self.button_save_motionVectors.resize(self.button_save_motionVectors.sizeHint())
            self.button_save_motionVectors.clicked.connect(self.on_saveMVs)
            self.button_save_motionVectors.setEnabled(False)
            
            #succed-button
            self.button_succeed_tab2 = QPushButton('Move on to the next tab if this button is green!')
            self.button_succeed_tab2.setStyleSheet("background-color: IndianRed")
            
            #progressbar in tab2    
            self.progressbar_tab2 = QProgressBar(self)
            self.progressbar_tab2.setMaximum(100)
            self.progressbar_tab2.setValue(0)
            
            self.tab2.layout = QGridLayout(self)
            self.tab2.layout.setSpacing(25)
            self.tab2.layout.addWidget(info_measurement, 0,0)
            self.tab2.layout.addWidget(label_settings, 1,0)
            self.tab2.layout.addWidget(label_blockwidth,2,0)
            self.tab2.layout.addWidget(self.spinbox_blockwidth,2,1)
            self.tab2.layout.addWidget(label_delay,3,0)
            self.tab2.layout.addWidget(self.spinbox_delay, 3,1)
            self.tab2.layout.addWidget(label_maxShift,4,0)
            self.tab2.layout.addWidget(self.spinbox_maxShift,4,1)
            self.tab2.layout.addWidget(label_addOptions, 5,0)
            self.tab2.layout.addWidget(self.check_scaling, 6,0)
            self.tab2.layout.addWidget(self.check_filter, 7,0 )
            self.tab2.layout.addWidget(label_measure, 8,0)
            self.tab2.layout.addWidget(self.button_getMVs, 9,0)
            self.tab2.layout.addWidget(self.progressbar_tab2, 10,0)
            self.tab2.layout.addWidget(self.button_succeed_tab2, 11,0)
            self.tab2.layout.addWidget(self.button_save_motionVectors, 12,0)
            
            self.tab2.setLayout(self.tab2.layout)
            
########### fill the third tab ##################
            info_analysisBasic = QTextEdit()
            info_analysisBasic.setText('In this tab you can plot the motion as an EKG and calculate statistics based on the found peaks. Change the parameters manually to optimize the peak detection. You can save the graphs and export the peaks.')
            info_analysisBasic.setReadOnly(True)
            info_analysisBasic.setMaximumHeight(40)
            info_analysisBasic.setMaximumWidth(800)
            info_analysisBasic.setStyleSheet("background-color: LightSkyBlue")
            
            
            label_results = QLabel('Results: ')
            label_results.setFont(QFont("Times",weight=QFont.Bold))
            
            #display the plotted EKG
            #self.EKG = PlotEKG(self, width=5, height=3)

            self.fig_kinetics, self.ax_kinetics = plt.subplots(1,1)
            self.fig_kinetics.set_size_inches(16,12)
            self.canvas_kinetics = FigureCanvas(self.fig_kinetics)           
            
            #spinboxes to choose for manual detection
            label_ratio = QLabel('Ratio of peaks: ')           
            self.spinbox_ratio = QDoubleSpinBox()
            self.spinbox_ratio.setRange(0.01, 0.90)
            self.spinbox_ratio.setSingleStep(0.01)
            self.spinbox_ratio.setValue(0.05)           
            #self.spinbox_ratio.valueChanged.connect(self.changeRatio)
            
            label_neighbours = QLabel('Number of neighbouring values for evaluation:') 
            self.spinbox_neighbours = QSpinBox()    
            self.spinbox_neighbours.setRange(2,10)
            self.spinbox_neighbours.setSingleStep(2)
            self.spinbox_neighbours.setValue(4)
            #self.spinbox_neighbours.valueChanged.connect(self.changeNeighbours)
            
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
            self.tab3.layout.addWidget(info_analysisBasic, 0,0)
            self.tab3.layout.addWidget(label_results, 1,0)
            self.tab3.layout.addWidget(label_ratio, 2,0)
            self.tab3.layout.addWidget(self.spinbox_ratio, 2,1)
            self.tab3.layout.addWidget(label_neighbours, 3,0)
            self.tab3.layout.addWidget(self.spinbox_neighbours, 3,1)
            self.tab3.layout.addWidget(self.button_detectPeaks, 4,0)
            self.tab3.layout.addWidget(self.canvas_kinetics, 5,0)
            self.tab3.layout.addWidget(label_max_contraction, 6,0)
            self.tab3.layout.addWidget(self.label_max_contraction_result, 6,1)
            self.tab3.layout.addWidget(label_max_relaxation, 7,0)
            self.tab3.layout.addWidget(self.label_max_relaxation_result, 7,1)
            self.tab3.layout.addWidget(label_time_contraction, 8,0)
            self.tab3.layout.addWidget(self.label_time_contraction_result, 8,1)
            self.tab3.layout.addWidget(label_time_relaxation, 9,0)            
            self.tab3.layout.addWidget(self.label_time_relaxation_result, 9,1)
            self.tab3.layout.addWidget(label_time_contr_relax, 10,0)
            self.tab3.layout.addWidget(self.label_time_contr_relax_result, 10,1)
            self.tab3.layout.addWidget(label_bpm, 11,0)
            self.tab3.layout.addWidget(self.label_bpm_result, 11,1)
            self.tab3.layout.addWidget(label_furtherAnalysis, 12,0)
            self.tab3.layout.addWidget(self.button_saveKinetics, 13,0)
            self.tab3.layout.addWidget(self.button_export_peaks, 14, 0)
            self.tab3.layout.addWidget(self.button_export_ekg_csv, 15,0)
            self.tab3.layout.addWidget(self.button_export_statistics, 16,0)
            self.tab3.setLayout(self.tab3.layout)

########### fill the fourth tab ##################
            info_heat_quiver = QTextEdit()
            info_heat_quiver.setText('In this tab you can calculate heatmaps and quiverplots and use the slider to look at the different frames.')
            info_heat_quiver.setReadOnly(True)
            info_heat_quiver.setMaximumHeight(40)
            info_heat_quiver.setMaximumWidth(800)
            info_heat_quiver.setStyleSheet("background-color: LightSkyBlue")
 
            label_heatmaps = QLabel('Heatmaps')
            label_heatmaps.setFont(QFont("Times",weight=QFont.Bold))
            
            label_quivers = QLabel('Quivers')
            label_quivers.setFont(QFont("Times",weight=QFont.Bold))

            #Button for starting the creation of heatmaps and heatmap video
            self.button_heatmaps_video = QPushButton('Create Heatmap Video')
            self.button_heatmaps_video.resize(self.button_heatmaps_video.sizeHint())
            self.button_heatmaps_video.clicked.connect(self.on_saveHeatmapvideo)            
            #is disabled, enabled after successful calculation of MotionVectors
            self.button_heatmaps_video.setEnabled(False)
                          
            #create  a slider to switch manually between the heatmaps
            self.label_slider_info = QLabel('Use the slider to switch between heatmaps of the different frames: ')
            self.slider_value = 0
            self.slider_heatmaps = QSlider(Qt.Horizontal)
            self.slider_heatmaps.setMinimum(0)
            self.slider_maximum = 100;
            self.slider_heatmaps.setMaximum(self.slider_maximum)
            self.slider_heatmaps.setValue(self.slider_value)
            self.slider_heatmaps.setTickPosition(QSlider.TicksBelow)
            self.slider_heatmaps.setTickInterval(5)
            self.slider_heatmaps.valueChanged.connect(self.slider_heatmaps_valueChanged)
            
            #create buttons for saving a specific heatmap or quiverplot frame
            self.button_save_Heatmap = QPushButton('Save this heatmap frame to image file...')
            self.button_save_Heatmap.resize(self.button_save_Heatmap.sizeHint())
            self.button_save_Heatmap.clicked.connect(self.on_saveHeatmap)      
            #is disabled, enabled after successful calculation of Heatmaps
            self.button_save_Heatmap.setEnabled(False)
            
            self.button_save_Quiver = QPushButton('Save this quiver frame to image file...')
            self.button_save_Quiver.resize(self.button_save_Quiver.sizeHint())
            self.button_save_Quiver.clicked.connect(self.on_saveQuiver)            
            #is disabled, enabled after successful calculation of QuiverPlots
            self.button_save_Quiver.setEnabled(False)
            
            #create a second slider for the quiver plots
            self.label_slider_quivers = QLabel('Use the slider to switch between quiverplots of the different frames: ')
            self.slider_quiver = QSlider(Qt.Horizontal)
            self.slider_quiver.setMinimum(0)
            self.slider_quiver.setMaximum(self.slider_maximum)
            self.slider_value_quiver = 0
            self.slider_quiver.setValue(self.slider_value_quiver)
            self.slider_quiver.setTickPosition(QSlider.TicksBelow)
            self.slider_quiver.setTickInterval(2)
            self.slider_quiver.valueChanged.connect(self.slider_quiver_valueChanged)
            self.slider_quiver.setTickPosition(QSlider.TicksBelow)
            self.slider_quiver.setTickInterval(5)
            
            #display the chosen heatmap
            self.label_heatmap_result = QLabel('Heatmap result:')
            #display the chosen heatmap
            self.label_heatmap_result = QLabel('Heatmap result:')
            self.image_heatmap = QLabel()
            self.image_heatmap.setPixmap(QPixmap('icons/dummy_heatmap.png').scaledToWidth(self.pixmap_width))
            
            # Bild mit Matplotlib Canvas ersetzt
            self.fig_heatmaps, self.ax_heatmaps = plt.subplots(1,1)
            self.fig_heatmaps.set_size_inches(16,12)
            self.ax_heatmaps.axis('off')
            
            self.canvas_heatmap = FigureCanvas(self.fig_heatmaps)

            #Button for starting the creation of quiver plots and quiver video
            self.button_quivers_video = QPushButton('Create quiver video')
            self.button_quivers_video.resize(self.button_quivers_video.sizeHint())
            self.button_quivers_video.clicked.connect(self.on_saveQuivervideo)
             #is disabled, enabled after successful calculation of MotionVectors
            self.button_quivers_video.setEnabled(False)
                     
             #display the chosen quiver plot
            self.label_quiver_result = QLabel('Quiver result: ')
            self.label_quiver_result = QLabel('Quiver result: ')
            self.image_quiver = QLabel()
            self.image_quiver.setPixmap(QPixmap('icons/dummy_quiver.png').scaledToWidth(self.pixmap_width))
 
            # Bild mit Matplotlib Canvas ersetzt
            self.fig_quivers, self.ax_quivers = plt.subplots(1,1)
            self.fig_quivers.set_size_inches(16,12)
            self.ax_quivers.axis('off')
            
            self.canvas_quivers = FigureCanvas(self.fig_quivers)
                  
            #succed-button
            self.button_succeed_heatmaps = QPushButton('Heatmap-video creation was successful')
            self.button_succeed_heatmaps.setStyleSheet("background-color: IndianRed")
            self.button_succeed_quivers = QPushButton('Quiver-video creation was successful')
            self.button_succeed_quivers.setStyleSheet("background-color: IndianRed")

            #progressbar fuer heatmaps
            self.progressbar_heatmaps = QProgressBar(self)
            self.progressbar_heatmaps.setMaximum(9)  # an Anzahl Bilder anpassen
            self.progressbar_heatmaps.setValue(0)
            
            #progressbar fuer quivers
            self.progressbar_quivers = QProgressBar(self)
            self.progressbar_quivers.setMaximum(9)  # an Anzahl Bilder anpassen
            self.progressbar_quivers.setValue(0)
        
            #define layout
            colHeatmap = 0
            colQuiver = 2
            self.tab4.layout = QGridLayout()
            self.tab4.layout.addWidget(info_heat_quiver, 0,0)
            self.tab4.layout.addWidget(label_heatmaps,              1,  colHeatmap)
            self.tab4.layout.addWidget(label_quivers,               1,  colQuiver)
            self.tab4.layout.addWidget(self.button_heatmaps_video,  2,  colHeatmap)
            self.tab4.layout.addWidget(self.button_quivers_video,   2,  colQuiver)
            self.tab4.layout.addWidget(self.progressbar_heatmaps,   3,  colHeatmap)
            self.tab4.layout.addWidget(self.progressbar_quivers,    3,  colQuiver)
            self.tab4.layout.addWidget(self.button_succeed_heatmaps,4,  colHeatmap)
            self.tab4.layout.addWidget(self.button_succeed_quivers, 4,  colQuiver)
            self.tab4.layout.addWidget(self.label_heatmap_result,   5,  colHeatmap)
            self.tab4.layout.addWidget(self.label_quiver_result,    5,  colQuiver)
            self.tab4.layout.addWidget(self.image_heatmap,          6,  colHeatmap)
            self.tab4.layout.addWidget(self.image_quiver,           6,  colQuiver)
            #self.tab4.layout.addWidget(self.label_slider_info,      7,  colHeatmap)
            #self.tab4.layout.addWidget(self.label_slider_quivers,   7,  colQuiver)
            #self.tab4.layout.addWidget(self.slider_heatmaps,        8,  colHeatmap)
            #self.tab4.layout.addWidget(self.slider_quiver,          8,  colQuiver)
            self.tab4.layout.addWidget(self.button_save_Heatmap,    9,  colHeatmap)
            self.tab4.layout.addWidget(self.button_save_Quiver,     9,  colQuiver)

            self.tab4.layout.setColumnStretch(0,1)
            self.tab4.layout.setColumnStretch(1,1)
            self.tab4.layout.setColumnStretch(2,1)
            self.tab4.layout.setHorizontalSpacing(20)
            self.tab4.setLayout(self.tab4.layout)
       

########### fill the fifth tab ##################
            info_timeAveraged = QTextEdit()
            info_timeAveraged.setText('In this tab you can save the time averaged motion: absolute contractility and contractility in x- and y-direction.')
            info_timeAveraged.setReadOnly(True)
            info_timeAveraged.setMaximumHeight(40)
            info_timeAveraged.setMaximumWidth(800)
            info_timeAveraged.setStyleSheet("background-color: LightSkyBlue")
            
            label_time_avg_motion = QLabel('Motion averaged over time')
            label_time_avg_motion.setFont(QFont("Times",weight=QFont.Bold))
         
            #display the calculated time averaged motion
            self.label_time_averaged_result_total = QLabel('Absolute contractility:')
            self.label_time_averaged_result_x = QLabel('Contractility in x-direction:')
            self.label_time_averaged_result_y = QLabel('Contractility in y-direction:')
            self.image_motion_total = QLabel()
            self.image_motion_x  = QLabel()
            self.image_motion_y = QLabel()
            
            self.image_motion_total.setPixmap(QPixmap('icons/dummy_TimeAveraged_totalMotion.png').scaledToWidth(self.pixmap_width))
            self.image_motion_x.setPixmap(QPixmap('icons/dummy_TimeAveraged_x.png').scaledToWidth(self.pixmap_width))
            self.image_motion_y.setPixmap(QPixmap('icons/dummy_TimeAveraged_y.png').scaledToWidth(self.pixmap_width))
            
            #figurecanvas for editing later
            # Bild mit Matplotlib Canvas ersetzt
            self.fig_motion_total, self.ax_motion_total = plt.subplots(1,1)
            self.fig_motion_x, self.ax_motion_x = plt.subplots(1,1)
            self.fig_motion_y, self.ax_motion_y = plt.subplots(1,1)
            
            self.fig_motion_total.set_size_inches(16,12)
            self.fig_motion_x.set_size_inches(16,12)
            self.fig_motion_y.set_size_inches(16,12)
            
            self.ax_motion_total.axis('off')
            self.ax_motion_x.axis('off')
            self.ax_motion_y.axis('off')
            
            self.canvas_motion_total = FigureCanvas(self.fig_motion_total)
            self.canvas_motion_x = FigureCanvas(self.fig_motion_x)
            self.canvas_motion_y = FigureCanvas(self.fig_motion_y)
            
            #save as
            label_save_motion = QLabel('Save the plots as: ')
            self.button_save_timeMotion = QPushButton('Click for saving')
            self.button_save_timeMotion.resize(self.button_save_timeMotion.sizeHint())
            self.button_save_timeMotion.clicked.connect(self.on_saveTimeAveragedMotion)
            self.button_save_timeMotion.setEnabled(False)
            
            #combobox for file extensions
            self.combo_avgExt = QComboBox(self)
            self.combo_avgExt.addItem('.png')
            self.combo_avgExt.addItem('.jpeg')
            self.combo_avgExt.addItem('.tiff')
            self.combo_avgExt.addItem('.svg')
            self.combo_avgExt.addItem('.eps')

            #succed-button
            self.button_succeed_motion = QPushButton('Plotting of time averaged motion was successful')
            self.button_succeed_motion.setStyleSheet("background-color: IndianRed")
 
            #define layout
            self.tab5.layout = QGridLayout()
            self.tab5.layout.addWidget(info_timeAveraged, 0,0)
            self.tab5.layout.addWidget(label_time_avg_motion, 1,0)
#            self.tab5.layout.addWidget(self.button_time_avg_motion, 2,0) 
            self.tab5.layout.addWidget(self.button_succeed_motion, 2,0)
            self.tab5.layout.addWidget(self.label_time_averaged_result_total, 3,0)
            self.tab5.layout.addWidget(self.image_motion_total, 4,0)
            self.tab5.layout.addWidget(self.label_time_averaged_result_x, 5,0)
            self.tab5.layout.addWidget(self.image_motion_x, 6,0)
            self.tab5.layout.addWidget(self.label_time_averaged_result_y, 5,1)
            self.tab5.layout.addWidget(self.image_motion_y, 6,1)

            self.tab5.layout.addWidget(label_save_motion, 7,0)
            self.tab5.layout.addWidget(self.combo_avgExt, 7,1)
            self.tab5.layout.addWidget(self.button_save_timeMotion, 8,0)

            self.tab5.layout.setHorizontalSpacing(20)
            self.tab5.setLayout(self.tab5.layout)
           

########### fill the sixth tab ##################
            info_batch = QTextEdit()
            info_batch.setText('In this tab you can automate the analysis of multiple folders without further interaction during the processing.')
            info_batch.setReadOnly(True)
            info_batch.setMaximumHeight(40)
            info_batch.setMaximumWidth(800)
            info_batch.setTextBackgroundColor(color_for_info)
            info_batch.setStyleSheet("background-color: LightSkyBlue")
            
            #select the folders
            self.batch_folders = []
            self.info_batchfolders = QLabel('Currently selected folders for automated analysis:')
            self.info_batchfolders.setFont(QFont("Times",weight=QFont.Bold))
            self.names_batchfolders = QTextEdit()
            
            #button for adding folders
            self.button_addBatchFolder = QPushButton('Add folders...')
            self.button_addBatchFolder.resize(self.button_addBatchFolder.sizeHint())
            self.button_addBatchFolder.clicked.connect(self.addBatchFolder)
            
            #dropdown for choosing folder to be removed
            self.combo_removefolder = QComboBox(self)
            
            #button for removing folders
            self.button_removeBatchFolder = QPushButton('... will be removed from folders.')
            self.button_removeBatchFolder.resize(self.button_removeBatchFolder.sizeHint())
            self.button_removeBatchFolder.clicked.connect(self.removeBatchFolder)
            self.button_removeBatchFolder.setEnabled(False)
            
            #options: needed parameters
            label_batch_parameters = QLabel('Settings during calculation of motion vectors:')
            label_batch_parameters.setFont(QFont("Times",weight=QFont.Bold))
            label_batch_blockwidth = QLabel('Blockwidth (in pixels)')
            label_batch_delay = QLabel('Delay (in frames)')
            label_batch_maxShift = QLabel('Maximum shift p (in pixels)')
            
            #spinboxes incl settings
            self.batch_spinbox_blockwidth  = QSpinBox()
            self.batch_spinbox_delay = QSpinBox()
            self.batch_spinbox_maxShift = QSpinBox()
            
            self.batch_spinbox_blockwidth.setRange(2,128)
            self.batch_spinbox_blockwidth.setSingleStep(2)
            self.batch_spinbox_blockwidth.setSuffix(' pixels')
            self.batch_spinbox_blockwidth.setValue(16)
            self.batch_spinbox_delay.setRange(2,10)
            self.batch_spinbox_delay.setSuffix(' frames')
            self.batch_spinbox_delay.setSingleStep(1)
            self.batch_spinbox_delay.setValue(2)
            self.batch_spinbox_maxShift.setSuffix(' pixels')
            self.batch_spinbox_maxShift.setValue(7)

            #if value of box is changed
            self.batch_spinbox_blockwidth.valueChanged.connect(self.changeBatchSettings)
            self.batch_spinbox_delay.valueChanged.connect(self.changeBatchSettings)
            self.batch_spinbox_maxShift.valueChanged.connect(self.changeBatchSettings)
            
            #options for automated analysis
            label_batchOptions = QLabel('Choose options for automated analysis of the chosen folders:')
            label_batchOptions.setFont(QFont("Times",weight=QFont.Bold))
            
            self.batch_checkFilter = QCheckBox("Filter motion vectors during calculation")
            self.batch_checkHeatmaps = QCheckBox("Create heatmap video")
            self.batch_checkQuivers = QCheckBox("Create quiver plot video")
            self.batch_checkTimeAveraged = QCheckBox("Create plots for time averaged motion")
            self.batch_checkSaveMotionVectors = QCheckBox("Save the generated motion vectors")
            self.batch_checkScaling = QCheckBox("Scale the image to 1024 x 1024 pixels during calculation")
            
            #create a variable for the checkbox status
            self.batch_filter_status = True
            self.batch_heatmap_status = True
            self.batch_quiver_status = True
            self.batch_timeAver_status = True
            self.batch_scaling_status = True
            self.batch_saveMotionVectors_status = False
            
            self.batch_checkFilter.setChecked(self.batch_filter_status)
            self.batch_checkSaveMotionVectors.setChecked(self.batch_saveMotionVectors_status)
            self.batch_checkHeatmaps.setChecked(self.batch_heatmap_status)
            self.batch_checkQuivers.setChecked(self.batch_quiver_status)
            self.batch_checkTimeAveraged.setChecked(self.batch_timeAver_status)
            self.batch_checkScaling.setChecked(self.batch_scaling_status)
            
            self.batch_checkFilter.stateChanged.connect(self.changeStatus)
            self.batch_checkHeatmaps.stateChanged.connect(self.changeStatus)
            self.batch_checkQuivers.stateChanged.connect(self.changeStatus)
            self.batch_checkSaveMotionVectors.stateChanged.connect(self.changeStatus)
            self.batch_checkScaling.stateChanged.connect(self.changeStatus)
            
            #button for starting the analysis
            self.button_batch_startAnalysis = QPushButton('Start the automated analysis of the chosen folders...')
            self.button_batch_startAnalysis.resize(self.button_batch_startAnalysis.sizeHint())
            self.button_batch_startAnalysis.clicked.connect(self.startBatchAnalysis)
            self.button_batch_startAnalysis.setEnabled(False)
            
            #button for aborting the analysis
            self.button_batch_stopAnalysis = QPushButton('Stop onging analysis')
            self.button_batch_stopAnalysis.resize(self.button_batch_stopAnalysis.sizeHint())
            self.button_batch_stopAnalysis.clicked.connect(self.stopBatchAnalysis)
            self.button_batch_stopAnalysis.setEnabled(False)
            
            #create a progressbar    
            self.progressbar_batch = QProgressBar(self)
            self.progressbar_batch.setMaximum(9)  
            self.progressbar_batch.setValue(0)
            
            #Layout management
            self.tab6.layout = QGridLayout(self)
    #        self.tab6.layout.setSpacing(25)
            self.tab6.layout.addWidget(info_batch,                      1,0)
            self.tab6.layout.addWidget(self.info_batchfolders,          2,0)
            self.tab6.layout.addWidget(self.names_batchfolders,         3,0)
            self.tab6.layout.addWidget(self.button_addBatchFolder,      3,1)
            self.tab6.layout.addWidget(self.combo_removefolder,         4,0)
            self.tab6.layout.addWidget(self.button_removeBatchFolder,   4,1)
            
            self.tab6.layout.addWidget(label_batch_parameters,          5,0)
            
            self.tab6.layout.addWidget(label_batch_blockwidth,          6,0)
            self.tab6.layout.addWidget(self.batch_spinbox_blockwidth,   6,1)
            self.tab6.layout.addWidget(label_batch_delay,               7,0)
            self.tab6.layout.addWidget(self.batch_spinbox_delay,        7,1)
            self.tab6.layout.addWidget(label_batch_maxShift,            8,0)
            self.tab6.layout.addWidget(self.batch_spinbox_maxShift,     8,1)            
            self.tab6.layout.addWidget(label_batchOptions,              9,0)
            self.tab6.layout.addWidget(self.batch_checkScaling,         10,0)
            self.tab6.layout.addWidget(self.batch_checkFilter,          11,0)
            self.tab6.layout.addWidget(self.batch_checkHeatmaps,        12,0)
            self.tab6.layout.addWidget(self.batch_checkQuivers,         13,0)  
            self.tab6.layout.addWidget(self.button_batch_startAnalysis, 14,0)
            self.tab6.layout.addWidget(self.progressbar_batch,          15,0)
            self.tab6.layout.addWidget(self.button_batch_stopAnalysis,  15,1)
            
            self.tab6.setLayout(self.tab6.layout)

##################################
        def changeBatchSettings(self):
            if self.sender() == self.batch_spinbox_blockwidth:
                self.blockwidth_batch = self.batch_spinbox_blockwidth.value()
                return self.batch_spinbox_blockwidth.value()
            
            elif self.sender() == self.batch_spinbox_delay:
                self.delay_batch = self.batch_spinbox_delay.value()
                return self.batch_spinbox_delay.value()
            
            elif self.sender() == self.batch_spinbox_maxShift:
                self.maxShift_batch = self.batch_spinbox_maxShift.value()
                return self.batch_spinbox_maxShift.value()
            
        def startBatchAnalysis(self):
            print('Starting the batch analysis...')
            print('These are your folders: ', self.batch_folders)
            self.button_addBatchFolder.setEnabled(False)
            self.button_batch_startAnalysis.setEnabled(False)
        
            
         #### calculate the motion vectors
           #user chooses a folder for saving all results to:
            start_folder = os.path.abspath(os.path.join(self.batch_folders[0], '..'))
            self.save_folder_batch = UserDialogs.chooseFolderByUser('Choose a folder for saving the results: ', start_folder)
            
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (self.save_folder_batch == ''):
                self.button_batch_startAnalysis.setEnabled(True)
                print('Batch analysis did not start correctly. Start again!')
                return
            
            #enable the stop button!
            self.button_batch_stopAnalysis.setEnabled(True)
            
            #get current settings from checkboxes and spinboxes
            self.blockwidth_batch = self.batch_spinbox_blockwidth.value()
            self.delay_batch = self.batch_spinbox_delay.value()
            self.maxShift_batch = self.batch_spinbox_maxShift.value()
            self.batch_factor_scaling = self.batch_checkScaling.isChecked()
            self.batch_filter_status = self.batch_checkFilter.isChecked()
            self.batch_heatmap_status = self.batch_checkHeatmaps.isChecked()
            self.batch_quiver_status = self.batch_checkQuivers.isChecked()
            self.batch_scaling_status = self.batch_checkScaling.isChecked()
            
            if (self.batch_scaling_status == True):
                self.batch_factor_scaling = 1024
            elif (self.batch_scaling_status == False): 
                self.batch_factor_scaling = 2048
                        
            #set maximum of corresponding progressbar:
            #at 4 places in the thread the signal is emitted --> 4*
            self.setMaximumProgressbar(5, 2*len(self.batch_folders))
           # self.setMaximumProgressbar(5, 4*len(self.batch_folders))
            self.batch_threads = []
                        
            #START THREADS
            for input_folder in self.batch_folders:
                newThread = BatchThread_file.BatchThread(self.save_folder_batch, input_folder, self.blockwidth_batch, self.delay_batch, self.maxShift_batch, self.batch_filter_status, self.batch_factor_scaling, self.batch_heatmap_status, self.batch_quiver_status)           
                newThread.progress.connect(self.updateProgressbar)
                #start the thread
                newThread.start()
                self.batch_threads.append(newThread)
                time.sleep(3)
            
            
        def stopBatchAnalysis(self):
            #end the threads
            for thread in self.batch_threads:
                thread.endThread()
            
            #get ready for new analysis:
            self.button_batch_startAnalysis.setEnabled(True)
            self.button_batch_stopAnalysis.setEnabled(False)
            self.progressbar_batch.setValue(0)
            print('Threads are terminated. Ready for new analysis.')
            
        def addBatchFolder(self):
            folderDialog = MultipleFoldersByUser.MultipleFoldersDialog()
            chosen_folders = folderDialog.getSelection()
            
            for item in chosen_folders:
                self.batch_folders.append(item)
                self.names_batchfolders.append(item)
                self.combo_removefolder.addItem(item)
            self.button_removeBatchFolder.setEnabled(True)
            
            if len(self.batch_folders)>0:
                self.button_batch_startAnalysis.setEnabled(True)
                
        def removeBatchFolder(self):
            print('Remove a folder..')
            folder_toberemoved = self.combo_removefolder.currentText()
            #remove the folder from the folder that should be analysed:
            self.batch_folders.remove(folder_toberemoved)
            #adapt the textedit and the combobox:
            self.names_batchfolders.clear()
            self.combo_removefolder.clear()
            
            for folder in self.batch_folders:
                self.names_batchfolders.append(folder)
                self.combo_removefolder.addItem(folder)
            
            if len(self.batch_folders)==0:
                self.button_removeBatchFolder.setEnabled(False)
                self.button_batch_startAnalysis.setEnabled(False)
                
            else:
                self.button_removeBatchFolder.setEnabled(True)
                            
        def setMaximumProgressbar(self, nr, maximum):
            if nr == 1:
                current_progressbar = self.progressbar_tab1
                current_text = "%p%  Loading data... "
            elif nr == 2:
                current_progressbar = self.progressbar_tab2
                current_text =  "%p%  Calculation of motion vectors... "
            elif nr == 3:
                current_progressbar = self.progressbar_heatmaps
                current_text = "%p%  Calculation of heatmaps... "
            elif nr == 4:
                current_progressbar = self.progressbar_quivers
                current_text = "%p%  Calculation of quiver plots... "
            elif nr == 5:
                current_progressbar = self.progressbar_batch
                current_text = "%p%  Folders are being analyzed "
                
            current_progressbar.setMaximum(maximum)
            #save the maximum in attribute of progressbar:
            current_progressbar.savedmaximum = maximum
            #print('Maximum of progressbar is:', str(maximum))
            #display a customized text on the progressbar:
            current_progressbar.setTextVisible(True)
            current_progressbar.setFormat(current_text)
            current_progressbar.setAlignment(Qt.AlignCenter)
        
        """
        def updateProgressbar(self, nr, value):
            if nr == 1:
                current_progressbar = self.progressbar_tab1
                current_text = "%p%  Loading data completed! "
                current_progressbar.setValue(value)
            elif nr == 2:
                current_progressbar = self.progressbar_tab2
                current_text = "%p%  Calculation of motion vectors completed! "
                current_progressbar.setValue(value)
            elif nr == 3:
                current_progressbar = self.progressbar_heatmaps
                current_text = "%p%  Calculation of heatmaps completed! "                
                current_progressbar.setValue(value)
            elif nr == 4:
                current_progressbar = self.progressbar_quivers
                current_text = "%p%  Calculation of quiver plots completed! "
                current_progressbar.setValue(value)
            
            elif nr == 5:
                current_progressbar = self.progressbar_batch
                current_progressbar.setValue(current_progressbar.value()+value)
                current_text =  "%p%  Analysis completed! "

            if current_progressbar.value() == current_progressbar.savedmaximum:
                current_progressbar.setFormat(current_text)
                #if quiver plots are finished, enable Heatmap calculation again:
                if nr == 2: 
                    self.button_getMVs.setEnabled(True)
                if nr == 4:
                    self.button_heatmaps_video.setEnabled(True)
                if nr == 5:
                    #prepare for another round of analysis:
                    self.button_batch_stopAnalysis.setEnabled(False)
                    self.button_batch_startAnalysis.setEnabled(True)
        """
                
        def receiveImageStack(self, images):
            #receive the outputs from the readImages thread
#            self.inputType = inputType
            self.imageStack = images
#
#            #Oli
#            print("info of image stack:", len(self.imageStack), self.imageStack[0].shape, self.imageStack[0].dtype)
#            # --> wird als rgb eingelesen obwohl nur Graustufen
#            # --> durch tifffile ersetzen
#            
            self.videoinfos_location = ''
            # check for videoinfos:
            for file in os.listdir(self.folderName):
                if file.endswith(".txt"):
                    self.videoinfos_location = self.folderName + '/' + file
            # print(self.videoinfos_location)
            if self.videoinfos_location != '':
                self.defineVideoInfos(self.videoinfos_location)
            elif self.videoinfos_location == '':
                print('No videoinfos.txt was found.')
            
             #display the chosen folder
            self.displayImage(self.folderName)
            print('Chosen folder: ')
            print(self.folderName)
            self.button_loadFolder.setEnabled(False)
            
            self.thread_countTime.endThread()
            self.updateProgressbar(1, self.progressbar_tab1.maximum())

        def on_loadFolder(self, grid):
            #choose a folder
            msg = 'Choose an input folder containing a sequence of .tif-images'
            folderName = UserDialogs.chooseFolderByUser(msg)  
            
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (folderName == ''):
                return
            
            #self.OHW.read_imagestack(folderName)
            read_imagestack_thread = self.OHW.read_imagestack_thread(folderName)
            read_imagestack_thread.start()
            #self.progressbar_tab1.setFormat("loading Folder")  #is not displayed yet?
            self.progressbar_tab1.setRange(0,0)
            read_imagestack_thread.finished.connect(self.finish_loadFolder)
                        
        def finish_loadFolder(self):
            self.progressbar_tab1.setRange(0,1)
            self.progressbar_tab1.setValue(1)
            
            self.line_fps.setText(str(self.OHW.videoMeta['fps']))
            # self.label_px_per_micron.setText('microns per pixel: ')
            self.line_px_perMicron.setText(str(self.OHW.videoMeta['microns_per_pixel']))            
            # vielleicht Feld sperren wenn videoinfos.txt vorhanden? if self.OHW.videoMeta['infofile_exists'] == True: ....
            
            # display first image and update controls
            self.imshow_firstImage = self.ax_firstIm.imshow(self.OHW.rawImageStack[0], cmap = 'gray', vmin = self.OHW.videoMeta["Blackval"], vmax = self.OHW.videoMeta["Whiteval"])
            self.canvas_firstImage.draw()            
            self.tab1.layout.addWidget(self.canvas_firstImage, 12,0)
            
            inputpath = str('Chosen folder: ' + str(self.OHW.inputpath))
            self.label_chosen_image.setText(inputpath)
            self.button_getMVs.setEnabled(True)
            self.button_succeed_tab1.setStyleSheet("background-color: YellowGreen")
            
            #display results folder and enable change of this folder
            current_folder = 'Current results folder: ' + str(pathlib.PureWindowsPath(self.OHW.results_folder))
            self.label_resultsfolder.setText(current_folder)
            self.button_change_resultsfolder.setEnabled(True)
        
        def on_change_resultsfolder(self):
            print('yeah')
            #choose a folder
            msg = 'Choose a new folder for saving your results'
            folderName = UserDialogs.chooseFolderByUser(msg)  
            
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (folderName == ''):
                return
            
            #change the results folder of the OHW class
            self.OHW.results_folder = pathlib.Path(folderName)
            print('New results folder:')
            print(folderName)
            
            #display new results folder
            current_folder = 'Current results folder: ' + str(pathlib.PureWindowsPath(self.OHW.results_folder))
            self.label_resultsfolder.setText(current_folder)
            
        def on_loadFile(self):
            #choose a file
            msg = 'Choose an input file of type .mp4, .avi, .mov'
            fileName = UserDialogs.chooseFileByUser(msg)     
            
            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (fileName == ''):
                return
                   
            #self.OHW.read_imagestack(fileName[0])  
            read_imagestack_thread = self.OHW.read_imagestack_thread(fileName[0])
            read_imagestack_thread.start()
            #self.progressbar_tab1.setFormat("loading Folder")  #is not displayed yet?
            self.progressbar_tab1.setRange(0,0)
            read_imagestack_thread.finished.connect(self.finish_loadFile)
            
        
        def finish_loadFile(self):
            self.progressbar_tab1.setRange(0,1)
            self.progressbar_tab1.setValue(1)
            
            self.line_fps.setText(str(self.OHW.videoMeta['fps']))
            self.line_px_perMicron.setText(str(self.OHW.videoMeta['microns_per_pixel']))
            
            # display first image and update controls
            self.imshow_firstImage = self.ax_firstIm.imshow(self.OHW.rawImageStack[0], cmap = 'gray', vmin = self.OHW.videoMeta["Blackval"], vmax = self.OHW.videoMeta["Whiteval"])
            self.canvas_firstImage.draw()            
            self.tab1.layout.addWidget(self.canvas_firstImage, 12,0) 
            
            inputpath = str('Chosen file: ' + str(self.OHW.inputpath))
            self.label_chosen_image.setText(inputpath)
            self.button_getMVs.setEnabled(True)
            self.button_succeed_tab1.setStyleSheet("background-color: YellowGreen")
            
            #display results folder and enable change of this folder
            current_folder = 'Current results folder: ' + str(pathlib.PureWindowsPath(self.OHW.results_folder))
            self.label_resultsfolder.setText(current_folder)
            self.button_change_resultsfolder.setEnabled(True)
        
        
        def defineVideoInfos(self, file_location, processtype='single'):
           
            # infofile = "videoinfos.txt"
            filereader = open(file_location,"r")
            self.videoinfos = eval(filereader.read())
            filereader.close()
            
            if processtype=='single':
                # get the data saved in the videofile
                self.px_per_micron = 1/(self.videoinfos['microns_per_pixel'])
                self.fps = self.videoinfos['fps']
                self.Blackval = self.videoinfos['Blackval']
                self.Whiteval = self.videoinfos['Whiteval']
            
#                #if there is a video-file: overwrite with fps from videofile
#                for file in os.listdir(self.folderName):
#                    if file.endswith((".mp4", ".avi")): 
#                        #extract the fps directly from the video file
#                        video = cv2.VideoCapture(self.folderName + '/' + file)
#                        self.fps = video.get(cv2.CAP_PROP_FPS)
#                        video.release()
                        
                # update the corresponding labels
                self.label_fps.setText('Framerate (as in videoinfo-file) [frames/sec]:')
                self.line_fps.setText(str(self.fps))
                self.line_fps.setEnabled(False)
                
                self.label_px_per_micron.setText('Number of micrometer per pixel (as in videoinfo-file): ')
                self.line_px_perMicron.setText(str(self.px_per_micron))            
                self.line_px_perMicron.setEnabled(False)
            
            elif processtype=='batch':
                self.px_per_micron_batch = 1/(self.videoinfos['microns_per_pixel'])
                self.fps_batch = self.videoinfos['fps']
                self.Blackval_batch = self.videoinfos['Blackval']
                self.Whiteval_batch = self.videoinfos['Whiteval']
                 
        def displayImage(self, folderName):
            #oli:
            #height, width, channel = self.imageStack[0].shape
            height, width = self.imageStack[0].shape
#            adjustedImage = exposure.rescale_intensity(self.imageStack[0], in_range=(self.Blackval, self.Whiteval))
#            print(adjustedImage)
#            print(self.imageStack[0])
  
  #          plt.imshow(self.imageStack[0], cmap = 'gray', vmin = self.Blackval, vmax = self.Whiteval)

            self.imshow_firstImage = self.ax_firstIm.imshow(self.imageStack[0], cmap = 'gray', vmin = self.Blackval, vmax = self.Whiteval)
            self.canvas_firstImage.draw()
            
            self.tab1.layout.addWidget(self.canvas_firstImage, 11,0)
            # --> klappt so mit richtiger Skalierung
            
            #old:
#            #read image and display it
#            height, width, channel = self.imageStack[0].shape
#            bytesPerLine = 3 * width
#            qImg = QImage(self.imageStack[0].data, width, height, bytesPerLine, QImage.Format_RGB888)
#            img = QPixmap(qImg)
#                
#            height_of_label = 250
#            self.image.resize(self.width(), height_of_label)
#            self.image.setPixmap(img.scaled(self.image.size(), Core.Qt.KeepAspectRatio))
#        
            #source = str('Chosen folder: ' + folderName)
            #self.label_chosen_image.setText(source)    
            #self.button_succeed_tab1.setStyleSheet("background-color: YellowGreen")
            #self.button_measure.setEnabled(True)
        
        def changeBlockwidth(self):
            self.blockwidth = self.spinbox_blockwidth.value()
            return self.blockwidth
        
        def changeDelay(self):
            self.delay = self.spinbox_delay.value()
            return self.delay    
        
        def changeMaxShift(self):
            self.maxShift = self.spinbox_maxShift.value()
            return self.maxShift
        
        def changeFPS(self):
            self.OHW.videoMeta['fps'] = np.float(self.line_fps.text())
        
        def changePxPerMicron(self):
            self.OHW.videoMeta['microns_per_pixel'] = np.float(self.line_px_perMicron.text())
    
        def on_detectPeaks(self):
            #detect peaks and draw them as EKG
            
            ratio = self.spinbox_ratio.value()
            number_of_neighbours = self.spinbox_neighbours.value()
            self.OHW.detect_peaks(ratio, number_of_neighbours)
            self.updatePeaks()

        def updatePeaks(self):
            """
                update detected peaks in graph
            """
            
            Peaks = self.OHW.get_peaks()     
            
            # clear old peaks first
            if self.plotted_peaks == True:
                self.highpeaks.remove()
                self.lowpeaks.remove()
                self.plotted_peaks = False
            
            #self.ax_kinetics.cla()
            #self.ax_kinetics.plot(self.OHW.timeindex, self.OHW.mean_absMotions, '-', linewidth = 2) #self.fig_kinetics

            if Peaks["t_peaks_low_sorted"] != None:
                # plot peaks, low peaks are marked as triangles , high peaks are marked as circles         
                self.highpeaks, = self.ax_kinetics.plot(Peaks["t_peaks_low_sorted"], Peaks["peaks_low_sorted"], marker='o', ls="", ms=5, color='r' )
                self.lowpeaks, = self.ax_kinetics.plot(Peaks["t_peaks_high_sorted"], Peaks["peaks_high_sorted"], marker='^', ls="", ms=5, color='r' )  #easier plotting without for loop          
                self.plotted_peaks = True
                
            self.canvas_kinetics.draw()

            peakstatistics = self.OHW.get_peakstatistics()
            peaktime_intervals = self.OHW.get_peaktime_intervals()
            bpm = self.OHW.get_bpm()
            
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
            
            self.OHW.export_peaks()
            
            #display a message for successful saving
            msg_text = 'Raw and analyzed peaks were successfully saved' # to: ' + text_for_saving
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass  
            
        def on_exportEKG_CSV(self):
            
            self.OHW.exportEKG_CSV()
            
            #display a message for successful saving
            msg_text = 'EKG values were successfully saved' # to: ' + save_file
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass  

            
        def on_exportStatistics(self):
            
            self.OHW.exportStatistics()
            
            #display a message for successful saving
            msg_text = 'Statistics were successfully saved' # to: ' + save_file
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass 

            
        def on_saveKinetics(self):
            
            mark_peaks = self.plotted_peaks
            
            #allowed file types:
            file_types = "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.tiff);;BMP(*.bmp);; Scalable Vector Graphics (*.svg)"
            #let the user choose a folder from the starting path
            path = str(pathlib.PureWindowsPath(self.OHW.results_folder / 'beating_kinetics.PNG'))
            filename_save = QFileDialog.getSaveFileName(None, 'Choose a folder and enter a filename', path, file_types)

            #if 'cancel' was pressed: simply do nothing and wait for user to click another button
            if (filename_save == ('','')):
                return
            try:
                self.OHW.plot_beatingKinetics(mark_peaks, filename_save)
                mainWidget = self.findMainWindow()
                mainWidget.adjustSize()
                #print(filename_save[0])
                print('Graphs were saved successfully.')
                
            except (IndexError, NameError, AttributeError):
                pass
            
        
        def on_getMVs(self):
            #get current parameters entered by user
            blockwidth = self.changeBlockwidth()
            maxShift = self.changeMaxShift()
            delay = self.changeDelay()
            
            if self.scaling_status == True:
                self.OHW.scale_ImageStack()
            else:
                self.OHW.scale_ImageStack(self.OHW.rawImageStack.shape[0][1])   # too hacky, refactor...
                
            self.OHW.calculate_MVs_threaded(blockwidth = blockwidth, delay = delay, max_shift = maxShift)#   16,2,7 as standard
                        
            self.OHW.thread_BM_stack.finished.connect(self.initialize_calculatedMVs)
            self.OHW.thread_BM_stack.progressSignal.connect(self.updateProgressBar)
            #self.initialize_calculatedMVs()
        
        def updateProgressBar(self, value):
                self.progressbar_tab2.setValue(value*100)
        
        def initialize_calculatedMVs(self):
        
            self.OHW.initialize_calculatedMVs()
            #set the succeed button to green:
            self.button_succeed_tab2.setStyleSheet("background-color: YellowGreen")
                
            #enable other buttons for further actions
            self.button_save_motionVectors.setEnabled(True)
            self.button_detectPeaks.setEnabled(True)
            self.button_saveKinetics.setEnabled(True)
            self.button_heatmaps_video.setEnabled(True)
            self.button_quivers_video.setEnabled(True)
            #self.button_time_avg_motion.setEnabled(True)
            
            #create sliders for heatmaps and quivers
            self.tab4.layout.addWidget(self.label_slider_info,      7,0)
            self.tab4.layout.addWidget(self.label_slider_quivers,   7,2)
            self.tab4.layout.addWidget(self.slider_heatmaps,        8,0)
            self.tab4.layout.addWidget(self.slider_quiver,          8,2)

            
            self.initialize_kinetics()
            
            # fill graphs with data from first frame
            self.initialize_MV_graphs()
                        
            # initialize time averaged motion
            self.initializeTimeAveragedMotion()

            #enable saving heatmap and quiver frames
            self.button_save_Heatmap.setEnabled(True)
            self.button_save_Quiver.setEnabled(True)
            
            #enable saving time averaged motion
            self.button_save_timeMotion.setEnabled(True)
        
        def startMeasurement(self):
            #get current parameters entered by user
            blockwidth = self.changeBlockwidth()
            maxShift = self.changeMaxShift()
            delay = self.changeDelay()
            px_per_micron = self.changePxPerMicron()
            fps = self.changeFPS()
            
            # new button where results_folder can be directly specified
            # use inputfolder/results as standard for saving
            
            try:
                #user chooses a folder for saving all results to:
                self.save_folder = UserDialogs.chooseFolderByUser('Choose a folder for saving the results: ', self.folderName)
                
                #if 'cancel' was pressed: simply do nothing and wait for user to click another button
                if (self.save_folder == ''):
                    return
                
                #calculate the MotionVectors and plot the corresponding EKG: meanAbsMotions, AbsMotions_trans und MaxMotions sind schon umgerechnet!
                #depending on filter_status MotionVectors will be filtered or not
                print('The MotionVectors are being calculated.')
                
                #start a new thread for calculation of motion vectors:
                self.thread_motionvectors = MotionVectorThread_file.MotionVectorThread(blockwidth, delay, maxShift, self.folderName, fps, 
                                                                                       self.save_folder, px_per_micron, self.filter_status, 
                                                                                       self.factor_scaling, self.imageStack)
                #connect the output signals to the main thread:
                self.thread_motionvectors.signal_receiveMV.connect(self.receiveMotionVectors)
                self.thread_motionvectors.maxProgress.connect(self.setMaximumProgressbar)
                self.thread_motionvectors.progressSignal.connect(self.updateProgressbar)
                
                #start the thread:
                self.thread_motionvectors.start()  #check when finished?
                self.button_getMVs.setEnabled(False)
 
            except NameError:
                #display a warning 
                msg_Text = 'Choose a folder before starting the calculation of the motion vectors!'
                msg_Title = 'Warning'
                msg = QMessageBox.warning(self, msg_Title, msg_Text, QMessageBox.Ok)
             
                if msg == QMessageBox.Ok:
                    pass

        def initialize_kinetics(self):
            """
                initializes graph for beating kinetics "EKG"
            """
            print("initialize beating kinetics graphs")
            
            self.ax_kinetics.plot(self.OHW.timeindex, self.OHW.mean_absMotions, '-', linewidth = 2) #self.fig_kinetics
            self.ax_kinetics.set_xlim(left = 0, right = self.OHW.timeindex[-1])
            self.fig_kinetics.subplots_adjust(bottom = 0.2)
            
            #self.ax.set_title('Beating kinetics', fontsize = 26)
            self.ax_kinetics.set_xlabel('t [s]', fontsize = 22)
            self.ax_kinetics.set_ylabel(u'Mean Absolute Motion [\xb5m/s]', fontsize = 18)
            self.ax_kinetics.tick_params(labelsize = 20)
            
            self.ax_kinetics.spines['top'].set_linewidth(2)
            self.ax_kinetics.spines['right'].set_linewidth(2)
            self.ax_kinetics.spines['bottom'].set_linewidth(2)
            self.ax_kinetics.spines['left'].set_linewidth(2)            
            
            self.canvas_kinetics.draw()
            
                    
        def initialize_MV_graphs(self):
            print("initialize MV graphs")
            # initialize heatmaps, display first frame
            
            #print("shape of unitMVs", self.OHW.unitMVs.shape)
            #print("shape of absMotions", self.OHW.absMotions.shape)
            
            #max_motion = self.mean_maxMotion    #np.max(self.MaxMotions_trans)
            #scale_max = np.mean(self.OHW.absMotions)    #should be mean of 1d-array of max motions
            
            scale_max = np.mean(np.max(self.OHW.absMotions,axis=(1,2)))
                        
            self.imshow_heatmaps = self.ax_heatmaps.imshow(self.OHW.absMotions[0], vmin = 0, vmax = scale_max, cmap = 'jet', interpolation = 'bilinear')
            self.slider_heatmaps.setMaximum(self.OHW.absMotions.shape[0]-1)
            
            """
            # Titel noch nicht in GUI hinzufügen bzw. Größe anpassen...
            cbar_heatmaps = self.fig_heatmaps.colorbar(self.imshow_heatmaps)
            cbar_heatmaps.ax.tick_params(labelsize=20)
            for l in cbar_heatmaps.ax.yaxis.get_ticklabels():
                l.set_weight("bold")
            self.ax_heatmaps.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')            
            """
            
            self.canvas_heatmap.draw()
            self.tab4.layout.addWidget(self.canvas_heatmap, 6, 0)
                       
            # initialize quivers, display first frame
           
            draw_scalebar = True
            if draw_scalebar:
                self.OHW.plot_scalebar()

            self.MV_zerofiltered = Filters.zeromotion_to_nan(self.OHW.unitMVs, copy=True)
            self.MotionX = self.MV_zerofiltered[:,0,:,:]
            self.MotionY = self.MV_zerofiltered[:,1,:,:]
            self.slider_quiver.setMaximum(self.MotionX.shape[0]-1)

            blockwidth = self.OHW.MV_parameters["blockwidth"]
            microns_per_pixel = self.OHW.videoMeta["microns_per_pixel"]
            scalingfactor = self.OHW.scalingfactor
            scale_max = np.mean(np.max(self.OHW.absMotions,axis=(1,2)))
            
            #print("before draw quiver canvas", self.OHW.scaledImageStack[0].shape, self.OHW.videoMeta["Blackval"], self.OHW.videoMeta["Whiteval"])
            
            arrowscale = scale_max / (blockwidth * microns_per_pixel / scalingfactor) #0.07 previously
            self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.OHW.scaledImageStack.shape[1], blockwidth), np.arange(blockwidth/2, self.OHW.scaledImageStack.shape[2], blockwidth))
            
            self.imshow_quivers = self.ax_quivers.imshow(self.OHW.scaledImageStack[0], cmap = "gray", vmin = self.OHW.videoMeta["Blackval"], vmax = self.OHW.videoMeta["Whiteval"])
            self.quiver_quivers = self.ax_quivers.quiver(self.MotionCoordinatesX, self.MotionCoordinatesY, self.MotionX[0], self.MotionY[0], pivot='mid', color='r', units ="xy", scale = arrowscale)    #adjust scale to max. movement and mpp value
            # abs. quiver length: µm/s --> 0.5 x-axis units
            # scale: Number of data units per arrow length unit: A/L --> l = a*(L/A) = a * scale^-1
            # max: blockwidth --> scale = max / (blockwidth * microns_per_pixel)
            
            self.canvas_quivers.draw()
            self.tab4.layout.addWidget(self.canvas_quivers,  6,  2)

        def on_saveMVs(self):
            """
                saves raw MVs to results folder
            """
            self.OHW.save_MVs()
            
            #display a message for successful saving
            msg_text = 'Motion vectors were successfully saved' # to: ' + save_file
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass
            
        def findMainWindow(self): #-> typing.Union[QMainWindow, None]:
            # Global function to find the (open) QMainWindow in application
            app = QApplication.instance()
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    return widget
            return None
        
        def restartGUI(self):
            #restarts the application to work with new data
            mainWidget = self.findMainWindow()
            mainWidget.restartGUI()
        
        def updateHeatMap(self, frame):
            #callback when slider is moved
            self.imshow_heatmaps.set_data(self.OHW.absMotions[frame])
            self.canvas_heatmap.draw()
 
        def updateQuiver(self, frame):
            #callback when slider is moved
            self.imshow_quivers.set_data(self.OHW.scaledImageStack[frame])
            self.quiver_quivers.set_UVC(self.MotionX[frame], self.MotionY[frame])
            self.canvas_quivers.draw()

        def on_saveHeatmapvideo(self):
            """
                saves the heatmpavideo
            """

            save_heatmap_thread = self.OHW.save_heatmap_thread(singleframe = False)
            save_heatmap_thread.start()
            self.progressbar_heatmaps.setRange(0,0)
            save_heatmap_thread.finished.connect(self.finish_saveHeatmapvideo)
        
        def finish_saveHeatmapvideo(self):

            self.progressbar_heatmaps.setRange(0,1)
            self.progressbar_heatmaps.setValue(1)
            #display a message for successful saving            
            msg_text = 'Heatmap video was saved successfully' # to: ' + heatmap_filename
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass
            
            #set succeed button to green if video creation finished
            self.button_succeed_heatmaps.setStyleSheet("background-color: YellowGreen")            
        
        def on_saveHeatmap(self):
            """
                saves the selected frame (singleframe = framenumber)
            """
            singleframe=self.slider_heatmaps.value()
            self.OHW.save_heatmap(singleframe = singleframe)

            #display a message for successful saving            
            msg_text = 'Heatmap of frame ' + str(singleframe) + ' was saved successfully' # to: ' + heatmap_filename
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass
        
        def on_saveQuivervideo(self):
            """
                saves the quivervideo
            """

            save_quiver_thread = self.OHW.save_quiver_thread(singleframe = False)
            save_quiver_thread.start()
            self.progressbar_quivers.setRange(0,0)
            save_quiver_thread.finished.connect(self.finish_saveQuivervideo)    
            
        def finish_saveQuivervideo(self):
            self.progressbar_quivers.setRange(0,1)
            self.progressbar_quivers.setValue(1)
            
            #display a message for successful saving
            msg_text = 'Quiver was saved successfully'  # to: ' + quivers_filename
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass      

            #set succeed button to green if video creation finished
            self.button_succeed_quivers.setStyleSheet("background-color: YellowGreen")

            
        def on_saveQuiver(self):
            """
                saves either the selected frame (singleframe = framenumber) or the whole heatmap video
            """     
            
            singleframe = self.slider_quiver.value()
            self.OHW.save_quiver(singleframe = singleframe)
            
            #display a message for successful saving
            msg_text = 'Quiver of frame ' + str(singleframe) + ' was saved successfully'  # to: ' + quivers_filename
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass                    

        def slider_heatmaps_valueChanged(self):
            #only allow slider to change value if MVs were calculated
            if self.button_save_motionVectors.isEnabled():
                frame = self.slider_heatmaps.value()
                time = round(frame / self.OHW.videoMeta["fps"], 3)
                self.updateHeatMap(frame)
                self.label_heatmap_result.setText('Heatmap of frame ' + str(frame) + ' at time ' + str(time) + 'sec')
        
        def slider_quiver_valueChanged(self): 
            #only allow slider to change value if MVs were calculated
            if self.button_save_motionVectors.isEnabled():
                frame = self.slider_quiver.value()
                time = round(frame / self.OHW.videoMeta["fps"], 3)
                self.updateQuiver(frame)
                self.label_quiver_result.setText('Quiverplot of frame ' + str(frame) + ' at time ' + str(time) + ' sec')            
                
        def initializeTimeAveragedMotion(self): 
            max_motion = self.OHW.max_avgMotion
            
            self.imshow_motion_total = self.ax_motion_total.imshow(self.OHW.avg_absMotion, vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")#, cmap = 'gray', vmin = self.Blackval, vmax = self.Whiteval)
            self.imshow_motion_x = self.ax_motion_x.imshow(self.OHW.avg_MotionX, vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
            self.imshow_motion_y = self.ax_motion_y.imshow(self.OHW.avg_MotionY, vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
            
            self.canvas_motion_total.draw()
            self.canvas_motion_x.draw()
            self.canvas_motion_y.draw()
            
            self.tab5.layout.addWidget(self.canvas_motion_total, 4,0)
            self.tab5.layout.addWidget(self.canvas_motion_x, 6,0)
            self.tab5.layout.addWidget(self.canvas_motion_y, 6,1)
            
            self.button_succeed_motion.setStyleSheet("background-color: YellowGreen")
            self.button_save_timeMotion.setEnabled(True)
            
            self.OHW.plot_TimeAveragedMotions('.png')
                
        def on_saveTimeAveragedMotion(self):
            
            file_ext = self.combo_avgExt.currentText()
            self.OHW.plot_TimeAveragedMotions(file_ext)
            
            #display a message for successful saving
            msg_text = 'Plots of time averaged motion were saved successfully.'
            msg_title = 'Successful'
            msg = QMessageBox.information(self, msg_title, msg_text, QMessageBox.Ok)
            if msg == QMessageBox.Ok:
                pass
            
        def changeStatus(self):
            #handle changes of filterstatus
            if self.sender() == self.check_filter:
                self.filter_status = self.check_filter.isChecked()
            
            #handle changes of batch scaling
            elif self.sender() == self.batch_checkScaling:
                self.batch_scaling_status = self.batch_checkScaling.isChecked()
                if (self.batch_scaling_status == True):
                    self.batch_factor_scaling = 1024
                elif (self.batch_scaling_status == False): 
                    self.batch_factor_scaling = 2048
            
            #handle changes of scaling options
            elif self.sender() == self.check_scaling:
                self.scaling_status = self.check_scaling.isChecked()
                if (self.scaling_status == True):
                    self.factor_scaling = 1024
                elif (self.scaling_status == False): 
                    self.factor_scaling = 2048
            
            #handle changes of batch filter option
            elif self.sender() == self.batch_checkFilter:
                self.batch_filter_status = self.batch_checkFilter.isChecked()
                
            #handle changes of save motion vector option
            elif self.sender() == self.batch_checkSaveMotionVectors:
                self.batch_saveMotionVectors_status = self.batch_checkSaveMotionVectors.isChecked()
                
            #handle changes of batch heatmap option
            elif self.sender() == self.batch_checkHeatmaps:
                self.batch_heatmap_status = self.batch_checkHeatmaps.isChecked()
            
            #handle changes of batch quiver option
            elif self.sender() == self.batch_checkQuivers:
                self.batch_quiver_status = self.batch_checkQuivers.isChecked()
