import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, 
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TabMotion(QWidget):
    
    def __init__(self, parent):
        super(TabMotion, self).__init__(parent)
        self.parent=parent
        self.initUI()
        
    def initUI(self):
        self.info = QTextEdit()
        self.info.setText('In this tab you set the settings for the block-matching algorithm and perform the calculation of the motion vectors or import an old analysis.')
        self.info.setReadOnly(True)
        self.info.setFixedHeight(50)
        self.info.setFixedWidth(700)
        self.info.setStyleSheet("background-color: LightSkyBlue")
        
        self.label_settings = QLabel('Settings: ')
        self.label_settings.setFont(QFont("Times",weight=QFont.Bold))
        self.label_addOptions = QLabel('Additional options: ')
        self.label_addOptions.setFont(QFont("Times",weight=QFont.Bold))
        
        #user settings
        #... adjust these according to selected algorithm and available options
        self.label_blockwidth =  QLabel('Blockwidth (in pixels):')
        self.label_delay =       QLabel('Delay (in frames): ')
        self.label_maxShift =    QLabel('Maximum shift p (in pixels): ')
        self.spinbox_blockwidth = QSpinBox()
        self.spinbox_delay = QSpinBox()
        self.spinbox_maxShift = QSpinBox()
        
        #settings for the spinboxes
        self.spinbox_blockwidth.setRange(2,128)
        self.spinbox_blockwidth.setSingleStep(1)
        self.spinbox_blockwidth.setSuffix(' pixels')
        self.spinbox_blockwidth.setValue(int(self.parent.config['DEFAULT VALUES']['blockwidth']))
        self.spinbox_delay.setRange(1,10)
        self.spinbox_delay.setSuffix(' frames')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_delay.setValue(int(self.parent.config['DEFAULT VALUES']['delay']))
        self.spinbox_maxShift.setSuffix(' pixels')
        self.spinbox_maxShift.setValue(int(self.parent.config['DEFAULT VALUES']['maxShift']))
        
        self.check_scaling = QCheckBox('Scale the longest side to 1024 px during calculation')
        self.check_scaling.setChecked(True) #connect with config here!
        
        #enable/disable filtering
        self.check_filter = QCheckBox("Filter motion vectors during calculation")
        self.check_filter.setChecked(True)#connect with config here!
        
        self.button_getMVs = QPushButton('Calculate motion vectors')
        #self.button_getMVs.resize(self.button_getMVs.sizeHint())
        self.button_getMVs.clicked.connect(self.parent.on_getMVs)
        self.button_getMVs.setEnabled(False)
        self.button_getMVs.setFixedWidth(150)
        
        self.button_save_MVs = QPushButton('Save motion vectors')
        #self.button_save_MVs.resize(self.button_save_MVs.sizeHint())
        self.button_save_MVs.clicked.connect(self.parent.on_saveMVs)
        self.button_save_MVs.setEnabled(False)
        self.button_save_MVs.setFixedWidth(150)
        
        self.btn_load_ohw = QPushButton('Load motion analysis')
        self.btn_load_ohw.clicked.connect(self.parent.on_load_ohw)
        self.btn_load_ohw.setFixedWidth(150)
        
        #succed-button
        self.button_succeed_MVs = QPushButton('No motion available yet. Calculate new one or load old')
        self.button_succeed_MVs.setStyleSheet("background-color: IndianRed")
        
        #progressbar in tab2    
        self.progressbar_MVs = QProgressBar(self)
        self.progressbar_MVs.setMaximum(100)
        self.progressbar_MVs.setValue(0)
        
        self.grid_overall = QGridLayout()#self._main)
        
        self.grid_overall.addWidget(self.info, 0,0,1,4)
        self.grid_overall.addWidget(self.label_settings, 1,0)
        self.grid_overall.addWidget(self.label_blockwidth,2,0)
        self.grid_overall.addWidget(self.spinbox_blockwidth,2,1)
        self.grid_overall.addWidget(self.label_delay,3,0)
        self.grid_overall.addWidget(self.spinbox_delay, 3,1)
        self.grid_overall.addWidget(self.label_maxShift,4,0)
        self.grid_overall.addWidget(self.spinbox_maxShift,4,1)
        self.grid_overall.addWidget(self.label_addOptions, 5,0)
        self.grid_overall.addWidget(self.check_scaling, 6,0,1,2)
        self.grid_overall.addWidget(self.check_filter, 7,0,1,2)
        self.grid_overall.addWidget(self.button_getMVs, 9,0)
        self.grid_overall.addWidget(self.button_save_MVs, 9,1)
        self.grid_overall.addWidget(self.btn_load_ohw,9,2)        
        self.grid_overall.addWidget(self.progressbar_MVs, 10,0,1,3)
        self.grid_overall.addWidget(self.button_succeed_MVs, 11,0,1,3)
        
        self.grid_overall.setSpacing(15)        
        self.grid_overall.setAlignment(Qt.AlignTop|Qt.AlignLeft)      
        self.setLayout(self.grid_overall)

        for label in self.findChildren(QLabel):
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for LineEdit in self.findChildren(QLineEdit):
            LineEdit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for Slider in self.findChildren(QSlider):
            Slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for SpinBox in self.findChildren(QSpinBox):
            SpinBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for CheckBox in self.findChildren(QCheckBox):
            CheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #for btn in self.findChildren(QPushButton):
        #    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
    def init_values(self, config):
        """
            set values from config
        """
        pass