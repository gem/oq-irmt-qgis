import numpy

# XXX the order of imports is important for pylint
from PyQt4 import QtGui
from PyQt4.QtCore import (QObject, SIGNAL, Qt, QString, pyqtSlot)

from qgis.core import QgsVectorFileWriter
from qgis.gui import QgsMapToolPan, QgsMapToolZoom

from hmtkwindow import Ui_HMTKWindow

from hmtk.seismicity import (
    DECLUSTERER_METHODS, COMPLETENESS_METHODS, OCCURRENCE_METHODS,
    MAX_MAGNITUDE_METHODS, SMOOTHED_SEISMICITY_METHODS)


from utils import alert
from catalogue_model import CatalogueModel
from catalogue_map import CatalogueMap
from widgets import add_form, add_fields, get_config, CompletenessDialog


class MainWindow(QtGui.QMainWindow, Ui_HMTKWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.catalogue_model = None
        self.catalogue_map = None

        self.forms = {}
        self.form_fields = {}
        self.form_completeness = {}

        self.method_selectors = {}

        self.toolZoomIn = None
        self.toolZoomOut = None
        self.toolPan = None

        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        # custom slots connections
        self.setupActions()

    def setupUi(self, _):
        super(MainWindow, self).setupUi(self)

        # setup dynamic forms
        # declustering
        GROUPS = (("declustering",
                   self.declusteringGroupBox, self.declusteringFormLayout,
                   DECLUSTERER_METHODS,
                   [self.declusterButton, self.declusteringPurgeButton]),
                  ("completeness",
                   self.completenessGroupBox, self.completenessFormLayout,
                   COMPLETENESS_METHODS,
                   [self.completenessButton, self.completenessPurgeButton]),
                  ("recurrence_model",
                   self.recurrenceModelGroupBox,
                   self.recurrenceModelFormLayout,
                   OCCURRENCE_METHODS,
                   [self.recurrenceModelButton]),
                  ("max_magnitude",
                   self.maxMagnitudeGroupBox, self.maxMagnitudeFormLayout,
                   MAX_MAGNITUDE_METHODS,
                   [self.maxMagnitudeButton]),
                  ("smoothed_seismicity",
                   self.smoothedSeismicityGroupBox,
                   self.smoothedSeismicityFormLayout,
                   SMOOTHED_SEISMICITY_METHODS,
                   [self.smoothedSeismicityButton]))
        for name, box, layout, registry, buttons in GROUPS:
            form, combo_box = add_form(box, registry, "declustering")
            self.method_selectors[name] = combo_box
            combo_box.currentIndexChanged.connect(
                self.select_method_fn(buttons, name, registry))
            self.forms[name] = form
            layout.insertLayout(0, form)
            for b in buttons:
                b.hide()

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

    def select_method_fn(self, buttons, name, registry):
        def on_select(index):
            if not index:
                for b in buttons:
                    b.hide()
                return
            else:
                for b in buttons:
                    b.show()
            form = self.forms[name]
            method = registry.values()[index - 1]
            self.form_fields[name] = add_fields(
                form, self.catalogue_model.catalogue,
                name, method.fields, method.completeness)

            if 'completeness' in self.form_fields[name]:
                inp = self.form_fields[name]['completeness']
                inp.activated.connect(self.get_completeness_function(name))
        return on_select

    def get_completeness_function(self, name):
        self.form_completeness[name] = numpy.array(
            [[numpy.min(self.catalogue_model.catalogue.data['year']),
              numpy.min(self.catalogue_model.catalogue.data['magnitude'])]])

        def on_select(index):
            if index == 0:
                self.form_completeness[name] = numpy.array(
                    [[numpy.min(
                        self.catalogue_model.catalogue.data['year']),
                      numpy.min(
                          self.catalogue_model.catalogue.data['magnitude'])]])
            elif index == 1:
                if self.catalogue_model.completeness_table is None:
                    alert("""You have not computed yet a completeness table.
Go to the Completeness tab or select another option""")
                else:
                    self.form_completeness[name] = (
                        self.catalogue_model.completeness_table)
            elif index == 2:
                threshold, ok = QtGui.QInputDialog.getDouble(
                    self, 'Input Dialog', 'Enter the threshold value:')
                if ok:
                    self.form_completeness[name] = numpy.array(
                        [[numpy.min(
                            self.catalogue_model.catalogue.data['year']),
                            threshold]])
            elif index == 3:
                dlg = CompletenessDialog()
                if dlg.exec_():
                    self.form_completeness[name] = dlg.get_table()
        return on_select

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

        self.declusteringChart.draw_occurrences(self.catalogue_model.catalogue)
        self.completenessChart.draw_timeline(self.catalogue_model.catalogue)
        self.recurrenceModelChart.draw_seismicity_rate(
            self.catalogue_model.catalogue, None)

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
        method = DECLUSTERER_METHODS.values()[
            self.method_selectors['declustering'].currentIndex() - 1]
        try:
            config = get_config(
                method,
                self.catalogue_model.catalogue,
                self.form_fields["declustering"])
        except ValueError as e:
            alert(str(e))
            return
        ret = self.catalogue_model.decluster(method, config)

        self.catalogue_map.update_catalogue_layer(
            ['Cluster_Index', 'Cluster_Flag'])

        # TODO. compute a new catalogue and draw new occurrences
        self.declusteringChart.draw_occurrences(self.catalogue_model.catalogue)
        return ret

    @pyqtSlot(name="on_declusteringPurgeButton_clicked")
    def purge_decluster(self):
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
        method = COMPLETENESS_METHODS.values()[
            self.method_selectors['completeness'].currentIndex() - 1]

        try:
            config = get_config(
                method,
                self.catalogue_model.catalogue,
                self.form_fields["completeness"])
        except ValueError as e:
            alert(str(e))
            return

        model = self.catalogue_model.completeness(method, config)
        self.catalogue_map.update_catalogue_layer(['Completeness_Flag'])

        if model is not None:
            self.completenessChart.draw_completeness(model)
        return True

    @pyqtSlot(name="on_recurrenceModelButton_clicked")
    def recurrence_model(self):
        method = OCCURRENCE_METHODS.values()[
            self.method_selectors['recurrence_model'].currentIndex() - 1]

        try:
            config = get_config(method,
                                self.catalogue_model.catalogue,
                                self.form_fields["recurrence_model"])
        except ValueError as e:
            alert(str(e))
            return

        ret = method(self.catalogue_model.catalogue, config,
                     self.form_completeness["recurrence_model"])
        alert(str(ret))

        if len(ret) == 4:
            self.recurrenceModelChart.draw_seismicity_rate(
                self.catalogue_model.catalogue,
                config.get('reference_magnitude', None), *ret)

    @pyqtSlot(name="on_maxMagnitudeButton_clicked")
    def max_magnitude(self):
        method = MAX_MAGNITUDE_METHODS.values()[
            self.method_selectors['max_magnitude'].currentIndex() - 1]

        try:
            config = get_config(method,
                                self.catalogue_model.catalogue,
                                self.form_fields["max_magnitude"])
        except ValueError as e:
            alert(str(e))
            return

        ret = method(self.catalogue_model.catalogue, config)
        alert(str(ret))

    @pyqtSlot(name="on_smoothedSeismicityButton_clicked")
    def smoothed_seismicity(self):
        method = SMOOTHED_SEISMICITY_METHODS.values()[
            self.method_selectors['smoothed_seismicity'].currentIndex() - 1]

        try:
            config = get_config(
                method,
                self.catalogue_model.catalogue,
                self.form_fields["smoothed_seismicity"])
        except ValueError as e:
            alert(str(e))
            return

        print self.catalogue_model.catalogue.data, config, self.form_completeness["smoothed_seismicity"]
        print method(self.catalogue_model.catalogue, config,
                     self.form_completeness["smoothed_seismicity"])

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
