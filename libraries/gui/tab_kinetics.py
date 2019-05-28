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
        self.initUI()
        self.parent=parent
        
    def initUI(self):
        self.move_peak = False #state if peak is selected and moved
        self.Peaks = []
        self.peakidx = None #don't select any peaks 
               
        self.info = QTextEdit()
        self.info.setText('In this tab you can plot beating kinetics and calculate statistics based on found peaks. Change parameters manually to optimize the peak detection. You can save the graphs and export the peaks.')
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
        self.spinbox_ratio.setValue(0.05)           
        
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
        self.button_saveKinetics = QPushButton('Save graph as...')
        self.button_export_peaks = QPushButton('Save peak analysis')
        self.button_export_ekg_csv = QPushButton('Save EKG as excel file (.xlsx)')
        
        self.btn_plot_settings = QPushButton('Change graph settings')
        self.button_detectPeaks.resize(self.button_detectPeaks.sizeHint())
        self.button_saveKinetics.resize(self.button_saveKinetics.sizeHint())
        self.button_export_peaks.resize(self.button_export_peaks.sizeHint())
        self.button_export_ekg_csv.resize(self.button_export_ekg_csv.sizeHint())

        self.button_saveKinetics.setEnabled(False)
        self.button_export_peaks.setEnabled(False)
        self.button_export_ekg_csv.setEnabled(False)
        
        self.button_detectPeaks.clicked.connect(self.on_detectPeaks)            
        self.button_saveKinetics.clicked.connect(self.on_saveKinetics)
        #self.button_export_peaks.clicked.connect(self.on_exportPeaks)
        #self.button_export_ekg_csv.clicked.connect(self.on_exportEKG_CSV)
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
        self.grid_btns.addWidget(self.button_saveKinetics, 0,1)
        self.grid_btns.addWidget(self.button_export_ekg_csv, 0,2)
        self.grid_btns.addWidget(self.button_export_peaks, 0,3)

        btnwidth = 300 
        self.button_saveKinetics.setFixedWidth(btnwidth)
        self.button_export_ekg_csv.setFixedWidth(btnwidth)
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
        """
        set values from current_ohw
        """
        self.current_ohw = self.parent.current_ohw
        self.timeindex = self.current_ohw.timeindex #easier to referene here...
        self.motion = self.current_ohw.mean_absMotions
        self.Peaks = [] # better: load saved peaks from ohw
        
        # init self.plotsettings based on config/ ohw-file
        self.kinplot_options = self.current_ohw.kinplot_options
        
        self.clear_fig()
        if self.current_ohw.analysis_meta["has_MVs"]:    # change here to appropriate variable
            self.init_kinetics()
            self.button_detectPeaks.setEnabled(True)
            self.button_saveKinetics.setEnabled(True)
            self.button_export_ekg_csv.setEnabled(True)
            self.btn_plot_settings.setEnabled(True)
            self.button_export_peaks.setEnabled(True)
        else:
            self.button_saveKinetics.setEnabled(False)
            self.button_detectPeaks.setEnabled(False)
            self.button_export_ekg_csv.setEnabled(False)
            self.btn_plot_settings.setEnabled(False)
            self.button_export_peaks.setEnabled(False)
            self.plotted_peaks = False

    def init_kinetics(self): 
        """
        initializes kinetics graph
        """        
        self.ax_kinetics.plot(self.timeindex, self.motion, 
                '-', linewidth = 2)
        self.ax_kinetics.set_xlim(left = 0, right = self.timeindex[-1])
        self.ax_kinetics.set_ylim(bottom = 0)

        self.canvas_kinetics.draw()

    def clear_fig(self):
        self.ax_kinetics.clear()        
        self.ax_kinetics.set_xlabel('t [s]', fontsize = 14)
        self.ax_kinetics.set_ylabel(u'Mean Absolute Motion [\xb5m/s]', fontsize = 14)
        self.ax_kinetics.tick_params(labelsize = 14)
        self.fig_kinetics.subplots_adjust(bottom=0.20, top=0.98, left=0.05, right=0.98)
    
        for side in ['top','right','bottom','left']:
            self.ax_kinetics.spines[side].set_linewidth(2)
        
        self.canvas_kinetics.draw()

    def on_detectPeaks(self):
        #detect peaks and draw them as EKG
        ratio = self.spinbox_ratio.value()
        number_of_neighbours = self.spinbox_neighbours.value()
        self.current_ohw.detect_peaks(ratio, number_of_neighbours)
        self.Peaks = self.current_ohw.get_peaks()
        
        self.updatePeaks()

    def updatePeaks(self):
        """
            update detected peaks in graph
        """
        # clear old peaks first
        if self.plotted_peaks == True:
            for marker in self.marker:
                marker.remove()
        
        self.hipeaks, self.lopeaks = self.orderPeaks()
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
        
        self.updateStatistics()
        """
        peakstatistics = self.current_ohw.get_peakstatistics()
        peaktime_intervals = self.current_ohw.get_peaktime_intervals()
        bpm = self.current_ohw.get_bpm()
                
        #enable saving of peaks and statistics
        self.button_export_peaks.setEnabled(True)
        self.button_export_ekg_csv.setEnabled(True)
        """
    
    def updateStatistics(self):
        peakstatistics = self.get_peakstatistics()
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
    
    def get_peakstatistics(self):
        decimals = 2
        motion_high = self.motion[self.hipeaks] if self.hipeaks != None else []
        motion_low = self.motion[self.lopeaks] if self.lopeaks != None else []
        times_high = self.timeindex[self.hipeaks] if self.hipeaks != None else []
        times_low = self.timeindex[self.lopeaks] if self.lopeaks != None else []

        max_contraction = np.round(np.mean(motion_high), decimals)
        max_contraction_std = np.round(np.std(motion_high),  decimals)        
        max_relaxation      = np.round(np.mean(motion_low),  decimals)
        max_relaxation_std  = np.round(np.std(motion_low),   decimals)
        
        contraction_intervals = np.diff(np.sort(times_high))
        relaxation_intervals = np.diff(np.sort(times_low))
        
        contraction_interval_mean = np.round(np.mean(contraction_intervals), decimals)
        contraction_interval_std = np.round(np.std(contraction_intervals), decimals)
        relaxation_interval_mean = np.round(np.mean(relaxation_intervals), decimals)
        relaxation_interval_std = np.round(np.std(relaxation_intervals), decimals)    
        
        contr_relax_intervals = []
        
        if len(self.Peaks) >= 2: # calculate contr_relax only if 1 relax peak after 1 contr peak detected
            shift = 0 if times_high[0] < times_low[0] else 1
            for low_peak, high_peak in zip(times_low[shift:], times_high):
                # depending on which peak is first the true interval might be from the next peak on....
                time_difference = low_peak - high_peak           
                contr_relax_intervals.append(time_difference)
        contr_relax_interval_mean = np.round(np.mean(np.asarray(contr_relax_intervals)), decimals)
        contr_relax_interval_std = np.round(np.std(np.asarray(contr_relax_intervals)), decimals)            

        bpm_mean = np.round(np.mean(60/contraction_intervals), decimals)
        bpm_std = np.round(np.std(60/contraction_intervals), decimals)        
        
        peakstatistics = {"max_contraction":max_contraction, "max_contraction_std":max_contraction_std,
                "max_relaxation":max_relaxation, "max_relaxation_std":max_relaxation_std,
                "contraction_interval_mean":contraction_interval_mean, "contraction_interval_std":contraction_interval_std,
                "relaxation_interval_mean":relaxation_interval_mean, "relaxation_interval_std":relaxation_interval_std,
                "bpm_mean":bpm_mean, "bpm_std": bpm_std,
                "contr_relax_interval_mean":contr_relax_interval_mean, "contr_relax_interval_std":contr_relax_interval_std}
        
        return peakstatistics
    
    def orderPeaks(self):
        '''order high/low peaks, return index'''
        if len(self.Peaks) == 0:
            return None, None
        
        # just order alternating, start with highest peak
        peakheights = self.motion[self.Peaks]
        highest_peak = np.argmax(peakheights)
        
        even = self.Peaks[::2]
        odd = self.Peaks[1::2]
        if highest_peak %2 == 0:    # if highest peak in even index
            hipeaks = even
            lopeaks = odd
        else:
            hipeaks = odd
            lopeaks = even
        return hipeaks, lopeaks
        
    def mouse_press_callback(self, event):
        '''mouse button is pressed'''
        #if not self.showverts:
        #    return
        #if event.inaxes is None:
        #    return
        
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
            print("selected peak: ",self.timeindex[Peak],self.motion[Peak])
            if event.button == 3:
                self.delete_peak()
    
    def mouse_release_callback(self, event):
        '''mouse button is released'''
        #if not self.showverts:
        #    return
        if event.button != 1:
            return
        
        if self.move_peak:
            removepeak = self.Peaks[self.peakidx]
            self.Peaks.remove(removepeak)
            newidx = self.get_closest(event.xdata)
            self.Peaks.append(newidx)
            self.Peaks.sort()  
            self.updatePeaks()
            self.move_peak = False
        
        self.peakidx = None
        
    def mouse_move_callback(self, event):
        '''mouse is moved'''
        #if not self.showverts:
        #    return
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
        #self.current_ohw.add_peak(newidx)
        if newidx not in self.Peaks:
            self.Peaks.append(newidx)
            self.Peaks.sort()
            print("peak added, Peaks:", self.Peaks)

        self.updatePeaks()
        
    def delete_peak(self):
        removepeak = self.Peaks[self.peakidx]
        self.Peaks.remove(removepeak)
        print("peak deleted, Peaks:", self.Peaks)
        #self.current_oh.delete_peak(self.peakidx)

        self.updatePeaks()
    
    def on_plotSettings(self):
        self.dialog_kinoptions = dialog_kinoptions.DialogKinoptions(plotsettings = self.kinplot_options)
        self.dialog_kinoptions.exec_()
        self.kinplot_options = self.dialog_kinoptions.get_settings()
        self.update_plotsettings()

    def on_saveKinetics(self):
        
        #mark_peaks = self.plotted_peaks
        
        #allowed file types:
        file_types = "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.tiff);;BMP(*.bmp);; Scalable Vector Graphics (*.svg)"
        #let the user choose a folder from the starting path
        path = str(pathlib.PureWindowsPath(self.current_ohw.analysis_meta["results_folder"] / 'beating_kinetics.PNG'))
        filename = QFileDialog.getSaveFileName(None, 'Choose a folder and enter a filename', path, file_types)[0]

        #if 'cancel' was pressed: simply do nothing and wait for user to click another button
        if (filename == ('','')):
            return
        try:
            self.current_ohw.plot_beatingKinetics(filename) # move mark_peaks into kinplot_options
            helpfunctions.msgbox(self, 'Plot was saved successfully.')
            
        except (IndexError, NameError, AttributeError):
            pass

    def update_plotsettings(self):
        self.current_ohw.set_kinplot_options(self.kinplot_options)
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
        