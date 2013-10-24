import collections
import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSlot

from qgis.core import QgsVectorFileWriter
from qgis.gui import (
    QgsMapToolPan, QgsMapToolZoom, QgsMapToolEmitPoint, QgsMessageBar)

from hmtkwindow import Ui_HMTKWindow

from hmtk.seismicity import (
    DECLUSTERER_METHODS, COMPLETENESS_METHODS, OCCURRENCE_METHODS,
    MAX_MAGNITUDE_METHODS, SMOOTHED_SEISMICITY_METHODS)
from hmtk.seismicity.catalogue import Catalogue

from openquake.nrmllib.hazard.parsers import SourceModelParser


from histogram import CATALOGUE_ANALYSIS_METHODS
from utils import alert
from tab import Tab
from selectors import SELECTORS, Invert
from catalogue_model import CatalogueModel
from catalogue_map import CatalogueMap
from widgets import CompletenessDialog, wait_cursor, SelectionDialog


class MainWindow(QtGui.QMainWindow, Ui_HMTKWindow):
    """
    :attr catalogue_model:
        a CatalogueModel instance holding the catalogue model (
        events, completeness, model for supporting tables)
    :attr catalogue_map:
        a CatalogueMap (which holds the state of the map)
    :attr list states:
        a stack of CatalogueModel instances used for undoing application
        state changes

    :attr QtDialog selection_editor:
        a dialog with the selection tools
    :attr list tabs:
        a set of `Tab` instances
    """

    def __init__(self):
        super(MainWindow, self).__init__()

        self.catalogue_model = None
        self.catalogue_map = None

        self.states = []

        # to be set in setupUi
        self.tabs = None
        self.selection_editor = None

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        # bind menu actions
        self.setup_actions()

    def push_state(self, state):
        if not self.states:
            self.actionUndo.setEnabled(True)
        self.states.append(state)

    def undo(self):
        if self.states:
            self.change_model(self.states.pop())

            if not self.states:
                self.actionUndo.setDisabled(True)

    def setupUi(self, _):
        """
        Add to the UI the following elements:

        1) the selection editor
        2) the tabs with the dynamic forms
        3) the map
        4) the toolbar with the map tools
        """
        super(MainWindow, self).setupUi(self)

        self.selection_editor = SelectionDialog(self)
        self.actionUndo.setDisabled(True)

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
                [self.smoothedSeismicityButton]),
            Tab("histogram",
                self.catalogueAnalysisFormLayout,
                CATALOGUE_ANALYSIS_METHODS,
                [self.catalogueAnalysisButton]))

        for tab in self.tabs:
            tab.setup_form(self.on_algorithm_select)
        self.stackedFormWidget.currentChanged.connect(self.change_tab)

        # setup Map
        self.mapWidget.setCanvasColor(Qt.white)
        self.mapWidget.enableAntiAliasing(True)
        self.mapWidget.show()
        #self.message_bar = QgsMessageBar(self.centralWidget)
        #self.outputVerticalLayout.insertWidget(0, self.message_bar)

        # setup toolbar
        group = QtGui.QActionGroup(self)
        group.addAction(self.actionZoomIn)
        group.addAction(self.actionZoomOut)
        group.addAction(self.actionPan)
        group.addAction(self.actionIdentify)

        # create the map tools
        toolPan = QgsMapToolPan(self.mapWidget)
        toolPan.setAction(self.actionPan)
        # false = in
        toolZoomIn = QgsMapToolZoom(self.mapWidget, False)
        toolZoomIn.setAction(self.actionZoomIn)
        # true = out
        toolZoomOut = QgsMapToolZoom(self.mapWidget, True)
        toolZoomOut.setAction(self.actionZoomOut)

        toolIdentify = QgsMapToolEmitPoint(self.mapWidget)
        toolIdentify.setAction(self.actionIdentify)
        toolIdentify.canvasClicked.connect(
            lambda point, button: self.catalogue_map.show_tip(point))

        self.actionZoomIn.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolZoomIn))
        self.actionZoomOut.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolZoomOut))
        self.actionPan.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolPan))
        self.actionIdentify.triggered.connect(
            lambda: self.mapWidget.setMapTool(toolIdentify))

        self.mapWidget.setMapTool(toolPan)

        self.stackedFormWidget.setCurrentIndex(0)

    def current_tab(self):
        """
        :returns: the current `Tab` selected
        """
        return self.tabs[self.stackedFormWidget.currentIndex()]

    # TODO: refactor. Use signal algorithmChanged
    def on_algorithm_select(self, index):
        """
        When a algorithm is selected we: show/Hide action `buttons`;
        update the form for the tab `name` with the algorithm fields

        :param int index: the ordinal of the algorithm selected
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

    # TODO. use signal changeCompletenessMethod
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

    def load_catalogue(self):
        """
        Open a file dialog, load a catalogue from a csv file,
        setup the maps and the charts
        """
        csv_file = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Catalogue', '')

        if not csv_file:
            return

        self.change_model(CatalogueModel.from_csv_file(csv_file))

    # FIXME. all the behaviors below should be handled with signals
    # TODO. Move this into a new singleton "Project" class
    @wait_cursor
    def change_model(self, model):
        if self.catalogue_model:
            self.push_state(self.catalogue_model)
        self.catalogue_model = model
        self.catalogueTableView.catalogue_model = model
        self.catalogueTableView.setModel(self.catalogue_model.item_model)
        if self.catalogue_map is None:
            self.catalogue_map = CatalogueMap(
                self.mapWidget, self.catalogue_model)
            self.actionCatalogueToggleLabels.triggered.connect(
                self.catalogue_map.toggle_catalogue_labels)
            self.actionSourcesToggleLabels.triggered.connect(
                self.catalogue_map.toggle_sources_labels)
            self.catalogueTableView.catalogue_map = self.catalogue_map
        else:
            self.catalogue_map.change_catalogue_model(self.catalogue_model)

        self.recurrenceModelChart.draw_seismicity_rate(
            self.catalogue_model.catalogue, None)

    @wait_cursor
    def load_fault_source(self, fname):
        """
        Open a file dialog, load a source model from a nrml file,
        draw the source on the map
        """
        self.catalogue_map.add_source_layers(SourceModelParser(fname).parse())

    # TODO. move to widgets.SelectionDialog
    def add_to_selection(self, idx):
        SELECTORS[idx](self)

    # TODO. move to widgets.SelectionDialog
    def update_selection(self):
        """
        :returns: a catalogue holding the selection
        """
        initial = catalogue = self.catalogue_model.catalogue

        if not self.selection_editor.selectorList.count():
            self.catalogue_map.select([])
        else:
            for i in range(self.selection_editor.selectorList.count()):
                selector = self.selection_editor.selectorList.item(i)
                if (not self.intersect_with_selection and not
                    isinstance(selector, Invert)):
                    union_data = selector.apply(initial, initial).data
                    if initial != catalogue:
                        union_data['eventID'] = numpy.append(
                            union_data['eventID'], catalogue.data['eventID'])
                        union_data['year'] = numpy.append(
                            union_data['year'], catalogue.data['year'])
                    catalogue = Catalogue.make_from_dict(union_data)
                else:
                    catalogue = selector.apply(catalogue, initial)
            self.catalogue_map.select(catalogue.data['eventID'])

        features_num = len(
            self.catalogue_map.catalogue_layer.selectedFeatures())
        if not features_num:
            self.selection_editor.selectorSummaryLabel.setText(
                "No event selected")
        elif features_num == initial.get_number_events():
            self.selection_editor.selectorSummaryLabel.setText(
                "All events selected")
        else:
            self.selection_editor.selectorSummaryLabel.setText(
                "%d events selected" % features_num)

        return catalogue

    # TODO. move to widgets.SelectionDialog
    def remove_unselected_events(self):
        # get the selected catalogue
        catalogue = self.update_selection()

        if QtGui.QMessageBox.question(
                self, "Remove unselected events", "Are you sure?",
                QtGui.QDialogButtonBox.Yes, QtGui.QDialogButtonBox.No):
            self.change_model(CatalogueModel(catalogue))
            for _ in range(self.selection_editor.selectorList.count()):
                self.selection_editor.selectorList.takeItem(0)

    def setup_actions(self):
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
        self.actionCatalogueAnalysis.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(5))
        self.actionEventsInspector.triggered.connect(
            lambda: self.stackedFormWidget.setCurrentIndex(6))

        # menu import/export actions
        self.actionLoadCatalogue.triggered.connect(self.load_catalogue)
        self.actionSaveCatalogue.triggered.connect(self.save_catalogue)
        self.actionLoadSourceNRML.triggered.connect(
            lambda: self.load_fault_source(
                QtGui.QFileDialog.getOpenFileName(
                    self, 'Open Source Model (NRML 4)', '.xml')))

        filters_formats = QgsVectorFileWriter.supportedFiltersAndFormats()
        for flt, fmt in filters_formats.items():
            action = QtGui.QAction(self)
            action.setText(
                QtGui.QApplication.translate(
                    "HMTKWindow", fmt, None, QtGui.QApplication.UnicodeUTF8))
            self.menuExport.addAction(action)
            action.triggered.connect(self.save_as(flt, fmt))

        # Selection management
        self.actionDeleteUnselectedEvents.triggered.connect(
            self.remove_unselected_events)
        self.actionUndo.triggered.connect(self.undo)

        self.actionInvertSelection.triggered.connect(
            lambda: self.add_to_selection(0))
        self.actionWithinPolygon.triggered.connect(
            lambda: self.add_to_selection(1))
        self.actionWithinJoynerBooreSource.triggered.connect(
            lambda: self.add_to_selection(2))
        self.actionWithinRuptureDistance.triggered.connect(
            lambda: self.add_to_selection(3))
        self.actionWithinSquare.triggered.connect(
            lambda: self.add_to_selection(4))
        self.actionWithinDistance.triggered.connect(
            lambda: self.add_to_selection(5))
        self.actionTimeBetween.triggered.connect(
            lambda: self.add_to_selection(6))
        self.actionFieldBetween.triggered.connect(
            lambda: self.add_to_selection(7))
        self.actionSelectionEditor.triggered.connect(
            self.selection_editor.exec_)

        # Style actions
        self.actionCatalogueStyleByCluster.triggered.connect(
            lambda: self.catalogue_map.set_catalogue_style("cluster"))
        self.actionCatalogueStyleByDepthMagnitude.triggered.connect(
            lambda: self.catalogue_map.set_catalogue_style("depth-magnitude"))
        self.actionCatalogueStyleByCompleteness.triggered.connect(
            lambda: self.catalogue_map.set_catalogue_style("completeness"))

        self.actionLoadOSMBaseMap.triggered.connect(
            lambda: self.catalogue_map.set_osm())

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

    def save_catalogue(self):
        """
        Open a file dialog to save the current catalogue in csv format
        """
        self.catalogue_model.save(
            QtGui.QFileDialog.getSaveFileName(
                self, "Save Catalogue", "", "*.csv"))

    # XXX. Maybe move to tabs.Tab
    @wait_cursor
    def _apply_algorithm(self, name):
        algorithm = self.current_tab().algorithm()
        try:
            config = self.current_tab().get_config()
        except ValueError as e:
            alert(str(e))
            return
        return getattr(self.catalogue_model, name)(algorithm, config)

    # TODO. Remove it. Connect output widgets to signal algorithmRun
    @pyqtSlot(name="on_catalogueAnalysisButton_clicked")
    def histogram(self):
        histogram_data = self._apply_algorithm("histogram")

        self.catalogue_model.histogram_output = histogram_data

        if len(histogram_data) == 2:
            bins, histogram = histogram_data
            self.catalogueAnalysisChart.draw_1d_histogram(histogram, bins)
        elif len(histogram_data) == 3:
            x_bins, y_bins, histogram = histogram_data
            self.catalogueAnalysisChart.draw_2d_histogram(
                histogram, x_bins, y_bins)
        else:
            raise RuntimeError("Can't draw histogram %s" % histogram_data)

        self.add_histogram_output()

    @pyqtSlot(name="on_declusterButton_clicked")
    def decluster(self):
        """
        Apply current selected declustering algorithm, then update the
        map
        """
        success = self._apply_algorithm("declustering")
        self.catalogueTableView.setModel(self.catalogue_model.item_model)
        self.catalogue_map.update_catalogue_layer(
            ['Cluster_Index', 'Cluster_Flag'])
        self.add_declustering_output()
        self.catalogue_map.set_catalogue_style("cluster")
        self.declusteringChart.draw_declustering_pie(
            self.catalogue_model.catalogue.data['Cluster_Index'],
            self.catalogue_model.catalogue.data['Cluster_Flag'])
        return success

    @pyqtSlot(name="on_declusteringPurgeButton_clicked")
    def purge_decluster(self):
        """
        Apply current selected declustering algorithm and purge the
        catalogue. Update the map, the table and the charts
        """
        if self.decluster():
            self.catalogue_model.purge_decluster()

            self.catalogueTableView.setModel(self.catalogue_model.item_model)
            self.catalogue_map.change_catalogue_model(self.catalogue_model)

    @pyqtSlot(name="on_completenessPurgeButton_clicked")
    def purge_completeness(self):
        """
        Apply current selected completeness algorithm and purge the
        catalogue. Update the map, the table and the charts
        """
        if self.completeness():
            self.catalogue_model.purge_completeness()
            self.catalogueTableView.setModel(self.catalogue_model.item_model)
            self.catalogue_map.change_catalogue_model(self.catalogue_model)

    @pyqtSlot(name="on_completenessButton_clicked")
    def completeness(self):
        """
        Apply current selected completeness algorithm, then update the
        map and the chart if needed
        """
        model = self._apply_algorithm("completeness")

        if model is not None:
            self.catalogue_map.update_catalogue_layer(['Completeness_Flag'])
            self.completenessChart.draw_completeness(model)
            self.add_completeness_output()
            self.catalogue_map.set_catalogue_style("completeness")
            return True

    @pyqtSlot(name="on_recurrenceModelButton_clicked")
    def recurrence_model(self):
        """
        Apply the selected algorithm for recurrence model analysis, open
        a popup with the returned values, and draw the results in a
        chart
        """
        params = self._apply_algorithm("recurrence_model")

        # the algorithm for performing recurrence model analysis returns
        # either 3 values, either 5. In the latter case we have the
        # parameter value to plot the seismicity rate chart.
        if len(params) == 5:
            self.recurrenceModelChart.draw_seismicity_rate(
                self.catalogue_model.catalogue, *params)

        self.catalogue_model.recurrence_model_output = params
        self.add_recurrence_model_output()

    @pyqtSlot(name="on_maxMagnitudeButton_clicked")
    def max_magnitude(self):
        """
        Apply the selected algorithm for maximum magnitude estimation, open
        a popup with the returned values
        """

        mmax_params = self._apply_algorithm("max_magnitude")
        self.catalogue_model.maximum_magnitude_output = mmax_params
        self.add_maximum_magnitude_output()

    @pyqtSlot(name="on_smoothedSeismicityButton_clicked")
    def smoothed_seismicity(self):
        """
        Apply the smoothing kernel selected algorithm and update the map
        accordingly
        """
        smoothed_matrix = self._apply_algorithm("smoothed_seismicity")
        self.catalogue_model.smoothed_seismicity_output = smoothed_matrix
        self.catalogue_map.set_raster(smoothed_matrix)
        self.add_smoothed_seismicity_output()

    def change_tab(self, index):
        if self.catalogue_map is None:
            return
        if index == 0:
            self.catalogue_map.set_catalogue_style("cluster")
            self.add_declustering_output()
        elif index == 1:
            self.catalogue_map.set_catalogue_style("completeness")
            self.add_completeness_output()
        elif index == 2:
            self.catalogue_map.set_catalogue_style("depth-magnitude")
            self.add_recurrence_model_output()
        elif index == 3:
            self.catalogue_map.set_catalogue_style("depth-magnitude")
            self.add_maximum_magnitude_output()
        elif index == 4:
            self.catalogue_map.set_catalogue_style("default")
            self.add_smoothed_seismicity_output()
        elif index == 5:
            self.catalogue_map.set_catalogue_style("depth-magnitude")
            self.add_histogram_output()
        else:
            self.catalogue_map.set_catalogue_style("depth-magnitude")

    def add_declustering_output(self):
        cat = self.catalogue_model.catalogue
        events = cat.load_to_array(
            ['Cluster_Index', 'Cluster_Flag', 'eventID']).astype(numpy.int32)

        clustered = events[events[:, 0] != 0]
        clusters = dict()

        Cluster = collections.namedtuple(
            'Cluster',
            'id mainshocks foreshocks aftershocks')

        for cluster_index, flag, event_id in clustered:
            if cluster_index not in clusters:
                if flag == 0:
                    cluster = Cluster(cluster_index, [event_id], [], [])
                elif flag == -1:
                    cluster = Cluster(cluster_index, [], [event_id], [])
                elif flag == 1:
                    cluster = Cluster(cluster_index, [], [], [event_id])
                else:
                    raise RuntimeError("Invalid cluster flag %s" % flag)
                clusters[cluster_index] = cluster
            else:
                cluster = clusters[cluster_index]
                if flag == 0:
                    cluster.mainshocks.append(event_id)
                elif flag == -1:
                    cluster.foreshocks.append(event_id)
                elif flag == 1:
                    cluster.aftershocks.append(event_id)
                else:
                    raise RuntimeError("Invalid cluster flag %s" % flag)

        groups = sorted(clusters.values(), key=(
            lambda cluster: sum([len(g) for g in cluster[1:]])))
        self.resultsTable.set_data(
            [[numpy.argwhere(cat.data['Cluster_Index'] != 0).size,
              numpy.argwhere(cat.data['Cluster_Index'] == 0).size,
              numpy.argwhere(cat.data['Cluster_Flag'] == -1).size,
              numpy.argwhere(cat.data['Cluster_Flag'] == 1).size]] + groups,
            ["Clusters", "Main shocks", "Foreshocks", "Aftershocks"],
            ["Totals"],
            lambda item: self.catalogue_map.center_on(
                'Cluster_Index', int(
                    self.resultsTable.item(item.row(), 0).data(0))))
        for row, (cluster_idx, _, _, _) in enumerate(groups, 1):
            self.resultsTable.item(row, 0).setData(
                Qt.ForegroundRole,
                self.catalogue_model.cluster_color(cluster_idx))

    def add_completeness_output(self):
        self.resultsTable.set_data(
            self.catalogue_model.completeness_table,
            ["Year", "Magnitude"])

    def add_histogram_output(self):
        if self.catalogue_model.histogram_output is None:
            return
        elif len(self.catalogue_model.histogram_output) == 2:
            self.resultsTable.set_data(
                zip(*self.catalogue_model.histogram_output),
                ["Bin", "Count"])
        elif len(self.catalogue_model.histogram_output) == 3:
            self.resultsTable.set_data(
                self.catalogue_model.histogram_output[2],
                [str(x)
                 for x in self.catalogue_model.histogram_output[0][:-1]],
                [str(x)
                 for x in self.catalogue_model.histogram_output[1][:-1]])
        else:
            raise RuntimeError(
                "Can't update resultsTable for %s" % (
                    self.catalogue_model.histogram_output))

    def add_recurrence_model_output(self):
        # see #recurrence_model
        if self.catalogue_model.recurrence_model_output is not None:
            if len(self.catalogue_model.recurrence_model_output) == 3:
                self.resultsTable.set_data(
                    [self.catalogue_model.recurrence_model_output[1:]],
                    ["b value", "sigma b"])
            elif len(self.catalogue_model.recurrence_model_output) == 5:
                self.resultsTable.set_data(
                    [self.catalogue_model.recurrence_model_output],
                    ["Reference Magnitude", "b value", "sigma b",
                     "rate", "sigma rate"])

    def add_maximum_magnitude_output(self):
        if self.catalogue_model.maximum_magnitude_output is not None:
            self.resultsTable.set_data(
                [self.catalogue_model.maximum_magnitude_output],
                ["Maximum Magnitude", "Standard deviation"])

    def add_smoothed_seismicity_output(self):
        if self.catalogue_model.smoothed_seismicity_output is not None:
            self.resultsTable.set_data(
                self.catalogue_model.smoothed_seismicity_output,
                ["Longitude", "Latitude", "Depth", "Observed", "Smoothed"])

    @property
    def intersect_with_selection(self):
        return self.actionIntersectWithSelection.isChecked()
