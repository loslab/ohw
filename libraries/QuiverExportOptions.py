# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 13:32:50 2019

@author: sailca
"""
import configparser
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QLabel, QGridLayout, QSpinBox, QPushButton, QWidget, QTabWidget, QLineEdit, QCheckBox
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import pyqtSignal

class QuiverExportOptions(QMainWindow):
    def __init__(self, prevSettings = None, videoLength=None, parent=None):
        super(QuiverExportOptions, self).__init__(parent)
      #  super().__init__()
        
        #initial settings
        self.title = 'Settings for Export of Quiver Video'
        self.resize(800,400)
        self.center()
        self.setWindowTitle(self.title)
        
        #create a TableWidget to use different tabs    
        self.table_widget = QuiverExportOptions_TableWidget(self, previousSettings=prevSettings)
        self.setCentralWidget(self.table_widget)

      #  self.show()

    def center(self):
        #method for centering the app on the scren
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
       
class QuiverExportOptions_TableWidget(QWidget):
    #define signals to be emitted
    got_settings = pyqtSignal(dict)
    
    def __init__(self, parent, previousSettings=None):
        super(QWidget, self).__init__(parent)
        self.layout = QGridLayout(self)
 
        # Initialize tab screen
        self.tabs = QTabWidget()
        # Add tabs to widget        
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.tab1 = QWidget()
        
        self.tabs.addTab(self.tab1,"Options")
        
        # default values for export
        if previousSettings is None:
            self.settings = {}
            
        self.settings = previousSettings
#        self.settings['one_view'] = False
#        self.settings['three_views'] = False
#        self.settings['show_scalebar'] = True
#        self.settings['quiver_density'] = 2
#        self.settings['video_length'] = videoLength
        
        self.show()
        
        ######tab1 
        #supported views
        label_settings = QLabel('Settings:')
        label_settings.setFont(QFont("Times",weight=QFont.Bold))
  
        #settings 
        self.check_showScalebar = QCheckBox('Display scalebar')
        self.check_showScalebar.setChecked(self.settings['show_scalebar'])
        self.check_showScalebar.stateChanged.connect(self.change_status)  
           
        label_spinbox_quiverDensity = QLabel('Quiver Density')
        self.spinbox_quiverDensity = QSpinBox()
        self.spinbox_quiverDensity.setRange(2, 10)
        self.spinbox_quiverDensity.setSingleStep(2)
        self.spinbox_quiverDensity.setValue(int(self.settings['quiver_density']))
        self.spinbox_quiverDensity.valueChanged.connect(self.change_status)
        
        label_cutVideo = QLabel('Cut video after ')
        self.spinbox_cutVideo = QSpinBox()
        self.spinbox_cutVideo.setRange(0, float(self.settings['video_length']))
        self.spinbox_cutVideo.setSingleStep(0.01)
        self.spinbox_cutVideo.setSuffix(' seconds')
        self.spinbox_cutVideo.setValue(float(self.settings['video_length']))
        self.spinbox_cutVideo.valueChanged.connect(self.change_status)
        
        #supported views
        label_views = QLabel('Supported View(s):')
        label_views.setFont(QFont("Times",weight=QFont.Bold))
        
        #set icons 
        self.image_quiver1 = QLabel()
        self.image_quiver1.setPixmap(QPixmap('icons/quivervid1.png').scaledToWidth(250))#.scaledToHeight())
        
        self.image_quiver3 = QLabel()
        self.image_quiver3.setPixmap(QPixmap('icons/quivervid3.png').scaledToWidth(250))#.scaledToHeight())
        
        self.check_useOneView = QCheckBox('One View')
        self.check_useOneView.setChecked(self.settings['one_view'])
        self.check_useOneView.stateChanged.connect(self.change_status)
                
        self.check_useThreeViews = QCheckBox('Three Views')
        self.check_useThreeViews.setChecked(self.settings['three_views'])
        self.check_useThreeViews.stateChanged.connect(self.change_status)
        
        self.button_saveSettings = QPushButton('Save Settings')            
        self.button_saveSettings.resize(self.button_saveSettings.sizeHint())
        self.button_saveSettings.clicked.connect(self.on_saveSettings)   

        #place widgets on layout
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(25)
        self.tab1.layout.addWidget(label_settings,               0,  0)
        self.tab1.layout.addWidget(label_spinbox_quiverDensity,  1,  0)
        self.tab1.layout.addWidget(self.spinbox_quiverDensity,   1,  1)
        self.tab1.layout.addWidget(label_cutVideo,               2,  0)
        self.tab1.layout.addWidget(self.spinbox_cutVideo,        2,  1)
        self.tab1.layout.addWidget(self.check_showScalebar,      3,  0)
        self.tab1.layout.addWidget(label_views,                  4,  0)
        self.tab1.layout.addWidget(self.check_useOneView,        5,  0)
        self.tab1.layout.addWidget(self.image_quiver1,           5,  1)
        self.tab1.layout.addWidget(self.check_useThreeViews,     6,  0)
        self.tab1.layout.addWidget(self.image_quiver3,           6,  1)
        self.tab1.layout.addWidget(self.button_saveSettings,     7,  0, 1, 2)
        self.tab1.setLayout(self.tab1.layout)
    
    def change_status(self):
        """
            handle changes of available checkboxes 
        """
        if self.sender() == self.check_useOneView:
            self.settings['one_view'] = self.check_useOneView.isChecked()
        elif self.sender() == self.check_useThreeViews:
            self.settings['three_views'] = self.check_useThreeViews.isChecked()
        elif self.sender() == self.check_showScalebar:
            self.settings['show_scalebar'] = self.check_showScalebar.isChecked()
        elif self.sender() == self.spinbox_quiverDensity:
            self.settings['quiver_density'] = self.spinbox_quiverDensity.value()
        elif self.sender() == self.spinbox_cutVideo:
            self.settings['video_length'] = str(self.spinbox_cutVideo.value())

    def on_saveSettings(self):
        """
            saves the chosen settings and closes the settings window
        """

        self.got_settings.emit(self.settings)
        
        self.close()
     #   self.parent.close()
#        mainWidget = self.findMainWindow()
 #       mainWidget.close()
        
    def findMainWindow(self): #-> typing.Union[QMainWindow, None]:
        # Global function to find the (open) QMainWindow in application
        app = QApplication.instance()
        for widget in app.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                return widget
        return None

    
if __name__ == '__main__':
    #start the application
    app = QApplication(sys.argv) 
    app.aboutToQuit.connect(app.deleteLater)
    newVideoExport = QuiverExportOptions()
    app.exec_()
    newVideoExport.show()
    sys.exit(app.exec_())