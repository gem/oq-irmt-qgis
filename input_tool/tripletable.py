import os
import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtCore, QtGui
from customtableview import TripleTableWidget, tr

from openquake.nrmllib.node import node_from_nrml, node_to_nrml
from openquake.nrmllib.record import TableSet


class Dialog(QtGui.QDialog):
    # left for reference, since I (MB) think that the main window of an
    # application is better modelled with a QMainWindow
    def __init__(self, t1, t2, t3):
        QtGui.QDialog.__init__(self)
        self.tt = TripleTableWidget(t1, t2, t3, self)
        self.setWindowTitle(tr("TripleTableWidget Example"))
        # this was the missing call where you set the layout of the tritable
        # widget to the dialog
        self.setLayout(self.tt.layout())


class MainWindow(QtGui.QMainWindow):
    def __init__(self, nrmlfile):
        QtGui.QMainWindow.__init__(self)
        self.nrmlfile = nrmlfile
        node = node_from_nrml(nrmlfile)[0]
        self.tableset = TableSet.from_node(node)
        self.ttw = TripleTableWidget(self.tableset, nrmlfile, self)
        self.setWindowTitle(tr("TripleTableWidget Example"))
        self.setCentralWidget(self.ttw)
        self.setupMenu()

        # menu actions
        self.actionOpen.triggered.connect(self.open_nrml)
        self.actionSave.triggered.connect(self.save_nrml)

    def setupMenu(self):
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1011, 25))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.setMenuBar(self.menubar)
        self.actionOpen = QtGui.QAction(self)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(self)
        self.actionSave.setObjectName("actionSave")
        self.actionCopy = QtGui.QAction(self)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtGui.QAction(self)
        self.actionPaste.setObjectName("actionPaste")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionCopy)
        self.menuFile.addAction(self.actionPaste)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.setTitle(tr("InputToolWindow"))

        # retranslateUi
        self.menuFile.setTitle(tr("File"))
        self.actionOpen.setText(tr("&Open"))
        self.actionOpen.setShortcut(tr("Ctrl+O"))
        self.actionSave.setText(tr("&Save"))
        self.actionSave.setShortcut(tr("Ctrl+S"))
        self.actionCopy.setText(tr("&Copy"))
        self.actionCopy.setShortcut(tr("Ctrl+C"))
        self.actionPaste.setText(tr("&Paste"))
        self.actionPaste.setShortcut(tr("Ctrl+V"))

    def open_nrml(self):
        pass

    def save_nrml(self):
        """
        Save the current content of the tableset in NRML format
        """
        # make a copy of the original file for safety reasons
        os.rename(self.nrmlfile, self.nrmlfile + '~')
        with open(self.nrmlfile, 'w') as f:
            node_to_nrml(self.tableset.to_node(), f)


def main(argv):
    if not argv[1:]:
        sys.exit('Please give the input NRML file')

    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')
    fname = sys.argv[1]
    mw = MainWindow(fname)
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
