import os
import sys
import sip
import traceback
sip.setapi("QString", 2)

from PyQt4 import QtCore, QtGui
from customtableview import TripleTableWidget, tr

from openquake.nrmllib.node import node_from_xml, node_to_nrml
from openquake.nrmllib.record import TableSet


class MainWindow(QtGui.QMainWindow):
    def __init__(self, nrmlfile):
        QtGui.QMainWindow.__init__(self)
        self.set_central_widget(nrmlfile)
        self.setWindowTitle(tr("Input Tool Window"))
        self.setupMenu()

        # menu actions
        self.actionNewVM.triggered.connect(self.new_vulnerability_model)
        self.actionOpen.triggered.connect(self.open_nrml)
        self.actionSave.triggered.connect(self.save_nrml)
        self.actionWrite.triggered.connect(self.write_nrml)
        self.actionQuit.triggered.connect(self.quit)
        self.actionCopy.triggered.connect(self.copy)
        self.actionPaste.triggered.connect(self.paste)

    def set_central_widget(self, nrmlfile):
        self.nrmlfile = nrmlfile
        node = node_from_xml(nrmlfile)[0]
        self.tableset = TableSet.from_node(node)
        if len(self.tableset.tables) != 3:
            # only models with three tables are implemented
            raise NotImplementedError(node.tag)
        self.widget = TripleTableWidget(self.tableset, nrmlfile, self)
        self.setCentralWidget(self.widget)

    def setupMenu(self):
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.setMenuBar(self.menubar)
        self.actionNewVM = QtGui.QAction(self)
        self.actionNewVM.setObjectName("actionNewVM")
        self.actionOpen = QtGui.QAction(self)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(self)
        self.actionSave.setObjectName("actionSave")
        self.actionWrite = QtGui.QAction(self)
        self.actionWrite.setObjectName("actionWrite")
        self.actionCopy = QtGui.QAction(self)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtGui.QAction(self)
        self.actionPaste.setObjectName("actionPaste")
        self.actionUndo = QtGui.QAction(self)
        self.actionUndo.setObjectName("actionUndo")
        self.actionQuit = QtGui.QAction(self)
        self.actionQuit.setObjectName("actionQuit")
        self.menuFile.addAction(self.actionNewVM)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionWrite)
        self.menuFile.addAction(self.actionCopy)
        self.menuFile.addAction(self.actionPaste)
        self.menuFile.addAction(self.actionUndo)
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.setTitle(tr("InputToolWindow"))

        # retranslateUi
        self.menuFile.setTitle(tr("File"))
        self.actionNewVM.setText(tr("&NewVM"))
        self.actionNewVM.setShortcut(tr("Ctrl+N"))
        self.actionOpen.setText(tr("&Open"))
        self.actionOpen.setShortcut(tr("Ctrl+O"))
        self.actionSave.setText(tr("&Save"))
        self.actionSave.setShortcut(tr("Ctrl+S"))
        self.actionWrite.setText(tr("&Write"))
        self.actionWrite.setShortcut(tr("Ctrl+W"))
        self.actionCopy.setText(tr("&Copy"))
        self.actionCopy.setShortcut(tr("Ctrl+C"))
        self.actionPaste.setText(tr("&Paste"))
        self.actionPaste.setShortcut(tr("Ctrl+V"))
        self.actionUndo.setText(tr("&Undo"))
        self.actionUndo.setShortcut(tr("Ctrl+U"))
        self.actionQuit.setText(tr("&Quit"))
        self.actionQuit.setShortcut(tr("Ctrl+Q"))

    def copy(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableView):
            return
        currsel = widget.parent().current_selection()
        QtGui.QApplication.clipboard().setText(currsel)

    def paste(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableView):
            return
        widget = widget.parent()  # CustomTableView
        lines = QtGui.QApplication.clipboard().text().split('\n')
        rows = [line.split('\t') for line in lines]
        if not rows:
            return
        ncolumns = len(widget.table.recordtype) - widget.table.ordinal
        for row in rows:
            assert len(row) <= ncolumns, 'Got %d columns, expected %d' % (
                len(row), ncolumns)
        indexes = widget.appendRows(len(rows))
        for index, row in zip(indexes, rows):
            widget.tableModel.set_row(index, row)

    def open_nrml(self):
        nrmlfile = unicode(QtGui.QFileDialog.getOpenFileName(
            self, 'Choose file',
            QtCore.QDir.homePath(),
            "Model file (*.xml);;Config files (*.ini)"))
        self.set_central_widget(nrmlfile)

    def new_vulnerability_model(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <vulnerabilityModel/>
        </nrml>'''
        open('vulnerability-model.xml', 'w').write(empty)
        self.set_central_widget('vulnerability-model.xml')

    def save(self, nrmlfile):
        try:
            node = self.tableset.to_node()
        except Exception:
            # TODO: improve
            traceback.print_exc()
            return
        # save to a temporary file
        with open(nrmlfile + '~', 'w') as f:
            node_to_nrml(node, f)
        # only if there are no errors rename the file
        os.rename(nrmlfile + '~', nrmlfile)

    def save_nrml(self):
        """
        Save the current content of the tableset in NRML format
        """
        self.save(self.nrmlfile)

    def write_nrml(self):
        """
        Save the current content of the tableset in NRML format
        """
        self.nrmlfile = QtGui.QFileDialog.getSaveFileName(
            self, 'Save NRML', '', 'XML (*.xml)')
        self.save(self.nrmlfile)

    def quit(self):
        # TODO: we should check if something has changed before quitting
        QtGui.QApplication.quit()


def main(argv):
    if not argv[1:]:
        sys.exit('Please give the input NRML file')

    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')
    mw = MainWindow(sys.argv[1])
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
