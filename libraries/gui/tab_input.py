import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import QLabel, QLineEdit, QGridLayout, QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TabInput(QWidget):
#Python classes follow the CapWords convention
    
    def __init__(self, parent):
        super(TabInput, self).__init__(parent)
        self.initUI()
        
    def initUI(self):
    
        self.info = QTextEdit()
        self.info.setText('In this tab you choose the input video. If a videoinfos.txt file is found, the information is processed automatically. Otherwise, please enter the framerate and microns per pixel.')
        self.info.setReadOnly(True)
        self.info.setMinimumWidth(700)
        self.info.setMaximumHeight(50)
        self.info.setMaximumWidth(800)
        self.info.setStyleSheet("background-color: LightSkyBlue")
    
        self.label_vidinfo = QLabel('Video info:')
        self.label_vidinfo.setFont(QFont("Times",weight=QFont.Bold))
        
        self.label_fps = QLabel('framerate [frames/s]')
        self.label_mpp = QLabel('scale [microns/pixel]')
        self.label_path = QLabel('Video path')
        self.label_input_path = QLabel('Path/...')
        self.label_results = QLabel('Current results folder')
        self.label_results_folder = QLabel('Path/results....')
        
        self.btn_results_folder = QPushButton('Change results folder')
        self.btn_results_folder.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.btn_results_folder.setEnabled(False)
        self.btn_results_folder.clicked.connect(self.parent().on_changeResultsfolder)
        
        #display first image
        self.fig_firstIm, self.ax_firstIm = plt.subplots(1,1)#, figsize = (5,5))
        self.fig_firstIm.patch.set_facecolor('#ffffff')##cd0e49')
        #self.ax_firstIm.axis('off')
        self.canvas_firstImage = FigureCanvas(self.fig_firstIm)
        self.canvas_firstImage.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.canvas_firstImage.setFixedSize(500,500)

        self.label_fps.setFixedWidth(120)
        
        self.edit_fps = QLineEdit()
        self.edit_mpp = QLineEdit()
        
        self.edit_fps.setFixedWidth(50)
        self.edit_mpp.setFixedWidth(50)
        
        self.button_loadVideo = QPushButton('Load video')
        self.button_loadVideo.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.button_loadVideo.clicked.connect(self.parent().on_loadVideo)
        
        self.progressbar_loadVideo = QProgressBar()#self)
        self.progressbar_loadVideo.setMaximum(1)  
        self.progressbar_loadVideo.setValue(0)
        self.progressbar_loadVideo.setFixedWidth(250)
        self.progressbar_loadVideo.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                
        self.label_slider_blackval = QLabel('Black value')
        self.slider_blackval = QSlider(Qt.Vertical)
        self.slider_blackval.setMinimum(0)
        self.slider_blackval.setMaximum(100)
        self.slider_blackval.setValue(0)
        self.slider_blackval.setFixedHeight(200)
        self.slider_blackval.setEnabled(False)
        self.slider_blackval.valueChanged.connect(self.parent().on_change_blackVal)
        
        self.label_slider_whiteval = QLabel('White value')
        self.slider_whiteval = QSlider(Qt.Vertical)
        self.slider_whiteval.setMinimum(0)
        self.slider_whiteval.setMaximum(100)
        self.slider_whiteval.setValue(0)
        self.slider_whiteval.setFixedHeight(200)
        self.slider_whiteval.setEnabled(False)
        self.slider_whiteval.valueChanged.connect(self.parent().on_change_whiteVal)
        
        self.label_brightness = QLabel('Adjust brightness:')
        self.label_brightness.setFont(QFont("Times",weight=QFont.Bold))
        
        self.btn_brightness = QPushButton('Reset brightness')
        self.btn_brightness.clicked.connect(self.parent().on_resetBrightness)
        
        self.grid_prop = QGridLayout()        
        self.grid_prop.setSpacing(10)
        self.grid_prop.setAlignment(Qt.AlignTop|Qt.AlignLeft)
               
        self.grid_prop.addWidget(self.button_loadVideo,0,0)
        self.grid_prop.addWidget(self.progressbar_loadVideo,0,1)
        self.grid_prop.addWidget(self.label_vidinfo,1,0,1,2)
        self.grid_prop.addWidget(self.label_path,2,0)
        self.grid_prop.addWidget(self.label_input_path,2,1)
        self.grid_prop.addWidget(self.label_fps, 3, 0)
        self.grid_prop.addWidget(self.edit_fps, 3, 1)
        self.grid_prop.addWidget(self.label_mpp, 4, 0)
        self.grid_prop.addWidget(self.edit_mpp, 4, 1)
        self.grid_prop.addWidget(self.label_results,5,0)
        self.grid_prop.addWidget(self.label_results_folder,5,1)
        self.grid_prop.addWidget(self.btn_results_folder,6,0,1,2)
        
        self.grid_slider = QGridLayout()
        self.grid_slider.setSpacing(10)
        self.grid_slider.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_slider.addWidget(self.label_brightness,0,0,1,2)
        self.grid_slider.addWidget(self.label_slider_blackval,1,0)
        self.grid_slider.addWidget(self.label_slider_whiteval,1,1)
        self.grid_slider.addWidget(self.slider_blackval,2,0, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.slider_whiteval,2,1, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.btn_brightness,1,2)
             
        self.grid_overall = QGridLayout()#self._main)
        self.grid_overall.addWidget(self.info,0,0,1,2)
        self.grid_overall.addLayout(self.grid_prop,1,0)
        self.grid_overall.addLayout(self.grid_slider,2,0,Qt.AlignTop|Qt.AlignLeft) # has to be added here?
        self.grid_overall.addWidget(self.canvas_firstImage,1,1,2,1,Qt.AlignTop|Qt.AlignLeft)#-1,1
        self.grid_overall.setAlignment(Qt.AlignTop|Qt.AlignLeft)      
        
        self.setLayout(self.grid_overall) 

        for label in self.findChildren(QLabel):
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for LineEdit in self.findChildren(QLineEdit):
            LineEdit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for Slider in self.findChildren(QSlider):
            Slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)