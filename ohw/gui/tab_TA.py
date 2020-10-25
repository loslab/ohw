import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ohw import helpfunctions

class TabTA(QWidget):
    """
        tab for display of time averaged motion
    """
    
    def __init__(self, parent, ctrl):
        super(TabTA, self).__init__(parent)
        self.update = True # update flag, set when motion calculation changed
        self.parent=parent
        self.ctrl = ctrl
        self.initUI()
        self.init_ohw()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw        

    def initUI(self):
        
        self.label_TA = QLabel('Motion averaged over time')
        self.label_TA.setFont(QFont("Times",weight=QFont.Bold))
        
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
        
        cansize = 350
        self.canvas_TA_tot.setFixedSize(cansize,cansize)
        self.canvas_TA_x.setFixedSize(cansize,cansize)
        self.canvas_TA_y.setFixedSize(cansize,cansize)
        
        #button for saving plots
        self.btn_save_TA = QPushButton('Save plots')
        self.btn_save_TA.clicked.connect(self.on_saveTimeAveragedMotion)
        self.btn_save_TA.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
               
        self.grid_overall = QGridLayout()
        
        self.grid_overall.addWidget(self.label_TA, 0,0)
        self.grid_overall.addWidget(self.label_TA_tot,1,0)
        self.grid_overall.addWidget(self.label_TA_x,1,1)
        self.grid_overall.addWidget(self.label_TA_y,1,2)
        self.grid_overall.addWidget(self.canvas_TA_tot, 2,0)
        self.grid_overall.addWidget(self.canvas_TA_x,2,1)
        self.grid_overall.addWidget(self.canvas_TA_y,2,2)
        self.grid_overall.addWidget(self.btn_save_TA,3,0)
        
        self.grid_overall.setColumnStretch(4,1)
        self.grid_overall.setRowStretch(4,1)

        self.setLayout(self.grid_overall)
        
    def init_ohw(self):
        """
            set values from cohw
            enable save button if MVs are present
        """
        
        # init only if sth changed
        # changes can happen if roi changed/ new motion loaded/...
        #if self.parent.tabstates["tab_TA"]["toupdate"] == True:
        if self.update == True:
       
            self.ceval = self.cohw.ceval
            if self.cohw.analysis_meta["has_MVs"]:
                self.btn_save_TA.setEnabled(True)
                self.init_TAmotion()
            else:
                self.btn_save_TA.setEnabled(False)
                self.clear_figs()
                
            self.update = False

    def init_TAmotion(self): 
        max_motion = self.ceval.max_avgMotion
        
        self.imshow_motion_total = self.ax_TA_tot.imshow(self.ceval.avg_absMotion, 
            vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
        self.imshow_motion_x = self.ax_TA_x.imshow(self.ceval.avg_MotionX, 
            vmin = 0, vmax = max_motion, cmap="jet", interpolation="bilinear")
        self.imshow_motion_y = self.ax_TA_y.imshow(self.ceval.avg_MotionY, 
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
        self.cohw.plot_TimeAveragedMotion() # is saved as .png, maybe allow specification in extra-menu but not here
        helpfunctions.msgbox(self, 'Plots of time averaged motion were saved successfully.')