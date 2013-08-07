import os
import sys
import nodes
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow


class MainWindow(Ui_InputToolWindow, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.vSetsTbl.resizeColumnsToContents()
        
        self.data = [{'a':1, 'b':2, 'c':3, 'd':4},
                     {'a':10, 'b':20, 'c':30, 'd':40}
        ]
        self.vSetsTbl.setRowCount(len(self.data))
        
        for row_index, row in enumerate(self.data):
          column_index = 0
          for column, content in row.iteritems():
              print content
              item = QtGui.QTableWidgetItem(str(content))
              self.vSetsTbl.setItem(row_index, column_index, item)
              column_index += 1
              
        self.vSetsTbl.setSortingEnabled(True)
        
        for vset in vsets:
            print vset


# Main entry to program.  Set up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv, True)

    # create main window
    wnd = MainWindow()
    wnd.show()

    # Start the app up
    retval = app.exec_()
    sys.exit(retval)

from openquake import nrmllib
SCHEMADIR = os.path.join(nrmllib.__path__[0], 'schema')
XMLDIR = os.path.join(SCHEMADIR, '../../../examples')
root, modeltype = nodes.parse_nrml(XMLDIR, 'vulnerability-model-discrete.xml')

vsets = list(root)[1:]

if __name__ == '__main__':
    main(sys.argv)
