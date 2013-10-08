import sip
sip.setapi("QString", 2)  # this is needed for value.toPyObject() in setData
from PyQt4 import QtCore, QtGui


def tr(name):
    return QtGui.QApplication.translate(
        name, name, None, QtGui.QApplication.UnicodeUTF8)


class CustomTableModel(QtCore.QAbstractTableModel):
    """
    Wrapper for table objects consistent with the API defined in
    nrmllib.record.Table.
    """
    def __init__(self, table, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.table = table

    def rowCount(self, parent=None):
        return len(self.table)

    def columnCount(self, parent=None):
        return len(self.table.recordtype)

    def flags(self, index):
        flag = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        field = self.table.recordtype.fields[index.column()]
        if not field.key:  # primary key fields are not editable
            flag |= QtCore.Qt.ItemIsEditable
        return flag

    def primaryKey(self, index):
        return self.table[index.row()].pkey

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            row = index.row()
            column = index.column()
            return self.table[row][column]

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            value = value.toPyObject().encode('utf-8')
            record = self.table[row]
            try:
                record[column] = value
            except ValueError:
                # TODO: add some notification
                return False
            else:
                self.dataChanged.emit(index, index)
                return True
        return False

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.table.recordtype.fieldnames[section]
            else:  # vertical header
                return section

    def insertRows(self, position, nrows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + nrows - 1)
        try:
            for i in range(nrows):
                self.table.insert(position, self.table.recordtype())
        except KeyError:  # duplicate key
            return False
        else:
            return True
        finally:
            self.endInsertRows()

    def removeRows(self, position, nrows, parent=QtCore.QModelIndex()):
        # delete rows in the underlying table in reverse order
        self.beginRemoveRows(parent, position, position + nrows - 1)
        try:
            for i in range(position + nrows - 1, position, -1):
                del self.table[i]
        except Exception as e:
            print e
            return False
        else:
            return True
        finally:
            self.endRemoveRows()

    def name(self):
        return self.table.recordtype.__name__


class CustomTableView(QtGui.QWidget):
    """
    Wrapper for CustomTableModel.
    """
    def __init__(self, table, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tableModel = CustomTableModel(table)
        self.parent = parent
        self.setupUi()

        self.addBtn.clicked.connect(self.appendRow)
        self.delBtn.clicked.connect(self.removeRows)

    def appendRow(self):
        self.tableModel.insertRows(self.tableModel.rowCount(), 1)
        # TODO: notification on errors

    def removeRows(self):
        row_ids = set(item.row() for item in self.tableView.selectedIndexes())
        if not row_ids:
            return
        self.tableModel.removeRows(min(row_ids), len(row_ids))
        # TODO: notification on errors

    def setupUi(self):
        self.tableView = QtGui.QTableView(self.parent)
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSizePolicy(  # ignored :-(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.tableView.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        #self.tableView.setSelectionMode(
        #    QtGui.QAbstractItemView.SingleSelection)
        self.tableView.setAlternatingRowColors(True)

        self.tableLabel = QtGui.QLabel(self.tableModel.name())

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.tableLabel)
        self.layout.addWidget(self.tableView)
        self.addBtn = QtGui.QPushButton(self.tableView)
        self.addBtn.setObjectName('addBtn')
        self.addBtn.setText(tr('Add Row'))
        self.delBtn = QtGui.QPushButton(self.tableView)
        self.addBtn.setObjectName('delBtn')
        self.delBtn.setText(tr('Delete Rows'))
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.addBtn)
        buttonLayout.addWidget(self.delBtn)
        self.layout.addLayout(buttonLayout)

        self.setLayout(self.layout)

    def showOnCondition(self, cond):
        for row in range(self.tableModel.rowCount()):
            if cond(self.tableModel.table[row]):
                self.tableView.showRow(row)
            else:
                self.tableView.hideRow(row)

    def show(self):
        self.tableView.resizeRowsToContents()  # has no effect :-(
        self.tableView.resizeColumnsToContents()  # has no effect :-(
        QtGui.QWidget.show(self)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            QtGui.QTableView.keyPressEvent(self.tableView, event)

    def copy(self):
        selection = self.tableView.selectionModel()
        row_indexes = selection.selectedRows()
        if not row_indexes:  # no row selected
            return
        text = []
        for row_idx in row_indexes:
            row = row_idx.row()
            r = []
            for col in range(self.tableModel.columnCount()):
                idx = row_idx.sibling(row, col)
                r.append(self.tableModel.data(idx))
            text.append('\t'.join(r))
        QtGui.QApplication.clipboard().setText('\n'.join(text))


class TripleTableWidget(QtGui.QWidget):

    def __init__(self, t1, t2, t3, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tv1 = CustomTableView(t1, parent)
        self.tv2 = CustomTableView(t2, parent)
        self.tv3 = CustomTableView(t3, parent)
        self.setupUi()
        self.tv1.tableView.clicked.connect(self.show_tv2)
        self.tv2.tableView.clicked.connect(self.show_tv3)

        # hide
        self.tv2.tableView.hideColumn(0)
        self.tv3.tableView.hideColumn(0)
        self.tv3.tableView.hideColumn(1)
        self.show_tv2(QtCore.QModelIndex().sibling(0, 0))
        self.show_tv3(QtCore.QModelIndex().sibling(0, 0))

    def show_tv2(self, row):
        vset, = self.tv1.tableModel.primaryKey(row)
        self.tv2.showOnCondition(lambda rec: rec[0] == vset)
        self.show_tv3(QtCore.QModelIndex().sibling(0, 0))

    def show_tv3(self, row):
        k0, k1 = self.tv2.tableModel.primaryKey(row)

        def cond(rec):
            return (rec[0] == k0 and rec[1] == k1)
        self.tv3.showOnCondition(cond)

    def setupUi(self):
        layout = QtGui.QVBoxLayout()
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self.tv1)
        hlayout.addWidget(self.tv2)
        layout.addLayout(hlayout)
        layout.addWidget(self.tv3)
        self.setLayout(layout)
