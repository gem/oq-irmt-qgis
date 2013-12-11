import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui, QtCore
from customtableview import CustomTableView

from openquake.nrmllib.node import node_from_nrml
from openquake.common.converter import Converter


def tr(name):
    return QtGui.QApplication.translate(
        name, name, None, QtGui.QApplication.UnicodeUTF8)


class Dialog(QtGui.QDialog):
    def __init__(self, table):
        QtGui.QDialog.__init__(self)
        self.customTable = CustomTableView(table, self)
        self.customTable.showOnCondition(
            lambda rec: rec['vulnerabilitySetID'] == 'PAGER')
        self.customTable.show()
        self.customTable.tableView.resizeColumnsToContents()
        self.setWindowTitle(tr("CustomTableView Example"))


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
    mw = Dialog(tbl['DiscreteVulnerability'])
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
