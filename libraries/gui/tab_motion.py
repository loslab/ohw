import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, 
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, 
    QWidget, QSpinBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from libraries import OHW, helpfunctions

class TabMotion(QWidget):
    
    def __init__(self, parent):
        super(TabMotion, self).__init__(parent)
        self.parent=parent
        self.initUI()
        
    def initUI(self):
        self.info = QTextEdit()
        self.info.setText('In this tab you set the settings for the block-matching algorithm and perform the calculation of the motion vectors or import an old analysis. Calculated motion vectors can be exported as numpy-array for further analysis')
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(50)
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
        self.spinbox_blockwidth.setValue(int(self.parent.config['DEFAULT VALUES']['blockwidth'])) # move to function
        self.spinbox_delay.setRange(1,10)
        self.spinbox_delay.setSuffix(' frames')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_delay.setValue(int(self.parent.config['DEFAULT VALUES']['delay']))
        self.spinbox_maxShift.setSuffix(' pixels')
        self.spinbox_maxShift.setValue(int(self.parent.config['DEFAULT VALUES']['maxShift']))
        
        self.check_scaling = QCheckBox('Scale longest side to 1024 px during calculation')
        self.check_scaling.setChecked(True) #connect with config here!
        
        #enable/disable filtering
        self.check_filter = QCheckBox("Filter motion vectors after calculation")
        self.check_filter.setChecked(True)#connect with config here!
        
        #canny edge
        self.check_canny = QCheckBox("Select region for calculation based on Canny filtering")
        self.check_canny.setChecked(True)#connect with config
        
        self.btn_getMVs = QPushButton('Calculate motion vectors')
        self.btn_getMVs.clicked.connect(self.on_getMVs)
        self.btn_getMVs.setEnabled(False)
        self.btn_getMVs.setFixedWidth(150)
        
        self.btn_save_MVs = QPushButton('Save motion vectors')
        self.btn_save_MVs.clicked.connect(self.on_saveMVs)
        self.btn_save_MVs.setEnabled(False)
        self.btn_save_MVs.setFixedWidth(150)
        
        self.btn_load_ohw = QPushButton('Load motion analysis')
        self.btn_load_ohw.clicked.connect(self.on_load_ohw)
        self.btn_load_ohw.setFixedWidth(150)
        
        #succed-button
        self.btn_succeed_MVs = QPushButton('No motion available yet. Calculate new one or load old')
        #self.btn_succeed_MVs.setStyleSheet("background-color: IndianRed")
        #self.btn_succeed_MVs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        #progressbar in tab2    
        self.progressbar_MVs = QProgressBar()
        self.progressbar_MVs.setMaximum(100)
        self.progressbar_MVs.setValue(0)
        #self.progressbar_MVs.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

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

        ###########

        self.grid_btns = QGridLayout()
        self.grid_btns.setSpacing(10)
        self.grid_btns.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_btns.addWidget(self.btn_getMVs, 0,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_btns.addWidget(self.btn_save_MVs, 0,1, Qt.AlignTop|Qt.AlignLeft)
        self.grid_btns.addWidget(self.btn_load_ohw, 0,2, Qt.AlignTop|Qt.AlignLeft)

        btnwidth = 250 
        self.btn_getMVs.setFixedWidth(btnwidth)
        self.btn_load_ohw.setFixedWidth(btnwidth)
        self.btn_save_MVs.setFixedWidth(btnwidth)

        self.grid_overall = QGridLayout()#self._main)
        self.setLayout(self.grid_overall) 
        
        self.grid_overall.setSpacing(15)        
        self.grid_overall.setAlignment(Qt.AlignTop|Qt.AlignLeft)      
        
        self.grid_overall.addWidget(self.info, 0,0,1,4, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.label_settings, 1,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.label_blockwidth,2,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.spinbox_blockwidth,2,1, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.label_delay,3,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.spinbox_delay, 3,1, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.label_maxShift,4,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.spinbox_maxShift,4,1, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.label_addOptions, 5,0, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.check_scaling, 6,0,1,2, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.check_canny, 7,0,1,2, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.check_filter, 8,0,1,2, Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addLayout(self.grid_btns, 9,0,1,4,Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.progressbar_MVs, 10,0,1,4)
        self.grid_overall.addWidget(self.btn_succeed_MVs, 11,0,1,4)
        
    def init_ohw(self):
        ''' set values from current_ohw '''
        self.current_ohw = self.parent.current_ohw
        
        if self.current_ohw.video_loaded:
            self.btn_getMVs.setEnabled(True)
        else:
            self.btn_getMVs.setEnabled(False)    
        
        if self.current_ohw.analysis_meta["has_MVs"]:    # change here to appropriate variable
            self.btn_succeed_MVs.setStyleSheet("background-color: YellowGreen")
            self.btn_succeed_MVs.setText("Motion available")
            self.btn_save_MVs.setEnabled(True)
        else:
            self.btn_succeed_MVs.setStyleSheet("background-color: IndianRed")
            self.btn_succeed_MVs.setText("No motion available yet. Calculate new one or load old")
            self.btn_save_MVs.setEnabled(False)
        
    def on_getMVs(self):
        #disable button to not cause interference between different calculations
        self.btn_getMVs.setEnabled(False)
        
        #get current parameters entered by user
        self.current_ohw.videometa['fps'] = float(self.parent.tab_input.edit_fps.text())
        self.current_ohw.videometa['microns_per_px'] = float(self.parent.tab_input.edit_mpp.text())
        
        blockwidth = self.spinbox_blockwidth.value()
        maxShift = self.spinbox_maxShift.value()
        delay = self.spinbox_delay.value()
        
        px_longest = None
        scaling_status = self.check_scaling.isChecked()
        canny_status = self.check_canny.isChecked()
        filter_status = self.check_filter.isChecked()

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
    
#            #always calculate the full image
            self.current_ohw.scale_ImageStack(self.current_ohw.rawImageStack.shape[1], self.current_ohw.rawImageStack.shape[2])     
        '''
        
        self.current_ohw.set_analysisImageStack(px_longest = px_longest) # scale + set roi, , roi=[0,0,500,500]
        self.current_ohw.analysis_meta["scaling_status"] = scaling_status
        self.current_ohw.analysis_meta["filter_status"] = filter_status
        
        calculate_motion_thread = self.current_ohw.calculate_motion_thread(
            blockwidth = blockwidth, delay = delay, max_shift = maxShift, canny = canny_status)
        calculate_motion_thread.start()
        calculate_motion_thread.progressSignal.connect(self.updateMVProgressBar)
        calculate_motion_thread.finished.connect(self.finish_motion)

    def finish_motion(self):
        # saves ohw_object when calculation is done and other general results
        self.current_ohw.init_motion()
        self.parent.init_ohw()
        
        self.current_ohw.save_ohw()
        #self.current_ohw.plot_TimeAveragedMotions('.png') #not really necessary
        
    def on_load_ohw(self):
        """
            loads already calculated motion and initializes gui
            ... how to optimize loading of rawImageStack?
        """
        msg = 'select .pickle-file of previous analysis'
        path = self.parent.config['LAST SESSION']['input_folder']
        pickle_file = QFileDialog.getOpenFileName(None, msg, path, 
            "ohw_analysis (*.pickle)")[0]
        if (pickle_file == ''):
            return
        self.parent.current_ohw.save_ohw()
        self.parent.current_ohw = OHW.OHW()    # creates new instance here
        self.current_ohw = self.parent.current_ohw # is not passed to parent automatically!
        self.current_ohw.load_ohw(pickle_file)

        #self.current_ohw.init_motion() # is already done in load_ohw
        self.parent.init_ohw()
        
        self.set_motion_param() # or move to init_ohw?

    def updateMVProgressBar(self, value):
        self.progressbar_MVs.setValue(value*100)      

    def on_saveMVs(self):
        ''' saves raw MVs to results folder '''
        self.current_ohw.save_MVs()
        helpfunctions.msgbox(self, 'Motion vectors were successfully saved')
        
    def set_motion_param(self):
        ''' sets values in gui from loaded ohw-file '''
        self.spinbox_blockwidth.setValue(self.current_ohw.analysis_meta["MV_parameters"]["blockwidth"])
        self.spinbox_delay.setValue(self.current_ohw.analysis_meta["MV_parameters"]["delay"])
        self.spinbox_maxShift.setValue(self.current_ohw.analysis_meta["MV_parameters"]["max_shift"])
        
        self.check_canny.setChecked(self.current_ohw.analysis_meta["MV_parameters"]["canny"])
        self.check_filter.setChecked(self.current_ohw.analysis_meta["filter_status"])
        self.check_scaling.setChecked(self.current_ohw.analysis_meta["scaling_status"])
        
    def init_values(self, config):
        """
            set values from config
        """
        pass