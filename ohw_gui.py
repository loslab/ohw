# -*- coding: utf-8 -*-

import sys
from libraries.gui import tabwidget_main
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget 
from PyQt5.QtGui import QIcon
import PyQt5.QtCore as Core

class OHWGUI(QMainWindow):
    """ QMainWindow incorporating TabWidgetMain with different tabs for ohw control"""

    def __init__(self, parent):
        super(OHWGUI, self).__init__(parent)
        
        self.title = 'OpenHeartWare (OHW) - Software for optical determination of Cardiomyocyte contractility'
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('icons/ohw-icon.PNG'))
        
        self.table_widget = tabwidget_main.TabWidgetMain(self)
        self.setCentralWidget(self.table_widget)
        self.show()
        self.resize(1150,800) # TODO: check if this makes sense
        self.center()        
    
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
   
    app = QApplication(sys.argv)
    app.setAttribute(Core.Qt.AA_DisableHighDpiScaling)
    app.aboutToQuit.connect(app.deleteLater)
    ohw_gui = OHWGUI(parent = None)    
    app.exec_()