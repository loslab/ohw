import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, 
    QSpinBox, QCheckBox, QListWidget, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from libraries import helpfunctions, UserDialogs, OHW
import pathlib

class TabBatch(QWidget):
    """
        for time averaged motion
    """
    
    def __init__(self, parent):
        super(TabBatch, self).__init__(parent)
        self.initUI()
        self.parent=parent
        
    def initUI(self):

        self.info = QTextEdit()
        self.info.setText('In this tab you can automate the analysis of multiple folders without further interaction during processing.')
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(40)
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
        #self.spinbox_blockwidth.setMinimumHeight(20)
        self.spinbox_blockwidth.setSingleStep(2)
        self.spinbox_blockwidth.setSuffix(' pixels')
        self.spinbox_blockwidth.setValue(16)  # set standard values somewhere else!
        self.spinbox_delay.setRange(1,20)
        self.spinbox_delay.setSuffix(' frames')
        self.spinbox_delay.setSingleStep(1)
        self.spinbox_delay.setValue(2)
        self.spinbox_maxShift.setSuffix(' pixels')
        self.spinbox_maxShift.setValue(7)
        
        #options for automated analysis
        label_batchOptions = QLabel('Choose options for automated analysis of chosen folders:')
        label_batchOptions.setFont(QFont("Times",weight=QFont.Bold))
        
        self.checkFilter = QCheckBox("Filter motion vectors during calculation")
        self.checkHeatmaps = QCheckBox("Create heatmap video")
        self.checkQuivers = QCheckBox("Create quiver plot video")
        self.checkTimeAveraged = QCheckBox("Create plots for time averaged motion")
        self.checkSaveMotionVectors = QCheckBox("Save the generated motion vectors")
        self.checkScaling = QCheckBox("Scale the longest side to 1024 px during calculation")
        self.check_batchresultsFolder = QCheckBox("Use standard results folder, individual for each video")
        
        # create a variable for the checkbox status
        # actually not needed anymore...
        self.filter_status = True
        self.heatmap_status = True
        self.quiver_status = True
        self.timeAver_status = True
        self.scaling_status = True
        self.saveMotionVectors_status = False
        self.check_batchresultsFolder.setChecked(True)
        
        self.checkFilter.setChecked(self.filter_status)
        self.checkSaveMotionVectors.setChecked(self.saveMotionVectors_status)
        self.checkHeatmaps.setChecked(self.heatmap_status)
        self.checkQuivers.setChecked(self.quiver_status)
        self.checkTimeAveraged.setChecked(self.timeAver_status)
        self.checkScaling.setChecked(self.scaling_status)
        
        #button for starting the analysis
        self.btn_startBatch = QPushButton('Start the automated analysis of chosen folders')
        self.btn_startBatch.clicked.connect(self.on_startBatch)
        self.btn_startBatch.setEnabled(False)
        
        #button for aborting the analysis
        self.btn_stopBatch = QPushButton('Stop onging analysis')
        #self.btn_stopBatch.clicked.connect(self.on_stopBatchAnalysis)
        self.btn_stopBatch.setEnabled(False)
        
        #label to display current results folder
        self.label_results_folder = QLabel('Current results folder: ')
        self.label_results_folder.setFont(QFont("Times",weight=QFont.Bold))
        
        #button for changing the results folder
        self.btn_resultsfolder = QPushButton('Change results folder ')
        #self.btn_resultsfolder.resize(self.btn_resultsfolder.sizeHint())
        #self.btn_resultsfolder.clicked.connect(self.on_changeResultsfolder)
        self.btn_resultsfolder.setEnabled(False)
        self.check_batchresultsFolder.stateChanged.connect(self.changeStatus)
        
        self.progressbar = QProgressBar()
        self.progressbar.setMaximum(100)  
        self.progressbar.setValue(0)
        self.progressbar.setFixedWidth(800)
        self.progressbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

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
        self.grid_overall.addWidget(self.checkScaling,          8,0)
        self.grid_overall.addWidget(self.check_batchresultsFolder,   9,0)
        self.grid_overall.addWidget(self.checkFilter,           10,0)
        self.grid_overall.addWidget(self.checkHeatmaps,         11,0)
        self.grid_overall.addWidget(self.checkQuivers,          12,0)
        self.grid_overall.addWidget(self.label_results_folder,  13,0)
        self.grid_overall.addWidget(self.btn_resultsfolder,  14,0)
        self.grid_overall.addWidget(self.btn_startBatch,        14,1)
        self.grid_overall.addWidget(self.btn_stopBatch,         14,2)
        self.grid_overall.addWidget(self.progressbar,          15,0,1,3)
       
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
    
        new_file = UserDialogs.chooseFileByUser("Select video to add for batch analysis", input_folder=self.parent.config['LAST SESSION']['input_folder'])
        self.qlist_batchvideos.addItem(new_file[0])
        # allow selection of folders/multiple files...
        #folderDialog = MultipleFoldersByUser.MultipleFoldersDialog()
        #chosen_folders = folderDialog.getSelection()
        
        if self.qlist_batchvideos.count() > 0:
            #sobald erster Folder hinzugefügt wird 
            self.btn_startBatch.setEnabled(True)
    
    def on_removeBatchVideo(self):
    
        for item in self.qlist_batchvideos.selectedItems():
            self.qlist_batchvideos.takeItem(self.qlist_batchvideos.row(item))
        if self.qlist_batchvideos.count() == 0:
            self.btn_startBatch.setEnabled(False)            
            
    def changeStatus(self):
        #disable or enable the option to choose results folder
        if self.sender() == self.check_batchresultsFolder:
            if self.check_batchresultsFolder.isChecked():
                self.btn_resultsfolder.setEnabled(False)
            else:
                self.btn_resultsfolder.setEnabled(True)
    
    def on_startBatch(self):
        print('Starting batch analysis...')
        self.btn_addVid.setEnabled(False)
        self.btn_remVid.setEnabled(False)
        self.btn_startBatch.setEnabled(False)
        self.btn_stopBatch.setEnabled(True)
        
        videofiles = [self.qlist_batchvideos.item(i).text() for i in range(self.qlist_batchvideos.count())]
        print(videofiles)
        
        blockwidth = self.spinbox_blockwidth.value()
        delay = self.spinbox_delay.value()
        maxShift = self.spinbox_maxShift.value()          
        
        # turn into thread...
        # use 2 progress bars? 1 for file progress, 1 for individual calculations....?
        for file in videofiles:
            filepath = pathlib.Path(file)
            curr_analysis = OHW.OHW()
            curr_analysis.import_video(filepath)
            
            if self.checkScaling.isChecked():
                curr_analysis.set_analysisImageStack(px_longest = 1024)
            else:
                curr_analysis.set_analysisImageStack()
        
            curr_analysis.calculate_motion(blockwidth = blockwidth, delay = delay, max_shift = maxShift)
            curr_analysis.initialize_motion()
            curr_analysis.save_MVs()
            curr_analysis.plot_TimeAveragedMotions('.png')
            
            if self.checkHeatmaps.isChecked():
                curr_analysis.save_heatmap(singleframe = False)
            if self.checkQuivers.isChecked():
                curr_analysis.save_quiver3(singleframe = False) #allow to choose between quiver and quiver3
            
            
        # enable buttons again
        self.btn_addVid.setEnabled(True)
        self.btn_remVid.setEnabled(True)
        self.btn_startBatch.setEnabled(True)
        self.btn_stopBatch.setEnabled(False)

        '''
        if (self.results_folder_batch == ''):
            self.button_batch_startAnalysis.setEnabled(True)
            print('Batch analysis did not start correctly. Start again!')
            return
        
        #create a thread for batch analysis:
        self.thread_batchAnalysis = self.perform_batchAnalysis_thread()
    
        self.thread_batchAnalysis.start()
        self.thread_batchAnalysis.finished.connect(self.finish_batchAnalysis)
        self.thread_batchAnalysis.progressSignal.connect(self.updateProgressBar_batch)
        '''