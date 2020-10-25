import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, 
    QSpinBox, QDoubleSpinBox, QCheckBox, QListWidget, QAbstractItemView, QGroupBox, QAbstractSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from ohw import helpfunctions, UserDialogs, OHW
from ohw.gui import tab_analysis
import pathlib

class TabBatch(QWidget):
    """
        tab for selecting various videos and performing batch analysis
    """
    
    def __init__(self, parent, ctrl):
        super(TabBatch, self).__init__(parent)
        self.update = False # analogous to other tabs, however not used here
        self.ctrl = ctrl
        self.initUI()
        
        self.videofiles = []
        self.stopBatch = False
        self.global_resultsfolder = None
        
    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw        

    def init_ohw(self):
        pass

    def initUI(self):
        
        self.box_input = BoxInput(self, self.ctrl) 
        self.box_anasettings = BoxAnasettings(self, self.ctrl)
        self.box_batchsettings = BoxBatchsettings(self, self.ctrl)
        self.box_controls = BoxControls(self, self.ctrl)
        
        #batch param
        # reuse box from tab_analysis instead of doing twice? todo: implement in v1.4 as
        # self.analysis_settings = tab_analysis.TabAnalysis(self, self.ctrl)
        
        #label to display current results folder
        # todo: reimplement!

        self.grid_overall = QGridLayout()
        
        self.grid_overall.addWidget(self.box_input,0,0,1,3)
        self.grid_overall.addWidget(self.box_anasettings,1,0)
        self.grid_overall.addWidget(self.box_batchsettings,1,1)
        self.grid_overall.addWidget(self.box_controls,2,0,1,2)
        
        self.grid_overall.setRowStretch(0,100) # set stretching priority on first row
        self.grid_overall.setRowStretch(3,1) # only stretch last row once maximum height of first row is reached
        self.grid_overall.setColumnStretch(2,1)
    
        # self.grid_overall.addWidget(self.label_results,         15,0)
        # self.grid_overall.addWidget(self.label_results_folder,  15,1,1,2)
        # self.grid_overall.addWidget(self.btn_resultsfolder,     16,0)
        
        self.setLayout(self.grid_overall)            

    def get_param(self):
        param = self.box_anasettings.get_param()
        param_batch = self.box_batchsettings.get_param()
        param.update(param_batch)
        return param
        
    def get_files(self):
        return self.box_input.get_files()
        
    def set_state(self,state):
        if state == "running":
            self.box_anasettings.setEnabled(False)
            self.box_batchsettings.setEnabled(False)
            self.box_input.setEnabled(False)
        if state == "idle":
            self.box_anasettings.setEnabled(True)
            self.box_batchsettings.setEnabled(True)
            self.box_input.setEnabled(True)

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

        # run method gets called thread is started
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
                
                # adjust each results folder if option selected
                if self.param["global_resultsfolder"] != None:
                    #print("change resultsfolder to...",self.param["global_resultsfolder"])
                    inputpath = curr_analysis.videometa["inputpath"] 
                    curr_analysis.analysis_meta["results_folder"] = self.param["global_resultsfolder"]/("results_" + str(inputpath.stem) )
                    #print("resultsfolder:", curr_analysis.analysis_meta["results_folder"])
                        
                    #if self.videometa["input_type"] == 'videofile':
                    #    self.analysis_meta["results_folder"] = inputpath.parent / ("results_" + str(inputpath.stem) )
                
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
                    curr_analysis.get_peakstatistics()
                    curr_analysis.export_analysis()
                
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
        
class BoxInput(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Video list"):
        super(BoxInput, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):

        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title
        self.setMaximumHeight(400)


        self.qlist_batchvideos = QListWidget()
        self.qlist_batchvideos.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.qlist_batchvideos.setMinimumWidth(600)
        
        self.btn_addVid = QPushButton('Add Video(s)')
        self.btn_addVid.resize(self.btn_addVid.sizeHint())
        self.btn_addVid.clicked.connect(self.on_addBatchVideo)
        
        self.btn_remVid = QPushButton('Remove selected Video(s)')
        self.btn_remVid.resize(self.btn_remVid.sizeHint())
        self.btn_remVid.clicked.connect(self.on_removeBatchVideo)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        
        self.grid.addWidget(self.qlist_batchvideos, 0,0,3,1)
        self.grid.addWidget(self.btn_addVid, 0,1)
        self.grid.addWidget(self.btn_remVid, 1,1)  

        self.setLayout(self.grid)
        
    def on_addBatchVideo(self):
    
        new_files = UserDialogs.chooseFilesByUser("Select video to add for batch analysis", input_folder=self.ctrl.config['LAST SESSION']['input_folder'])
        curr_files = [self.qlist_batchvideos.item(i).text() for i in range(self.qlist_batchvideos.count())]

        for new_file in new_files[0]:
            if new_file not in curr_files:
                self.qlist_batchvideos.addItem(new_file)
        # allow selection of folders/multiple files...
        #folderDialog = MultipleFoldersByUser.MultipleFoldersDialog()
        #chosen_folders = folderDialog.getSelection()

        if self.qlist_batchvideos.count() > 0:
            #if folders are present in list
            self.parent.box_controls.btn_startBatch.setEnabled(True) #todo: quite ugly
    
    def on_removeBatchVideo(self):
        
        for item in self.qlist_batchvideos.selectedItems():
            self.qlist_batchvideos.takeItem(self.qlist_batchvideos.row(item))
        if self.qlist_batchvideos.count() == 0:
            self.parent.box_controls.btn_startBatch.setEnabled(False)
        
    def get_files(self):
        files  = [self.qlist_batchvideos.item(i).text() for i in range(self.qlist_batchvideos.count())]
        return files
        
        
class BoxAnasettings(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Blockmatch analysis settings"):
        super(BoxAnasettings, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):

        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title

        self.label_blockwidth = QLabel('Blockwidth:')
        self.label_delay = QLabel('Delay:')
        self.label_maxShift = QLabel('Maximum shift:')

        #spinboxes incl settings
        self.spinbox_blockwidth  = QSpinBox()
        self.spinbox_delay = QSpinBox()
        self.spinbox_maxShift = QSpinBox()
        
        self.label_mpp = QLabel('scale [microns/px]:')
        self.edit_mpp = QLineEdit()#QDoubleSpinBox()
        self.edit_mpp.setFixedWidth(90)
        self.edit_mpp.setText(self.ctrl.config['DEFAULT VALUES']['microns_per_px'])

        # self.edit_mpp.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # self.edit_mpp.setRange(0.0,1000.0)
        # self.edit_mpp.setSingleStep(0.001)
        # self.edit_mpp.setSuffix('microns/px')
        
        self.checkScaling = QCheckBox("Scale longest side to 1024 px during calculation")
        self.checkCanny = QCheckBox("Select region for calculation based on Canny filtering")
        
        self.spinbox_blockwidth.setRange(2,128)
        self.spinbox_blockwidth.setSingleStep(2)
        self.spinbox_blockwidth.setSuffix(' px')
        self.spinbox_delay.setRange(1,20)
        self.spinbox_delay.setSuffix(' frame(s)')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_maxShift.setSuffix(' px')
        
        blockwidth = int(self.ctrl.config['DEFAULT VALUES']['blockwidth'])
        delay = int(self.ctrl.config['DEFAULT VALUES']['delay'])
        max_shift = int(self.ctrl.config['DEFAULT VALUES']['maxshift'])

        self.spinbox_blockwidth.setValue(blockwidth)
        self.spinbox_delay.setValue(delay)
        self.spinbox_maxShift.setValue(max_shift)
        self.checkScaling.setChecked(True)
        self.checkCanny.setChecked(True)

        
        self.grid = QGridLayout()
        
        self.grid.addWidget(self.label_blockwidth,        0,0)
        self.grid.addWidget(self.spinbox_blockwidth,      0,1)
        self.grid.addWidget(self.label_delay,             1,0)
        self.grid.addWidget(self.spinbox_delay,           1,1)
        self.grid.addWidget(self.label_maxShift,          2,0)
        self.grid.addWidget(self.spinbox_maxShift,        2,1)
        self.grid.addWidget(self.label_mpp,               3,0)
        self.grid.addWidget(self.edit_mpp,                3,1)
        self.grid.addWidget(self.checkScaling,            4,0,1,3)
        self.grid.addWidget(self.checkCanny,              5,0,1,3)

        self.grid.setColumnStretch(2,1)
        self.setLayout(self.grid)
        # self.grid_param.setSpacing(15)
        # self.grid_param.setAlignment(Qt.AlignTop|Qt.AlignLeft)
    
    def get_param(self):
        param = {"blockwidth": self.spinbox_blockwidth.value(),
                 "max_shift": self.spinbox_maxShift.value(),
                 "delay": self.spinbox_delay.value(),
                 "scaling": self.checkScaling.isChecked(),
                 "canny": self.checkCanny.isChecked(),
                 "mpp": float(self.edit_mpp.text())}
        return param
        
class BoxBatchsettings(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Batch settings"):
        super(BoxBatchsettings, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()
        
        # init with default settings, so far hardcoded
        self.batchparam = {"heatmaps":True, "quivers":True, "filter":True, "autoPeak":True, 
                    "global_resultsfolder":None}
        self.show_resultsfolder()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def get_param(self):
        """ returns parameterdict of parameters which can be set in this box """
        global_resultsfolder = self.batchparam["global_resultsfolder"]
        if (self.check_batchresultsFolder.isChecked() == True) or (global_resultsfolder is None):
            global_resultsfolder = None
        
        self.batchparam = {"heatmaps":self.checkHeatmaps.isChecked(), 
                            "quivers":self.checkQuivers.isChecked(), 
                            "filter":self.checkFilter.isChecked(), 
                            "autoPeak":self.check_autoPeak.isChecked(), 
                            "global_resultsfolder":global_resultsfolder}
        return self.batchparam

    def init_ui(self):

        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title

        self.checkFilter = QCheckBox("Filter motion vectors after calculation")
        self.checkHeatmaps = QCheckBox("Create heatmap video")
        self.checkQuivers = QCheckBox("Create quiver plot video")
        #self.checkTimeAveraged = QCheckBox("Create plots for time averaged motion")
        # self.checkSaveMotionVectors = QCheckBox("Save the generated motion vectors")
        
        self.check_batchresultsFolder = QCheckBox("Use standard results folder, individual for each video")
        self.label_results_caption = QLabel('Current results folder: ')
        self.label_results_caption.setFont(QFont("Times",weight=QFont.Bold))
        self.label_results_folder = QLabel()
        
        #button for changing the results folder
        self.btn_resultsfolder = QPushButton('Change results folder ')
        self.btn_resultsfolder.clicked.connect(self.on_changeResultsfolder)
        self.btn_resultsfolder.setEnabled(False) 
        
        self.check_autoPeak = QCheckBox("Detect Peaks and export graph")
        
        # initial checked options
                
        self.checkFilter.setChecked(True)
        self.check_autoPeak.setChecked(True)
        # self.checkSaveMotionVectors.setChecked(False)
        self.checkHeatmaps.setChecked(True)
        self.checkQuivers.setChecked(True)
        #self.checkTimeAveraged.setChecked(self.timeAver_status)
        self.check_batchresultsFolder.setChecked(True)        
        
        # callbacks
        self.check_batchresultsFolder.stateChanged.connect(self.on_check_batchresultsFolder) # todo: enable again 
        
        self.grid = QGridLayout()
        
        self.grid.addWidget(self.check_batchresultsFolder,   0,0,1,2)
        self.grid.addWidget(self.label_results_caption, 1,0,1,1)
        self.grid.addWidget(self.label_results_folder, 1,1,1,1)
        self.grid.addWidget(self.btn_resultsfolder, 2,0,1,1)
        
        self.grid.addWidget(self.checkFilter,           3,0,1,2)
        self.grid.addWidget(self.check_autoPeak,        4,0,1,2)
        self.grid.addWidget(self.checkHeatmaps,         5,0,1,2)
        self.grid.addWidget(self.checkQuivers,          6,0,1,2)
        self.grid.setColumnStretch(1,1)

        self.setLayout(self.grid)
        
    def on_check_batchresultsFolder(self):
        #disable or enable the option to choose results folder
        if self.check_batchresultsFolder.isChecked():
            self.btn_resultsfolder.setEnabled(False)
        else:
            self.btn_resultsfolder.setEnabled(True)
        self.show_resultsfolder()
            
    def on_changeResultsfolder(self):
        
        msg = 'Choose a global results folder for saving batch results'
        folder = UserDialogs.chooseFolderByUser(msg)#, input_folder=self.current_ohw.analysis_meta['results_folder'])#, input_folder=self.config['LAST SESSION']['results_folder'])  
        
        if (folder == ''): #cancel pressed
            return
        
        self.batchparam["global_resultsfolder"] = pathlib.Path(folder)
        self.show_resultsfolder()
    
    def show_resultsfolder(self):
        """ sets resultsfolder in label, truncates for nice formatting """
        folder = self.batchparam["global_resultsfolder"]
        if (self.check_batchresultsFolder.isChecked() == True) or (folder is None):
                restext = "individual for each video"
        else:
            restext = str(folder)
        
        if len(restext) > 80:
            restext = restext[-80:]
            restext = "..." + restext[3:]
        self.label_results_folder.setText(restext)        

class BoxControls(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Batch controls"):
        super(BoxControls, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):

        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title

        self.btn_startBatch = QPushButton('Start batch analysis')
        self.btn_startBatch.clicked.connect(self.on_startBatch)
        self.btn_startBatch.setEnabled(False)
        
        self.btn_stopBatch = QPushButton('Stop batch analysis')
        self.btn_stopBatch.clicked.connect(self.on_stopBatch)
        self.btn_stopBatch.setEnabled(False)
        
        self.progressbar = QProgressBar()
        self.progressbar.setMaximum(100)  
        self.progressbar.setValue(0)
        self.progressbar.setFixedWidth(800)

        self.label_state = QLabel('idle')
        self.label_state.setStyleSheet("color: rgb(255,0,0)")        
        
        self.grid = QGridLayout()
        self.grid.addWidget(self.btn_startBatch,        0,0)
        self.grid.addWidget(self.btn_stopBatch,         0,1)
        self.grid.addWidget(self.label_state,           0,2)        
        self.grid.addWidget(self.progressbar,           1,0,1,3)
        self.grid.setColumnStretch(2,1)
        self.grid.setRowStretch(3,1)
        
        self.setLayout(self.grid)
        
        self.stopBatch = False # tracks if batch aborted
        
    def on_startBatch(self):
        self.ctrl.cohw.save_ohw() # saves again as marked peaks might have changed
        self.ctrl.update_tabs()
        print('Starting batch analysis...')
        self.btn_stopBatch.setEnabled(True)
        self.btn_startBatch.setEnabled(False)
        
        videofiles = self.parent.get_files()
        self.Nfiles = len(videofiles)
        param = self.parent.get_param()
        self.thread_batch = OHW.batch_thread(videofiles, param)
        self.thread_batch.progressSignal.connect(self.updateState)
        self.thread_batch.start()
        self.thread_batch.finished.connect(self.finishBatch)
        self.parent.set_state("running") # disables fields

        # use 2 progress bars later? 1 for file progress, 1 for individual calculations....?

        
    def finishBatch(self):
        # enable buttons again
        self.parent.set_state("idle")
        
        if not self.stopBatch:
            self.label_state.setText("idle, batch finished")
        else:
            self.label_state.setText("idle, batch aborted at file " + str(self.filenr))
            self.stopBatch = False

        self.progressbar.setRange(0,1)
        self.progressbar.setValue(1)
        self.btn_startBatch.setEnabled(True)        

    def updateState(self, statedict):
        statemsg = {"load":"loading video","scale":"scaling video", "mcalc":"calculating motion",
                        "heatmapvideo":"creating heatmap video", "quivervideo":"creating quivervideo"}
        state = statedict["state"]
        self.filenr = statedict["filenr"] + 1
        # fullstate = "file " + str(self.filenr) + "/" + str(self.Nfiles) + " files, " + statemsg[state]
        fullstate = "file " + str(self.filenr) + "/" + str(self.Nfiles) + " files, " + statemsg[state]
        self.label_state.setText(fullstate)
        
        if state != "mcalc":    #update progress for motioncalc in percentage... to be implemented
            self.progressbar.setRange(0,0)        

    def on_stopBatch(self):
        self.stopBatch = True
        self.thread_batch.stop_flag.set() #stopping thread_batch
        self.label_state.setText("aborting batch....")
        self.btn_stopBatch.setEnabled(False)        