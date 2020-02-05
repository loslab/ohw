import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from libraries import helpfunctions

class TabTA(QWidget):
    """
        for time averaged motion
    """
    
    def __init__(self, parent):
        super(TabTA, self).__init__(parent)
        self.initUI()
        self.parent=parent
        
    def initUI(self):
    
        self.info = QTextEdit()
        self.info.setText('In this tab you can save the time averaged motion: absolute contractility and contractility in x- and y-direction.')
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(50)
        self.info.setFixedWidth(700)
        self.info.setStyleSheet("background-color: LightSkyBlue")
        
        self.label_TA = QLabel('Motion averaged over time')
        self.label_TA.setFont(QFont("Times",weight=QFont.Bold))
        
        """
        #create a label for choosing the ROI
        label_timeavg_chooseROI = QLabel('Choose the ROI to be displayed: ')
        label_timeavg_chooseROI.setFont(QFont("Times",weight=QFont.Bold))
        
        
        #create a drop-down menu for choosing the ROI to be displayed
        self.timeavg_combobox = QComboBox()
        self.timeavg_combobox.addItem('Full image')    
        self.timeavg_combobox.currentIndexChanged[int].connect(self.on_chooseROI)
        """
        
        #display the calculated time averaged motion
        self.label_TA_tot = QLabel('Absolute contractility:')
        self.label_TA_x = QLabel('Contractility in x-direction:')
        self.label_TA_y = QLabel('Contractility in y-direction:')
                
        # create mpl figurecanvas for display of averaged motion
        self.fig_TA_tot, self.ax_TA_tot = plt.subplots(1,1, figsize = (16,12))
        self.fig_TA_x, self.ax_TA_x = plt.subplots(1,1, figsize = (16,12))
        self.fig_TA_y, self.ax_TA_y = plt.subplots(1,1, figsize = (16,12))
        
        self.fig_TA_tot.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.fig_TA_x.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.fig_TA_y.subplots_adjust(bottom=0, top=1, left=0, right=1)
        
        self.canvas_TA_tot = FigureCanvas(self.fig_TA_tot)
        self.canvas_TA_x = FigureCanvas(self.fig_TA_x)
        self.canvas_TA_y = FigureCanvas(self.fig_TA_y)
        
        self.canvas_TA_tot.setFixedSize(500,500)
        self.canvas_TA_x.setFixedSize(500,500)
        self.canvas_TA_y.setFixedSize(500,500)
        
        #button for saving plots
        self.label_save_TA = QLabel('Save the plots as: ')
        self.btn_save_TA = QPushButton('Click for saving')
        #self.btn_save_TA.resize(self.button_save_timeMotion.sizeHint())
        self.btn_save_TA.clicked.connect(self.on_saveTimeAveragedMotion)
        self.btn_save_TA.setEnabled(False)
        
        #combobox for file extensions
        self.combo_TA_ext = QComboBox(self)
        for suffix in ['.png','.jpeg','.tiff','.svg','.eps']:
            self.combo_TA_ext.addItem(suffix)
        
        self.grid_overall = QGridLayout()
        
        self.grid_overall.addWidget(self.info, 0,0,1,3)
        self.grid_overall.addWidget(self.label_TA, 1,0)
        self.grid_overall.addWidget(self.label_TA_tot,2,0)
        self.grid_overall.addWidget(self.label_TA_x,2,1)
        self.grid_overall.addWidget(self.label_TA_y,2,2)
        self.grid_overall.addWidget(self.canvas_TA_tot, 3,0)
        self.grid_overall.addWidget(self.canvas_TA_x,3,1)
        self.grid_overall.addWidget(self.canvas_TA_y,3,2)
        
        self.grid_save = QGridLayout()
        self.grid_save.setSpacing(10)
        self.grid_save.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_save.addWidget(self.label_save_TA, 0,0)
        self.grid_save.addWidget(self.combo_TA_ext, 0,1)
        self.grid_save.addWidget(self.btn_save_TA, 0,2)        
        
        self.grid_overall.addLayout(self.grid_save,4,0,1,3,Qt.AlignTop|Qt.AlignLeft)
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
        
    def init_ohw(self):
        """
            set values from cohw
            enable save button if MVs are present
        """
        if self.parent.cohw.analysis_meta["has_MVs"]:
            self.btn_save_TA.setEnabled(True)
            self.init_TAmotion()
        else:
            self.btn_save_TA.setEnabled(False)
            self.clear_figs()

    def init_TAmotion(self): 
        max_motion = self.parent.cohw.max_avgMotion
        
        self.imshow_motion_total = self.ax_TA_tot.imshow(self.parent.cohw.avg_absMotion, 
            vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
        self.imshow_motion_x = self.ax_TA_x.imshow(self.parent.cohw.avg_MotionX, 
            vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
        self.imshow_motion_y = self.ax_TA_y.imshow(self.parent.cohw.avg_MotionY, 
            vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
        
        self.canvas_TA_tot.draw()
        self.canvas_TA_x.draw()
        self.canvas_TA_y.draw()
    
    def clear_figs(self):
        self.ax_TA_tot.clear()
        self.ax_TA_x.clear()
        self.ax_TA_y.clear()
        
        self.ax_TA_tot.axis('off')
        self.ax_TA_x.axis('off')
        self.ax_TA_y.axis('off')
        
        self.canvas_TA_tot.draw()
        self.canvas_TA_x.draw()
        self.canvas_TA_y.draw()
    
    def on_saveTimeAveragedMotion(self): 
        file_ext = self.combo_TA_ext.currentText()
        self.parent.cohw.plot_TimeAveragedMotions(file_ext)
        helpfunctions.msgbox(self, 'Plots of time averaged motion were saved successfully.')