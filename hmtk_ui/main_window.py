import numpy

# XXX the order of imports is important for pylint
from PyQt4 import QtGui
from PyQt4.QtCore import (QObject, SIGNAL, Qt, QString, pyqtSlot)

from qgis.core import QgsVectorFileWriter
from qgis.gui import QgsMapToolPan, QgsMapToolZoom

from hmtkwindow import Ui_HMTKWindow

from utils import alert
from catalogue_model import CatalogueModel
from catalogue_map import CatalogueMap


class MainWindow(QtGui.QMainWindow, Ui_HMTKWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.catalogue_model = None
        self.catalogue_map = None

        self.toolZoomIn = None
        self.toolZoomOut = None
        self.toolPan = None

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        # custom slots connections
        self.setupActions()

    def setupUi(self, _window):
        super(MainWindow, self).setupUi(self)

        # setup toolbar
        self.mapWidget.setCanvasColor(Qt.white)
        self.mapWidget.enableAntiAliasing(True)
        self.mapWidget.show()

        actionZoomIn = QtGui.QAction(QString("Zoom in"), self)
        actionZoomOut = QtGui.QAction(QString("Zoom out"), self)
        actionPan = QtGui.QAction(QString("Pan"), self)
        actionZoomIn.setCheckable(True)
        actionZoomOut.setCheckable(True)
        actionPan.setCheckable(True)

        actionZoomIn.triggered.connect(
            lambda: self.mapWidget.setMapTool(self.toolZoomIn))
        actionZoomOut.triggered.connect(
            lambda: self.mapWidget.setMapTool(self.toolZoomOut))
        actionPan.triggered.connect(
            lambda: self.mapWidget.setMapTool(self.toolPan))
        self.toolBar.addAction(actionZoomIn)
        self.toolBar.addAction(actionZoomOut)
        self.toolBar.addAction(actionPan)

        # create the map tools
        self.toolPan = QgsMapToolPan(self.mapWidget)
        self.toolPan.setAction(actionPan)
        # false = in
        self.toolZoomIn = QgsMapToolZoom(self.mapWidget, False)
        self.toolZoomIn.setAction(actionZoomIn)
        # true = out
        self.toolZoomOut = QgsMapToolZoom(self.mapWidget, True)
        self.toolZoomOut.setAction(actionZoomOut)

    @pyqtSlot(name='on_actionLoad_catalogue_triggered')
    def load_catalogue(self):
        self.catalogue_model = CatalogueModel.from_csv_file(
            QtGui.QFileDialog.getOpenFileName(
                self, 'Open Catalogue', ''), self)
        self.outputTableView.setModel(self.catalogue_model.item_model)
        if self.catalogue_map is None:
            self.catalogue_map = CatalogueMap(
                self.mapWidget, self.catalogue_model)
        else:
            self.catalogue_map.change_catalogue_model(self.catalogue_model)

        self.completenessChart.axes.hist(
            self.catalogue_model.catalogue.data['magnitude'])
        self.completenessChart.axes.set_xlabel(
            'Magnitude', dict(fontsize=13))
        self.completenessChart.axes.set_ylabel(
            'Occurrences', dict(fontsize=13))
        self.completenessChart.draw()

        self.declusteringChart.axes.plot(
            self.catalogue_model.catalogue.get_decimal_time(),
            self.catalogue_model.catalogue.data['magnitude'])
        self.declusteringChart.axes.set_xlabel(
            'Time', dict(fontsize=13))
        self.declusteringChart.axes.set_ylabel(
            'Magnitude', dict(fontsize=13))
        self.declusteringChart.draw()

    def setupActions(self):
        # menu actions
        self.actionDeclustering.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(0))
        self.actionCompleteness.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(1))
        self.actionRecurrenceModel.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(2))
        self.actionMaximumMagnitude.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(3))
        self.actionSmoothedSeismicity.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(4))

        # menu export actions
        filters_formats = QgsVectorFileWriter.supportedFiltersAndFormats()
        for flt, fmt in filters_formats.items():
            action = QtGui.QAction(self)
            action.setText(
                QtGui.QApplication.translate(
                    "HMTKWindow", fmt, None, QtGui.QApplication.UnicodeUTF8))
            self.menuExport.addAction(action)
            action.triggered.connect(self.save_as(flt, fmt))

        # table view actions
        QObject.connect(
            self.outputTableView,
            SIGNAL("clicked(QModelIndex)"), self.cellClicked)

    def save_as(self, flt, fmt):
        def wrapped():
            QgsVectorFileWriter.writeAsVectorFormat(
                self.mapWidget.layer(0),
                QtGui.QFileDialog.getSaveFileName(
                    self, "Save Layer", "", flt),
                "CP1250", None, fmt)
        return wrapped

    @pyqtSlot(name="on_actionSave_catalogue_triggered")
    def save_catalogue(self):
        self.catalogue_model.save(
            QtGui.QFileDialog.getSaveFileName(
                self, "Save Catalogue", "", "*.csv"))

    @pyqtSlot(name="on_declusterButton_clicked")
    def decluster(self):
        if self.catalogue_model is None:
            alert("Load a catalogue before starting using the "
                  "seismicity tools")

        self.catalogue_model.decluster(
            self.declusteringMethodComboBox.currentIndex(),
            self.declusteringTimeWindowFunctionCombo.currentIndex(),
            self.declusteringTimeWindowInput.text())

        self.catalogue_map.update_catalogue_layer(
            ['Cluster_Index', 'Cluster_Flag'])

    @pyqtSlot(name="on_declusteringPurgeButton_clicked")
    def purge_decluster(self):
        if self.catalogue_model is None:
            alert("Load a catalogue before starting using the "
                  "seismicity tools")

        self.catalogue_model.decluster(
            self.declusteringMethodComboBox.currentIndex(),
            self.declusteringTimeWindowFunctionCombo.currentIndex(),
            self.declusteringTimeWindowInput.text())

        self.catalogue_model.purge_decluster()

        self.outputTableView.setModel(self.catalogue_model.item_model)
        self.catalogue_map.change_catalogue_model(
            self.catalogue_model)

    @pyqtSlot(name="on_completenessButton_triggered")
    def completeness(self):
        if self.catalogue_model is None:
            alert("Load a catalogue before starting using the "
                  "seismicity tools")

        model = self.catalogue_model.completeness(
            self.completenessMagnitudeBinInput.text(),
            self.completenessTimeBinInput.text(),
            self.completenessIncrementLockInput.currentIndex())

        if model is None:
            return

        self.catalogue_map.update_catalogue_layer(['Completeness_Flag'])

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
            self.completenessChart.axes.loglog(
                model.time_values, model.sigma[:, iloc],
                linestyle='None', marker=marker_vals[iloc],
                color=rgb_list[iloc])

        self.completenessChart.axes.legend(legend_list)
        # Plot expected Poisson rate
        for iloc in range(0, len(model.magnitude_bin) - 1):
            self.completenessChart.axes.loglog(
                model.time_values, model.model_line[:, iloc],
                linestyle='-', marker='None', color=rgb_list[iloc])
            xmarker = model.end_year - model.completeness_table[iloc, 0]
            id0 = model.model_line[:, iloc] > 0.
            ymarker = 10.0 ** numpy.interp(
                numpy.log10(xmarker), numpy.log10(model.time_values[id0]),
                numpy.log10(model.model_line[id0, iloc]))
            self.completenessChart.axes.loglog(xmarker, ymarker, 'ks')
        self.completenessChart.axes.set_xlabel('Time (years)',
                                               dict(fontsize=13))
        self.completenessChart.axes.set_ylabel(
            '$\sigma_{\lambda} = \sqrt{\lambda} / \sqrt{T}$', dict(fontsize=13))
        self.completenessChart.draw()

    def cellClicked(self, modelIndex):
        catalogue = self.catalogue_model.catalogue

        if self.catalogue_model.field_idx(
                'Cluster_Index') == modelIndex.column():
            # user clicked on the column with cluster data
            cluster = int(float(self.catalogue_model.at(modelIndex)))
            if not cluster or not catalogue.data['Cluster_Index'].any():
                print "no cluster to select"
                return
            self.catalogue_map.filter('Cluster_Index', cluster)
        elif self.catalogue_model.field_idx(
                'Cluster_Flag') == modelIndex.column():
            # user clicked on the column with cluster flags
            if not catalogue.data['Cluster_Flag'].any():
                print "catalogue not declustered"
                return
            self.catalogue_map.filter(
                'Cluster_Flag',
                int(float(self.catalogue_model.at(modelIndex))))
        else:
            self.catalogue_map.select(
                self.catalogue_model.event_at(modelIndex))
