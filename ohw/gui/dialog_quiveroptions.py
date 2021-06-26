# -*- coding: utf-8 -*-

import configparser
import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QLabel, QGridLayout, QSpinBox, 
    QPushButton, QWidget, QTabWidget, QLineEdit, QCheckBox, QDialog, QRadioButton, QGroupBox, QHBoxLayout)
from PyQt5.QtGui import QFont, QPixmap, QDoubleValidator, QIntValidator
from PyQt5.QtCore import pyqtSignal, Qt, QLocale
import math

class DialogQuiveroptions(QDialog):
    ''' window in which options for quiver exports can be changed'''
    
    def __init__(self, ctrl, settings): #parent = None?
        super(DialogQuiveroptions, self).__init__()
        self.cohw = ctrl.cohw # take care, changes in self.cohw will not propagate to main window!
        self.ctrl = ctrl
        self.settings = settings
        #self.quiversettings = quiversettings        
        
        self.grid = QGridLayout(self)
        self.setFixedSize(self.size()) #450,100self.size()
        self.title = 'Settings for Quiver export'
        self.setLayout(self.grid)
                
        self.group_range = QGroupBox('videorange')
        self.label_startframe = QLabel('startframe:')
        self.label_endframe = QLabel('endframe:')
        self.edit_startframe = QLineEdit() # todo: other widget might be more useful for ints...
        self.edit_startframe.setFixedWidth(50)
        self.edit_endframe = QLineEdit()
        self.edit_endframe.setFixedWidth(50)
        self.label_length = QLabel('videolength: ')
        self.label_maxlength = QLabel('max length [s]:')
        self.edit_maxlength = QLineEdit()
        self.edit_maxlength.setFixedWidth(50)
        self.btn_default = QPushButton("set as default length")
        self.btn_default.setFixedWidth(200)
        self.btn_default.clicked.connect(self.on_default)
               
        grid = QGridLayout()
        grid.addWidget(self.label_startframe,0,0)
        grid.addWidget(self.edit_startframe,0,1)
        grid.addWidget(self.label_endframe,0,2)
        grid.addWidget(self.edit_endframe,0,3)
        grid.addWidget(self.label_length,0,4)
        grid.addWidget(self.label_maxlength,1,0)
        grid.addWidget(self.edit_maxlength,1,1)
        grid.addWidget(self.btn_default,1,2,1,3)
        grid.setRowStretch(2,1)
        grid.setColumnStretch(5,1)
        self.group_range.setLayout(grid)
        
        self.group_view = QGroupBox('exported view')
        self.sel_singleview = QRadioButton('export single view')
        self.sel_tripleview = QRadioButton('export triple view (video + quiver + velocity graph)')

        hbox = QHBoxLayout()
        hbox.addWidget(self.sel_singleview)
        hbox.addWidget(self.sel_tripleview) 
        hbox.addStretch(1)
        self.group_view.setLayout(hbox)
        
        self.grid.addWidget(self.group_range,0,0)
        self.grid.addWidget(self.group_view,1,0)
        self.grid.setRowStretch(2,1)
        self.grid.setAlignment(Qt.AlignTop|Qt.AlignLeft)        

        # self.init_settings()
        self.edit_startframe.textChanged.connect(self.on_change_range)
        self.edit_endframe.textChanged.connect(self.on_change_range)
        self.edit_maxlength.textChanged.connect(self.on_change_maxlength)
        self.init_settings()

        # self.edit_maxlength.editingFinished.connect(lambda: print("edFinishSignal"))
        # self.sel_tripleview.setChecked(True)
        set = self.get_settings()
        print(set)
        
    def init_settings(self):
    
        # get info on framenumber and set input validators
        self.max_frame = self.cohw.videometa["frameCount"] - 1
        fps = self.cohw.videometa["fps"]
        self.max_length = self.max_frame / fps

        framevalidator = QIntValidator(0,self.max_frame) # constrain input to ints in range of frames
        self.edit_startframe.setValidator(framevalidator)        
        self.edit_endframe.setValidator(framevalidator)
        #lengthvalidator = QDoubleValidator(0.00, max_length, 2, notation=QDoubleValidator.StandardNotation) # does not work perfectly as intermediate input accepted
        lengthvalidator = QDoubleValidator(0.00, 1000.0, 2, notation = QDoubleValidator.StandardNotation)
        lengthvalidator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates)) # set locale to english to accept only "." as decimal separator
        self.edit_maxlength.setValidator(lengthvalidator)

        # self.edit_endframe.setText(str(self.max_frame))
        # self.edit_startframe.setText("0")
        
        self.edit_startframe.setText(str(self.settings["startframe"]))
        self.edit_endframe.setText(str(self.settings["endframe"]))
        if self.settings["view"] == "single":
            self.sel_singleview.setChecked(True)
        else:
            self.sel_tripleview.setChecked(True)
        
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

    def on_change_maxlength(self):
        """ called on changes in maxlength input """
        fps = self.cohw.videometa["fps"]
        fstart = int(self.edit_startframe.text())
        maxlength = float(self.edit_maxlength.text()) if self.edit_maxlength.text() != "" else 0
        flength = math.floor(maxlength*fps)
        fend = fstart + flength
        if fend > self.max_frame:
            fend = self.max_frame
        length = (fend - fstart) / fps
        
        self.edit_endframe.blockSignals(True)
        self.edit_endframe.setText(str(fend))
        self.label_length.setText('videolength: ' + "{:.2f}".format(length) + " s")
        self.edit_endframe.blockSignals(False)

    def on_change_range(self):
        """ is called when start/ end changed to recalc length """
        
        fps  = self.cohw.videometa["fps"]
        fstart = int(self.edit_startframe.text()) if self.edit_startframe.text() != "" else 0 # set to 0 if field empty
        fend = int(self.edit_endframe.text()) if self.edit_endframe.text() != "" else 0
        flength = fend - fstart
        length = flength / fps
        # prevent firing of on_change_length
        self.edit_maxlength.blockSignals(True)
        self.edit_maxlength.setText("{:.2f}".format(length))
        self.label_length.setText('videolength: ' + "{:.2f}".format(length) + " s")
        self.edit_maxlength.blockSignals(False)

    def on_default(self):
        """ set specified max_length as default video_length in config """
        self.ctrl.config['QUIVER OPTIONS']['video_length'] = self.edit_maxlength.text()

    def get_settings(self):

        view = "single" if self.sel_singleview.isChecked() else "triple"
        startf = int(self.edit_startframe.text())
        endf = int(self.edit_endframe.text())
        settings = {"view":view,"startframe":startf,"endframe":endf}#, "default_max_length":}
        
        return settings