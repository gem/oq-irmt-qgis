import sys
import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from customtableview import TripleTableWidget

from openquake.nrmllib.node import node_from_nrml
from openquake.nrmllib.converter import Converter


def tr(name):
    return QtGui.QApplication.translate(
        name, name, None, QtGui.QApplication.UnicodeUTF8)


class Dialog(QtGui.QDialog):
    def __init__(self, t1, t2, t3):
        QtGui.QDialog.__init__(self)
        self.tt = TripleTableWidget(t1, t2, t3, self)
        self.tt.setSizePolicy(  # ignored :-(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.tt.show()
        self.setWindowTitle(tr("TripleTableWidget Example"))


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
    print tables
    mw = Dialog(*tables)
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
