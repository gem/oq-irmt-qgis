import collections

from openquake.hazardlib import geo
from hmtk.seismicity.selector import CatalogueSelector

from PyQt4 import QtGui
from PyQt4 import QtCore

from qgis.core import (
    QGis, QgsGeometry, QgsCoordinateTransform, QgsCoordinateReferenceSystem)
from qgis.gui import QgsMapTool, QgsRubberBand


class AbortSelection(Exception):
    pass


class SelectionTool(object):
    def run(self):
        raise NotImplementedError

    def next_tools(self):
        try:
            self.selector.tools.next().run()
        except StopIteration:
            self.selector.add()
        except AbortSelection:
            print "Selection aborted"


class PolygonTool(QgsMapTool, SelectionTool):
    def __init__(self, selector, name):
        super(PolygonTool, self).__init__(selector.window.mapWidget)
        self.cursor = QtCore.Qt.ArrowCursor
        self.selector = selector
        self.name = name

        # to be set upon first click
        self.rubber_band = None

        # to be set on selection end
        self.polygon = None

    def canvasPressEvent(self, e):
        # XXX: I apologize, uncle Demetrius
        canvas = self.selector.window.mapWidget
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(canvas, QGis.Polygon)
            self.rubber_band.setColor(QtGui.QColor(0, 0, 0, 100))

        if e.modifiers() & QtCore.Qt.ShiftModifier:
            self.selector.union = False
        else:
            self.selector.union = True

        if e.button() == QtCore.Qt.LeftButton:
            self.rubber_band.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rubber_band.numberOfVertices() <= 2:
                raise AbortSelection
            else:
                self.polygon = QgsGeometry(self.rubber_band.asGeometry())
            self.rubber_band.reset(QGis.Polygon)
            self.selector.window.mapWidget.unsetMapTool(self)

    def canvasMoveEvent(self, e):
        if self.rubber_band is None:
            return

        if self.rubber_band.numberOfVertices() > 0:
            self.rubber_band.removeLastPoint(0)
            self.rubber_band.addPoint(self.toMapCoordinates(e.pos()))

    def run(self):
        self.selector.window.statusBar.showMessage(
            "Draw a polygon on the map. Left Click adds point. "
            "Right click marks end. Press Shift to intersect with selection",
            8000)
        self.selector.window.mapWidget.setMapTool(self)

    def deactivate(self):
        if self.polygon is None:
            raise AbortSelection
        self.polygon.transform(
            QgsCoordinateTransform(
                self.selector.window.catalogue_map.ol_plugin.layer.crs(),
                QgsCoordinateReferenceSystem(4326)))
        self.selector.values[self.name] = geo.polygon.Polygon(
            [geo.point.Point(x, y)
             for x, y in self.polygon.asPolygon()[0][:-1]])
        self.next_tools()


class FloatDialog(QtGui.QDialog, SelectionTool):
    def __init__(self, selector, fields):
        super(FloatDialog, self).__init__()
        self.selector = selector
        self.fields = fields
        self.input_fields = dict()

        # to be set in #run
        self.layout = None
        self.button_box = None
        self.form = None

    def run(self):
        self.resize(400, 400)
        self.layout = QtGui.QVBoxLayout(self)
        self.form = QtGui.QFormLayout(self)

        for i, (name, text) in enumerate(self.fields.items()):
            label = QtGui.QLabel()
            label.setText(text)
            self.form.setWidget(i, QtGui.QFormLayout.LabelRole, label)
            self.input_fields[name] = QtGui.QLineEdit()
            self.form.setWidget(
                i, QtGui.QFormLayout.FieldRole, self.input_fields[name])

        self.button_box = QtGui.QDialogButtonBox(self)
        self.button_box.setGeometry(QtCore.QRect(290, 20, 81, 341))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.insertLayout(0, self.form)
        self.layout.insertWidget(1, self.button_box)

        if self.exec_():
            for name, input_field in self.input_fields.items():
                if input_field.text():
                    self.selector.values[name] = float(input_field.text())
                else:
                    self.selector.values[name] = None
            self.next_tools()
        else:
            raise AbortSelection


class Invert(QtGui.QListWidgetItem):
    def __init__(self, window):
        super(Invert, self).__init__("Invert selection")
        self.union = False
        window.selectorList.addItem(self)
        window.update_selection()

    def apply(self, catalogue, initial_catalogue):
        return CatalogueSelector(initial_catalogue, True).select_catalogue(
            [x not in catalogue.data['eventID']
             for x in initial_catalogue.data['eventID']])


class WithinJBSource(QtGui.QListWidgetItem):
    pass


class WithinPolyhedra(QtGui.QListWidgetItem):
    def __init__(self, window):
        super(WithinPolyhedra, self).__init__("Within polyhedra")
        self.union = True
        self.window = window
        self.tools = iter(
            [PolygonTool(self, "polygon"),
             FloatDialog(self, collections.OrderedDict(
                 distance="Distance",
                 upper_depth="Upper seismogenic depth",
                 lower_depth="Lower seismogenic depth"))])

        self.values = dict()
        self.tools.next().run()

    def add(self):
        points = zip(self.values['polygon'].lons, self.values['polygon'].lats)
        points = ", ".join(["%.4f %.4f" % (x, y) for x, y in points])
        if self.union:
            text = "Add"
        else:
            text = "Intersect"
        self.setText("%s within poly %s %s %s %s" % (
            text,
            points,
            self.values['distance'],
            self.values['upper_depth'], self.values['lower_depth']))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).within_polygon(
            self.values['polygon'],
            self.values['distance'],
            upper_depth=self.values['upper_depth'],
            lower_depth=self.values['lower_depth'])


SELECTORS = [Invert, WithinPolyhedra, WithinJBSource]
