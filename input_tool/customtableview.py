from PyQt4 import QtCore, QtGui
from message_bar import MessageBar

def tr(basename, name=None):
    """Shortcut for QtGui.QApplication.translate"""
    if name is None:
        name = basename
    return QtGui.QApplication.translate(
        basename, name, None, QtGui.QApplication.UnicodeUTF8)


class CustomTableModel(QtCore.QAbstractTableModel):
    """
    Wrapper for table objects consistent with the API defined in
    nrmllib.record.Table.
    """
    RED = QtGui.QColor('#ff5050')

    # the signal below can not be in init, see
    # http://stackoverflow.com/questions/2970312/#2971426
    validationFailed = QtCore.pyqtSignal(QtCore.QModelIndex, ValueError)

    def __init__(self, table, getdefault, parent=None):
        # getdefault is a callable taking the table object
        # and returning a default record (or raising an error)
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.table = table
        self.getdefault = getdefault

    def rowCount(self, parent=None):
        return len(self.table)

    def columnCount(self, parent=None):
        return len(self.table.recordtype)

    def flags(self, index):
        flag = (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable)
        return flag

    def primaryKey(self, index):
        return self.table[index.row()].pkey

    # this method is called several times with different roles by Qt
    def data(self, index, role=QtCore.Qt.DisplayRole):
        record = self.table[index.row()]
        column = index.column()
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return record[column]
        elif role == QtCore.Qt.BackgroundRole and not record.is_valid(column):
            return QtGui.QBrush(self.RED)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            value = value.toString().encode('utf-8')
            record = self.table[row]
            try:
                record[column] = value
            except ValueError as e:
                self.validationFailed.emit(index, e)
                return False
            else:
                self.dataChanged.emit(index, index)
                return True
        return False

    def set_row(self, i, row):
        self.table[i].row[self.table.ordinal:] = row
        ##index = QtCore.QModelIndex().sibling(i, 0)
        ##self.dataChanged.emit(index, index)
        print self.table[i]

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.table.recordtype.fieldnames[section]
            else:  # vertical header
                # comment this if you do not want to display the row ids
                return section
                return

    def insertRows(self, position, nrows, parent=QtCore.QModelIndex()):
        try:
            default = self.table.recordtype(*self.getdefault(self.table))
        except TypeError as e:
            # this happens if no record is selected in the GUI
            print e
            return False
        self.beginInsertRows(parent, position, position + nrows - 1)
        for i in range(nrows):
            self.table._records.insert(position, default)
        self.endInsertRows()
        return True

    def removeRows(self, position, nrows, parent=QtCore.QModelIndex()):
        # delete rows in the underlying table in reverse order
        self.beginRemoveRows(parent, position, position + nrows - 1)
        try:
            for i in range(position + nrows - 1, position, -1):
                del self.table[i]
        except Exception as e:
            print e  # TODO: improve this
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
    def __init__(self, table, getdefault, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.table = table
        self.getdefault = getdefault
        self.tableModel = CustomTableModel(table, getdefault)
        self.parent = parent
        self.setupUi()

        self.addBtn.clicked.connect(lambda: self.appendRows(1))
        self.delBtn.clicked.connect(self.removeRows)

    def appendRows(self, nrows):
        start = self.tableModel.rowCount()
        self.tableModel.insertRows(start, nrows)
        return range(start, start + nrows)

    def removeRows(self):
        row_ids = set(item.row() for item in self.tableView.selectedIndexes())
        if not row_ids:
            return
        self.tableModel.removeRows(min(row_ids), len(row_ids))
        # TODO: notification on errors, for instance foreign key violations

    def current_record(self):
        """The record currently selected, or None"""
        indexes = self.tableView.selectedIndexes()
        if not indexes:
            return
        row_idx = indexes[-1].row()
        return self.tableModel.table[row_idx]

    def current_selection(self):
        """The currently selected rows, as tab-separated string of lines"""
        row_ids = set(item.row() for item in self.tableView.selectedIndexes())
        sel = []
        for row_id in row_ids:
            row = self.table[row_id]
            sel.append('\t'.join(row[self.table.ordinal:]))
        return '\n'.join(sel)

    def setupUi(self):
        self.tableView = QtGui.QTableView(self)
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)
        self.tableView.setMinimumSize(420, 200)

        self.tableView.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)
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
        # display only the rows satisfying the condition
        for row in range(self.tableModel.rowCount()):
            if cond(self.tableModel.table[row]):
                self.tableView.showRow(row)
            else:
                self.tableView.hideRow(row)

class TripleTableWidget(QtGui.QWidget):

    def __init__(self, tableset, nrmlfile, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tableset = tableset
        self.nrmlfile = nrmlfile
        self.message_bar = MessageBar(nrmlfile, self)
        self.tv = [CustomTableView(table, self.getdefault, parent)
                   for table in tableset.tables]
        self.setupUi()

        # connect clicked
        self.tv[0].tableView.clicked.connect(self.show_tv1)
        self.tv[1].tableView.clicked.connect(self.show_tv2)

        # connect errors
        for tv in self.tv:
            tv.tableModel.validationFailed.connect(
                lambda idx, err: self.show_validation_error(tv, idx, err))

        # hide primary key columns
        self.tv[1].tableView.hideColumn(0)
        self.tv[2].tableView.hideColumn(0)
        self.tv[2].tableView.hideColumn(1)

        # display table 1 and table 2 as if rows 0 and 0 where selected
        self.show_tv1(QtCore.QModelIndex().sibling(0, 0))
        self.show_tv2(QtCore.QModelIndex().sibling(0, 0))

    def getdefault(self, table):
        # return the primary key tuple partially filled, depending on
        # the currently selected rows
        # raise a TypeError if nothing is selected
        ordinal = table.ordinal
        if not ordinal:  # top left table
            return []
        return self.tv[ordinal - 1].current_record()[:ordinal]

    def setupUi(self):
        layout = QtGui.QVBoxLayout()
        hlayout = QtGui.QHBoxLayout()
        layout.addWidget(self.message_bar)
        hlayout.addWidget(self.tv[0])
        hlayout.addWidget(self.tv[1])
        layout.addLayout(hlayout)
        layout.addWidget(self.tv[2])
        self.setLayout(layout)
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)

    @QtCore.pyqtSlot(QtCore.QModelIndex, ValueError)
    def show_validation_error(self, table_view, index, error):
        record = table_view.tableModel.table[index.row()]
        fieldname = record.fields[index.column()].name
        message = '%s: %s' % (fieldname, error)
        self.message_bar.show_message(message)

    def show_tv1(self, row):
        k0, = self.tv[0].tableModel.primaryKey(row)
        # show only the rows in table 1 corresponding to k0
        self.tv[1].showOnCondition(lambda rec: rec[0] == k0)
        # table 2 must disappear because no row in table 1 is selected
        self.tv[2].showOnCondition(lambda rec: False)

    def show_tv2(self, row):
        # show only the rows in table 2 corresponding to k0 and k1
        k0, k1 = self.tv[1].tableModel.primaryKey(row)
        self.tv[2].showOnCondition(lambda rec: rec[0] == k0 and rec[1] == k1)


# Note: the copy functionality can be implemented also as follows:
#
# def keyPressEvent(self, event):
#     if event.matches(QtGui.QKeySequence.Copy):
#         selection = self.tableView.selectionModel()
#         row_indexes = selection.selectedRows()
#         if not row_indexes:  # no row selected
#             return
#         text = []
#         for row_idx in row_indexes:
#             row = row_idx.row()
#             r = []
#             for col in range(self.tableModel.columnCount()):
#                 idx = row_idx.sibling(row, col)
#                 r.append(self.tableModel.data(idx))
#             text.append('\t'.join(r))
#         QtGui.QApplication.clipboard().setText('\n'.join(text))
#     else:
#         QtGui.QTableView.keyPressEvent(self.tableView, event)
