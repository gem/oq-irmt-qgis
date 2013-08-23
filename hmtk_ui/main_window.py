import csv

# XXX the order of imports is important for pylint
from PyQt4 import QtGui
from PyQt4.QtCore import (QObject, SIGNAL, Qt, QString)

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

        self.connect(actionZoomIn, SIGNAL("triggered()"),
                     lambda: self.mapWidget.setMapTool(self.toolZoomIn))
        self.connect(actionZoomOut, SIGNAL("triggered()"),
                     lambda: self.mapWidget.setMapTool(self.toolZoomOut))
        self.connect(actionPan, SIGNAL("triggered()"),
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
        self.chartWidget.axes.hist(
            self.catalogue_model.catalogue.data['magnitude'])
        self.chartWidget.draw()

    def setupActions(self):
        # menu actions
        QObject.connect(
            self.actionLoad_catalogue, SIGNAL("triggered()"),
            self.load_catalogue)
        QObject.connect(
            self.actionDeclustering, SIGNAL("triggered()"),
            lambda: self.stackedFormWidget.setCurrentIndex(0))
        QObject.connect(
            self.actionCompleteness, SIGNAL("triggered()"),
            lambda: self.stackedFormWidget.setCurrentIndex(1))
        QObject.connect(
            self.actionRecurrenceModel, SIGNAL("triggered()"),
            lambda: self.stackedFormWidget.setCurrentIndex(2))
        QObject.connect(
            self.actionMaximumMagnitude, SIGNAL("triggered()"),
            lambda: self.stackedFormWidget.setCurrentIndex(3))
        QObject.connect(
            self.actionSmoothedSeismicity, SIGNAL("triggered()"),
            lambda: self.stackedFormWidget.setCurrentIndex(4))

        # menu export actions
        filters_formats = QgsVectorFileWriter.supportedFiltersAndFormats()
        for flt, fmt in filters_formats.items():
            action = QtGui.QAction(self)
            action.setText(
                QtGui.QApplication.translate(
                    "HMTKWindow", fmt, None, QtGui.QApplication.UnicodeUTF8))
            self.menuExport.addAction(action)
            QObject.connect(
                action, SIGNAL("triggered()"),
                self.save_as(flt, fmt))

        QObject.connect(
            self.actionSave_catalogue, SIGNAL("triggered()"),
            self.save_catalogue)

        # form actions
        QObject.connect(
            self.declusterButton, SIGNAL("clicked()"),
            self.decluster)
        QObject.connect(
            self.purgeCatalogue, SIGNAL("clicked()"),
            self.purge_decluster)

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

    def save_catalogue(self):
        filename = QtGui.QFileDialog.getSaveFileName(
            self, "Save Catalogue", "", "*.csv")
        with file(filename, 'w') as f:
            writer = csv.writer(f)
            keys = ['eventID', 'longitude', 'latitude', 'depth', 'magnitude',
                    'year', 'month', 'day', 'hour', 'minute', 'second']
            writer.writerow(keys)
            for row in self.catalogue_model.catalogue.load_to_array(keys):
                writer.writerow(row)

    def decluster(self):
        if self.catalogue_model is None:
            alert("Load a catalogue before starting using the "
                  "seismicity tools")

        self.catalogue_model.decluster(
            self.methodComboBox_2.currentIndex(),
            self.timeWindowFunctionCombo.currentIndex(),
            self.TimeWindowInput.text())

        self.catalogue_map.update_catalogue_layer(
            ['Cluster_Index', 'Cluster_Flag'])

    def purge_decluster(self):
        if self.catalogue_model is None:
            alert("Load a catalogue before starting using the "
                  "seismicity tools")

        self.catalogue_model.decluster(
            self.methodComboBox_2.currentIndex(),
            self.timeWindowFunctionCombo.currentIndex(),
            self.TimeWindowInput.text())

        self.catalogue_model.purge_decluster()

        self.catalogue_map.change_catalogue_model(
            self.catalogue_model)

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
                self.catalogue_model.eventIdAt(modelIndex))
