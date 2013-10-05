import sip
sip.setapi("QString", 2)  # this is needed for value.toPyObject() in setData
from PyQt4 import QtCore, QtGui


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

    def data(self, index, role):
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
        for i in range(nrows):
            self.table.insert(position, self.table.recordtype())
        self.endInsertRows()
        return True

    def removeRows(self, position, nrows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + nrows - 1)
        del self.table[position, position + nrows - 1]
        self.endRemoveRows()
        return True


class CustomTableView(QtGui.QTableView):
    """
    Wrapper for CustomTableModel.
    """
    def __init__(self, table, parent=None):
        QtGui.QTableView.__init__(self, parent)
        self.setModel(CustomTableModel(table))
        self.resizeColumnsToContents()  # has not effect :-(
        self.setSelectionBehavior(self.SelectRows)
        #self.setSelectionMode(self.SingleSelection)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            QtGui.QTableView.keyPressEvent(self, event)

    def copy(self):
        selection = self.selectionModel()
        indexes = selection.selectedRows()
        if not indexes:  # no row selected
            return
        text = ''
        for idx in indexes:
            row = idx.row()
            for col in range(0, self.columnCount()):
                item = self.item(row, col)
                if item:
                    text += item.text()
                text += '\t'
            text += '\n'
        QtCore.QApplication.clipboard().setText(text)
