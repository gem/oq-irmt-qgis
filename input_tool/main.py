import os
import sys
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow
from openquake import nrmllib
from openquake.nrmllib.node import node_from_nrml, node_copy, Node

SCHEMADIR = os.path.join(nrmllib.__path__[0], 'schema')


# hackish
def is_valid(item):
    return item and item.background() != QtCore.Qt.red


def getdata(widget, rowrange, colrange, ignore_invalid=False):
    data = []
    for r in rowrange:
        row = []
        for c in colrange:
            item = widget.item(r, c)
            if not ignore_invalid and not is_valid(item):
                raise ValueError(
                    'row=%d, col=%d, val=%s' % (r, c, item.text()))
            row.append(unicode(item.text()))
        data.append(row)
    return data


class Validator(QtGui.QValidator):
    def __init__(self, validator):
        self.validator = validator

    def validate(self, value):
        try:
            self.validator(value)
        except ValueError:
            return QtGui.QValidator.Invalid
        else:
            return QtGui.QValidator.Acceptable

    def validate_cell(self, item):
        text = unicode(item.text())
        valid = self.validate(text)
        if not valid:
            item.setBackground(QtCore.Qt.red)
        elif not is_valid(item):
            item.setBackground(QtCore.Qt.white)
        return valid


def split_numbers(node):
    return node.text.split()


def set_list_item(node, i, value):
    numbers = node.text.split()
    numbers[i] = value
    node.text = ' '.join(numbers)

VSET = dict(enumerate('vulnerabilitySetID assetCategory lossCategory IMT'
                      .split()))

VFN = dict(enumerate('vulnerabilityFunctionID probabilisticDistribution'
                     .split()))

IMLS = dict(enumerate('imls lossRatio coefficientsVariation'.split()))


DVSET_NODE = Node('discreteVulnerabilitySet', dict(
    assetCategory="population",
    lossCategory="fatalities",
    vulnerabilitySetID="XXX"))

VFN_NODE = Node('discreteVulnerability', dict(
    probabilisticDistribution="LN",
    vulnerabilityFunctionID="XX"))


class MainWindow(Ui_InputToolWindow, QtGui.QMainWindow):
    def __init__(self, inputdir):
        QtGui.QMainWindow.__init__(self)
        self.inputdir = inputdir
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

        self.actionCopy.triggered.connect(self.copy)
        self.actionPaste.triggered.connect(self.paste)

        # menu actions
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)

        ## HARD-CODED FOR THE MOMENT
        root = node_from_nrml(
            os.path.join(inputdir, 'vulnerability-model-discrete.xml'))[0]
        self.fileNameLbl.setText('vulnerability-model-discrete.xml')
        tab = self.tabwidget.findChild(QtGui.QWidget, root.tag)
        tab.root = root
        self.tabwidget.setCurrentWidget(tab)
        self.populate_table_widgets()

    @property
    def root(self):
        return self.tabwidget.currentWidget().root

    @property
    def vsets(self):
        return list(self.root.getnodes('discreteVulnerabilitySet'))

    def update_vSets(self, row, col):
        try:
            self.vsets[row]
        except IndexError:
            return
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
        item = self.imlsTbl.item(row, col)
        text = unicode(item.text())
        valid = self.imlsTbl.floatvalidator.validate_cell(item)
        if not valid:
            return

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
        widget.setRowCount(len(data))

        for row_index, row in enumerate(data):
            for col_index, content in enumerate(row):
                item = QtGui.QTableWidgetItem(content)
                widget.setItem(row_index, col_index, item)
                if widget.objectName == 'imlsTbl':
                    widget.floatvalidator.validate_cell(item)
        # widget.sortByColumn(0, QtCore.Qt.AscendingOrder)
        widget.resizeColumnsToContents()

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

        vfs = list(vset.getnodes('discreteVulnerability'))

        for vf in vfs:
            data.append([vf['vulnerabilityFunctionID'],
                         vf['probabilisticDistribution'],
                         ])
        self.populate_table_widget(self.vFnTbl, data)
        if data:
            self.vFnTbl.selectRow(0)
            self.populate_imlsTbl()

    def populate_imlsTbl(self):

        self.imlsTbl.floatvalidator = Validator(float)

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
        vfns = list(vset.getnodes('discreteVulnerability'))
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

    def open_file(self):
        fname = unicode(QtGui.QFileDialog.getOpenFileName(
            self, 'Choose file',
            self.inputdir,  # QtCore.QDir.homePath(),
            "Model file (*.xml);;Config files (*.ini)"))
        self.fileNameLbl.setText(fname)
        root = node_from_nrml(fname)
        tab = self.tabwidget.findChild(QtGui.QWidget, root.tag)
        tab.root = root
        self.tabwidget.setCurrentWidget(tab)
        self.populate_table_widgets()
        # print validate_ex()

    def save_file(self):
        fname = self.fileNameLbl.text()
        if self.imlsTbl.floatvalidator.n_invalid:
            print 'Cannot save: there are invalid entries'
        else:
            print 'Saving', fname

    def copy(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableWidget):
            return
        select_range = widget.selectedRanges()[0]
        r1, r2 = select_range.topRow(), select_range.bottomRow()
        c1, c2 = select_range.leftColumn(), select_range.rightColumn()
        rows = getdata(widget, range(r1, r2 + 1), range(c1, c2 + 1))
        QtGui.QApplication.clipboard().setText(
            '\n'.join('\t'.join(row) for row in rows))

    def paste(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableWidget):
            return
        lines = QtGui.QApplication.clipboard().text().split('\n')
        rows = [line.split('\t') for line in lines]
        if not rows:
            return
        ncolumns = widget.columnCount()
        data = getdata(widget, range(widget.rowCount()), range(ncolumns))
        for row in rows:
            assert len(row) <= ncolumns, 'Got %d columns, expected %d' % (
                len(row), ncolumns)
        self.populate_table_widget(widget, data + rows)

    def rowAdd(self, widget):
        if widget.objectName == 'vSetsTbl':
            self.root.append(node_copy(DVSET_NODE))
        elif widget.objectName == 'vFnTbl':
            row_index = self.vSetsTbl.currentRow()
            vset = self.vsets[row_index]
            vset.append(node_copy(VFN_NODE))
        lastrow = widget.rowCount()
        widget.insertRow(lastrow)
        for i in range(widget.columnCount()):
            item = QtGui.QTableWidgetItem('XXX')
            widget.setItem(lastrow + 1, i, item)

    def rowDel(self, widget):
        # selectedIndexes() returns both empty and non empty items
        row_ids = set(item.row() for item in widget.selectedIndexes())
        for row_id in sorted(row_ids, reverse=True):
            widget.removeRow(row_id)


# a quick test showing that Qt cannot understand nrml.xsd :-(
def validate_ex():
    from PyQt4.QtCore import QUrl
    from PyQt4.QtXmlPatterns import QXmlSchema, QXmlSchemaValidator
    qurl = QUrl(
        'file:///home/michele/oq-nrmllib/openquake/nrmllib/schema/nrml.xsd')
    schema = QXmlSchema()
    schema.load(qurl)
    if schema.isValid():
        v = QXmlSchemaValidator(schema)
        print v.validate(QUrl('file:///home/michele/oq-nrmllib/examples/'
                              'vulnerability-model-discrete.xml'))
    else:
        print 'schema invalid'


def main(argv):
    if not argv[1:]:
        sys.exit('Please give the input directory')

    # create Qt application
    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')

    # create main window
    wnd = MainWindow(argv[1])
    wnd.show()

    # Start the app up
    retval = app.exec_()
    sys.exit(retval)

if __name__ == '__main__':
    main(sys.argv)
