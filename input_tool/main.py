import os
import sys
import nodes
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow
from openquake import nrmllib
SCHEMADIR = os.path.join(nrmllib.__path__[0], 'schema')


def split_numbers(node):
    return node._value.split()


def set_list_item(node, i, value):
    numbers = node._value.split()
    numbers[i] = value
    node._value = ' '.join(numbers)

VSET = dict(enumerate('vulnerabilitySetID assetCategory lossCategory IMT'
                      .split()))

VFN = dict(enumerate('vulnerabilityFunctionID probabilisticDistribution'
                     .split()))

IMLS = dict(enumerate('imls lossRatio coefficientsVariation'.split()))


class MainWindow(Ui_InputToolWindow, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.tabwidget.currentWidget().root = None

        # table widgets
        self.vSetsTbl.itemSelectionChanged.connect(self.populate_vFnTbl)
        self.vFnTbl.itemSelectionChanged.connect(self.populate_imlsTbl)
        self.vSetsTbl.cellChanged.connect(self.update_vSets)
        self.vFnTbl.cellChanged.connect(self.update_vFn)
        self.imlsTbl.cellChanged.connect(self.update_imls)

        # add/del buttons
        self.vSetsAddBtn.clicked.connect(lambda: self.rowAdd(self.vSetsTbl))
        self.vSetsDelBtn.clicked.connect(lambda: self.rowDel(self.vSetsTbl))
        self.vFnAddBtn.clicked.connect(lambda: self.rowAdd(self.vFnTbl))
        self.vFnDelBtn.clicked.connect(lambda: self.rowDel(self.vFnTbl))
        self.imlsAddBtn.clicked.connect(lambda: self.rowAdd(self.imlsTbl))
        self.imlsDelBtn.clicked.connect(lambda: self.rowDel(self.imlsTbl))

        # menu actions
        self.actionOpen.triggered.connect(self.load_file)

    @property
    def vsets(self):
        root = self.tabwidget.currentWidget().root
        return root.getnodes('discreteVulnerabilitySet')

    def update_vSets(self, row, col):
        text = unicode(self.vSetsTbl.item(row, col).text())
        attr = VSET[col]
        if attr == 'IMT':
            self.vsets[row].IML[attr] = text
        else:
            self.vsets[row][attr] = text

    def update_vFn(self, row, col):
        text = unicode(self.vFnTbl.item(row, col).text())
        attr = VFN[col]
        current_vset = self.vSetsTbl.currentRow()
        self.vsets[current_vset][row][attr] = text

    def update_imls(self, row, col):
        text = unicode(self.imlsTbl.item(row, col).text())
        attr = IMLS[col]
        current_vset = self.vSetsTbl.currentRow()
        current_vfn = self.vFnTbl.currentRow()
        vfn = self.vsets[current_vset][current_vfn + 1]  # +1 to skip IML node
        if attr == 'lossRatio':
            set_list_item(vfn.lossRatio, row, text)
        elif attr == 'coefficientsVariation':
            set_list_item(vfn.coefficientsVariation, row, text)
        elif attr == 'imls':
            set_list_item(self.vsets[current_vset].IML, row, text)

    def populate_table_widget(self, widget, data):
        widget.clearContents()
        widget.resizeColumnsToContents()
        widget.setRowCount(len(data))

        for row_index, row in enumerate(data):
            for col_index, content in enumerate(row):
                item = QtGui.QTableWidgetItem(content)
                widget.setItem(row_index, col_index, item)

    def populate_table_widgets(self):
        data = []
        for vset in self.vsets:
            data.append([vset['vulnerabilitySetID'],
                         vset['assetCategory'],
                         vset['lossCategory'],
                         vset.IML['IMT'],
                         ])
        self.populate_table_widget(self.vSetsTbl, data)

        if data:
            self.vSetsTbl.selectRow(0)
            self.populate_vFnTbl()

    def populate_vFnTbl(self):
        row_index = self.vSetsTbl.currentRow()
        data = []
        try:
            vset = self.vsets[row_index]
        except IndexError:  # trying to access a non-populated row
            self.vFnTbl.clearContents()
            self.vFnTbl.setRowCount(1)
            return

        vfs = vset.getnodes('discreteVulnerability')

        for vf in vfs:
            data.append([vf['vulnerabilityFunctionID'],
                         vf['probabilisticDistribution'],
                         ])
        self.populate_table_widget(self.vFnTbl, data)
        if data:
            self.vFnTbl.selectRow(0)
            self.populate_imlsTbl()

    def populate_imlsTbl(self):
        set_index = self.vSetsTbl.currentRow()
        vfn_index = self.vFnTbl.currentRow()
        try:
            vset = self.vsets[set_index]
        except IndexError:  # trying to access a non-populated row
            self.imlsTbl.clearContents()
            self.imlsTbl.setRowCount(1)
            return

        imt = QtGui.QTableWidgetItem(vset.IML['IMT'])
        self.imlsTbl.setHorizontalHeaderItem(0, imt)
        imls = split_numbers(vset.IML)
        vfns = self.vsets[set_index].getnodes('discreteVulnerability')
        try:
            vfn = vfns[vfn_index]
        except IndexError:
            self.imlsTbl.clearContents()
            self.imlsTbl.setRowCount(1)
            return
        loss_ratios = split_numbers(vfn.lossRatio)
        coeff_vars = split_numbers(vfn.coefficientsVariation)
        data = zip(imls, loss_ratios, coeff_vars)
        self.populate_table_widget(self.imlsTbl, data)

    def load_file(self):
        XMLDIR = os.path.join(SCHEMADIR, '../../../examples')
        fname = unicode(QtGui.QFileDialog.getOpenFileName(
            self, 'Choose file',
            XMLDIR,  # QtCore.QDir.homePath(),
            "Model file (*.xml);;Config files (*.ini)"))
        root, modeltype = nodes.parse_nrml(
            os.path.dirname(fname), os.path.basename(fname))
        tab = self.tabwidget.findChild(QtGui.QWidget, modeltype)
        tab.root = root
        self.tabwidget.setCurrentWidget(tab)

        self.populate_table_widgets()

    def rowAdd(self, widget):
        widget.insertRow(widget.rowCount())

    def rowDel(self, widget):
        for item in widget.selectedItems():
            widget.removeRow(item.row())


def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('QTableWidget::item:selected'
                      '{ background-color: palette(highlight) }')

    # create main window
    wnd = MainWindow()
    wnd.show()

    # Start the app up
    retval = app.exec_()
    sys.exit(retval)

if __name__ == '__main__':
    main(sys.argv)
