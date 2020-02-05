import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox, QFileDialog,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from libraries import helpfunctions
import numpy as np
from libraries.gui import dialog_kinoptions
import pathlib

class TabKinetics(QWidget):
    """
        for time averaged motion
    """
    
    def __init__(self, parent):
        super(TabKinetics, self).__init__(parent)
        self.parent=parent
        self.initUI()
        
    def initUI(self):
        self.move_peak = False #state if peak is selected and moved
        self.Peaks = []
        self.peakidx = None #don't select any peaks
        self.plotted_peaks = False
        
        self.info = QTextEdit()
        self.info.setText("In this tab, beating kinetics are shown and statistics calculated " \
                "based on found peaks. By 'Detect Peaks', an automatic peak detection based on " \
                "the 2 parameters 'ratio of peaks' and 'number of neighbouring values' is conducted. " \
                "You can manually add a peak (left click), shift a peak (left click + drag) or delete " \
                "a peak (right click).")
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(50)
        self.info.setMaximumWidth(800)
        self.info.setStyleSheet("background-color: LightSkyBlue")
        
        """
        #create a label for choosing the ROI
        label_ekg_choose_ROI = QLabel('Choose the ROI to be displayed: ')
        label_ekg_choose_ROI.setFont(QFont("Times",weight=QFont.Bold))
        
        #create a drop-down menu for choosing the ROI to be displayed
        self.ekg_combobox = QComboBox()
        self.ekg_combobox.addItem('Full image')    
        #self.ekg_combobox.activated[str].connect(self.on_chooseROI)
        self.ekg_combobox.currentIndexChanged[int].connect(self.on_chooseROI)
        """
        
        #label_results = QLabel('Results: ')
        #label_results.setFont(QFont("Times",weight=QFont.Bold))

        self.fig_kinetics, self.ax_kinetics = plt.subplots(1,1, figsize = (16,12))
        self.canvas_kinetics = FigureCanvas(self.fig_kinetics)
        self.canvas_kinetics.mpl_connect('button_press_event', self.mouse_press_callback)
        self.canvas_kinetics.mpl_connect('motion_notify_event', self.mouse_move_callback)
        self.canvas_kinetics.mpl_connect('button_release_event', self.mouse_release_callback)
        
        #spinboxes to choose for manual detection
        self.label_ratio = QLabel('Ratio of peaks: ')           
        self.spinbox_ratio = QDoubleSpinBox()
        self.spinbox_ratio.setRange(0.01, 0.90)
        self.spinbox_ratio.setSingleStep(0.01)
        self.spinbox_ratio.setValue(0.3) #move to config           
        
        self.label_neighbours = QLabel('Number of neighbouring values for evaluation:') 
        self.spinbox_neighbours = QSpinBox()    
        self.spinbox_neighbours.setRange(2,10)
        self.spinbox_neighbours.setSingleStep(2)
        self.spinbox_neighbours.setValue(4)
        
        self.label_max_contraction = QLabel('Detected maximum contraction: ')
        self.label_max_relaxation = QLabel('Detected maximum relaxation: ')
        self.label_time_contraction = QLabel('Mean contraction interval: ')
        self.label_time_relaxation = QLabel('Mean relaxation interval: ')
        self.label_time_contr_relax = QLabel('Mean interval between contraction and relaxation: ')
        self.label_bpm = QLabel('Beating rate: ')
        
        self.label_max_contraction_result = QLabel('not enough peaks')            
        self.label_max_relaxation_result = QLabel('not enough peaks')
        self.label_time_contraction_result = QLabel('not enough peaks')
        self.label_time_relaxation_result = QLabel('not enough peaks')
        self.label_time_contr_relax_result = QLabel('not enough peaks')
        self.label_bpm_result = QLabel('not enough peaks')
        
        #self.label_furtherAnalysis = QLabel('Further options:')
        #self.label_furtherAnalysis.setFont(QFont("Times",weight=QFont.Bold))
        
        self.label_evaluate = QLabel('Start evaluation')
        self.label_evaluate.setFont(QFont("Times",weight=QFont.Bold))
        
        self.button_detectPeaks = QPushButton('Detect Peaks')
        self.button_detectPeaks.setMaximumWidth(300)
        self.button_saveKinPlot = QPushButton('Save graph as...')
        self.button_export_peaks = QPushButton('Save peak analysis')
        
        self.btn_plot_settings = QPushButton('Change graph settings')
        self.button_detectPeaks.resize(self.button_detectPeaks.sizeHint())
        self.button_saveKinPlot.resize(self.button_saveKinPlot.sizeHint())
        self.button_export_peaks.resize(self.button_export_peaks.sizeHint())

        self.button_saveKinPlot.setEnabled(False)
        self.button_export_peaks.setEnabled(False)
        
        self.button_detectPeaks.clicked.connect(self.on_detectPeaks)            
        self.button_saveKinPlot.clicked.connect(self.on_saveKinPlot)
        self.button_export_peaks.clicked.connect(self.on_exportAnalysis)
        self.btn_plot_settings.clicked.connect(self.on_plotSettings)
                  
        self.grid_overall = QGridLayout()
        self.grid_overall.addWidget(self.info,               0,0,1,4)
        #self.grid_overall.addWidget(label_ekg_choose_ROI,    1,0)
        #self.grid_overall.addWidget(self.ekg_combobox,       2,0)
        #self.grid_overall.addWidget(self.label_results,           3,0)
        self.grid_overall.addWidget(self.label_ratio,             1,0)
        self.grid_overall.addWidget(self.spinbox_ratio,      1,1)
        self.grid_overall.addWidget(self.label_neighbours,        2,0)
        self.grid_overall.addWidget(self.spinbox_neighbours, 2,1)
        self.grid_overall.addWidget(self.button_detectPeaks, 2,2)
        self.grid_overall.addWidget(self.canvas_kinetics,    3,0,1,6)
        
        self.grid_overall.addWidget(self.label_max_contraction,   4,0)
        self.grid_overall.addWidget(self.label_max_contraction_result, 4,1)
        self.grid_overall.addWidget(self.label_max_relaxation,    5,0)
        self.grid_overall.addWidget(self.label_max_relaxation_result, 5,1)
        self.grid_overall.addWidget(self.label_bpm,              6,0)
        self.grid_overall.addWidget(self.label_bpm_result,   6,1)        
        
        self.grid_overall.addWidget(self.label_time_contraction,  4,3)
        self.grid_overall.addWidget(self.label_time_contraction_result, 4,4)
        self.grid_overall.addWidget(self.label_time_relaxation,  5,3)            
        self.grid_overall.addWidget(self.label_time_relaxation_result, 5,4)
        self.grid_overall.addWidget(self.label_time_contr_relax,  6,3)
        self.grid_overall.addWidget(self.label_time_contr_relax_result, 6,4)

        self.grid_btns = QGridLayout()
        self.grid_btns.setSpacing(10)
        self.grid_btns.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        
        self.grid_btns.addWidget(self.btn_plot_settings, 0,0)
        self.grid_btns.addWidget(self.button_saveKinPlot, 0,1)
        self.grid_btns.addWidget(self.button_export_peaks, 0,2)

        btnwidth = 300 
        self.button_saveKinPlot.setFixedWidth(btnwidth)
        self.button_export_peaks.setFixedWidth(btnwidth)
        self.btn_plot_settings.setFixedWidth(btnwidth)

        self.grid_overall.addLayout(self.grid_btns,7,0,1,6,Qt.AlignTop|Qt.AlignLeft)
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
        ''' set values from cohw '''
        self.cohw = self.parent.cohw
        self.ceval = self.cohw.ceval
        
        self.timeindex = self.ceval.timeindex #easier to referene here...
        self.motion = self.ceval.mean_absMotions
        self.Peaks, self.hipeaks, self.lopeaks = self.ceval.get_peaks()
        
        self.kinplot_options = self.cohw.kinplot_options
        
        self.clear_fig()
        if self.cohw.analysis_meta["has_MVs"]:    # change here to appropriate variable
            self.init_kinetics()
            self.button_detectPeaks.setEnabled(True)
            self.button_saveKinPlot.setEnabled(True)
            self.btn_plot_settings.setEnabled(True)
            self.button_export_peaks.setEnabled(True)
        else:
            self.button_saveKinPlot.setEnabled(False)
            self.button_detectPeaks.setEnabled(False)
            self.btn_plot_settings.setEnabled(False)
            self.button_export_peaks.setEnabled(False)

    def init_kinetics(self): 
        ''' initializes kinetics graph and sets statistics'''
        self.ax_kinetics.plot(self.timeindex, self.motion, 
                '-', linewidth = 2)
        self.ax_kinetics.set_xlim(left = 0, right = self.timeindex[-1])
        self.ax_kinetics.set_ylim(bottom = 0)

        self.plot_Peaks()
        self.updateStatistics()
        self.canvas_kinetics.draw()

    def clear_fig(self):
        self.ax_kinetics.clear()
        self.plotted_peaks = False        
        self.ax_kinetics.set_xlabel('t [s]', fontsize = 14)
        self.ax_kinetics.set_ylabel(u'Mean Absolute Motion [\xb5m/s]', fontsize = 14)
        self.ax_kinetics.tick_params(labelsize = 14)
        self.fig_kinetics.subplots_adjust(bottom=0.20, top=0.98, left=0.05, right=0.98)
    
        for side in ['top','right','bottom','left']:
            self.ax_kinetics.spines[side].set_linewidth(2)
        
        self.canvas_kinetics.draw()

    def on_detectPeaks(self):
        '''detect peaks and draw them as 'EKG' '''
        ratio = self.spinbox_ratio.value()
        number_of_neighbours = self.spinbox_neighbours.value()
        self.cohw.detect_peaks(ratio, number_of_neighbours)
        self.Peaks, self.hipeaks, self.lopeaks = self.cohw.get_peaks()
        self.plot_Peaks()
        self.updateStatistics()

    def plot_Peaks(self):
        ''' clear old peaks and plot all self.hipeaks, self.lopeaks '''
        
        # clear old peaks first
        if self.plotted_peaks == True:
            for marker in self.marker:
                marker.remove()

        self.Peaks, self.hipeaks, self.lopeaks = self.cohw.get_peaks()
        himarker, lomarker = [],[]
        self.markerpeaks = []
        
        if self.hipeaks != None:
            himarker = [self.ax_kinetics.plot(self.timeindex[Peak],self.motion[Peak],'o', ls="",color='r',ms=5)[0] for Peak in self.hipeaks]
        if self.lopeaks != None:
            lomarker = [self.ax_kinetics.plot(self.timeindex[Peak],self.motion[Peak],'^', ls="",color='r',ms=5)[0] for Peak in self.lopeaks]
        self.marker = himarker+lomarker #concatenate all marker
        
        if self.hipeaks != None:
            self.markerpeaks = self.hipeaks + self.lopeaks # markerpeaks: peaks ordered corresponding to marker (same concatenation)

        self.plotted_peaks = True
        self.canvas_kinetics.draw()
    
    def update_Peaks(self):
        ''' update manually changed Peaks with cohw '''
        self.cohw.set_peaks(self.Peaks)
        self.updateStatistics()
    
    def updateStatistics(self):
        peakstatistics = self.cohw.get_peakstatistics()
        text_contraction = str(peakstatistics["max_contraction"]) + ' +- ' + str(peakstatistics["max_contraction_std"]) +  u' \xb5m/s'
        text_relaxation = str(peakstatistics["max_relaxation"]) + ' +- ' + str(peakstatistics["max_relaxation_std"]) +  u' \xb5m/s'
        text_time_contraction = str(peakstatistics["contraction_interval_mean"]) + ' +- ' + str(peakstatistics["contraction_interval_std"]) + ' s'
        text_time_relaxation = str(peakstatistics["relaxation_interval_mean"]) + ' +- ' + str(peakstatistics["relaxation_interval_std"]) + ' s'
        text_bpm = str(peakstatistics["bpm_mean"]) + ' +- ' + str(peakstatistics["bpm_std"]) + ' beats/min'
        text_time_contr_relax = str(peakstatistics["contr_relax_interval_mean"]) + ' +- ' + str(peakstatistics["contr_relax_interval_std"]) + ' s'
        
        self.label_max_contraction_result.setText(text_contraction)
        self.label_max_relaxation_result.setText(text_relaxation)
        self.label_time_contraction_result.setText(text_time_contraction)
        self.label_time_relaxation_result.setText(text_time_relaxation)
        self.label_bpm_result.setText(text_bpm)
        self.label_time_contr_relax_result.setText(text_time_contr_relax)
        
    def mouse_press_callback(self, event):
        '''mouse button is pressed'''
        if event.inaxes is None:
            return
        
        if event.button not in [1,3]: # only accept left/right mouse click
            return
        self.peakidx = self.sel_peak(event) # index of selected peak (refers to position in list of peaks, not absolute position)
        
        if (self.peakidx == None): # add new peak if no peak selected and left mouse click
            if event.button == 1:
                self.add_peak(event)
            else:
                return
        
        else: # delete peak if peak selected and right mouse click
            Peak = self.Peaks[self.peakidx]
            #print("selected peak: ",self.timeindex[Peak],self.motion[Peak])
            if event.button == 3:
                self.delete_peak()
    
    def mouse_release_callback(self, event):
        '''mouse button is released'''
        if event.button != 1:
            return
        
        if self.move_peak:
            removepeak = self.Peaks[self.peakidx]
            self.Peaks.remove(removepeak)
            newidx = self.get_closest(event.xdata)
            self.Peaks.append(newidx)
            self.Peaks.sort()  
            self.update_Peaks()
            self.plot_Peaks()
            self.move_peak = False
        
        self.peakidx = None
        
    def mouse_move_callback(self, event):
        '''mouse is moved'''
        if self.peakidx is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return

        self.move_peak = True
        if event.xdata != None:
            selidx = self.get_closest(event.xdata)
        
            x = self.timeindex[selidx]
            y = self.motion[selidx]
            
            Peak = self.Peaks[self.peakidx]
            markeridx = self.markerpeaks.index(Peak) #position of selection in concatenated marker array...
            self.marker[markeridx].set_data(x,y)
        
            self.canvas_kinetics.draw() 

    def sel_peak(self,event):
        '''returns index of selected peak'''
        if len(self.Peaks) == 0: # if no peaks available, none can be selected
            return None
        
        delta = 25
        xPeaks = self.timeindex[self.Peaks]
        yPeaks = self.motion[self.Peaks]
        xy = list(zip(xPeaks, yPeaks))#convert to list of tuples to enable transformation
        #https://stackoverflow.com/questions/44409084/how-to-zip-two-1d-numpy-array-to-2d-numpy-array
        xyt = self.ax_kinetics.transData.transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        peakidx = indseq[0] # index of value which fits best in list of xpeaks 
        
        if d[peakidx] >= delta:
            peakidx = None
        return peakidx # index of selected peak
        
    def get_closest(self, xcursor):
        '''returns index of closest datapoint next to cursor location'''
        minidx = np.argmin(np.abs(self.timeindex-xcursor)) #xcursor = event.xdata
        return minidx 
        
    def add_peak(self, event):
        newidx = self.get_closest(event.xdata)
        
        if newidx not in self.Peaks:
            self.Peaks.append(newidx)
            self.Peaks.sort()
            print("peak added, Peaks:", self.Peaks)

        self.update_Peaks()
        self.plot_Peaks()
        
    def delete_peak(self):
        removepeak = self.Peaks[self.peakidx]
        self.Peaks.remove(removepeak)
        print("peak deleted, Peaks:", self.Peaks)

        self.update_Peaks()
        self.plot_Peaks()
    
    def on_plotSettings(self):
        self.dialog_kinoptions = dialog_kinoptions.DialogKinoptions(plotsettings = self.kinplot_options)
        self.dialog_kinoptions.exec_()
        self.kinplot_options = self.dialog_kinoptions.get_settings()
        self.update_plotsettings()

    def on_saveKinPlot(self):
        
        file_types = "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.tiff);;BMP(*.bmp);; Scalable Vector Graphics (*.svg)"
        #let the user choose a folder from the starting path
        path = str(pathlib.PureWindowsPath(self.cohw.analysis_meta["results_folder"] / 'beating_kinetics.PNG'))
        filename = QFileDialog.getSaveFileName(None, 'Choose a folder and enter a filename', path, file_types)[0]

        if (filename == ''): # if 'cancel' was pressed:
            return

        self.cohw.plot_beatingKinetics(filename) # move mark_peaks into kinplot_options
        helpfunctions.msgbox(self, 'Plot was saved successfully.')

    def on_exportAnalysis(self):
        self.cohw.export_analysis()
        helpfunctions.msgbox(self, 'analyzed Peaks were saved successfully.')

    def update_plotsettings(self):
        ''' updates plot appearence after plotoptions like axis extent changed '''
        self.cohw.set_kinplot_options(self.kinplot_options)
        if self.kinplot_options["tmax"] != None:
            self.ax_kinetics.set_xlim(right = self.kinplot_options["tmax"])
        else:
            self.ax_kinetics.set_xlim(right = self.timeindex[-1])
            
        if self.kinplot_options["vmax"] != None:
            self.ax_kinetics.set_ylim(top = self.kinplot_options["vmax"])
        else:
            self.ax_kinetics.autoscale(axis = 'y')
        self.ax_kinetics.set_ylim(bottom = 0)
        self.canvas_kinetics.draw()
        