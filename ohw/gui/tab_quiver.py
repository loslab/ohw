import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, 
    QSpinBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ohw import helpfunctions
from ohw.gui import dialog_quiveroptions
import math

class TabQuiver(QWidget):
    """
        display + save motion as heatmap and quiver plot
    """
    
    def __init__(self, parent, ctrl):
        super(TabQuiver, self).__init__(parent)
        self.update = True # update flag, set when motion calculation changed
        self.parent=parent
        self.ctrl = ctrl
        self.initUI()
        self.init_ohw()        

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
        
    def initUI(self):

        # self.info = QTextEdit()
        # self.info.setText('In this tab, motion is vizualized by heatmaps and quiverplots. Use the slider to look at different frames. You can save individual frames or the whole video.')
        # self.info.setReadOnly(True)
        # self.info.setMaximumHeight(50)
        # self.info.setFixedWidth(700)
        # self.info.setStyleSheet("background-color: LightSkyBlue")
 
        # TODO: ...introduce dropdown and allow selection of postprocessing evaluation?

        # create box-widgets
        self.box_quiver = BoxQuiver(self, self.ctrl)
        self.box_heatmap = BoxHeatmap(self, self.ctrl)

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        layout.addWidget(self.box_heatmap,0,0)
        layout.addWidget(self.box_quiver,0,1)
        
        layout.setColumnStretch(2,1)
        self.setLayout(layout)   
        
    def init_ohw(self):
        """
            set values from cohw
            enable sliders/ plot if corresponding data is present
        """

        if self.update == True:
                   
            self.box_heatmap.init_ohw()
            self.box_quiver.init_ohw()
            
            self.update = False
           
class BoxHeatmap(QGroupBox):    
    """
        QGroupBox providing:
        - display of Heatmaps controlled by slider
        - buttons to save video or individual frame
    """
    def __init__(self, parent, ctrl, boxtitle = "Heatmaps"):
        super(BoxHeatmap, self).__init__(boxtitle, parent = parent) # take care of correct superclass init, order of args
        #or self.setTitle(boxtitle)
        self.parent=parent
        self.ctrl = ctrl #introduce controller object
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
      
        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title
        
        self.grid = QGridLayout()
        
        self.fig_heatmaps, self.ax_heatmaps = plt.subplots(1,1, figsize = (16,12))
        self.fig_heatmaps.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.canvas_heatmaps = FigureCanvas(self.fig_heatmaps)
        self.canvas_heatmaps.setFixedSize(500,500)
        
        self.label_heatmap_idx = QLabel("Frame: ")
        self.label_heatmap_time = QLabel("Time: ")
        
        self.slider_heatmaps = QSlider(Qt.Horizontal)
        self.slider_heatmaps.setMinimum(0)
        self.slider_heatmaps.setMaximum(100)
        self.slider_heatmaps.setValue(0)
        # self.slider_heatmaps.setFixedWidth(500)
        self.slider_heatmaps.valueChanged.connect(self.slider_heatmaps_valueChanged)        

        self.btn_heatmap_save = QPushButton('Save this frame')
        self.btn_heatmap_save.clicked.connect(self.on_saveHeatmap)        
        
        self.progressbar_heatmaps = QProgressBar(self)
        self.progressbar_heatmaps.setValue(0)
        # self.progressbar_heatmaps.setFixedWidth(300)

        self.btn_heatmap_vid = QPushButton('Export Heatmap Video')
        self.btn_heatmap_vid.clicked.connect(self.on_saveHeatmapvideo)   
        
        self.grid.addWidget(self.canvas_heatmaps, 0,0,1,2)
        self.grid.addWidget(self.label_heatmap_idx, 1,0)
        self.grid.addWidget(self.label_heatmap_time, 1,1)
        self.grid.addWidget(self.slider_heatmaps, 2,0,1,2)
        self.grid.addWidget(self.btn_heatmap_save, 3,0)
        self.grid.addWidget(self.btn_heatmap_vid, 4,0)
        self.grid.addWidget(self.progressbar_heatmaps, 4,1)
        
        self.grid.setColumnStretch(1,1)
        self.setLayout(self.grid)
        
    def init_ohw(self):
        self.ceval = self.cohw.ceval
        self.clear_heatmaps()

        if self.cohw.analysis_meta["calc_finish"]:
            self.btn_heatmap_vid.setEnabled(True)
            self.btn_heatmap_save.setEnabled(True)
            self.slider_heatmaps.setMaximum(self.ceval.absMotions.shape[0]-1)
            self.slider_heatmaps.setValue(0)
            self.slider_heatmaps.setEnabled(True)
            self.init_heatmaps()
        else:
            self.btn_heatmap_vid.setEnabled(False)
            self.btn_heatmap_save.setEnabled(False)
            self.slider_heatmaps.setEnabled(False)
            self.placeholder_heatmaps()

    def clear_heatmaps(self):
        self.ax_heatmaps.clear()
        self.ax_heatmaps.axis('off')
        self.canvas_heatmaps.draw()
        
    def placeholder_heatmaps(self):
        self.ax_heatmaps.text(0.5, 0.5,'no motion calculated/ loaded',
        size=16, ha='center', va='center', backgroundcolor='indianred', color='w')
        self.canvas_heatmaps.draw()

    def init_heatmaps(self):
            
        scale_max = helpfunctions.get_scale_maxMotion2(self.ceval.absMotions) # decide on which scale to use
        self.imshow_heatmaps = self.ax_heatmaps.imshow(self.ceval.absMotions[0], 
            vmin = 0, vmax = scale_max, cmap = 'jet', interpolation = 'bilinear')

        self.canvas_heatmaps.draw()
        """
        # don't add title in gui yet/ adjust size...
        cbar_heatmaps = self.fig_heatmaps.colorbar(self.imshow_heatmaps)
        cbar_heatmaps.ax.tick_params(labelsize=20)
        for l in cbar_heatmaps.ax.yaxis.get_ticklabels():
            l.set_weight("bold")
        self.ax_heatmaps.set_title('Motion [µm/s]', fontsize = 16, fontweight = 'bold')            
        """        
        
    def slider_heatmaps_valueChanged(self):
        frame = self.slider_heatmaps.value()
        time = round(frame / self.cohw.videometa["fps"], 3) # round to ms digit accuracy
        self.update_Heatmap(frame)
        self.label_heatmap_idx.setText('Frame: ' + str(frame) )
        self.label_heatmap_time.setText('Time: ' + str(time) + ' s')
        
    def update_Heatmap(self, frame):
        #callback when slider is moved
        self.imshow_heatmaps.set_data(self.ceval.absMotions[frame])
        self.canvas_heatmaps.draw()

    def on_saveHeatmapvideo(self):
        """
            saves the heatmpavideo
        """
        self.progressbar_heatmaps.setValue(0)
        
        save_heatmap_thread = self.cohw.save_heatmap_thread(singleframe = False)
        save_heatmap_thread.start()
        self.progressbar_heatmaps.setRange(0,0)
        save_heatmap_thread.finished.connect(self.finish_saveHeatmapvideo)
    
    def finish_saveHeatmapvideo(self):
        self.progressbar_heatmaps.setRange(0,1)
        self.progressbar_heatmaps.setValue(1)
        helpfunctions.msgbox(self, 'Heatmap video was saved successfully')         
    
    def on_saveHeatmap(self):
        """
            saves the selected frame (singleframe = framenumber)
        """
        singleframe=self.slider_heatmaps.value()
        self.cohw.save_heatmap(singleframe = singleframe)
        helpfunctions.msgbox(self, 'Heatmap of frame ' + str(singleframe) + ' was saved successfully')        
        
        
class BoxQuiver(QGroupBox):    
    """
        QGroupBox providing:
        - display of Quivers controlled by slider
        - buttons to save video or individual frame
    """
    def __init__(self, parent, ctrl, boxtitle = "Quivers"):
        super(BoxQuiver, self).__init__(boxtitle, parent = parent) # take care of correct superclass init, order of args
        self.parent=parent
        self.ctrl = ctrl #introduce controller object
        self.initUI()

    @property
    def cohw(self):
        return self.ctrl.cohw #simplify calls to cohw
    
    def initUI(self):
      
        self.setStyleSheet("QGroupBox { font-weight: bold; } ") # bold title
        
        self.grid = QGridLayout()
        
        self.fig_quivers, self.ax_quivers = plt.subplots(1,1, figsize = (16,12))
        self.fig_quivers.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.canvas_quivers = FigureCanvas(self.fig_quivers)
        self.canvas_quivers.setFixedSize(500,500)
        
        self.label_quiver_idx = QLabel("Frame: ")
        self.label_quiver_time = QLabel("Time: ")
        
        self.btn_quiver_save = QPushButton('Save this frame')
        self.btn_quiver_save.clicked.connect(self.on_saveQuiver)            

        self.btn_quiver_sett = QPushButton('Export settings')
        self.btn_quiver_sett.clicked.connect(self.on_quiversett)

        self.btn_quivers_video = QPushButton('Export quiver video')
        self.btn_quivers_video.clicked.connect(self.on_saveQuivervideo)
       
        #progressbar for quivers
        self.progressbar_quivers = QProgressBar(self)
        self.progressbar_quivers.setValue(0)
        #self.progressbar_quivers.setFixedWidth(300)
        
        self.slider_quiver = QSlider(Qt.Horizontal)
        self.slider_quiver.setMinimum(0)
        self.slider_quiver.setMaximum(100)
        self.slider_quiver.setValue(0)
        # self.slider_quiver.setFixedWidth(500)
        self.slider_quiver.valueChanged.connect(self.slider_quiver_valueChanged)
                
        self.grid.addWidget(self.canvas_quivers, 0,0,1,3)
        self.grid.addWidget(self.label_quiver_idx, 1,0)
        self.grid.addWidget(self.label_quiver_time, 1,1)
        self.grid.addWidget(self.slider_quiver, 2,0,1,3)
        self.grid.addWidget(self.btn_quiver_save, 3,0)
        self.grid.addWidget(self.btn_quiver_sett, 3,1)
        self.grid.addWidget(self.btn_quivers_video, 4,0)
        self.grid.addWidget(self.progressbar_quivers, 4,1,1,3)
        
        self.grid.setColumnStretch(2,1)
        self.setLayout(self.grid)
        
    def init_ohw(self):
        self.ceval = self.cohw.ceval
        self.clear_quivers()        
        
        if self.cohw.analysis_meta["has_MVs"] and self.cohw.video_loaded: # todo: refactor!
            self.btn_quiver_save.setEnabled(True)
            self.btn_quivers_video.setEnabled(True)
            self.btn_quiver_sett.setEnabled(True)
            
            fend = math.floor(self.ctrl.config['QUIVER OPTIONS'].getfloat('video_length')*self.cohw.videometa["fps"])
            self.quiveroptions = {"view":"triple","startframe":0,"endframe":fend}# rudimentary test... todo:refactor
            # todo: truncate if too long
            
            
            self.slider_quiver.setMaximum(self.ceval.mean_absMotions.shape[0]-1)# or introduce new variable which counts the amount of motion timepoints
            self.slider_quiver.setValue(0)
            self.slider_quiver.setEnabled(True)
            self.init_quivers()
        else:
            self.btn_quiver_save.setEnabled(False)
            self.btn_quivers_video.setEnabled(False)
            self.slider_quiver.setEnabled(False)
            self.btn_quiver_sett.setEnabled(False)
            self.placeholder_quivers()
            
    def clear_quivers(self):
        self.ax_quivers.clear()
        self.ax_quivers.axis('off')
        self.canvas_quivers.draw()

    def placeholder_quivers(self):
        self.ax_quivers.text(0.5, 0.5,'no motion + video calculated/ loaded',
        size=16, ha='center', va='center', backgroundcolor='indianred', color='w')
        self.canvas_quivers.draw()        
        
    def init_quivers(self):

        blockwidth = self.cohw.analysis_meta["motion_parameters"]["blockwidth"]
        microns_per_px = self.cohw.videometa["microns_per_px"]
        scalingfactor = self.cohw.analysis_meta["scalingfactor"]
        scale_max = helpfunctions.get_scale_maxMotion2(self.ceval.absMotions)
        
        skipquivers =  int(self.ctrl.config["QUIVER OPTIONS"]['quiver_density']) # store in ohw object!
        distance_between_arrows = blockwidth * skipquivers
        arrowscale = 1 / (distance_between_arrows / scale_max)
        
        #self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.cohw.scaledImageStack.shape[2]-blockwidth/2, blockwidth)+1, np.arange(blockwidth/2, self.cohw.scaledImageStack.shape[1]-blockwidth/2+1, blockwidth))  #changed arange range, double check!
        
        self.qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers)) #slice determining which MVs are shown as quivers
        qslice = self.qslice

        # work in progress here
        
        """
        def plot_analysis_img(self):
            analysis_roi = self.cohw.analysis_meta["roi"]
            if analysis_roi != None:
                scaled_roi = [int(coord*self.cohw.videometa["prev_scale"]) for coord in analysis_roi]
                self.analysis_img = self.cohw.videometa["prev800px"][scaled_roi[1]:scaled_roi[1]+scaled_roi[3],
                                                                scaled_roi[0]:scaled_roi[0]+scaled_roi[2]]
            else:
                self.analysis_img = self.cohw.videometa["prev800px"]
            self.box_postprocess.ax.imshow(self.analysis_img, cmap = 'gray')
        """

        subroi = self.cohw.ceval.roi
        
        if subroi is None:
            self.subroi_slicex = slice(0,-1) # select all if no roi selected
            self.subroi_slicey = slice(0,-1)
        else:
            self.subroi_slicex = slice(subroi[0],subroi[0]+subroi[2])
            self.subroi_slicey = slice(subroi[1],subroi[1]+subroi[3])
        
        # show current frame, self.cohw.analysisImageStack[0] is already cropped to analysis roi
        # further adjust to ceval roi with slice
        self.imshow_quivers = self.ax_quivers.imshow(
                self.cohw.analysisImageStack[0,self.subroi_slicey,self.subroi_slicex], cmap = "gray",
                vmin = self.cohw.videometa["Blackval"], vmax = self.cohw.videometa["Whiteval"])
        
        # show quivers, quiver components are already cropped to ceval roi, as
        # ceval.process() selects subset in prepare_quiver_components()
        self.quiver_quivers = self.ax_quivers.quiver(
                self.ceval.MotionCoordinatesX[qslice], 
                self.ceval.MotionCoordinatesY[qslice], 
                self.ceval.QuiverMotionX[0][qslice], 
                self.ceval.QuiverMotionY[0][qslice], 
                pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", 
                scale = arrowscale, width = 3, headwidth = 2, headlength = 3) #adjust scale to max. movement   #width = blockwidth / 4?

        self.canvas_quivers.draw()        
        
    def slider_quiver_valueChanged(self): 
        frame = self.slider_quiver.value()
        time = round(frame / self.cohw.videometa["fps"], 3)
        self.updateQuiver(frame)
        self.label_quiver_idx.setText('Frame: ' + str(frame) )
        self.label_quiver_time.setText('Time: ' + str(time) + ' s')
        
    def updateQuiver(self, frame):
        #callback when slider is moved
        self.imshow_quivers.set_data(self.cohw.analysisImageStack[frame,self.subroi_slicey, self.subroi_slicex])    #introduce a displayImageStack here?
        self.quiver_quivers.set_UVC(self.ceval.QuiverMotionX[frame][self.qslice], self.ceval.QuiverMotionY[frame][self.qslice])
        self.canvas_quivers.draw()

    def on_saveQuivervideo(self):
        """
            saves the quivervideo
        """
        
        """
        if self.quiver_settings['one_view']:
            #export one view quivers
            save_quiver1_thread = self.cohw.save_quiver_thread(singleframe = False, skipquivers = int(self.quiver_settings['quiver_density']), t_cut=float(self.quiver_settings['video_length']))
            save_quiver1_thread.start()
            self.progressbar_quivers.setRange(0,0)
            save_quiver1_thread.finished.connect(self.finish_saveQuivervideo)
                          
        if self.quiver_settings['three_views']:
            #export three views quivers
            save_quiver3_thread = self.cohw.save_quivervid3_thread(skipquivers = int(self.quiver_settings['quiver_density']), t_cut=float(self.quiver_settings['video_length']))
            save_quiver3_thread.start()
            self.progressbar_quivers.setRange(0,0)
            save_quiver3_thread.finished.connect(self.finish_saveQuivervideo)
        """
        
        save_quiver_thread = self.cohw.save_quiver3_thread(singleframe = False, skipquivers = 4) # todo: reconnect to settings, hardcoded density here!
        save_quiver_thread.start()
        self.progressbar_quivers.setRange(0,0)
        save_quiver_thread.finished.connect(self.finish_saveQuivervideo)        
        
    def finish_saveQuivervideo(self):
        self.progressbar_quivers.setRange(0,1)
        self.progressbar_quivers.setValue(1)
        
        helpfunctions.msgbox(self, 'Quiver was saved successfully')
        
    def on_saveQuiver(self):   
        singleframe = int(self.slider_quiver.value())
        """
        #save the different views if chosen by the user
        if self.quiver_settings['one_view']:

            self.cohw.save_quiver(singleframe = singleframe, skipquivers = int(self.quiver_settings['quiver_density']))
        
        if self.quiver_settings['three_views']:
            self.cohw.save_quivervid3(singleframe = singleframe, skipquivers = int(self.quiver_settings['quiver_density']))
        """
        self.cohw.save_quiver3(singleframe = singleframe)
        helpfunctions.msgbox(self, 'Quiver of frame ' + str(singleframe) + ' was saved successfully')
    
    def on_quiversett(self):
        self.dialog_quiveroptions = dialog_quiveroptions.DialogQuiveroptions(self.ctrl, settings = self.quiveroptions) #
        #plotsettings = self.cohw.kinplot_options) # where to store? in cohw or local in tab?
        self.dialog_quiveroptions.exec_()
        #self.kinplot_options.update(self.dialog_kinoptions.get_settings())
        
        # self.cohw.update_kinplot_options(self.dialog_kinoptions.get_settings())

    def updateQuiverBrightness(self,vmin,vmax): # todo: check if this is used correctly
        self.imshow_quivers.set_clim(vmin=vmin, vmax=vmax)
        self.canvas_quivers.draw()        