# -*- coding: utf-8 -*-

#chooseMultipleFolders
from PyQt5.QtWidgets import QFileDialog, QTreeView, QListView, QFileSystemModel, QAbstractItemView, QApplication
import pathlib

class MultipleFoldersDialog(QFileDialog):
    def __init__(self, *args):
        current_path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
        current_message = 'Add folders for automated analysis'
        
        QFileDialog.__init__(self, caption=current_message, directory=current_path)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        for view in self.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), QFileSystemModel):
                view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.selection = self.selectedFiles()
        
        if (self.exec_()):
            self.selection = self.selectedFiles()     

    def getSelection(self):
        return self.selection

#def chooseMultipleFoldersByUser(message, input_folder=''):
#     path = str((pathlib.Path(__file__) / ".." / "..").resolve())    
#     dialog = MultipleFoldersDialog(None, message, path)
#     dialog.exec()
#     if (dialog.exec_()):
#         print(dialog.selectedFiles())     
#         return dialog.selectedFiles()
#     else:
#         return None

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)    
    path = str((pathlib.Path(__file__) / ".." / "..").resolve()) 
    message = 'Select multiple folders'
    ex = MultipleFoldersDialog(None, message, path)
   # ex.exec()
    print(ex.getSelection())
  #  multiple_folders = chooseMultipleFoldersByUser(message)
#    print(ex.selectedFiles())
    sys.exit(app.exec_())