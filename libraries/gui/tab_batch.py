import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, 
    QSpinBox, QCheckBox, QListWidget, QAbstractItemView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from libraries import helpfunctions, UserDialogs, OHW
import pathlib

class TabBatch(QWidget):
    """
        for time averaged motion
    """
    
    def __init__(self, parent):
        super(TabBatch, self).__init__(parent)
        self.parent=parent
        self.initUI()
        
        self.videofiles = []
        self.stopBatch = False

    def initUI(self):

        self.info = QTextEdit()
        self.info.setText('In this tab you can automate the analysis of multiple folders without further interaction during processing.')
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(50)
        self.info.setMaximumWidth(800)
        self.info.setStyleSheet("background-color: LightSkyBlue")
        
        #select the folders
        self.info_batchfolders = QLabel('Currently selected videos for automated analysis:')
        self.info_batchfolders.setFont(QFont("Times",weight=QFont.Bold))
        self.qlist_batchvideos = QListWidget()
        self.qlist_batchvideos.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.qlist_batchvideos.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.qlist_batchvideos.setMinimumWidth(600)
        
        #button for adding folders
        self.btn_addVid = QPushButton('Add Videos...')
        self.btn_addVid.resize(self.btn_addVid.sizeHint())
        self.btn_addVid.clicked.connect(self.on_addBatchVideo)
        
        #button for removing folders
        self.btn_remVid = QPushButton('Remove selected Videos')
        self.btn_remVid.resize(self.btn_remVid.sizeHint())
        self.btn_remVid.clicked.connect(self.on_removeBatchVideo)
        
        #batch param
        self.label_parameters = QLabel('Settings during calculation of motion vectors:')
        self.label_parameters.setFont(QFont("Times",weight=QFont.Bold))
        self.label_blockwidth = QLabel('Blockwidth (in pixels)')
        self.label_delay = QLabel('Delay (in frames)')
        self.label_maxShift = QLabel('Maximum shift p (in pixels)')
        
        #use own grid for spinboxes...
        
        #spinboxes incl settings
        self.spinbox_blockwidth  = QSpinBox()
        self.spinbox_delay = QSpinBox()
        self.spinbox_maxShift = QSpinBox()
        
        self.spinbox_blockwidth.setRange(2,128)
        self.spinbox_blockwidth.setSingleStep(2)
        self.spinbox_blockwidth.setSuffix(' pixels')
        self.spinbox_delay.setRange(1,20)
        self.spinbox_delay.setSuffix(' frames')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_maxShift.setSuffix(' pixels')
        
        blockwidth = int(self.parent.config['DEFAULT VALUES']['blockwidth'])
        delay = int(self.parent.config['DEFAULT VALUES']['delay'])
        max_shift = int(self.parent.config['DEFAULT VALUES']['maxshift'])

        self.spinbox_blockwidth.setValue(blockwidth)
        self.spinbox_delay.setValue(delay)
        self.spinbox_maxShift.setValue(max_shift)
        
        #options for automated analysis
        label_batchOptions = QLabel('Choose options for automated analysis of chosen folders:')
        label_batchOptions.setFont(QFont("Times",weight=QFont.Bold))
        
        self.checkFilter = QCheckBox("Filter motion vectors during calculation")
        self.checkCanny = QCheckBox("Select region for calculation based on Canny filtering")
        self.checkHeatmaps = QCheckBox("Create heatmap video")
        self.checkQuivers = QCheckBox("Create quiver plot video")
        #self.checkTimeAveraged = QCheckBox("Create plots for time averaged motion")
        self.checkSaveMotionVectors = QCheckBox("Save the generated motion vectors")
        self.checkScaling = QCheckBox("Scale longest side to 1024 px during calculation")
        self.check_batchresultsFolder = QCheckBox("Use standard results folder, individual for each video")
        self.check_autoPeak = QCheckBox("Detect Peaks and export graph")
        
        # create a variable for the checkbox status
        # actually not needed anymore...
        self.heatmap_status = True
        self.quiver_status = True
        self.timeAver_status = True
        self.scaling_status = True
        self.saveMotionVectors_status = False
        self.check_batchresultsFolder.setChecked(True)
        self.check_batchresultsFolder.setEnabled(False) # to be implemented...
        
        self.checkFilter.setChecked(True)
        self.checkCanny.setChecked(True)
        self.check_autoPeak.setChecked(True)
        #self.checkFilter.setEnabled(False)  # to be implemented...
        self.checkSaveMotionVectors.setChecked(self.saveMotionVectors_status)
        self.checkHeatmaps.setChecked(self.heatmap_status)
        self.checkQuivers.setChecked(self.quiver_status)
        #self.checkTimeAveraged.setChecked(self.timeAver_status)
        self.checkScaling.setChecked(self.scaling_status)
        
        self.btn_startBatch = QPushButton('Start the automated analysis of chosen folders')
        self.btn_startBatch.clicked.connect(self.on_startBatch)
        self.btn_startBatch.setEnabled(False)
        
        self.btn_stopBatch = QPushButton('Stop onging analysis')
        self.btn_stopBatch.clicked.connect(self.on_stopBatch)
        self.btn_stopBatch.setEnabled(False)
        
        #label to display current results folder
        self.label_results_folder = QLabel('Current results folder: ')
        self.label_results_folder.setFont(QFont("Times",weight=QFont.Bold))
        
        #button for changing the results folder
        self.btn_resultsfolder = QPushButton('Change results folder ')
        #self.btn_resultsfolder.clicked.connect(self.on_changeResultsfolder)
        self.btn_resultsfolder.setEnabled(False)
        self.check_batchresultsFolder.stateChanged.connect(self.changeStatus)
        
        self.progressbar = QProgressBar()
        self.progressbar.setMaximum(100)  
        self.progressbar.setValue(0)
        self.progressbar.setFixedWidth(800)
        self.progressbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.label_state = QLabel('idle')
        self.label_state.setStyleSheet("color: rgb(255,0,0)")

        ########## add widgets
        
        self.grid_param = QGridLayout()
        
        self.grid_param.addWidget(self.label_parameters,        0,0,1,2)
        self.grid_param.addWidget(self.label_blockwidth,        1,0)
        self.grid_param.addWidget(self.spinbox_blockwidth,      1,1)
        self.grid_param.addWidget(self.label_delay,             2,0)
        self.grid_param.addWidget(self.spinbox_delay,           2,1)
        self.grid_param.addWidget(self.label_maxShift,          3,0)
        self.grid_param.addWidget(self.spinbox_maxShift,        3,1)

        self.grid_param.setSpacing(15)
        self.grid_param.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_overall = QGridLayout()

        self.grid_overall.addWidget(self.info,                  1,0,1,3)
        self.grid_overall.addWidget(self.info_batchfolders,     2,0)
        self.grid_overall.addWidget(self.qlist_batchvideos,     3,0,3,2)#,Qt.AlignTop|Qt.AlignLeft)# spans 3 rows and 1 column
        self.grid_overall.addWidget(self.btn_addVid,            3,2)
        self.grid_overall.addWidget(self.btn_remVid,            4,2)
        self.grid_overall.setRowStretch(5,2)    #otherwise gird_param will also stretch?
        
        self.grid_overall.addLayout(self.grid_param,            6,0,1,3,Qt.AlignTop|Qt.AlignLeft)#,Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(label_batchOptions,         7,0)#,Qt.AlignTop|Qt.AlignLeft)
        self.grid_overall.addWidget(self.check_batchresultsFolder,   8,0)
        self.grid_overall.addWidget(self.checkScaling,          9,0)
        self.grid_overall.addWidget(self.checkCanny,            10,0)
        self.grid_overall.addWidget(self.checkFilter,           11,0)
        self.grid_overall.addWidget(self.check_autoPeak,        12,0)
        self.grid_overall.addWidget(self.checkHeatmaps,         13,0)
        self.grid_overall.addWidget(self.checkQuivers,          14,0)
        self.grid_overall.addWidget(self.label_results_folder,  15,0)
        self.grid_overall.addWidget(self.btn_resultsfolder,     16,0)
        self.grid_overall.addWidget(self.btn_startBatch,        16,1)
        self.grid_overall.addWidget(self.btn_stopBatch,         16,2)
        self.grid_overall.addWidget(self.progressbar,           17,0,1,3)
        self.grid_overall.addWidget(self.label_state,           18,0,1,3)
       
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
        #   btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
    def on_addBatchVideo(self):
    
        new_files = UserDialogs.chooseFilesByUser("Select video to add for batch analysis", input_folder=self.parent.config['LAST SESSION']['input_folder'])

        for new_file in new_files[0]:
            if new_file not in self.videofiles:
                self.qlist_batchvideos.addItem(new_file)
        # allow selection of folders/multiple files...
        #folderDialog = MultipleFoldersByUser.MultipleFoldersDialog()
        #chosen_folders = folderDialog.getSelection()

        self.videofiles = [self.qlist_batchvideos.item(i).text() for i in range(self.qlist_batchvideos.count())]        
        if self.qlist_batchvideos.count() > 0:
            #if folders are present in list
            self.btn_startBatch.setEnabled(True)
    
    def on_removeBatchVideo(self):
        
        for item in self.qlist_batchvideos.selectedItems():
            self.qlist_batchvideos.takeItem(self.qlist_batchvideos.row(item))
        if self.qlist_batchvideos.count() == 0:
            self.btn_startBatch.setEnabled(False)
        self.videofiles = [self.qlist_batchvideos.item(i).text() for i in range(self.qlist_batchvideos.count())]
            
    def changeStatus(self):
        #disable or enable the option to choose results folder
        if self.sender() == self.check_batchresultsFolder:
            if self.check_batchresultsFolder.isChecked():
                self.btn_resultsfolder.setEnabled(False)
            else:
                self.btn_resultsfolder.setEnabled(True)

    # might be better to move somewhere else....
    class BatchThread(QThread):
        """ thread to evaluate list of files"""
        stateSignal = pyqtSignal(object)
            
        def __init__(self, videofiles, param, *arg, **kwargs):
            QThread.__init__(self)
            self.videofiles = videofiles
            self.param = param
            self.stop_flag = False

        def set_state(self, filenr, state):
            statedict = {"filenr":filenr,"state":state}
            self.stateSignal.emit(statedict)

        # run method gets called when we start the thread
        def run(self):
            for filenr, file in enumerate(self.videofiles):
                self.set_state(filenr,'load')
                if self.stop_flag: break
                
                filepath = pathlib.Path(file)
                curr_analysis = OHW.OHW()
                curr_analysis.import_video(filepath)
                if self.stop_flag: break    #break controlled if stop flag is triggered
                
                if self.param["scaling"]:
                    curr_analysis.set_analysisImageStack(px_longest = 1024)
                else:
                    curr_analysis.set_analysisImageStack()
                
                curr_analysis.analysis_meta["scaling_status"] = self.param["scaling"]
                curr_analysis.analysis_meta["filter_status"] = self.param["filter"]
                
                if self.stop_flag: break
                self.set_state(filenr,'mcalc')
                curr_analysis.calculate_motion(**self.param)
                curr_analysis.init_motion()
                #curr_analysis.save_MVs()
                #curr_analysis.plot_TimeAveragedMotions('.png') # make available via settings...
                if self.stop_flag: break
            
                if self.param["autoPeak"]:
                    curr_analysis.detect_peaks(0.3, 4)  #take care, values hardcoded here so far!
                    kinplot_path = curr_analysis.analysis_meta["results_folder"] / 'beating_kinetics.PNG'
                    curr_analysis.plot_beatingKinetics(kinplot_path)
                
                if self.param["heatmaps"]:
                    self.set_state(filenr,'heatmapvideo')
                    curr_analysis.save_heatmap(singleframe = False)
                if self.stop_flag: break
                if self.param["quivers"]:
                    self.set_state(filenr,'quivervideo')
                    curr_analysis.save_quiver3(singleframe = False, skipquivers = 4) #allow to choose between quiver and quiver3 in future
                
                curr_analysis.save_ohw()
                
        def isAlive(self):
            self.isAlive()
            
        def endThread(self):
            self.terminate()
      
        def stopThread(self):
            self.stop_flag = True
    
    def on_startBatch(self):
        self.parent.current_ohw.save_ohw() # saves again as marked peaks might have changed
        self.parent.current_ohw = OHW.OHW() # clears loaded analysis such that no crosstalk takes place
        self.parent.init_ohw()
        print('Starting batch analysis...')
        self.btn_addVid.setEnabled(False)
        self.btn_remVid.setEnabled(False)
        self.btn_startBatch.setEnabled(False)
        self.btn_stopBatch.setEnabled(True)
        
        self.Nfiles = len(self.videofiles)
        
        blockwidth = self.spinbox_blockwidth.value()
        delay = self.spinbox_delay.value()
        max_shift = self.spinbox_maxShift.value()
        scaling = self.checkScaling.isChecked()
        heatmaps = self.checkHeatmaps.isChecked()
        quivers = self.checkQuivers.isChecked()
        filter = self.checkFilter.isChecked()
        canny = self.checkCanny.isChecked()
        autoPeak = self.check_autoPeak.isChecked()
        param = {"blockwidth":blockwidth, "delay":delay, "max_shift":max_shift, "scaling":scaling,
                    "heatmaps":heatmaps, "quivers":quivers, "canny":canny,"filter":filter, "autoPeak":autoPeak}

        #create a thread for batch analysis:
        self.thread_batch = self.BatchThread(self.videofiles, param)
    
        self.thread_batch.start()
        # use 2 progress bars later? 1 for file progress, 1 for individual calculations....?
        self.thread_batch.finished.connect(self.finishBatch)
        self.thread_batch.stateSignal.connect(self.updateState)  

    def on_stopBatch(self):
        self.stopBatch = True
        self.btn_stopBatch.setEnabled(False)
        self.thread_batch.stopThread()
        
    def updateState(self, statedict):
        statemsg = {"load":"loading video","scale":"scaling video", "mcalc":"calculating motion",
                        "heatmapvideo":"creating heatmap video", "quivervideo":"creating quivervideo"}
        state = statedict["state"]
        self.filenr = statedict["filenr"] + 1
        fullstate = "file " + str(self.filenr) + "/" + str(self.Nfiles) + " files, " + statemsg[state]
        self.label_state.setText(fullstate)
        
        if state != "mcalc":    #update progress for motioncalc in percentage... to be implemented
            self.progressbar.setRange(0,0)
    
    def finishBatch(self):
        # enable buttons again
        self.btn_addVid.setEnabled(True)
        self.btn_remVid.setEnabled(True)
        self.btn_startBatch.setEnabled(True)
        self.btn_stopBatch.setEnabled(False) 
        if not self.stopBatch:
            self.label_state.setText("idle, batch finished")
        else:
            self.label_state.setText("idle, batch aborted at file " + str(self.filenr))
            self.stopBatch = False
        self.progressbar.setRange(0,1)
        self.progressbar.setValue(1)