import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QWidget, QGridLayout,QPushButton, QApplication)
from PyQt5 import QtCore

from PyQt5.QtWidgets import (QLabel, QLineEdit, QGridLayout, QComboBox,
    QTextEdit,QSizePolicy, QPushButton, QProgressBar,QSlider, QWidget, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from libraries import helpfunctions

class TabQuiver(QWidget):
    """
        display + save motion as heatmap and quiver plot
    """
    
    def __init__(self, parent):
        super(TabQuiver, self).__init__(parent)
        self.initUI()
        self.parent=parent
        
    def initUI(self):
        # define + place gui elements
        self.info = QTextEdit()
        self.info.setText('In this tab, motion is vizualized by heatmaps and quiverplots. Use the slider to look at different frames. You can save individual frames or the whole video.')
        self.info.setReadOnly(True)
        self.info.setMaximumHeight(50)
        self.info.setFixedWidth(700)
        self.info.setStyleSheet("background-color: LightSkyBlue")
 
        """
        #create a label for choosing the ROI
        label_advanced_choose_ROI = QLabel('Choose the ROI to be displayed: ')
        label_advanced_choose_ROI.setFont(QFont("Times",weight=QFont.Bold))
        
        #create a drop-down menu for choosing the ROI to be displayed
        self.advanced_combobox = QComboBox()
        self.advanced_combobox.addItem('Full image')    
        #self.advanced_combobox.activated[str].connect(self.on_chooseROI)
        self.advanced_combobox.currentIndexChanged[int].connect(self.on_chooseROI)
        """
        
        self.label_heatmaps = QLabel('Heatmaps')
        self.label_heatmaps.setFont(QFont("Times",weight=QFont.Bold))
        
        self.label_quivers = QLabel('Quivers')
        self.label_quivers.setFont(QFont("Times",weight=QFont.Bold))

        self.btn_heatmap_vid = QPushButton('Export Heatmap Video')
        self.btn_heatmap_vid.clicked.connect(self.on_saveHeatmapvideo)            
                      
        #slider to switch between heatmaps
        self.slider_heatmaps = QSlider(Qt.Horizontal)
        self.slider_heatmaps.setMinimum(0)
        self.slider_heatmaps.setMaximum(100)
        self.slider_heatmaps.setValue(0)
        #self.slider_heatmaps.setTickPosition(QSlider.TicksBelow)
        #self.slider_heatmaps.setTickInterval(5)
        self.slider_heatmaps.setFixedWidth(500)
        self.slider_heatmaps.valueChanged.connect(self.slider_heatmaps_valueChanged)
        
        self.btn_heatmap_save = QPushButton('Save this frame')
        self.btn_heatmap_save.clicked.connect(self.on_saveHeatmap)      
        
        self.btn_quiver_save = QPushButton('Save this frame')
        self.btn_quiver_save.clicked.connect(self.on_saveQuiver)            
        
        self.slider_quiver = QSlider(Qt.Horizontal)
        self.slider_quiver.setMinimum(0)
        self.slider_quiver.setMaximum(100)
        self.slider_quiver.setValue(0)
        self.slider_quiver.setFixedWidth(500)
        #self.slider_quiver.setTickPosition(QSlider.TicksBelow)
        self.slider_quiver.valueChanged.connect(self.slider_quiver_valueChanged)
        #self.slider_quiver.setTickPosition(QSlider.TicksBelow)
        self.slider_quiver.setTickInterval(5)
        
        #display the chosen heatmap
        self.label_heatmap_result = QLabel('Heatmap result:')
        
        self.fig_heatmaps, self.ax_heatmaps = plt.subplots(1,1, figsize = (16,12))
        self.fig_heatmaps.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.canvas_heatmaps = FigureCanvas(self.fig_heatmaps)
        
        #button for changing the quiver export settings
        self.btn_quiver_settings = QPushButton('Change quiver export settings')
        #self.btn_quiver_settings.clicked.connect(self.on_change_quiverSettings)
        
        #Button for starting the creation of quiver plots and quiver video
        self.btn_quivers_video = QPushButton('Export quiver video')
        self.btn_quivers_video.clicked.connect(self.on_saveQuivervideo)

        #display the chosen quiver plot
        self.label_quiver_result = QLabel('Quiver result: ')
 
        # display figures for quivers in Canvas
        self.fig_quivers, self.ax_quivers = plt.subplots(1,1, figsize = (16,12))
        self.fig_quivers.subplots_adjust(bottom=0, top=1, left=0, right=1)
        self.canvas_quivers = FigureCanvas(self.fig_quivers)

        self.canvas_heatmaps.setFixedSize(500,500)
        self.canvas_quivers.setFixedSize(500,500)
        
        """
        #succed-button
        self.button_succeed_heatmaps = QPushButton('Heatmap-video creation was successful')
        self.button_succeed_heatmaps.setStyleSheet("background-color: IndianRed")
        self.button_succeed_quivers = QPushButton('Quiver-video creation was successful')
        self.button_succeed_quivers.setStyleSheet("background-color: IndianRed")
        """

        #progressbar for heatmaps
        self.progressbar_heatmaps = QProgressBar(self)
        self.progressbar_heatmaps.setValue(0)
        self.progressbar_heatmaps.setFixedWidth(300)
        
        #progressbar for quivers
        self.progressbar_quivers = QProgressBar(self)
        self.progressbar_quivers.setValue(0)
        self.progressbar_quivers.setFixedWidth(300)
        
        #define layout
        colHeatmap = 0
        colQuiver = 2
        
        self.grid_overall = QGridLayout()
        
        self.grid_overall.addWidget(self.info, 0,0,1,4)        
        self.grid_overall.addWidget(self.label_heatmaps,            1,  colHeatmap,1,2)
        self.grid_overall.addWidget(self.label_quivers,             1,  colQuiver,1,2)
        self.grid_overall.addWidget(self.canvas_heatmaps,           2,  colHeatmap,1,2)
        self.grid_overall.addWidget(self.canvas_quivers,            2,  colQuiver,1,2)      
        self.grid_overall.addWidget(self.label_heatmap_result,      3,  colHeatmap,1,2)
        self.grid_overall.addWidget(self.label_quiver_result,       3,  colQuiver,1,2)
        self.grid_overall.addWidget(self.slider_heatmaps,           4, colHeatmap,1,2)
        self.grid_overall.addWidget(self.slider_quiver,             4, colQuiver,1,2)
        
        self.grid_overall.addWidget(self.btn_heatmap_vid,           5,  colHeatmap)
        self.grid_overall.addWidget(self.btn_quivers_video,         5,  colQuiver)

        self.grid_overall.addWidget(self.progressbar_heatmaps,      5,  colHeatmap+1)
        self.grid_overall.addWidget(self.progressbar_quivers,       5,  colQuiver+1)     

        #self.grid_overall.addWidget(self.btn_quiver_settings, 2, colQuiver)

        self.grid_overall.addWidget(self.btn_heatmap_save,          6,  colHeatmap)
        self.grid_overall.addWidget(self.btn_quiver_save,           6,  colQuiver)

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
        for progbar in self.findChildren(QProgressBar):
            progbar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #for btn in self.findChildren(QPushButton):
        #    btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
    def init_ohw(self):
        """
            set values from current_ohw
            enable sliders/ plot if corresponding data is present
        """
        self.current_ohw = self.parent.current_ohw  #check if this works... looks good
        self.clear_heatmaps()
        self.clear_quivers()        
        
        # init heatmap part
        if self.parent.current_ohw.analysis_meta["motion_calculated"]:
            self.btn_heatmap_vid.setEnabled(True)
            self.btn_heatmap_save.setEnabled(True)
            self.slider_heatmaps.setMaximum(self.current_ohw.absMotions.shape[0]-1)
            self.slider_heatmaps.setValue(0)
            self.slider_heatmaps.setEnabled(True)
            self.init_heatmaps()
        else:
            self.btn_heatmap_vid.setEnabled(False)
            self.btn_heatmap_save.setEnabled(False)
            self.slider_heatmaps.setEnabled(False)
            self.placeholder_heatmaps()
        
        # init quiver part
        if self.parent.current_ohw.analysis_meta["has_MVs"] and self.parent.current_ohw.video_loaded:       
            self.btn_quiver_save.setEnabled(True)
            self.btn_quivers_video.setEnabled(True)
            self.slider_quiver.setMaximum(self.current_ohw.mean_absMotions.shape[0]-1)# or introduce new variable which counts the amount of motion timepoints
            self.slider_quiver.setValue(0)
            self.slider_quiver.setEnabled(True)
            self.init_quivers()
        else:
            self.btn_quiver_save.setEnabled(False)
            self.btn_quivers_video.setEnabled(False)
            self.slider_quiver.setEnabled(False)
            self.placeholder_quivers()
    
    def init_heatmaps(self):
            
        scale_max = helpfunctions.get_scale_maxMotion2(self.current_ohw.absMotions) #decide on which scale to use
        self.imshow_heatmaps = self.ax_heatmaps.imshow(self.current_ohw.absMotions[0], 
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
    
    def clear_heatmaps(self):
        self.ax_heatmaps.clear()
        self.ax_heatmaps.axis('off')
        self.canvas_heatmaps.draw()
    
    def placeholder_heatmaps(self):
        self.ax_heatmaps.text(0.5, 0.5,'no motion calculated/ loaded',
        size=16, ha='center', va='center', backgroundcolor='indianred', color='w')
        self.canvas_heatmaps.draw()
    
    def init_quivers(self):

        blockwidth = self.current_ohw.analysis_meta["MV_parameters"]["blockwidth"]
        microns_per_px = self.current_ohw.videometa["microns_per_px"]
        scalingfactor = self.current_ohw.analysis_meta["scalingfactor"]
        scale_max = helpfunctions.get_scale_maxMotion2(self.current_ohw.absMotions)
        
        skipquivers =  int(self.parent.config["DEFAULT QUIVER SETTINGS"]['quiver_density']) # store in ohw object!
        distance_between_arrows = blockwidth * skipquivers
        arrowscale = 1 / (distance_between_arrows / scale_max)
        
        #self.MotionCoordinatesX, self.MotionCoordinatesY = np.meshgrid(np.arange(blockwidth/2, self.current_ohw.scaledImageStack.shape[2]-blockwidth/2, blockwidth)+1, np.arange(blockwidth/2, self.current_ohw.scaledImageStack.shape[1]-blockwidth/2+1, blockwidth))  #changed arange range, double check!
        
        self.qslice=(slice(None,None,skipquivers),slice(None,None,skipquivers))
        qslice = self.qslice

        self.imshow_quivers = self.ax_quivers.imshow(
                self.current_ohw.analysisImageStack[0], cmap = "gray", 
                vmin = self.current_ohw.videometa["Blackval"], vmax = self.current_ohw.videometa["Whiteval"])
        self.quiver_quivers = self.ax_quivers.quiver(
                self.current_ohw.MotionCoordinatesX[qslice], 
                self.current_ohw.MotionCoordinatesY[qslice], 
                self.current_ohw.QuiverMotionX[0][qslice], 
                self.current_ohw.QuiverMotionY[0][qslice], 
                pivot='mid', color='r', units ="xy", scale_units = "xy", angles = "xy", 
                scale = arrowscale, width = 3, headwidth = 2, headlength = 3) #adjust scale to max. movement   #width = blockwidth / 4?

        self.canvas_quivers.draw()
    
    def clear_quivers(self):
        self.ax_quivers.clear()
        self.ax_quivers.axis('off')
        self.canvas_quivers.draw()
        
    def placeholder_quivers(self):
        self.ax_quivers.text(0.5, 0.5,'no motion + video calculated/ loaded',
        size=16, ha='center', va='center', backgroundcolor='indianred', color='w')
        self.canvas_quivers.draw()
        
    def slider_quiver_valueChanged(self): 
        frame = self.slider_quiver.value()
        time = round(frame / self.current_ohw.videometa["fps"], 3)
        self.updateQuiver(frame)
        self.label_quiver_result.setText('Quiverplot of frame ' + str(frame) + ' at t = ' + str(time) + ' s')

    def slider_heatmaps_valueChanged(self):
        frame = self.slider_heatmaps.value()
        time = round(frame / self.current_ohw.videometa["fps"], 3)
        self.updateHeatMap(frame)
        self.label_heatmap_result.setText('Heatmap of frame ' + str(frame) + ' at t = ' + str(time) + ' s')

    def updateQuiver(self, frame):
        #callback when slider is moved
        self.imshow_quivers.set_data(self.current_ohw.analysisImageStack[frame])    #introduce a displayImageStack here?
        self.quiver_quivers.set_UVC(self.current_ohw.QuiverMotionX[frame][self.qslice], self.current_ohw.QuiverMotionY[frame][self.qslice])
        self.canvas_quivers.draw()
        
    def updateHeatMap(self, frame):
        #callback when slider is moved
        self.imshow_heatmaps.set_data(self.current_ohw.absMotions[frame])
        self.canvas_heatmaps.draw()
    
    def updateQuiverBrightness(self,vmin,vmax):
        self.imshow_quivers.set_clim(vmin=vmin, vmax=vmax)
        self.canvas_quivers.draw()

    def on_saveQuivervideo(self):
        """
            saves the quivervideo
        """
        #reset the color of success-button
        #self.button_succeed_quivers.setStyleSheet("background-color: IndianRed")
        #self.progressbar_quivers.setValue(0)
        
        """
        if self.quiver_settings['one_view']:
            #export one view quivers
            save_quiver1_thread = self.current_ohw.save_quiver_thread(singleframe = False, skipquivers = int(self.quiver_settings['quiver_density']), t_cut=float(self.quiver_settings['video_length']))
            save_quiver1_thread.start()
            self.progressbar_quivers.setRange(0,0)
            save_quiver1_thread.finished.connect(self.finish_saveQuivervideo)
                          
        if self.quiver_settings['three_views']:
            #export three views quivers
            save_quiver3_thread = self.current_ohw.save_quivervid3_thread(skipquivers = int(self.quiver_settings['quiver_density']), t_cut=float(self.quiver_settings['video_length']))
            save_quiver3_thread.start()
            self.progressbar_quivers.setRange(0,0)
            save_quiver3_thread.finished.connect(self.finish_saveQuivervideo)
        """
        
        save_quiver_thread = self.current_ohw.save_quiver3_thread(singleframe = False, skipquivers = 4)
        save_quiver_thread.start()
        self.progressbar_quivers.setRange(0,0)
        save_quiver_thread.finished.connect(self.finish_saveQuivervideo)

    def finish_saveQuivervideo(self):
        self.progressbar_quivers.setRange(0,1)
        self.progressbar_quivers.setValue(1)
        
        helpfunctions.msgbox(self, 'Quiver was saved successfully')
        #self.button_succeed_quivers.setStyleSheet("background-color: YellowGreen")
        
    def on_saveQuiver(self):   
        singleframe = int(self.slider_quiver.value())
        """
        #save the different views if chosen by the user
        if self.quiver_settings['one_view']:

            self.current_ohw.save_quiver(singleframe = singleframe, skipquivers = int(self.quiver_settings['quiver_density']))
        
        if self.quiver_settings['three_views']:
            self.current_ohw.save_quivervid3(singleframe = singleframe, skipquivers = int(self.quiver_settings['quiver_density']))
        """
        self.current_ohw.save_quiver3(singleframe = singleframe)
        helpfunctions.msgbox(self, 'Quiver of frame ' + str(singleframe) + ' was saved successfully')

    def on_saveHeatmapvideo(self):
        """
            saves the heatmpavideo
        """
        self.progressbar_heatmaps.setValue(0)
        
        save_heatmap_thread = self.current_ohw.save_heatmap_thread(singleframe = False)
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
        self.current_ohw.save_heatmap(singleframe = singleframe)
        helpfunctions.msgbox(self, 'Heatmap of frame ' + str(singleframe) + ' was saved successfully')        