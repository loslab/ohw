import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox, QGridLayout, 
    QVBoxLayout, QHBoxLayout, QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, 
    QWidget, QGroupBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics

import pathlib
import numpy as np
from libraries import OHW, UserDialogs, helpfunctions

class TabAnalysis(QWidget):
    #Python classes follow the CapWords convention
    """
        Analysis tab, bundles video input + settings for analysis
    """

    def __init__(self, parent, ctrl):
        super(TabAnalysis, self).__init__(parent)
        self.update = True
        self.parent=parent
        self.ctrl = ctrl
        self.initUI()
        self.init_ohw()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
        
        # create box-widgets
        self.box_video_input = BoxVideoInput(self, self.ctrl)
        self.box_adjust_video = BoxAdjustVideo(self, self.ctrl)
        self.box_preprocess = BoxPreprocess(self, self.ctrl)
        self.box_motion = BoxMotion(self, self.ctrl)
        
        # create canvas to display prev image
        self.fig_firstIm, self.ax_firstIm = plt.subplots(1,1)#, figsize = (5,5))
        self.fig_firstIm.patch.set_facecolor('#ffffff')##cd0e49')
        self.fig_firstIm.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.ax_firstIm.axis('off')
        self.canvas_firstImage = FigureCanvas(self.fig_firstIm)
        self.canvas_firstImage.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.canvas_firstImage.setFixedSize(500,500)      
        self.roi_rect = None
        
        # create progressbar
        self.progbar = QProgressBar()
        self.progbar.setMaximum(100)
        self.progbar.setValue(0)        
        
        # add all to layout
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        layout.addWidget(self.box_video_input,0,0,1,2)
        layout.addWidget(self.box_adjust_video,0,2)
        layout.addWidget(self.box_preprocess,1,0)
        layout.addWidget(self.box_motion,1,1,1,2)
        layout.addWidget(self.progbar,2,0,1,3)
        layout.setColumnStretch(1,1)
        layout.addWidget(self.canvas_firstImage,0,3,3,1)
        layout.setColumnStretch(4,100)
        #layout.setRowStretch(1,1) #double check if both necessary
        layout.setRowStretch(3,1)
        self.setLayout(layout)

    def display_firstImage(self, image = None):
        """ displays 800 px prev of cohw or placeholder """
        self.ax_firstIm.clear()
        self.ax_firstIm.axis('off')

        if type(image) == np.ndarray:
            self.imshow_firstImage = self.ax_firstIm.imshow(image, cmap = 'gray', vmin = self.cohw.videometa["Blackval"], vmax = self.cohw.videometa["Whiteval"])
        else:
            self.ax_firstIm.text(0.5, 0.5,'no video loaded yet',
                size=14, ha='center', va='center', backgroundcolor='indianred', color='w')
        self.canvas_firstImage.draw()

    def update_roi(self):
        #draw roi on preview img
        if self.roi_rect is not None:
            self.roi_rect.remove()
        
        roi_raw = self.cohw.analysis_meta["roi"]
        
        if roi_raw is not None:
            roi = [int(coord*self.cohw.videometa["prev_scale"]) for coord in roi_raw]
            self.roi_rect = plt.Rectangle((roi[0],roi[1]), roi[2], roi[3], facecolor='None', edgecolor='red', linewidth = 5)
        else:
            wx, wy = self.cohw.videometa["prev800px"].shape
            self.roi_rect = plt.Rectangle((0,0), wx, wy, facecolor='None', edgecolor='red', linewidth = 5) #TODO:hardcoded width, change!
        self.ax_firstIm.add_patch(self.roi_rect)
        self.canvas_firstImage.draw()
        
    def enable_controls(self, enabled):
        self.box_adjust_video.setEnabled(enabled)
        self.box_video_input.setEnabled(enabled)
        self.box_motion.setEnabled(enabled)
        self.box_preprocess.setEnabled(enabled)
    
    def init_ohw(self):
        """
            updates info displayed in inputtab
            -> loading of new video or loading of analysis file
        """
        
        if self.update == True:

            self.box_video_input.init_ohw()
            self.box_adjust_video.init_ohw()
            self.box_motion.init_ohw()
            
            loaded = self.cohw.video_loaded
            finish = self.cohw.analysis_meta["calc_finish"]
            
            if (loaded == True) and (finish == False):
                self.box_preprocess.setEnabled(True)
            else:
                print("no vid loaded, nothing calculated")
                self.box_preprocess.setEnabled(False)
            
            # check if video is loaded and update controls
            if finish or loaded:
                self.display_firstImage(self.cohw.videometa["prev800px"])
                self.update_roi()
                self.box_adjust_video.setEnabled(True)
                self.box_adjust_video.set_start_brightness()
            else:
                self.display_firstImage()
                self.box_adjust_video.setEnabled(False)

            # TODO: each box would consequently have its own init_ohw...            
            self.update = False        
        
class BoxVideoInput(QGroupBox):    
    """
        QGroupBox providing:
        - display of video parameters
        - buttons to load/ reload video + set results folder
    """
    def __init__(self, parent, ctrl, boxtitle = "Video input"):
        print(boxtitle)
        super(BoxVideoInput, self).__init__(boxtitle, parent = parent) # take care of correct superclass init, order of args
        #or self.setTitle(boxtitle)
        self.parent=parent
        self.ctrl = ctrl #introduce controller object
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
      
        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title

        self.pargrid = QGridLayout()
        #self.pargrid.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.pargrid.setSpacing(10)
        
        # create widgets for video input parameters
        self.label_fps = QLabel('framerate [frames/s]:')
        self.label_mpp = QLabel('scale [microns/pixel]:')
        self.label_path = QLabel('Video path:')
        self.label_results = QLabel('results folder:')
        
        self.label_path_var = QLabel('Path/...')
        self.label_path_var.setFixedWidth(350)
        self.set_path("__________##########__________##########")      
        self.label_results_var = QLabel('') #__________##########__________########## placeholder
        self.label_results_var.setFixedWidth(350) # prevent resizing, show only last part of path if too long
        self.set_results("__________##########__________#results##")
        self.edit_fps = QLineEdit() #TODO: replace with other widget which can check type?
        self.edit_mpp = QLineEdit()
        
        self.edit_fps.setFixedWidth(70)
        self.edit_mpp.setFixedWidth(70)        
        
        # add widgets to parameter grid
        self.pargrid.addWidget(self.label_path,0,0)
        self.pargrid.addWidget(self.label_path_var, 0,1)
        self.pargrid.addWidget(self.label_results,1,0)
        self.pargrid.addWidget(self.label_results_var, 1,1)
        self.pargrid.addWidget(self.label_fps, 2,0)
        self.pargrid.addWidget(self.edit_fps, 2,1)
        self.pargrid.addWidget(self.label_mpp, 3,0)
        self.pargrid.addWidget(self.edit_mpp, 3,1)
        
        self.pargrid.setColumnStretch(1,1)
        
        # layout for button row
        self.buttons = QHBoxLayout()
        #self.buttons.setAlignment(Qt.AlignTop|Qt.AlignLeft) # expanding policy is overwritten if set
        self.buttons.setSpacing(10)
        
        # create buttons
        self.btn_load_video = QPushButton('Load video')
        self.btn_load_video.clicked.connect(self.on_load_video)
        
        self.btn_results = QPushButton('Change results folder')
        self.btn_results.setEnabled(True)
        self.btn_results.clicked.connect(self.on_change_results)

        self.btn_reload_video = QPushButton('Reload analysis video')
        self.btn_reload_video.clicked.connect(self.on_reload_video)
        
        # add buttons
        self.buttons.addWidget(self.btn_load_video)
        self.buttons.addWidget(self.btn_results)
        self.buttons.addWidget(self.btn_reload_video)
        
        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.pargrid)
        self.vlayout.addLayout(self.buttons)
        #self.vlayout.addStretch(1)
        self.setLayout(self.vlayout)
        
    def set_path(self, path):
        """
            sets path in label, truncates too long path while maintaining fixed width + alignment
            adapted from https://stackoverflow.com/questions/11446478/pyside-pyqt-truncate-text-in-qlabel-based-on-minimumsize
        """
        sysfont = QApplication.font()
        sysmetric = QFontMetrics(sysfont) #could be stored just once...
        elided  = sysmetric.elidedText(path, Qt.ElideLeft, 350)
        self.label_path_var.setText(elided)

    def init_ohw(self):
        loaded = self.cohw.video_loaded
        finish = self.cohw.analysis_meta["calc_finish"]
    
        self.edit_fps.setText(str(self.cohw.videometa['fps']))
        self.edit_mpp.setText(str(self.cohw.videometa['microns_per_px']))
        
        inputpath = str(self.cohw.videometa['inputpath'])
        self.set_path(inputpath)
        results_folder = str(self.cohw.analysis_meta['results_folder'])
        self.set_results(results_folder)
        
        if finish == True:
            self.edit_fps.setEnabled(False)
            self.edit_mpp.setEnabled(False)
        else:
            self.edit_fps.setEnabled(True)
            self.edit_mpp.setEnabled(True)
        
        if (loaded == False) and (finish == True):
            self.btn_reload_video.setEnabled(True)            
        else:
            self.btn_reload_video.setEnabled(False)            

    def on_change_results(self):
        #choose a folder
        msg = 'Choose a new folder for saving your results'
        folder_name = UserDialogs.chooseFolderByUser(msg, input_folder=self.cohw.analysis_meta['results_folder'])
        
        #if 'cancel' was pressed: simply do nothing and wait for user to click another button
        if (folder_name == ''):
            return
        
        self.cohw.analysis_meta["results_folder"] = pathlib.Path(folder_name)
        self.set_results(folder_name)
        
    def set_results(self, path):
        """
            similar to set_path
        """
        sysfont = QApplication.font()
        sysmetric = QFontMetrics(sysfont) #could be stored just once...
        elided  = sysmetric.elidedText(path, Qt.ElideLeft, 350)
        self.label_results_var.setText(elided)        

    def on_load_video(self):
        self.parent.progbar.setValue(0)
        
        #choose a folder
        msg = 'Choose an input video: file of type .mp4, .avi, .mov or a .tif file in a folder containing a sequence of .tif-images'
        try:
            fileName  = UserDialogs.chooseFileByUser(message=msg, input_folder=self.ctrl.config['LAST SESSION']['input_folder'])
        except Exception:
            fileName  = UserDialogs.chooseFileByUser(message=msg)
        
        #if 'cancel' was pressed: simply do nothing and wait for user to click another button
        if (fileName[0]  == ''):
            return

        inputpath = pathlib.Path(fileName[0])
        #save changes to config file
        self.ctrl.config.set("LAST SESSION", "input_folder", str((inputpath / "..").resolve()))
        helpfunctions.save_config(self.ctrl.config)

        # create OHW object to work with motion vectors
        self.cohw.save_ohw() #save old ohw when loading new file
        self.ctrl.cohw = OHW.create_analysis() # need to call self.ctrl.cohw to propagate to controller + other frames
        #self.cohw = self.ctrl.cohw
        # TODO: make sure this is transmitted properly to parent!
        
        #read imagestack
        self.import_video_thread = self.cohw.import_video_thread(inputpath)
        self.import_video_thread.start()
        self.parent.progbar.setRange(0,0)
        self.import_video_thread.finished.connect(self.finish_load_video)

    def on_reload_video(self):
        """
            reloads video files into cohw
            e.g. when analysis file is opened
        """
        self.parent.progbar.setValue(0)            
        self.reload_video_thread = self.cohw.reload_video_thread()
        self.reload_video_thread.start()
        self.parent.progbar.setRange(0,0)
        self.reload_video_thread.finished.connect(self.finish_load_video)

    def finish_load_video(self):
    
        self.parent.progbar.setRange(0,100) #TODO: improve self.parent call
        self.parent.progbar.setValue(100)
        
        self.parent.update = True
        self.parent.init_ohw() # TODO: change to self.ctrl.update_tabs()
        
        #update videoinfos with data from cohw

class BoxAdjustVideo(QGroupBox):
    """
        QGroupBox providing:
        - adjustment of brightness
        - selection of roi
    """
    def __init__(self, parent, ctrl, boxtitle = 'Brightness'):
        super(BoxAdjustVideo, self).__init__(boxtitle, parent=parent)
        self.parent=parent
        self.ctrl = ctrl
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
        
    def init_ohw(self):
        pass
        #self.cohw = self.ctrl.cohw
        
    def initUI(self):    
  
        self.setStyleSheet("QGroupBox { font-weight: bold; } ")
        
        # create widgets
        self.label_slider_blackval = QLabel('black')#Black value')
        self.slider_blackval = QSlider(Qt.Vertical)
        self.slider_blackval.setMinimum(0)
        self.slider_blackval.setMaximum(100)
        self.slider_blackval.setValue(0)
        self.slider_blackval.setFixedHeight(100)
        self.slider_blackval.valueChanged.connect(self.on_change_blackval)
        
        self.label_slider_whiteval = QLabel('white')#White value')
        self.slider_whiteval = QSlider(Qt.Vertical)
        self.slider_whiteval.setMinimum(0)
        self.slider_whiteval.setMaximum(100)
        self.slider_whiteval.setValue(0)
        self.slider_whiteval.setFixedHeight(100)
        self.slider_whiteval.valueChanged.connect(self.on_change_whiteval)
        
        self.btn_brightness = QPushButton('reset')
        self.btn_brightness.setMinimumWidth(50) # overwrite size hint to allow smaller button
        self.btn_brightness.clicked.connect(self.on_reset_brightness)

        # create layout for sliders
        self.grid_slider = QGridLayout()
        self.grid_slider.setSpacing(10)
        #self.grid_slider.setAlignment()#Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_slider.addWidget(self.label_slider_blackval,0,0, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.label_slider_whiteval,0,1, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.slider_blackval,1,0, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.slider_whiteval,1,1, Qt.AlignHCenter)
        self.grid_slider.addWidget(self.btn_brightness,2,0,1,2)#, Qt.AlignTop|Qt.AlignLeft)
        self.grid_slider.setColumnStretch(2,1)
        
        self.setLayout(self.grid_slider)
        
    def on_change_blackval(self):          
        """
            change the blac/ white values for image display
            using a slider with 2 handles would be easiest option...
        """
     
        # save the new value to videometa
        self.cohw.videometa["Blackval"] = self.slider_blackval.value()

        # set allowed whitevals and blackvals           
        self.slider_whiteval.setMinimum(self.cohw.videometa["Blackval"])            
        self.update_brightness()

    def on_change_whiteval(self):          
        """
            change the white values for image display
        """
        # save the new value to videometa
        self.cohw.videometa["Whiteval"] = self.slider_whiteval.value()

        # set allowed whitevals and blackvals           
        self.slider_blackval.setMaximum(self.cohw.videometa["Whiteval"])            
        self.update_brightness()

    def on_reset_brightness(self):
        """ resets the image display back to the original values
        """
        self.cohw.videometa["Blackval"] = self.cohw.raw_videometa["Blackval"]
        self.cohw.videometa["Whiteval"] = self.cohw.raw_videometa["Whiteval"]
        
        self.set_start_brightness()
        self.update_brightness()        

    def set_start_brightness(self):
        ''' set brightness sliders to raw values '''
        self.slider_whiteval.blockSignals(True)# prevent calling on_change_whiteVal/blackVal
        self.slider_blackval.blockSignals(True)
        self.slider_whiteval.setMaximum(self.cohw.videometa["Whiteval"]*3)
        self.slider_blackval.setMaximum(self.cohw.videometa["Whiteval"])      
        self.slider_whiteval.setValue(self.cohw.videometa["Whiteval"])
        self.slider_blackval.setValue(self.cohw.videometa["Blackval"])
        self.slider_whiteval.setMinimum(self.cohw.videometa["Blackval"])
        self.slider_whiteval.blockSignals(False)
        self.slider_blackval.blockSignals(False)

    def update_brightness(self):
        vmin, vmax = self.cohw.videometa["Blackval"], self.cohw.videometa["Whiteval"]
        self.parent.imshow_firstImage.set_clim(vmin=vmin, vmax=vmax)
        self.parent.canvas_firstImage.draw()
        """
        if (self.cohw.video_loaded and self.cohw.analysis_meta["has_MVs"]):
            self.parent.tab_quiver.updateQuiverBrightness(vmin=vmin, vmax=vmax) # how can this be done in a nice way?
        """
        # TODO: change to sth like self.controller.update_quiver_brightness?

class BoxPreprocess(QGroupBox):
    """
        QGroupBox providing:  
        - selection of roi  
        - activation of Canny prefilter + scaling to 1024 px for analysis
    """
    def __init__(self, parent, ctrl, boxtitle = 'Preprocessing'):
        super(BoxPreprocess, self).__init__(boxtitle, parent=parent)
        self.parent=parent
        self.ctrl = ctrl      
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
      
        self.setStyleSheet("QGroupBox { font-weight: bold; } ")
    
        self.btn_sel_roi = QPushButton('select ROI')
        self.btn_sel_roi.clicked.connect(self.on_sel_roi)
        
        self.btn_reset_roi = QPushButton('reset ROI')
        #self.btn_resetROI.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed) # can mess with alignment
        self.btn_reset_roi.clicked.connect(self.on_reset_roi)
        
        self.check_canny = QCheckBox('use Canny')
        self.check_scale1024 = QCheckBox('Scale to 1024 px')
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.btn_sel_roi)
        self.layout.addWidget(self.btn_reset_roi)
        self.layout.addWidget(self.check_canny)
        self.layout.addWidget(self.check_scale1024)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def on_sel_roi(self):
        self.cohw.set_roi()
        self.parent.update_roi()
    
    def on_reset_roi(self):
        self.cohw.reset_roi()
        self.parent.update_roi()
    
    def get_options(self):
        canny_state = self.check_canny.isChecked()
        scale1024_state = self.check_scale1024.isChecked()
        return canny_state, scale1024_state

class BoxMotion(QGroupBox):
    """
        QGroupBox providing:  
        - controls for starting + loading analysis  
        - 
    """

    def __init__(self, parent, ctrl, boxtitle = 'Motion Analysis'):
        super(BoxMotion, self).__init__(boxtitle, parent=parent)
        self.parent=parent
        self.ctrl = ctrl       
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def init_ohw(self):
        loaded = self.cohw.video_loaded
        finish = self.cohw.analysis_meta["calc_finish"]
                
        #for widget in self.findChildren(QWidget):
        #    widget.setEnabled(False)
        self.btn_calcmotion.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.frame_settings.setEnabled(False)
        self.combo_method.setEnabled(False)
        
        # enable widgets according to specific cases:
        if (loaded == True) and (finish == False):
            self.btn_calcmotion.setEnabled(True)
        
        if (loaded == True) and (finish == True):
            self.btn_reset.setEnabled(True)
        
        if finish == False:
            self.frame_settings.setEnabled(True)
            self.combo_method.setEnabled(True)
        
        self.btn_load_ohw.setEnabled(True)
    
    def initUI(self):
  
        self.setStyleSheet("QGroupBox { font-weight: bold; } ")
        self.combo_method = QComboBox()
        for method in ['Blockmatch','Fluo-Intensity']:
            self.combo_method.addItem(method)
        self.combo_method.setCurrentIndex(0)
        self.combo_method.currentTextChanged.connect(self.on_combo_method_changed)
        self.frame_settings = BM_settings(self, self.ctrl)

        self.label_method = QLabel('Method: ')
        #self.label_method.setFont(QFont("Times",weight=QFont.Bold))        
        self.label_settings = QLabel('Settings: ')
        #self.label_settings.setFont(QFont("Times",weight=QFont.Bold))
        self.label_settings.setAlignment(Qt.AlignTop)
        
        self.grid_overall = QGridLayout()
        self.grid_overall.addWidget(self.label_method,0,0)
        self.grid_overall.addWidget(self.combo_method,0,1)
        self.grid_overall.addWidget(self.label_settings,1,0)
        self.grid_overall.addWidget(self.frame_settings,1,1)
        self.grid_overall.setColumnStretch(2,1)
        self.grid_overall.setRowStretch(3,1)
        self.grid_overall.setRowMinimumHeight(1,120) #TODO: hardcoded, make flexible dependent on method with most parameters
        
        # add buttons:
        self.hbuttons = QHBoxLayout()
        
        self.btn_calcmotion = QPushButton('start analysis')
        self.btn_calcmotion.clicked.connect(self.on_calcmotion)
        self.btn_calcmotion.setEnabled(False)
        
        self.btn_reset = QPushButton('reset analysis')    
        self.btn_reset.clicked.connect(self.on_reset)        
        
        self.btn_load_ohw = QPushButton('load analysis')
        self.btn_load_ohw.clicked.connect(self.on_load_ohw)
        
        self.hbuttons.addWidget(self.btn_calcmotion)
        self.hbuttons.addWidget(self.btn_reset)
        self.hbuttons.addWidget(self.btn_load_ohw)
        self.grid_overall.addLayout(self.hbuttons,2,1)

        self.setLayout(self.grid_overall)

    def on_load_ohw(self):
        """
            loads already calculated motion and initializes gui
            ... how to optimize loading of rawImageStack?
        """
        msg = 'select .pickle-file of previous analysis'
        path = self.ctrl.config['LAST SESSION']['input_folder']
        pickle_file = QFileDialog.getOpenFileName(None, msg, path, 
            "ohw_analysis (*.pickle)")[0]
        if (pickle_file == ''):
            return
        
        if self.cohw.analysis_meta["calc_finish"]:
            self.cohw.save_ohw()
        self.ctrl.cohw = OHW.load_analysis(pickle_file) # creates new instance here, must refer to ctrl

        print(self.cohw.analysis_meta)

        self.parent.update = True
        self.parent.init_ohw()
        #self.parent.update_tabs()
        self.set_motion_param() # or move to init_ohw?

    def set_motion_param(self):
        ''' sets values in gui from loaded ohw-file '''
        
        if self.cohw.analysis_meta["calc_finish"] != True: # pickle does not contain any calculation
            return
        
        method = self.cohw.analysis_meta["motion_method"]
        
        # fill with loaded values
        if method == "Blockmatch":
            self.combo_method.setCurrentIndex(0) # TODO: remove hardcode      
            MV_param = self.cohw.analysis_meta["motion_parameters"]
            BMsettings = {param:MV_param[param] for param in ["blockwidth", "delay", "max_shift"]} # more elegant
            self.frame_settings.set_settings(**BMsettings)
        
        elif method == "Fluo-Intensity":
            self.combo_method.setCurrentIndex(1)
        
    def on_combo_method_changed(self):
        method = self.combo_method.currentText()
        
        if method == "Fluo-Intensity":
            self.frame_settings.deleteLater()
            self.frame_settings = FI_settings(self, self.ctrl)
            self.grid_overall.addWidget(self.frame_settings,1,1)            
            
        elif method == "Blockmatch":
            self.frame_settings.deleteLater()
            self.frame_settings = BM_settings(self, self.ctrl)
            self.grid_overall.addWidget(self.frame_settings,1,1)
    
    def on_reset(self):
        self.cohw.reset()
        self.parent.update = True #TODO: workaround, reimplement when tabs added
        self.parent.init_ohw()
    
    def on_calcmotion(self):
        
        if self.cohw.analysis_meta["calc_finish"] == True: # ask user if a finished calculation is already loaded as it would be overwritten
            if helpfunctions.questionbox(self, "A calculation already exists. Do you want to start a new one and overwrite?") == False:
                return
        
        #disable buttons to not cause interference between different calculations
        #self.btn_calcmotion.setEnabled(False)
        self.parent.enable_controls(False)

        method = self.combo_method.currentText()
        if method == "Blockmatch":
            self.calc_BM()
        
        elif method == "Fluo-Intensity":
            self.calc_FluoI()
            self.finish_motion()

    def calc_FluoI(self):
        self.cohw.set_scale(float(self.parent.box_video_input.edit_mpp.text()))
        self.cohw.set_fps(float(self.parent.box_video_input.edit_fps.text()))
        self.cohw.calculate_motion(method = "Fluo-Intensity", overwrite = True) #TODO: overwrite option still quite sketchy

    def calc_BM(self):
        #get current parameters entered by user
        # TODO: create function to return these values!
        #self.cohw.videometa['fps'] = float(self.parent.box_video_input.edit_fps.text())
        #self.cohw.videometa['microns_per_px'] = float(self.parent.box_video_input.edit_mpp.text())
        self.cohw.set_scale(float(self.parent.box_video_input.edit_mpp.text()))
        self.cohw.set_fps(float(self.parent.box_video_input.edit_fps.text()))
        
        blockwidth, maxShift, delay = self.frame_settings.get_settings()
        canny_stat, scaling_stat = self.parent.box_preprocess.get_options() #TODO: ugly, refactor
        
        px_longest = None

        if scaling_stat == True:
            px_longest = 1024
        
        self.cohw.set_px_longest(px_longest = px_longest)
        """
        if filter_stat == True:
            self.cohw.set_filter(filtername = 'filter_singlemov', on = True)
        """
        if canny_stat == True:
            self.cohw.set_prefilter("Canny", on = True)

        calculate_motion_thread = self.cohw.calculate_motion_thread(
            blockwidth = blockwidth, delay = delay, max_shift = maxShift)
        calculate_motion_thread.start()
        calculate_motion_thread.progressSignal.connect(self.updateMVProgressBar)
        calculate_motion_thread.finished.connect(self.finish_motion)

    def finish_motion(self):
        # saves ohw_object when calculation is done and other general results
        #self.cohw.init_motion()
        #self.parent.update_tabs() # TODO:re-enable, transit to self.ctrl.update_tabs()
        self.parent.enable_controls(True)
        self.parent.update = True
        self.parent.init_ohw()
        self.cohw.save_ohw()            

    def updateMVProgressBar(self, value):
        self.parent.progbar.setValue(value*100)   
        
class BM_settings(QWidget):
    
    def __init__(self, parent, ctrl):
        super(BM_settings, self).__init__(parent)
        self.parent = parent
        self.ctrl = ctrl        
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
        
    def get_settings(self):
        blockwidth = self.spinbox_blockwidth.value()
        max_shift = self.spinbox_maxShift.value()
        delay = self.spinbox_delay.value()
        
        return blockwidth, max_shift, delay
    
    def set_settings(self, blockwidth, max_shift, delay):
        self.spinbox_blockwidth.setValue(blockwidth)
        self.spinbox_maxShift.setValue(max_shift)
        self.spinbox_delay.setValue(delay)
    
    def initUI(self):
        self.layout = QGridLayout()
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.setLayout(self.layout)
        
        self.label_blockwidth =  QLabel('Blockwidth:')
        self.label_delay =       QLabel('Delay:')
        self.label_maxShift =    QLabel('Maximum shift:')
        self.spinbox_blockwidth = QSpinBox()
        self.spinbox_delay = QSpinBox()
        self.spinbox_maxShift = QSpinBox()
        
        #settings for the spinboxes
        self.spinbox_blockwidth.setRange(2,128)
        self.spinbox_blockwidth.setSingleStep(1)
        self.spinbox_blockwidth.setSuffix(' px')
        self.spinbox_blockwidth.setValue(int(self.ctrl.config['DEFAULT VALUES']['blockwidth'])) # move to function
        self.spinbox_delay.setRange(1,10)
        self.spinbox_delay.setSuffix(' frame(s)')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_delay.setValue(int(self.ctrl.config['DEFAULT VALUES']['delay']))
        self.spinbox_maxShift.setSuffix(' px')
        self.spinbox_maxShift.setValue(int(self.ctrl.config['DEFAULT VALUES']['maxShift']))
        
        self.layout.addWidget(self.label_blockwidth,1,0, Qt.AlignTop|Qt.AlignLeft)
        self.layout.addWidget(self.spinbox_blockwidth,1,1, Qt.AlignTop|Qt.AlignLeft)
        self.layout.addWidget(self.label_delay,2,0, Qt.AlignTop|Qt.AlignLeft)
        self.layout.addWidget(self.spinbox_delay, 2,1, Qt.AlignTop|Qt.AlignLeft)
        self.layout.addWidget(self.label_maxShift,3,0, Qt.AlignTop|Qt.AlignLeft)
        self.layout.addWidget(self.spinbox_maxShift,3,1, Qt.AlignTop|Qt.AlignLeft)    
        
class FI_settings(QWidget):
        
    def __init__(self, parent, ctrl):
        super(FI_settings, self).__init__(parent)
        self.parent=parent
        self.ctrl = ctrl             
        self.initUI()
        
    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw        
        
    def initUI(self):
        # has so far no special settings
        pass