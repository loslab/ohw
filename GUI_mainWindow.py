# -*- coding: utf-8 -*-

import sys
from libraries.Main_Setup import TableWidget
#from classes.MyHorizontalTabWidget import HorizontalTabWidget
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget 
from PyQt5.QtGui import QIcon
import PyQt5.QtCore as Core

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        
        #initial settings
        self.title = 'OpenHeartWare (OHW) - Software for optical determination of Cardiomyocyte contractility'
        self.resize(1150,800)
        self.center()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('icons/ohw-icon.PNG'))
        
        #create a TableWidget to use different tabs in the GUI       
        self.table_widget = TableWidget(self)
        self.setCentralWidget(self.table_widget)
        self.show()
    
    def center(self):
        # method for centering the app on the screen
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def keyPressEvent(self, e):
        ''' close window when escape pressed '''
        if e.key() == Core.Qt.Key_Escape:
            self.close()
            sys.exit(app.exec_())
            
    def adjustSize(self):
        #used for resizing the whole GUI after saving of the plot 
        self.resize(self.width()+1, self.height()+1)
        
    def closeEvent(self, event):
        self.table_widget.close_Window()    
    
if __name__ == '__main__':
    
    #suppress warnings for the user
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter("ignore")
    
    #enable the following code when testing instead of line 57:
       # warnings.simplefilter("default") # Change the filter in this process
        #os.environ["PYTHONWARNINGS"] = "default" # Also affect subprocesses
   
    #start the application
    app = QApplication(sys.argv)
    app.setAttribute(Core.Qt.AA_DisableHighDpiScaling)
    app.aboutToQuit.connect(app.deleteLater)
    heartware_gui = App()    
    app.exec_()