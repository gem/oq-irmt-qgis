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
        self.data = []
        for vset in vsets:
            self.data.append([vset['vulnerabilitySetID'],
                              vset['assetCategory'],
                              vset['lossCategory'],
                              vset.IML['IMT'],
                              ])

        self.vSetsTbl.setRowCount(len(self.data))

        for row_index, row in enumerate(self.data):
            for col_index, content in enumerate(row):
                item = QtGui.QTableWidgetItem(str(content))
                self.vSetsTbl.setItem(row_index, col_index, item)

        self.vSetsTbl.setSortingEnabled(True)


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
