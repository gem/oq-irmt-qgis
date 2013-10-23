import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from customtableview import TripleTableWidget, tr

from openquake.nrmllib.node import node_from_nrml
from openquake.nrmllib.converter import Converter


class Dialog(QtGui.QDialog):
    def __init__(self, t1, t2, t3):
        QtGui.QDialog.__init__(self)
        self.tt = TripleTableWidget(t1, t2, t3, self)
        self.setWindowTitle(tr("TripleTableWidget Example"))
        # this was the missing call where you set the layout of the tritable
        # widget to the dialog
        self.setLayout(self.tt.layout())


def main(argv):
    if not argv[1:]:
        sys.exit('Please give the input NRML file')

    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')
    node = node_from_nrml(sys.argv[1])[0]
    tables = Converter.node_to_tables(node)
    mw = Dialog(*tables)
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
