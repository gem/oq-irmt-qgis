from decorator import decorator

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSlot

from plot_occurrence_model import GutenbergRichterModel, plotSeismicityRates
import completeness_dialog
import grid_dialog
import selection_dialog
import numpy

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from hmtk.seismicity.smoothing.smoothed_seismicity import Grid
from utils import alert


class FigureCanvasQTAggWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=4, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        FigureCanvasQTAgg.__init__(self, self.fig)
        self.setParent(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.updateGeometry()

    def get_default_filetype(self):
        return "png"

    def draw_seismicity_rate(self, catalogue, mag, *args):
        self.axes.cla()
        if mag and args:
            b_value, sigma_b, a_value, sigma_a = args
            model = GutenbergRichterModel(b_value,
                                          10 ** (a_value - b_value * mag),
                                          a_val=a_value,
                                          sigma_b=sigma_b,
                                          sigma_a=sigma_a)
        else:
            model = None
        plotSeismicityRates(catalogue).plot(self.axes, model=model)
        self.draw()

    def draw_1d_histogram(self, hist, bins):
        self.axes.cla()
        w = (bins[-1] - bins[0]) / len(bins)
        self.axes.bar(bins[:-1], hist, width=w)
        self.axes.set_xticks(bins)
        self.draw()

    def draw_2d_histogram(self, hist, x_bins, y_bins):
        self.axes.cla()
        extent = [x_bins[0], x_bins[-2], y_bins[0], y_bins[-2]]
        self.axes.imshow(
            hist.T, extent=extent, interpolation='nearest', origin='lower',
            aspect="auto")
        self.draw()

    def draw_declustering_pie(self, cluster_indexes, cluster_flags):
        self.axes.cla()
        mainshocks_mask = numpy.logical_and(
            cluster_indexes != 0, cluster_flags == 0)
        mainshocks_nr = numpy.argwhere(mainshocks_mask == 1).size
        not_clustered = numpy.argwhere(cluster_indexes == 0).size

        self.axes.pie(
            [not_clustered,
             mainshocks_nr,
             numpy.argwhere(cluster_flags == -1).size,
             numpy.argwhere(cluster_flags == 1).size],
            labels=["Unclustered", "Main shocks",
                    "Foreshocks", "Aftershocks"],
            radius=0.65)
        self.draw()

    def draw_completeness(self, model):
        self.axes.cla()
        # FIXME(lp). refactor with plot_stepp_1972.py in hmtk
        valid_markers = ['*', '+', '1', '2', '3', '4', '8', '<', '>', 'D', 'H',
                         '^', '_', 'd', 'h', 'o', 'p', 's', 'v', 'x', '|']

        legend_list = [(str(model.magnitude_bin[iloc] + 0.01) + ' - ' +
                        str(model.magnitude_bin[iloc + 1]))
                       for iloc in range(0, len(model.magnitude_bin) - 1)]
        rgb_list, marker_vals = [], []
        # Get marker from valid list
        while len(valid_markers) < len(model.magnitude_bin):
            valid_markers.append(valid_markers)
        marker_sampler = numpy.arange(0, len(valid_markers), 1)
        numpy.random.shuffle(marker_sampler)
        # Get colour for each bin
        for value in range(0, len(model.magnitude_bin) - 1):
            rgb_samp = numpy.random.uniform(0., 1., 3)
            rgb_list.append((rgb_samp[0], rgb_samp[1], rgb_samp[2]))
            marker_vals.append(valid_markers[marker_sampler[value]])
        # Plot observed Sigma lambda
        for iloc in range(0, len(model.magnitude_bin) - 1):
            self.axes.loglog(
                model.time_values, model.sigma[:, iloc],
                linestyle='None', marker=marker_vals[iloc],
                color=rgb_list[iloc])

        self.axes.legend(legend_list)
        # Plot expected Poisson rate
        for iloc in range(0, len(model.magnitude_bin) - 1):
            self.axes.loglog(
                model.time_values, model.model_line[:, iloc],
                linestyle='-', marker='None', color=rgb_list[iloc])
            xmarker = model.end_year - model.completeness_table[iloc, 0]
            id0 = model.model_line[:, iloc] > 0.
            ymarker = 10.0 ** numpy.interp(
                numpy.log10(xmarker), numpy.log10(model.time_values[id0]),
                numpy.log10(model.model_line[id0, iloc]))
            self.axes.loglog(xmarker, ymarker, 'ks')
        self.axes.set_xlabel('Time (years)', dict(fontsize=13))
        self.axes.set_ylabel(
            '$\sigma_{\lambda} = \sqrt{\lambda} / \sqrt{T}$',
            dict(fontsize=13))
        self.draw()


class GridInputWidget(QtGui.QPushButton):
    def __init__(self, catalogue, fields):
        QtGui.QPushButton.__init__(self, "Grid Editor")
        self.grid = None
        self.catalogue = catalogue
        self.fields = fields
        self.clicked.connect(self.on_click)
        self.grid_dialog = GridDialog()

    def on_click(self):
        try:
            ll = float(self.fields['Length_Limit'].widget.text())
            bw = float(self.fields['BandWidth'].widget.text())
            dilate = ll * bw
        except ValueError:
            dilate = 0

        self.grid_dialog.set_grid(
            Grid.make_from_catalogue(self.catalogue, 1, dilate))
        if self.grid_dialog.exec_():
            self.grid = self.grid_dialog.get_grid()


class CompletenessDialog(QtGui.QDialog, completeness_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(CompletenessDialog, self).__init__(parent)
        self.setupUi(self)
        self.addRowButton.clicked.connect(self.add_row)
        self.removeRowButton.clicked.connect(self.remove_row)

    def add_row(self):
        self.tableWidget.insertRow(self.tableWidget.rowCount())

    def remove_row(self):
        self.tableWidget.removeRow(self.tableWidget.currentRow())

    def get_table(self):
        table = self.tableWidget

        ret = []

        for row in range(table.rowCount()):
            data = [table.item(row, 0).data(0), table.item(row, 1).data(0)]

            if not data[0]:
                break

            ret.append([float(d) for d in data])

        if not ret:
            alert("Invalid completeness table")

        # sort by year (most recent to oldest)
        ret = sorted(ret, key=lambda row: -row[0])

        # check that magnitude is increasing
        magnitude, years = zip(*ret)
        if (len(magnitude) > 1 and
            all(x < y for x, y in zip(magnitude, magnitude[1:]))):
            alert("""Your completeness table is not properly ordered.
This might cause instability (E.g. in Weichert)""")

        return numpy.array(ret)


class GridDialog(QtGui.QDialog, grid_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(GridDialog, self).__init__(parent)
        self.setupUi(self)
        self.dilateByButton.clicked.connect(self.dilate_by)

    def dilate_by(self):
        width, ok = QtGui.QInputDialog.getDouble(
            self, 'Input Dialog', 'Dilate by:')
        if ok:
            self.set_grid(self.get_grid().dilate(width))

    def get_grid(self):
        table = self.tableWidget

        ret = []

        for row in range(table.rowCount()):
            data = [table.item(row, 0).data(0),
                    table.item(row, 1).data(0),
                    table.item(row, 2).data(0)]

            ret.extend([float(d) for d in data])

        return Grid.make_from_list(ret)

    def set_grid(self, grid):
        table = self.tableWidget

        for i in range(9):
            item = table.item(i / 3, i % 3)

            if item is None:
                item = QtGui.QTableWidgetItem()
                table.setItem(i / 3, i % 3, item)

            item.setData(0, str(grid.as_list()[i]))


class WaitCursor(object):
    def __enter__(self, *args, **kwargs):
        QtGui.QApplication.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, *args, **kwargs):
        QtGui.QApplication.restoreOverrideCursor()

    @classmethod
    def as_decorator(cls, func, *args, **kwargs):
        with cls():
            return func(*args, **kwargs)


def wait_cursor(func):
    return decorator(WaitCursor.as_decorator, func)


class SelectionDialog(QtGui.QDialog, selection_dialog.Ui_Dialog):
    def __init__(self, window=None):
        super(SelectionDialog, self).__init__(window)
        self.setupUi(self)
        self.window = window
        self.invertSelectionButton.clicked.connect(
            lambda: self.window.add_to_selection(
                self.selectorComboBox.currentIndex()))
        self.selectButton.clicked.connect(
            lambda: self.window.add_to_selection(
                self.selectorComboBox.currentIndex()))
        self.removeFromRuleListButton.clicked.connect(self.remove_selector)
        self.purgeUnselectedEventsButton.clicked.connect(
            self.window.remove_unselected_events)

    def remove_selector(self):
        for item in self.selectorList.selectedItems():
            self.selectorList.takeItem(self.selectorList.row(item))
        self.window.update_selection()


class ResultsTable(QtGui.QTableWidget):
    def __init__(self, *args, **kwargs):
        super(ResultsTable, self).__init__(*args, **kwargs)
        self.callback = None

    def set_data(self, rows, hlabels, vlabels=None, callback=None):
        if self.callback is not None:
            self.itemClicked.disconnect(self.callback)
        self.callback = callback

        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)

        for i, row in enumerate(rows):
            self.insertRow(i)

            if vlabels is not None:
                self.verticalHeader().show()
                if i < len(vlabels):
                    self.setVerticalHeaderItem(
                        i, QtGui.QTableWidgetItem(vlabels[i]))
                else:
                    self.setVerticalHeaderItem(
                        i, QtGui.QTableWidgetItem(str(i)))
            else:
                self.verticalHeader().hide()

            for j, data in enumerate(row):
                if not i:
                    self.insertColumn(j)
                    self.setHorizontalHeaderItem(
                        j, QtGui.QTableWidgetItem(hlabels[j]))
                self.setItem(i, j, QtGui.QTableWidgetItem(str(data)))
        if callback is not None:
            self.itemClicked.connect(callback)


class CatalogueView(QtGui.QTableView):
    def __init__(self, *args, **kwargs):
        super(CatalogueView, self).__init__(*args, **kwargs)
        self.catalogue_map = None
        self.catalogue_model = None
        self.clicked.connect(self.on_cell_clicked)

    @pyqtSlot("QModelIndex")
    def on_cell_clicked(self, modelIndex):
        """
        Callback when a cell in the catalogue table is clicked. Filter
        the map by showing only the selected feature at cell row.
        """
        self.catalogue_map.select([self.catalogue_model.event_at(modelIndex)])
