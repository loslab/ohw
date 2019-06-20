# -*- coding: utf-8 -*-

import configparser
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QLabel, QGridLayout, QSpinBox, QPushButton, QWidget, QTabWidget, QLineEdit, QCheckBox, QDialog
from PyQt5.QtGui import QFont, QPixmap, QDoubleValidator
from PyQt5.QtCore import pyqtSignal, Qt

class DialogKinoptions(QDialog):
    ''' window in which options for beating kinetics plot can be changed'''
    
    def __init__(self, plotsettings):#parent = None?
        super(DialogKinoptions, self).__init__()
        self.grid = QGridLayout(self)
        self.setFixedSize(self.size()) #450,100self.size()
        self.title = 'Settings for Beating Kinetics Graph'
        self.setLayout(self.grid)
        
        self.plotsettings = plotsettings
        
        self.label_settings = QLabel('Axis extents:')
        self.label_settings.setFont(QFont("Times",weight=QFont.Bold))
        
        self.check_tmax = QCheckBox('Set t max automatically')
        self.check_vmax = QCheckBox('Set v max automatically')
        
        self.check_tmax.stateChanged.connect(self.change_status)
        self.check_vmax.stateChanged.connect(self.change_status)
        
        self.label_tmax = QLabel('t max [s]')
        self.label_vmax = QLabel('v max [µm/s]')
        
        self.edit_tmax = QLineEdit()
        self.edit_vmax = QLineEdit()
        
        self.check_mark_peaks = QCheckBox('mark export peaks')
        
        validator = QDoubleValidator() # constrain input tu float numbers
        self.edit_tmax.setValidator(validator)
        self.edit_vmax.setValidator(validator)
        
        self.grid.setSpacing(15)
        self.grid.addWidget(self.label_settings, 0, 0, 1, 3)
        self.grid.addWidget(self.check_tmax, 1,  0)
        self.grid.addWidget(self.label_tmax, 1,  1)
        self.grid.addWidget(self.edit_tmax, 1,  2)
        self.grid.addWidget(self.check_vmax, 2,  0)
        self.grid.addWidget(self.label_vmax, 2,  1)
        self.grid.addWidget(self.edit_vmax, 2,  2)
        self.grid.addWidget(self.check_mark_peaks,3,0)
        
        self.grid.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.init_settings()
        
    def init_settings(self):
        if self.plotsettings["vmax"] == None:
            self.check_vmax.setChecked(True)
        else:
            self.check_vmax.setChecked(False)
            self.edit_vmax.setText(str(self.plotsettings["vmax"]))
            
        if self.plotsettings["tmax"] == None:
            self.check_tmax.setChecked(True)
        else:
            self.check_tmax.setChecked(False)
            self.edit_tmax.setText(str(self.plotsettings["tmax"]))
    
        self.check_mark_peaks.setChecked(self.plotsettings["mark_peaks"])
    
    def change_status(self):
        """
            handle changes of available checkboxes 
        """
        if self.sender() == self.check_tmax:
            if self.check_tmax.isChecked():
                self.edit_tmax.setEnabled(False)
            else:
                self.edit_tmax.setEnabled(True)
                
        elif self.sender() == self.check_vmax:
            if self.check_vmax.isChecked():
                self.edit_vmax.setEnabled(False)
            else:
                self.edit_vmax.setEnabled(True)

    def get_settings(self):
        if self.check_tmax.isChecked():
            tmax = None
        else:
            tmax = float(self.edit_tmax.text()) if self.edit_tmax.text() != "" else None
        if self.check_vmax.isChecked():
            vmax = None
        else:
            vmax = float(self.edit_vmax.text()) if self.edit_vmax.text() != "" else None
        mark_peaks = self.check_mark_peaks.isChecked()
        settings = {"vmax":vmax,"tmax":tmax,"mark_peaks":mark_peaks}
        
        return settings