import os
import sys
import nodes
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow


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
        self.populate_table_widgets()
        self.vSetsTbl.itemSelectionChanged.connect(self.populate_vFnTbl)
        self.vFnTbl.itemSelectionChanged.connect(self.populate_imlsTbl)
        self.vSetsTbl.cellChanged.connect(self.update_vSets)
        self.vFnTbl.cellChanged.connect(self.update_vFn)
        self.imlsTbl.cellChanged.connect(self.update_imls)

    def update_vSets(self, row, col):
        text = unicode(self.vSetsTbl.item(row, col).text())
        attr = VSET[col]
        if attr == 'IMT':
            vsets[row].IML[attr] = text
        else:
            vsets[row][attr] = text

    def update_vFn(self, row, col):
        text = unicode(self.vFnTbl.item(row, col).text())
        attr = VFN[col]
        current_vset = self.vSetsTbl.currentRow()
        vsets[current_vset][row][attr] = text

    def update_imls(self, row, col):
        text = unicode(self.imlsTbl.item(row, col).text())
        attr = IMLS[col]
        current_vset = self.vSetsTbl.currentRow()
        current_vfn = self.vFnTbl.currentRow()
        vfn = vsets[current_vset][current_vfn + 1]
        if attr == 'lossRatio':
            set_list_item(vfn.lossRatio, row, text)
        elif attr == 'coefficientsVariation':
            set_list_item(vfn.coefficientsVariation, row, text)
        elif attr == 'imls':
            set_list_item(vsets[current_vset].IML, row, text)
        print vfn

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
        for vset in vsets:
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
        vset = vsets[row_index]
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
        vset = vsets[set_index]
        imt = QtGui.QTableWidgetItem(vset.IML['IMT'])
        self.imlsTbl.setHorizontalHeaderItem(0, imt)
        imls = split_numbers(vset.IML)
        vfn = vsets[set_index].getnodes('discreteVulnerability')[vfn_index]
        loss_ratios = split_numbers(vfn.lossRatio)
        coeff_vars = split_numbers(vfn.coefficientsVariation)
        data = zip(imls, loss_ratios, coeff_vars)
        self.populate_table_widget(self.imlsTbl, data)


def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv, True)
    # app.setStyleSheet('QTableWidget::item:selected{ background-color: red }')

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
