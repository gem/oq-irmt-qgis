import os
import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtCore, QtGui
from customtableview import TripleTableWidget, tr, messagebox

from openquake.nrmllib.node import node_from_xml, node_to_nrml
from openquake.common.converter import Converter


class MainWindow(QtGui.QMainWindow):
    def __init__(self, nrmlfile):
        QtGui.QMainWindow.__init__(self)
        self.set_central_widget(nrmlfile)
        self.setWindowTitle(tr("Input Tool Window"))
        self.setupMenu()

    def set_central_widget(self, nrmlfile):
        self.nrmlfile = nrmlfile
        with messagebox(self):
            node = node_from_xml(nrmlfile)[0]
            self.tableset = Converter.from_node(node).tableset
        if len(self.tableset) != 3:
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

        self.menuNew = QtGui.QMenu(self.menuFile)
        self.menuNew.setObjectName("menuNew")

        self.actionNewVM = QtGui.QAction(self)
        self.actionNewVM.setObjectName("actionNewVM")
        self.actionOpen = QtGui.QAction(self)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(self)
        self.actionSave.setObjectName("actionSave")
        self.actionWrite = QtGui.QAction(self)
        self.actionWrite.setObjectName("actionWrite")
        self.actionFullCheck = QtGui.QAction(self)
        self.actionFullCheck.setObjectName("actionFullCheck")
        self.actionCopy = QtGui.QAction(self)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtGui.QAction(self)
        self.actionPaste.setObjectName("actionPaste")
        self.actionReload = QtGui.QAction(self)
        self.actionReload.setObjectName("actionReload")
        self.actionQuit = QtGui.QAction(self)
        self.actionQuit.setObjectName("actionQuit")

        self.menuFile.addMenu(self.menuNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionWrite)
        self.menuFile.addAction(self.actionCopy)
        self.menuFile.addAction(self.actionFullCheck)
        self.menuFile.addAction(self.actionPaste)
        self.menuFile.addAction(self.actionReload)
        self.menuFile.addAction(self.actionQuit)

        self.menuNew.addAction(self.actionNewVM)

        self.menubar.addMenu(self.menuFile)
        self.menuFile.setTitle(tr("InputToolWindow"))

        # retranslateUi
        self.menuNew.setTitle(tr("New"))

        self.menuFile.setTitle(tr("File"))
        self.actionNewVM.setText(tr("&VulnerabilityModel"))
        self.actionNewVM.setShortcut(tr("Ctrl+N"))
        self.actionOpen.setText(tr("&Open"))
        self.actionOpen.setShortcut(tr("Ctrl+O"))
        self.actionSave.setText(tr("&Save"))
        self.actionSave.setShortcut(tr("Ctrl+S"))
        self.actionWrite.setText(tr("&Save As"))
        self.actionWrite.setShortcut(tr("Ctrl+Shift+S"))
        self.actionCopy.setText(tr("&Copy"))
        self.actionCopy.setShortcut(tr("Ctrl+C"))
        self.actionFullCheck.setText(tr("&FullCheck"))
        self.actionFullCheck.setShortcut(tr("Ctrl+F"))
        self.actionPaste.setText(tr("&Paste"))
        self.actionPaste.setShortcut(tr("Ctrl+V"))
        self.actionReload.setText(tr("&Reload"))
        self.actionReload.setShortcut(tr("Ctrl+R"))
        self.actionQuit.setText(tr("&Quit"))
        self.actionQuit.setShortcut(tr("Ctrl+Q"))

        # menu actions
        self.actionNewVM.triggered.connect(self.new_vulnerability_model)
        self.actionOpen.triggered.connect(self.open_nrml)
        self.actionSave.triggered.connect(self.save_nrml)
        self.actionWrite.triggered.connect(self.write_nrml)
        self.actionQuit.triggered.connect(self.quit)
        self.actionCopy.triggered.connect(self.copy)
        self.actionPaste.triggered.connect(self.paste)
        self.actionFullCheck.triggered.connect(self.full_check)
        self.actionReload.triggered.connect(
            lambda: self.set_central_widget(self.nrmlfile))

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
        with messagebox(self):
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

    def full_check(self):
        with messagebox(self):
            self.tableset.to_node()

    def save(self, nrmlfile):
        try:
            node = self.full_check()
        except:
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
        if self.nrmlfile:  # can be the empty string if nothing is selected
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
