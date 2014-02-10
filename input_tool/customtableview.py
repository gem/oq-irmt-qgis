import copy
import traceback
import collections
from contextlib import contextmanager
from PyQt4 import QtCore, QtGui
from message_bar import MessageBar
from openquake.common.record import Record, Table, TableSet, Unique, Field
from openquake.risklib.scientific import LogNormalDistribution
from numpy import linspace

LEFT = 0
RIGHT = 1
DOWN = 2

try:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
except ImportError:
    Figure = None


def tr(basename, name=None):
    """Shortcut for QtGui.QApplication.translate"""
    if name is None:
        name = basename
    return QtGui.QApplication.translate(
        basename, name, None, QtGui.QApplication.UnicodeUTF8)


@contextmanager
def messagebox(widget=None):
    try:
        yield
    except Exception:
        tb_str = traceback.format_exc()
        QtGui.QMessageBox.critical(widget, 'Invalid model', tb_str)
        raise


class _ItemModel(QtCore.QAbstractItemModel):
    def index(self, row, column):
        return QtCore.QAbstractItemModel.createIndex(self, row, column)

index = _ItemModel().index


class NoRecordSelected(Exception):
    pass


class CustomTableModel(QtCore.QAbstractTableModel):
    """
    Wrapper for table objects consistent with the API defined in
    common.record.Table.
    """
    RED = QtGui.QColor('#ff5050')

    # the signal below can not be in init, see
    # http://stackoverflow.com/questions/2970312/#2971426
    validationFailed = QtCore.pyqtSignal(QtCore.QModelIndex, Exception)

    def __init__(self, table, getdefault):
        # getdefault is a callable taking the table object
        # and returning a default record (or raising an error)
        # it is used only in insertRows
        QtCore.QAbstractTableModel.__init__(self)
        self.table = table
        self.getdefault = getdefault

    def rowCount(self, parent=None):
        return len(self.table)

    def columnCount(self, parent=None):
        return len(self.table.recordtype)

    def flags(self, index):
        flag = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() != self.table.attr.get('readonly_column'):
            flag |= QtCore.Qt.ItemIsEditable
        return flag

    def primaryKey(self, index):
        return self.table[index.row()].pkey

    # this method is called several times with different roles by Qt
    def data(self, index, role=QtCore.Qt.DisplayRole):
        with messagebox():
            record = self.table[index.row()]
            column_i = index.column()
            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
                return record[column_i]
            elif (role == QtCore.Qt.BackgroundRole and not
                  record.is_valid(column_i)):
                return QtGui.QBrush(self.RED)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            value = value.toString().encode('utf-8')
            record = copy.deepcopy(self.table[row])
            try:
                record[column] = value
            except ValueError as e:
                self.validationFailed.emit(index, e)
                return False
            else:
                self.table[row] = record
                self.dataChanged.emit(index, index)
                return True
        return False

    def set_row(self, i, row):
        """Set the i-th record of the table to the given row"""
        with messagebox():
            rec = self.table[i]
            # NB: the ordinal of the table specifies the number of fields in
            # the primary key: 0 for ordinal=0, 1 for ordinal=1, and 2
            # for ordinal=2; row is a list with N - ordinal elements, where
            # N is the total number of fields in the record
            rec.row[self.table.ordinal:] = row

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.table.recordtype.fieldnames[section]
            else:  # vertical header
                # comment this if you do not want to display the row ids
                # return section
                return

    def insertRows(self, position, nrows, parent=QtCore.QModelIndex()):
        try:
            default = self.getdefault(self.table)
        except NoRecordSelected:
            self.validationFailed.emit(
                index(0, 0), NoRecordSelected('no record selected'))
            return True
        try:
            self.beginInsertRows(parent, position, position + nrows - 1)
            for i in range(nrows):
                rec = self.table.recordtype(*default + ['dummy%d' % i])
                self.table.insert(position, rec)
        except Exception as e:
            self.validationFailed.emit(index(i, 0), e)
            err = True
        else:
            err = False
        finally:
            self.endInsertRows()
        return err

    def removeRows(self, position, nrows, parent=QtCore.QModelIndex()):
        # delete rows in the underlying table in reverse order
        self.beginRemoveRows(parent, position, position + nrows - 1)
        try:
            with messagebox():
                for i in range(position + nrows - 1, position - 1, -1):
                    del self.table[i]
        except:
            return False
        else:
            return True
        finally:
            self.endRemoveRows()

    def name(self):
        return self.table.recordtype.__name__


class CustomTableView(QtGui.QWidget):
    """
    Wrapper for CustomTableModel. `getdefault` is used to generate
    a default record when adding a new row. If it is None, it is
    not possible to add/remove rows.
    """
    def __init__(self, table, getdefault=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.table = table
        self.getdefault = getdefault
        self.tableModel = CustomTableModel(table, getdefault)
        self.tableView = QtGui.QTableView(self)
        self.setupUi()

        if table.attr.get('addBtn'):
            self.addBtn.clicked.connect(lambda: self.appendRows(1))
        if table.attr.get('delBtn'):
            self.delBtn.clicked.connect(self.removeRows)

    def appendRows(self, nrows):
        start = self.tableModel.rowCount()
        err = self.tableModel.insertRows(start, nrows)
        if err:
            return []
        else:
            return range(start, start + nrows)

    def removeRows(self):
        row_ids = set(item.row() for item in self.tableView.selectedIndexes())
        if not row_ids:
            return
        self.tableModel.removeRows(min(row_ids), len(row_ids))

    def current_record(self):
        """Return the record currently selected"""
        indexes = self.tableView.selectedIndexes()
        if not indexes:
            raise NoRecordSelected
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
        label = '%s (%d rows)' % (
            self.tableModel.name(), self.tableModel.rowCount())
        self.tableLabel = QtGui.QLabel(label)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.tableLabel)
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)

        if self.table.attr.get('addBtn'):  # define add/del buttons
            self.addBtn = QtGui.QPushButton(self.tableView)
            self.addBtn.setObjectName('addBtn')
            self.addBtn.setText(tr('Add Row'))
        if self.table.attr.get('delBtn'):
            self.delBtn = QtGui.QPushButton(self.tableView)
            self.addBtn.setObjectName('delBtn')
            self.delBtn.setText(tr('Delete Rows'))
        buttonLayout = QtGui.QHBoxLayout()
        if self.table.attr.get('addBtn'):
            buttonLayout.addWidget(self.addBtn)
        if self.table.attr.get('delBtn'):
            buttonLayout.addWidget(self.delBtn)
        self.layout.addLayout(buttonLayout)

    def showOnCondition(self, cond):
        # display only the rows satisfying the condition
        for row in range(self.tableModel.rowCount()):
            if cond(self.tableModel.table[row]):
                self.tableView.showRow(row)
            else:
                self.tableView.hideRow(row)


class NameValue(Record):
    pkey = Unique('attr_name')
    attr_name = Field(str)
    attr_value = Field(str)


class NameValueView(QtGui.QWidget):
    """
    Wrapper around a table with a single record
    """
    def __init__(self, orig_table, dummy=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        assert len(orig_table) == 1, len(orig_table)

        orig_record = orig_table[0]
        fieldnames = orig_record.__class__.fieldnames
        self.name = orig_record.__class__.__name__
        recs = [NameValue(n, v) for n, v in zip(fieldnames, orig_record)]
        self.table = Table(NameValue, recs)
        self.table.attr['readonly_column'] = 0
        self.tableModel = CustomTableModel(self.table, None)
        self.tableView = QtGui.QTableView(self)
        self.setupUi()

    def current_record(self):
        """Return the record currently selected"""
        indexes = self.tableView.selectedIndexes()
        if not indexes:
            raise NoRecordSelected
        row_idx = indexes[-1].row()
        return self.tableModel.table[row_idx]

    def current_selection(self):
        """The currently selected rows, as tab-separated string of lines"""
        row_ids = set(item.row() for item in self.tableView.selectedIndexes())
        sel = []
        for row_id in row_ids:
            row = self.table[row_id]
            sel.append('\t'.join(row))
        return '\n'.join(sel)

    def setupUi(self):
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)
        self.tableView.setMinimumSize(420, 270)

        self.tableView.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)
        self.tableLabel = QtGui.QLabel(self.name)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.tableLabel)
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)


class TripleTableWidget(QtGui.QWidget):
    table_attrs = {}

    def __init__(self, tableset, nrmlfile, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tableset = tableset
        self.nrmlfile = nrmlfile
        self.message_bar = MessageBar(nrmlfile, self)
        self.init_tv()  # this goes before setupUi
        self.setupUi()

    def init_tv(self):
        self.tv = collections.OrderedDict()
        n_attrs = len(self.table_attrs)
        n_tables = len(self.tableset.tables)
        if n_attrs != n_tables:
            raise RuntimeError('There are %d tables but %d table attributes!' %
                               (n_tables, n_attrs))
        for i, (tablename, attr) in enumerate(self.table_attrs.items()):
            table = getattr(self.tableset, tablename)
            table.attr.update(attr)
            self.tv[table.name] = CustomTableView(table, self.getdefault, self)
            self.tv[i] = self.tv[table.name]

        # signals
        self.tv[LEFT].tableView.clicked.connect(self.show_right)
        self.tv[RIGHT].tableView.clicked.connect(self.show_down)
        for tv in self.tv.values():
            tv.tableModel.validationFailed.connect(
                lambda idx, err, tv=tv:
                self.show_validation_error(tv, idx, err))

        # hide primary key columns
        self.tv[RIGHT].tableView.hideColumn(0)
        self.tv[DOWN].tableView.hideColumn(0)
        self.tv[DOWN].tableView.hideColumn(1)

    def getdefault(self, table):
        # return the primary key tuple partially filled, depending on
        # the currently selected rows
        ordinal = table.ordinal
        if not ordinal:  # top left table
            return []
        return self.tv[ordinal - 1].current_record()[:ordinal]

    def plot(self, records, x_field, y_field, label):
        can_plot = Figure and records
        if can_plot:
            xs = [rec[x_field] for rec in records]
            ys = [rec[y_field] for rec in records]
            self.axes.clear()
            self.axes.grid(True)
            self.axes.plot(xs, ys, label=label)
            self.axes.legend(loc='upper left')
            self.canvas.draw()

    def reset_plot(self):
        if Figure:
            self.axes.clear()
            self.axes.grid(True)
            self.canvas.draw()

    def setupUi(self):
        layout = QtGui.QVBoxLayout()
        hlayout1 = QtGui.QHBoxLayout()
        hlayout2 = QtGui.QHBoxLayout()
        layout.addWidget(self.message_bar)
        hlayout1.addWidget(self.tv[LEFT])
        hlayout1.addWidget(self.tv[RIGHT])
        layout.addLayout(hlayout1)
        hlayout2.addWidget(self.tv[DOWN])
        if Figure:  # matplotlib is available
            self.fig = Figure()
            self.axes = self.fig.add_subplot(111)
            self.canvas = FigureCanvasQTAgg(self.fig)
            self.canvas.setParent(self)
            hlayout2.addWidget(self.canvas)
        layout.addLayout(hlayout2)
        self.setLayout(layout)
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)

        # display table 1 and table 2 as if rows 0 and 0 where selected
        self.show_right(index(0, 0))
        self.show_down(index(0, 0))

    @QtCore.pyqtSlot(QtCore.QModelIndex, Exception)
    def show_validation_error(self, table_view, index, error):
        record = table_view.tableModel.table[index.row()]
        fieldname = record.fields[index.column()].name
        message = '%s: %s' % (fieldname, error)
        self.message_bar.show_message(message)

    def show_right(self, index):
        try:
            k0, = self.tv[LEFT].tableModel.primaryKey(index)
        except IndexError:  # empty table, nothing to show
            return
        # show only the rows in table 1 corresponding to k0
        self.tv[RIGHT].showOnCondition(lambda rec: rec[0] == k0)
        # table 2 must disappear because no index in table 1 is selected
        self.tv[DOWN].showOnCondition(lambda rec: False)
        self.reset_plot()

    def show_down(self, index):
        # show only the rows in table 2 corresponding to k0 and k1
        try:
            k0, k1 = self.tv[RIGHT].tableModel.primaryKey(index)
        except IndexError:  # empty table, nothing to show
            return
        self.tv[DOWN].showOnCondition(
            lambda rec: rec[0] == k0 and rec[1] == k1)
        self.plot([rec for rec in self.tableset.tables[2]
                   if rec[0] == k0 and rec[1] == k1],
                  'IML', 'lossRatio', '%s-%s' % (k0, k1))


# NB: the names of the widgets are related to the names of the Converter
# subclasses in openquake.common.converter

class VulnerabilityWidget(TripleTableWidget):
    table_attrs = collections.OrderedDict(
        tableDiscreteVulnerabilitySet={'addBtn': 1, 'delBtn': 1},
        tableDiscreteVulnerability={'addBtn': 1, 'delBtn': 1},
        tableDiscreteVulnerabilityData={'addBtn': 1, 'delBtn': 1},
    )


class FragilityWidget(TripleTableWidget):

    def show_right(self, index):
        self.tv[DOWN].showOnCondition(lambda rec: False)
        self.reset_plot()
        self.index_tv0 = index

    def show_down(self, index):
        # show only the rows in table 2 corresponding to k0 and k1
        try:
            # limit state
            ls, = self.tv[LEFT].tableModel.primaryKey(
                self.index_tv0)
            fi, = self.tv[RIGHT].tableModel.primaryKey(
                index)  #
        except IndexError:  # empty table, nothing to show
            return
        self.tv[DOWN].showOnCondition(
            lambda rec: rec[0] == ls and rec[1] == fi)
        self.plot_([rec for rec in self.tableset.tables[DOWN]
                   if rec[0] == ls and rec[1] == fi],
                   '%s-%s' % (ls, fi), ls, fi)

    def plot_(self, records, label, ls, fi):
        self.plot(records, 'iml', 'poe', label)

    def getdefault(self, table):
        # return the primary key tuple partially filled, depending on
        # the currently selected rows
        ordinal = table.ordinal
        if ordinal in (0, 1):  # top tables
            return []
        limit_state = self.tv[LEFT].current_record()[0]
        ffs_ordinal = self.tv[RIGHT].current_record()[0]
        return [limit_state, ffs_ordinal]


class FragilityDiscreteWidget(FragilityWidget):
    def __init__(self, tableset, nrmlfile, parent=None):
        tset = TableSet(tableset.convertertype,
                        [tableset.tableFFLimitStateDiscrete,
                         tableset.tableFFSetDiscrete,
                         tableset.tableFFDataDiscrete])
        TripleTableWidget.__init__(self, tset, nrmlfile, parent)
        self.index_tv0 = 0


class FragilityContinuousWidget(FragilityWidget):
    def __init__(self, tableset, nrmlfile, parent=None):
        tset = TableSet(tableset.convertertype,
                        [tableset.tableFFLimitStateContinuous,
                         tableset.tableFFSetContinuous,
                         tableset.tableFFDataContinuous])
        TripleTableWidget.__init__(self, tset, nrmlfile, parent)
        type_idx = tableset.tableFFSetContinuous.recordtype.get_field_index(
            'type')
        self.tv['tableFFSetContinuous'].tableView.hideColumn(type_idx)

    def plot_(self, records, label, ls, fi):
        mean = records[0].value
        stddev = records[1].value
        ffc = self.tableset.tableFFSetContinuous[int(fi) - 1]
        x_range = linspace(ffc.minIML,
                           ffc.maxIML, num=100)
        y_range = LogNormalDistribution().survival(x_range, mean, stddev)
        points = [dict(x=x, y=y) for x, y in zip(x_range, y_range)]
        self.plot(points, 'x', 'y', label)


# the exposure tableset contains 6 tables:
# Exposure, CostType, Location, Asset, Cost, Occupancy
class ExposureWidget(QtGui.QWidget):
    table_attrs = [
        {'addBtn': 0, 'delBtn': 0, 'viewclass': CustomTableView},
        {'addBtn': 1, 'delBtn': 1, 'viewclass': CustomTableView},
        {'addBtn': 1, 'delBtn': 1, 'viewclass': CustomTableView},
        {'addBtn': 1, 'delBtn': 1, 'viewclass': CustomTableView},
        {'addBtn': 1, 'delBtn': 1, 'viewclass': CustomTableView},
        {'addBtn': 1, 'delBtn': 1, 'viewclass': CustomTableView},
    ]

    def __init__(self, tableset, nrmlfile, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tableset = tableset
        self.nrmlfile = nrmlfile
        self.message_bar = MessageBar(nrmlfile, self)
        self.tables = [tableset.tableExposure,
                       tableset.tableCostType,
                       tableset.tableLocation,
                       tableset.tableAsset,
                       tableset.tableCost,
                       tableset.tableOccupancy]
        self.tv = collections.OrderedDict()
        for table, attr in zip(self.tables, self.table_attrs):
            table.attr.update(attr)
            tv = attr['viewclass'](table, self.getdefault)
            if len(table) == 0:  # hide empty tables
                tv.hide()
            tv.tableModel.validationFailed.connect(
                lambda idx, err, tv=tv:
                self.show_validation_error(tv, idx, err))
            self.tv[table.name] = tv
        self.setupUi()

        self.tv['tableLocation'].tableView.clicked.connect(
            self.show_asset)
        self.tv['tableAsset'].tableView.clicked.connect(
            self.show_cost_occupancy)

    def setupUi(self):
        layout = QtGui.QVBoxLayout()
        hlayout1 = QtGui.QHBoxLayout()
        hlayout2 = QtGui.QHBoxLayout()
        layout.addWidget(self.message_bar)
        hlayout1.addWidget(self.tv['tableExposure'])
        hlayout1.addWidget(self.tv['tableCostType'])
        hlayout1.addWidget(self.tv['tableLocation'])
        layout.addLayout(hlayout1)
        hlayout2.addWidget(self.tv['tableAsset'])
        hlayout2.addWidget(self.tv['tableCost'])
        hlayout2.addWidget(self.tv['tableOccupancy'])
        layout.addLayout(hlayout2)
        self.setLayout(layout)
        self.setSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)

        self.tv['tableAsset'].tableView.hideColumn(0)
        self.tv['tableCost'].tableView.hideColumn(0)
        self.tv['tableOccupancy'].tableView.hideColumn(0)
        self.tv['tableLocation'].tableView.hideColumn(0)

        self.show_asset(index(0, 0))
        self.show_cost_occupancy(index(0, 0))

    @QtCore.pyqtSlot(QtCore.QModelIndex, Exception)
    def show_validation_error(self, table_view, index, error):
        record = table_view.tableModel.table[index.row()]
        fieldname = record.fields[index.column()].name
        message = '%s: %s' % (fieldname, error)
        self.message_bar.show_message(message)

    def show_asset(self, row):
        # show only the assets at the given location
        try:
            loc_id, = self.tv['tableLocation'].tableModel.primaryKey(row)
        except IndexError:  # empty table, nothing to show
            return
        self.tv['tableAsset'].showOnCondition(
            lambda rec: rec['location_id'] == loc_id)

        # reset Cost and Occupancy
        self.tv['tableCost'].showOnCondition(lambda rec: False)
        self.tv['tableOccupancy'].showOnCondition(lambda rec: False)

    def show_cost_occupancy(self, row):
        try:
            asset_ref, = self.tv['tableAsset'].tableModel.primaryKey(row)
        except IndexError:  # empty table, nothing to show
            return
        # show only the rows corresponding to asset_ref
        self.tv['tableCost'].showOnCondition(
            lambda rec: rec['asset_ref'] == asset_ref)
        # show only the rows corresponding to asset_ref
        self.tv['tableOccupancy'].showOnCondition(
            lambda rec: rec['asset_ref'] == asset_ref)

    def getdefault(self, table):
        if table.name == 'tableAsset':
            return self.tv['tableLocation'].current_record()[:1]
        elif table.name in ('tableCost', 'tableOccupancy'):
            return [self.tv['tableAsset'].current_record()[1]]
        else:
            return []
