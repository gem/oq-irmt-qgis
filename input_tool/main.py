import os
import sys
import nodes
from PyQt4 import QtGui, QtCore
from ui_input_tool_window import Ui_InputToolWindow
from openquake import nrmllib

SCHEMADIR = os.path.join(nrmllib.__path__[0], 'schema')


class Validator(QtGui.QValidator):
    def __init__(self, validator):
        self.validator = validator
        self.n_invalid = 0

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
            self.n_invalid += 1
        elif item.background() == QtCore.Qt.red:
            item.setBackground(QtCore.Qt.white)
            self.n_invalid -= 1
            print self.n_invalid
        return valid


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

        # menu actions
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)

        ## HARD-CODED FOR THE MOMENT
        root, modeltype = nodes.parse_nrml(
            inputdir, 'vulnerability-model-discrete.xml')
        self.fileNameLbl.setText('vulnerability-model-discrete.xml')
        tab = self.tabwidget.findChild(QtGui.QWidget, modeltype)
        tab.root = root
        self.tabwidget.setCurrentWidget(tab)
        self.populate_table_widgets()

    @property
    def vsets(self):
        root = self.tabwidget.currentWidget().root
        return root.getnodes('discreteVulnerabilitySet')

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
        widget.resizeColumnsToContents()
        widget.setRowCount(len(data))

        for row_index, row in enumerate(data):
            for col_index, content in enumerate(row):
                item = QtGui.QTableWidgetItem(content)
                widget.setItem(row_index, col_index, item)
                if widget.objectName == 'imlsTbl':
                    widget.floatvalidator.validate_cell(item)

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
        vfns = vset.getnodes('discreteVulnerability')
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
        root, modeltype = nodes.parse_nrml(
            os.path.dirname(fname), os.path.basename(fname))
        tab = self.tabwidget.findChild(QtGui.QWidget, modeltype)
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

    def rowAdd(self, widget):
        widget.insertRow(widget.rowCount())

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
