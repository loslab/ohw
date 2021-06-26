import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox, QFileDialog,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox, 
    QGroupBox, QVBoxLayout, QHBoxLayout, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ohw import helpfunctions
import numpy as np
from ohw.gui import dialog_kinoptions
import pathlib

class TabKinetics(QWidget):
    
    def __init__(self, parent, ctrl):
        super(TabKinetics, self).__init__(parent)
        self.update = True # update flag, set when motion calculation changed        
        self.parent = parent
        self.ctrl = ctrl
        self.initUI()
        self.init_ohw()
        
    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
        # variables for peak manupulation
        self.move_peak = False #state if peak is selected and moved
        self.Peaks = []
        self.peakidx = None #idx of sel peak, don't select any peaks at start
        self.plotted_peaks = False
        
        """
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
        
        self.fig_kinetics, self.ax_kinetics = plt.subplots(1,1, figsize = (16,12))
        self.canvas_kinetics = FigureCanvas(self.fig_kinetics)
        self.canvas_kinetics.mpl_connect('button_press_event', self.mouse_press_callback)
        self.canvas_kinetics.mpl_connect('motion_notify_event', self.mouse_move_callback)
        self.canvas_kinetics.mpl_connect('button_release_event', self.mouse_release_callback)
        self.roi_rect = None
       
        self.grid_overall = QGridLayout()
        
        self.box_postprocess = BoxPostprocess(self, self.ctrl)
        self.box_peakdetection = BoxPeakdetection(self, self.ctrl)
        self.box_metrics = BoxMetrics(self, self.ctrl)
        self.box_controls = BoxControls(self, self.ctrl)
        self.grid_overall.addWidget(self.box_postprocess,               0,0,2,1)
        self.grid_overall.addWidget(self.box_peakdetection,               0,1,1,1)
        self.grid_overall.addWidget(self.box_metrics,               1,1,1,3)
        self.grid_overall.addWidget(self.box_controls,               0,2,1,1)
        
        #self.grid_overall.addWidget(self.info,               0,0,1,4)
        self.grid_overall.addWidget(self.canvas_kinetics,    2,0,1,4)

        self.grid_overall.setSpacing(10)        
        self.grid_overall.setAlignment(Qt.AlignTop|Qt.AlignLeft)      
        self.setLayout(self.grid_overall)

    def init_ohw(self):
        ''' set values from cohw '''

        if self.update == True:
            self.timeindex = self.cohw.ceval.PeakDetection.timeindex #easier to referene here...
            self.motion = self.cohw.ceval.PeakDetection.motion
            self.Peaks, self.hipeaks, self.lopeaks = self.cohw.ceval.get_peaks()
            
            #self.kinplot_options = self.cohw.kinplot_options
            
            loaded = self.cohw.video_loaded
            finish = self.cohw.analysis_meta["calc_finish"]            
            
            if finish or loaded:
                self.plot_analysis_img()
                self.update_roi()
            
            self.clear_fig()
            if self.cohw.analysis_meta["calc_finish"]:    # if any analysis is done elements can be enabled, as every analysis should have a 1D-representation
                self.init_kinetics()
                self.box_peakdetection.btn_detect_peaks.setEnabled(True)
                self.box_controls.btn_save_kinplot.setEnabled(True)
                self.box_controls.btn_plotsettings.setEnabled(True)
                self.box_controls.btn_export_analysis.setEnabled(True)
                self.box_postprocess.btn_roi.setEnabled(True)
            else:
                self.box_peakdetection.btn_detect_peaks.setEnabled(False)
                self.box_controls.btn_save_kinplot.setEnabled(False)
                self.box_controls.btn_plotsettings.setEnabled(False)
                self.box_controls.btn_export_analysis.setEnabled(False)
                self.box_postprocess.btn_roi.setEnabled(False)
        
            self.update = False

    def init_kinetics(self): 
        ''' initializes kinetics graph and sets statistics'''
        self.ax_kinetics.plot(self.timeindex, self.motion, 
                '-', linewidth = 2)
        self.update_plotview()
        self.plot_Peaks()
        self.box_metrics.update()

        self.canvas_kinetics.draw()

    def set_cohw_peaks(self):
        ''' sets peaks from cohw.ceval to current peaks + plots'''
        self.Peaks, self.hipeaks, self.lopeaks = self.cohw.get_peaks()
        self.plot_Peaks()
        self.box_metrics.update()        

    def plot_analysis_img(self):
        analysis_roi = self.cohw.analysis_meta["roi"]
        if analysis_roi != None:
            scaled_roi = [int(coord*self.cohw.videometa["prev_scale"]) for coord in analysis_roi]
            self.analysis_img = self.cohw.videometa["prev800px"][scaled_roi[1]:scaled_roi[1]+scaled_roi[3],
                                                            scaled_roi[0]:scaled_roi[0]+scaled_roi[2]]
        else:
            self.analysis_img = self.cohw.videometa["prev800px"]
        self.box_postprocess.ax.imshow(self.analysis_img, cmap = 'gray')
            

    def update_roi(self):
        #draw roi on preview img
        if self.roi_rect is not None:
            self.roi_rect.remove()
        
        roi_raw = self.cohw.ceval.roi
        
        if roi_raw is not None:
            roi = [int(coord*self.cohw.videometa["prev_scale"]) for coord in roi_raw]
            self.roi_rect = plt.Rectangle((roi[0],roi[1]), roi[2], roi[3], facecolor='None', edgecolor='red', linewidth = 5)
        else:
            wy, wx = self.analysis_img.shape
            self.roi_rect = plt.Rectangle((0,0), wx-1, wy-1, facecolor='None', edgecolor='red', linewidth = 5) #TODO:hardcoded width, change!
        self.box_postprocess.ax.add_patch(self.roi_rect)
        self.box_postprocess.canvas.draw()

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
        self.box_metrics.update()
        
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
            print("peak added, Peaks:", self.Peaks)

        self.update_Peaks()
        self.plot_Peaks()
        
    def delete_peak(self):
        removepeak = self.Peaks[self.peakidx]
        self.Peaks.remove(removepeak)
        print("peak deleted, Peaks:", self.Peaks)

        self.update_Peaks()
        self.plot_Peaks()
    
    def update_plotview(self):
        ''' updates plot appearence after plotoptions like axis extent changed '''
        
        if self.cohw.kinplot_options["tmax"] != None:
            self.ax_kinetics.set_xlim(right = self.cohw.kinplot_options["tmax"])
        else:
            self.ax_kinetics.set_xlim(right = self.timeindex[-1])
        if self.cohw.kinplot_options["tmin"] != None:
            self.ax_kinetics.set_xlim(left = self.cohw.kinplot_options["tmin"])        
        
        if self.cohw.kinplot_options["vmax"] != None:
            self.ax_kinetics.set_ylim(top = self.cohw.kinplot_options["vmax"])
        else:
            self.ax_kinetics.autoscale(axis = 'y')
        if self.cohw.kinplot_options["vmin"] != None:
            self.ax_kinetics.set_ylim(bottom = self.cohw.kinplot_options["vmin"])
        self.canvas_kinetics.draw()
        
        
class BoxPostprocess(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Postprocessing"):
        super(BoxPostprocess, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
        
    def init_ui(self):
        self.btn_roi = QPushButton("Select rubroi")
        self.btn_roi.clicked.connect(self.on_roi)
        self.btn_reset_roi = QPushButton("Reset subroi")
        self.btn_reset_roi.clicked.connect(self.on_reset)
        self.check_filter = QCheckBox('Filter MVs')
        self.check_filter.setCheckState(False)
        self.check_filter.stateChanged.connect(self.on_check_filter)
        
        # create canvas to display prev image
        self.fig, self.ax = plt.subplots(1,1)#, figsize = (5,5))
        self.fig.patch.set_facecolor('#ffffff')##cd0e49')
        self.fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.ax.axis('off')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.canvas.setFixedSize(250,250)      
        self.roi_rect = None        
        
        
        self.grid = QGridLayout()
        self.grid.addWidget(self.btn_roi,0,1)
        self.grid.addWidget(self.btn_reset_roi,1,1)
        self.grid.addWidget(self.check_filter,2,1)
        self.grid.addWidget(self.canvas,0,0,4,1)
        
        self.setLayout(self.grid)

    def on_roi(self):
        self.cohw.ceval.set_roi()
        #self.parent.update_roi()
        self.cohw.ceval.process() #TODO:reimplement
        self.ctrl.update_tabs()
        
    def on_reset(self):
        self.cohw.ceval.reset_roi()
        self.cohw.ceval.process()
        self.ctrl.update_tabs()
        
    def on_check_filter(self):
        filterstate = self.check_filter.isChecked()
        self.cohw.set_filter('filter_singlemov', filterstate)
        self.cohw.ceval.process()
        self.ctrl.update_tabs()
        
class BoxPeakdetection(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Peakdetection"):
        super(BoxPeakdetection, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):
        
        #spinboxes to choose for manual detection
        self.label_ratio = QLabel('Ratio of peaks: ')           
        self.spinbox_ratio = QDoubleSpinBox()
        self.spinbox_ratio.setRange(0.01, 0.90)
        self.spinbox_ratio.setSingleStep(0.01)
        self.spinbox_ratio.setValue(0.3) #init from config           
        
        self.label_neighbours = QLabel('Number of neighbours:') 
        self.spinbox_neighbours = QSpinBox()    
        self.spinbox_neighbours.setRange(2,99)
        self.spinbox_neighbours.setSingleStep(2)
        self.spinbox_neighbours.setValue(4)        
        
        self.btn_detect_peaks = QPushButton('Detect Peaks')
        self.btn_detect_peaks.clicked.connect(self.on_detect_peaks)
        self.btn_remove_peaks = QPushButton('Remove Peaks')
        self.btn_remove_peaks.clicked.connect(self.on_remove_peaks)

        self.grid = QGridLayout()
        self.grid.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.grid.addWidget(self.label_ratio,0,0)
        self.grid.addWidget(self.label_neighbours,1,0)
        self.grid.addWidget(self.spinbox_ratio,0,1)
        self.grid.addWidget(self.spinbox_neighbours,1,1)
        self.grid.addWidget(self.btn_detect_peaks,2,1)
        self.grid.addWidget(self.btn_remove_peaks,3,1)
        
        self.setLayout(self.grid)        
        
    def on_detect_peaks(self):
        '''detect peaks and draw them as 'EKG' '''
        ratio = self.spinbox_ratio.value()
        neighbours = self.spinbox_neighbours.value()
        self.cohw.detect_peaks(ratio, neighbours)
        self.parent.set_cohw_peaks()

    def on_remove_peaks(self):
        self.cohw.set_peaks([])
        self.parent.set_cohw_peaks()

class BoxMetrics(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Peak metrics"):
        super(BoxMetrics, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):
        
        self.lbl = QLabel('value: ')           
        
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.grid.addWidget(QLabel('Max contraction:'),0,0)
        self.grid.addWidget(QLabel('Max relaxation:'),1,0)
        self.grid.addWidget(QLabel('Beating rate:'),2,0)
        self.grid.addWidget(QLabel('Mean contraction interval:'),0,2)
        self.grid.addWidget(QLabel('Mean relaxation interval:'),1,2)
        self.grid.addWidget(QLabel('Mean contraction-relaxation interval:'),2,2)
        
        self.label_max_contraction = QLabel("NA")
        self.label_max_relaxation = QLabel("NA")
        self.label_bpm = QLabel("NA")
        self.label_time_contraction = QLabel("NA")
        self.label_time_relaxation = QLabel("NA")
        self.label_time_contr_relax = QLabel("NA")
        
        #self.label_max_contraction.setFixedWidth(100) # TODO: improve handling/ display, constrain digits
        #self.label_time_contr_relax.setFixedWidth(100)

        self.grid.addWidget(self.label_max_contraction,0,1)
        self.grid.addWidget(self.label_max_relaxation,1,1)
        self.grid.addWidget(self.label_bpm,2,1)
        self.grid.addWidget(self.label_time_contraction,0,3)
        self.grid.addWidget(self.label_time_relaxation,1,3)
        self.grid.addWidget(self.label_time_contr_relax,2,3)
        
        self.grid.setColumnMinimumWidth(1,150)
        self.grid.setColumnMinimumWidth(3,150)
        self.grid.setColumnStretch(1,1)
        self.grid.setColumnStretch(3,1)
        
        self.setLayout(self.grid)

    def update(self):
        peakstat = self.cohw.get_peakstatistics()
        text_contraction = str(peakstat["max_contraction"]) + ' +- ' + str(peakstat["max_contraction_std"]) +  u' µm/s'
        text_relaxation = str(peakstat["max_relaxation"]) + ' +- ' + str(peakstat["max_relaxation_std"]) +  u' µm/s'
        text_time_contraction = str(peakstat["contraction_interval_mean"]) + ' +- ' + str(peakstat["contraction_interval_std"]) + ' s'
        text_time_relaxation = str(peakstat["relaxation_interval_mean"]) + ' +- ' + str(peakstat["relaxation_interval_std"]) + ' s'
        text_bpm = str(peakstat["bpm_mean"]) + ' +- ' + str(peakstat["bpm_std"]) + ' bpm'
        text_time_contr_relax = str(peakstat["contr_relax_interval_mean"]) + ' +- ' + str(peakstat["contr_relax_interval_std"]) + ' s'

        self.label_max_contraction.setText(text_contraction)
        self.label_max_relaxation.setText(text_relaxation)
        self.label_time_contraction.setText(text_time_contraction)
        self.label_time_relaxation.setText(text_time_relaxation)
        self.label_bpm.setText(text_bpm)
        self.label_time_contr_relax.setText(text_time_contr_relax)

class BoxControls(QGroupBox):
    def __init__(self, parent, ctrl, boxtitle = "Controls"):
        super(BoxControls, self).__init__(boxtitle, parent = parent)
        self.parent=parent
        self.ctrl = ctrl
        self.init_ui()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw    

    def init_ui(self):

        self.btn_save_kinplot = QPushButton('Save graph as...')
        self.btn_export_analysis = QPushButton('Save peak analysis')
        self.btn_plotsettings = QPushButton('Change graph settings')
        
        self.btn_save_kinplot.clicked.connect(self.on_save_kinplot)
        self.btn_export_analysis.clicked.connect(self.on_export_analysis)
        self.btn_plotsettings.clicked.connect(self.on_plotsettings)

        
        self.grid_btns = QGridLayout()
        self.grid_btns.setSpacing(10)
        #self.grid_btns.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        #self.grid_btns.setColumnStretch(1,1)
        
        self.grid_btns.addWidget(self.btn_export_analysis, 0,0)
        self.grid_btns.addWidget(self.btn_plotsettings, 1,0)
        self.grid_btns.addWidget(self.btn_save_kinplot, 2,0)       

        self.setLayout(self.grid_btns)            
        
    def on_plotsettings(self):
        self.dialog_kinoptions = dialog_kinoptions.DialogKinoptions(plotsettings = self.cohw.kinplot_options)
        self.dialog_kinoptions.exec_()
        #self.kinplot_options.update(self.dialog_kinoptions.get_settings())
        self.cohw.update_kinplot_options(self.dialog_kinoptions.get_settings())
        self.parent.update_plotview()

    def on_save_kinplot(self):
        
        file_types = "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.tiff);;BMP(*.bmp);; Scalable Vector Graphics (*.svg)"
        #let the user choose a folder from the starting path
        path = str(pathlib.PureWindowsPath(self.cohw.analysis_meta["results_folder"] / 'beating_kinetics.PNG'))
        filename = QFileDialog.getSaveFileName(None, 'Choose a folder and enter a filename', path, file_types)[0]

        if (filename == ''): # if 'cancel' was pressed:
            return

        self.cohw.plot_kinetics(filename) # move mark_peaks into kinplot_options
        helpfunctions.msgbox(self, 'Plot was saved successfully.')

    def on_export_analysis(self):
        self.cohw.export_analysis()
        helpfunctions.msgbox(self, 'analyzed Peaks were saved successfully.')        