from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL, Qt, pyqtSlot

from qgis.core import QgsVectorFileWriter
from qgis.gui import QgsMapToolPan, QgsMapToolZoom, QgsMapToolEmitPoint

from hmtkwindow import Ui_HMTKWindow

from hmtk.seismicity import (
    DECLUSTERER_METHODS, COMPLETENESS_METHODS, OCCURRENCE_METHODS,
    MAX_MAGNITUDE_METHODS, SMOOTHED_SEISMICITY_METHODS)


from utils import alert
from tab import Tab
from catalogue_model import CatalogueModel
from catalogue_map import CatalogueMap
from widgets import CompletenessDialog


class MainWindow(QtGui.QMainWindow, Ui_HMTKWindow):
    """
    :attr catalogue_model:
        a CatalogueModel instance holding the catalogue model (
        events, completeness, model for supporting tables)
    :attr catalogue_map:
        a CatalogueMap (which holds the state of the map)

    :attr tabs:
        a set of `Tab` instances
    """

    def __init__(self):
        super(MainWindow, self).__init__()

        self.catalogue_model = None
        self.catalogue_map = None

        # to be set in setupUi
        self.tabs = None

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        # custom slots connections
        self.setupActions()

    def setupUi(self, _):
        super(MainWindow, self).setupUi(self)

        # setup dynamic forms
        self.tabs = (
            Tab("declustering",
                self.declusteringFormLayout,
                DECLUSTERER_METHODS,
                [self.declusterButton, self.declusteringPurgeButton]),
            Tab("completeness",
                self.completenessFormLayout,
                COMPLETENESS_METHODS,
                [self.completenessButton, self.completenessPurgeButton]),
            Tab("recurrence_model",
                self.recurrenceModelFormLayout,
                OCCURRENCE_METHODS,
                [self.recurrenceModelButton]),
            Tab("max_magnitude",
                self.maxMagnitudeFormLayout,
                MAX_MAGNITUDE_METHODS,
                [self.maxMagnitudeButton]),
            Tab("smoothed_seismicity",
                self.smoothedSeismicityFormLayout,
                SMOOTHED_SEISMICITY_METHODS,
                [self.smoothedSeismicityButton]))

        for tab in self.tabs:
            tab.setup_form(self.on_method_select)

        # setup Map
        self.mapWidget.setCanvasColor(Qt.white)
        self.mapWidget.enableAntiAliasing(True)
        self.mapWidget.show()

        # setup toolbar
        group = QtGui.QActionGroup(self)
        actionZoomIn = QtGui.QAction("Zoom in", group)
        actionZoomOut = QtGui.QAction("Zoom out", group)
        actionPan = QtGui.QAction("Pan", group)
        actionIdentify = QtGui.QAction("Info", group)
        actionZoomIn.setCheckable(True)
        actionZoomOut.setCheckable(True)
        actionPan.setCheckable(True)
        actionIdentify.setCheckable(True)

        # create the map tools
        toolPan = QgsMapToolPan(self.mapWidget)
        toolPan.setAction(actionPan)
        # false = in
        toolZoomIn = QgsMapToolZoom(self.mapWidget, False)
        toolZoomIn.setAction(actionZoomIn)
        # true = out
        toolZoomOut = QgsMapToolZoom(self.mapWidget, True)
        toolZoomOut.setAction(actionZoomOut)

        toolIdentify = QgsMapToolEmitPoint(self.mapWidget)
        toolIdentify.setAction(actionIdentify)
        toolIdentify.canvasClicked.connect(
            lambda point, button: self.catalogue_map.show_tip(point))

        actionZoomIn.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolZoomIn))
        actionZoomOut.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolZoomOut))
        actionPan.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolPan))
        actionIdentify.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolIdentify))

        self.toolBar.addAction(actionZoomIn)
        self.toolBar.addAction(actionZoomOut)
        self.toolBar.addAction(actionPan)
        self.toolBar.addAction(actionIdentify)

    def current_tab(self):
        """
        :returns: the current `Tab` selected
        """
        return self.tabs[self.stackedFormWidget.currentIndex()]

    def on_method_select(self, index):
        """
        When a method is selected we: show/Hide action `buttons`;
        update the form for the tab `name` with the method fields

        :param int index: the ordinal of the method selected
        """
        tab = self.current_tab()

        if not index:
            tab.hide_action_buttons()
            tab.clear_form()
        else:
            tab.show_action_buttons()
            tab.update_form(
                self.catalogue_model.catalogue,
                self.on_completeness_select)

    def on_completeness_select(self, index):
        """
        Select Completeness table callback
        """
        # Use the whole catalogue
        if index == 0:
            self.catalogue_model.completeness_table = (
                self.catalogue_model.default_completeness(
                    self.catalogue_model.catalogue))

        # Use the computed one in the completeness table
        elif index == 1:
            self.catalogue_model.completeness_table = (
                self.catalogue_model.last_computed_completeness_table)

        # Input a completeness table based on a completeness threshold
        elif index == 2:
            threshold, ok = QtGui.QInputDialog.getDouble(
                self, 'Input Dialog', 'Enter the threshold value:')
            if ok:
                self.catalogue_model.completeness_table = (
                    self.catalogue_model.completeness_from_threshold(
                        threshold))
        # Input a custom completeness table by opening a table editor
        elif index == 3:
            dlg = CompletenessDialog()
            if dlg.exec_():
                self.catalogue_model.completeness_table = dlg.get_table()

    @pyqtSlot(name='on_actionLoad_catalogue_triggered')
    def load_catalogue(self):
        """
        Open a file dialog, load a catalogue from a csv file,
        setup the maps and the charts
        """
        self.catalogue_model = CatalogueModel.from_csv_file(
            QtGui.QFileDialog.getOpenFileName(self, 'Open Catalogue', ''))
        self.outputTableView.setModel(self.catalogue_model.item_model)
        if self.catalogue_map is None:
            self.catalogue_map = CatalogueMap(
                self.mapWidget, self.catalogue_model)
        else:
            self.catalogue_map.change_catalogue_model(self.catalogue_model)

        self.declusteringChart.draw_occurrences(self.catalogue_model.catalogue)
        self.completenessChart.draw_timeline(self.catalogue_model.catalogue)
        self.recurrenceModelChart.draw_seismicity_rate(
            self.catalogue_model.catalogue, None)

    def setupActions(self):
        """
        Connect menu, table and form actions to the proper slots
        """
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
        """
        :returns:
            a callback function to be used as an action for save menu item
        """
        def wrapped():
            QgsVectorFileWriter.writeAsVectorFormat(
                self.mapWidget.layer(0),
                QtGui.QFileDialog.getSaveFileName(
                    self, "Save Layer", "", flt),
                "CP1250", None, fmt)
        return wrapped

    @pyqtSlot(name="on_actionSave_catalogue_triggered")
    def save_catalogue(self):
        """
        Open a file dialog to save the current catalogue in csv format
        """
        self.catalogue_model.save(
            QtGui.QFileDialog.getSaveFileName(
                self, "Save Catalogue", "", "*.csv"))

    def _apply_method(self, name):
        method = self.current_tab().method()
        try:
            config = self.current_tab().get_config()
        except ValueError as e:
            alert(str(e))
            return
        return getattr(self.catalogue_model, name)(method, config)

    @pyqtSlot(name="on_declusterButton_clicked")
    def decluster(self):
        """
        Apply current selected declustering algorithm, then update the
        map
        """
        success = self._apply_method("declustering")
        self.outputTableView.setModel(self.catalogue_model.item_model)
        self.catalogue_map.update_catalogue_layer(
            ['Cluster_Index', 'Cluster_Flag'])

        # TODO. compute a new catalogue and draw new occurrences

        return success

    @pyqtSlot(name="on_declusteringPurgeButton_clicked")
    def purge_decluster(self):
        """
        Apply current selected declustering algorithm and purge the
        catalogue. Update the map, the table and the charts
        """
        if self.decluster():
            self.catalogue_model.purge_decluster()

            self.outputTableView.setModel(self.catalogue_model.item_model)
            self.catalogue_map.change_catalogue_model(self.catalogue_model)
            self.declusteringChart.draw_occurrences(
                self.catalogue_model.catalogue)
            self.completenessChart.draw_timeline(
                self.catalogue_model.catalogue)

    @pyqtSlot(name="on_completenessPurgeButton_clicked")
    def purge_completeness(self):
        """
        Apply current selected completeness algorithm and purge the
        catalogue. Update the map, the table and the charts
        """
        if self.completeness():
            self.catalogue_model.purge_completeness()
            self.outputTableView.setModel(self.catalogue_model.item_model)
            self.catalogue_map.change_catalogue_model(self.catalogue_model)
            self.declusteringChart.draw_occurrences(
                self.catalogue_model.catalogue)
            self.completenessChart.draw_timeline(
                self.catalogue_model.catalogue)

    @pyqtSlot(name="on_completenessButton_clicked")
    def completeness(self):
        """
        Apply current selected completeness algorithm, then update the
        map and the chart if needed
        """
        model = self._apply_method("completeness")

        if model is not None:
            self.catalogue_map.update_catalogue_layer(['Completeness_Flag'])
            self.completenessChart.draw_completeness(model)
            return True

    @pyqtSlot(name="on_recurrenceModelButton_clicked")
    def recurrence_model(self):
        """
        Apply the selected method for recurrence model analysis, open
        a popup with the returned values, and draw the results in a
        chart
        """
        params = self._apply_method("recurrence_model")
        alert(str(params))

        if len(params) == 5:
            self.recurrenceModelChart.draw_seismicity_rate(
                self.catalogue_model.catalogue, *params)

    @pyqtSlot(name="on_maxMagnitudeButton_clicked")
    def max_magnitude(self):
        """
        Apply the selected method for maximum magnitude estimation, open
        a popup with the returned values
        """

        mmax_params = self._apply_method("max_magnitude")
        alert(str(mmax_params))

    @pyqtSlot(name="on_smoothedSeismicityButton_clicked")
    def smoothed_seismicity(self):
        """
        Apply the smoothing kernel selected method and update the map
        accordingly
        """
        smoothed_matrix = self._apply_method("smoothed_seismicity")
        self.catalogue_map.set_raster(smoothed_matrix)

    def cellClicked(self, modelIndex):
        """
        Callback when a cell in the catalogue table is clicked.

        if the selected cell identifies a cluster (i.e. the selected
        cell is in the column "Cluster_Index"), then we filter the map
        such that only the features of that cluster are visible.

        if the selected cell identifies a cluster flag (i.e. the
        selected cell is in the column "Cluster_Flag"), then we filter
        the map such that only the features with that flag are visible.

        Otherwise, we filter the map by showing only the selected
        feature at cell row
        """
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
