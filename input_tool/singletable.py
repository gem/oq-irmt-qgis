import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui, QtCore
from customtableview import CustomTableView

from openquake.nrmllib.node import node_from_nrml
from openquake.nrmllib.converter import Converter


class MainWindow(QtGui.QDialog):
    def __init__(self, table):
        QtGui.QMainWindow.__init__(self)
        tableLabel = QtGui.QLabel("Behold, some data, in a table:")
        self.customTable = CustomTableView(table)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(tableLabel)
        layout.addWidget(self.customTable)
        self.setLayout(layout)
        self.setWindowTitle("Copy and Paste Example")


def main(argv):
    if not argv[1:]:
        sys.exit('Please give the input NRML file')

    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')
    node = node_from_nrml(sys.argv[1])[0]
    tbl = Converter.node_to_tables(node)
    mw = MainWindow(tbl['DiscreteVulnerabilitySet'])
    mw.show()
    # tableView.resizeColumnsToContents() has no effect
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
