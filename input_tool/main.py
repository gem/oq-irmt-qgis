import os
import sys
import nodes
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow


def split_numbers(node):
    return node._value.split()


class MainWindow(Ui_InputToolWindow, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.populate_table_widgets()

    def populate_table_widget(self, widget, data):
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
            #self.vSetsTbl.setSortingEnabled(True)

    def populate_vFnTbl(self):
        row_index = self.vSetsTbl.currentRow()
        data = []
        vfs = vsets[row_index].getnodes('discreteVulnerability')
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
        imls = split_numbers(vset.IML)
        vfn = vsets[set_index].getnodes('discreteVulnerability')[vfn_index]
        loss_ratios = split_numbers(vfn.lossRatio)
        coeff_vars = split_numbers(vfn.coefficientsVariation)
        data = zip(imls, loss_ratios, coeff_vars)
        self.populate_table_widget(self.imlsTbl, data)


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
