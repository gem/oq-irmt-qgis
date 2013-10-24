import collections

import numpy

from openquake.hazardlib import geo
from hmtk.seismicity.selector import CatalogueSelector

from PyQt4 import QtGui
from PyQt4 import QtCore

from qgis.core import (
    QGis, QgsGeometry, QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsRectangle, QgsFeatureRequest, QgsPoint)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolEmitPoint

from extended_dates_widget import ExtendedDatesWidget
from utils import alert


class AbortSelection(Exception):
    pass


class SelectionTool(object):
    """
    Mixin class for selection tool.

    A selection tool allows the user to select events on a catalogue
    database. In general, a selection tool is part of a chain.

    :attr Selector selector:
        a Selector instance holding the whole chain of SelectionTool
    """

    def __init__(self, field=None):
        self.field = field
        self.selector = None

    def run(self):
        raise NotImplementedError

    def safe_run(self):
        try:
            self.run()
        except AbortSelection:
            print "Selection aborted"

    def next_tools(self):
        try:
            self.selector.run()
        except StopIteration:
            self.selector.callback()

    @property
    def catalogue_map(self):
        return self.selector.window.catalogue_map

    @property
    def map_widget(self):
        return self.catalogue_map.canvas

    @property
    def catalogue(self):
        return self.selector.window.catalogue_model.catalogue

    def set_filter_param(self, value):
        self.selector.filter_params[self.field] = value

    def set_filter_params(self, values):
        self.selector.filter_params.update(values)

    def show_message(self, msg):
        self.selector.window.statusBar.showMessage(msg, 8000)

    @property
    def map2layer(self):
        # If the OSM layer has been correctly loaded deal with CRS
        # Transform
        if getattr(self.catalogue_map.ol_plugin, 'layer', None):
            return QgsCoordinateTransform(
                self.catalogue_map.ol_plugin.layer.crs(),
                QgsCoordinateReferenceSystem(4326))
        else:
            return QgsCoordinateTransform(
                QgsCoordinateReferenceSystem(4326),
                QgsCoordinateReferenceSystem(4326))

    def _rubber_band_to_poly(self, rubber_band):
        geometry = rubber_band.asGeometry()
        geometry.transform(self.map2layer)
        return geo.polygon.Polygon(
            [geo.point.Point(x, y)
             for x, y in geometry.asPolygon()[0][:-1]])


class BooleanTool(SelectionTool):
    """
    Ask the user a boolean question ``msg`` and sets the ``field`` to
    ``value``
    """
    def __init__(self, msg, field, value):
        super(BooleanTool, self).__init__(field)
        self.value = value
        self.msg = msg

    def run(self):
        reply = QtGui.QMessageBox.question(
            self.selector.window, 'Question',
            self.msg, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.set_filter_param(self.value)
        else:
            self.set_filter_param(None)
        self.next_tools()


class SourceTool(QgsMapToolEmitPoint, SelectionTool):
    def __init__(self, field, window):
        QgsMapToolEmitPoint.__init__(self, window.mapWidget)
        SelectionTool.__init__(self, field)

        # to be set on selection end
        self.source = None

    @property
    def layer(self):
        return self.catalogue_map.source_layers['SimpleFaultSource']

    def search_source_at(self, point):
        rectangle = QgsRectangle()
        # 5% of the map width
        radius = self.map_widget.extent().width() / 100 * 5
        rectangle.setXMinimum(point.x() - radius)
        rectangle.setYMinimum(point.y() - radius)
        rectangle.setXMaximum(point.x() + radius)
        rectangle.setYMaximum(point.y() + radius)

        return self.layer.getFeatures(
            QgsFeatureRequest().setFilterRect(
                self.map_widget.mapRenderer().mapToLayerCoordinates(
                    self.layer, rectangle)))

    def canvasPressEvent(self, e):
        """
        Left click -> select a source
        Right click -> Abort
        """
        if e.button() == QtCore.Qt.LeftButton:
            features = self.search_source_at(self.toMapCoordinates(e.pos()))

            try:
                feat = features.next()
                self.source = self.catalogue_map.sources[feat['source_id']]
            except StopIteration:
                alert("Please select a Simple Fault Source")
                self.source = None
        else:
            self.source = None

        self.map_widget.unsetMapTool(self)

    def run(self):
        self.show_message(
            "Left Click selects a source on the map. Right click aborts")
        self.map_widget.setMapTool(self)

    def deactivate(self):
        if self.source is None:
            return
        self.set_filter_param(self.source)
        self.next_tools()


class PolygonTool(QgsMapTool, SelectionTool):
    def __init__(self, field, window):
        QgsMapTool.__init__(self, window.mapWidget)
        SelectionTool.__init__(self, field)
        self.cursor = QtCore.Qt.ArrowCursor

        # to be set upon first click
        self.rubber_band = None

        # to be set on selection end
        self.polygon = None

    def canvasPressEvent(self, e):
        """
        Left click -> add point to polygon
        Right click -> end selection
        """
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.map_widget, QGis.Polygon)
            self.rubber_band.setColor(QtGui.QColor(0, 0, 0, 100))

        if e.button() == QtCore.Qt.LeftButton:
            self.rubber_band.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rubber_band.numberOfVertices() > 2:
                self.polygon = self._rubber_band_to_poly(self.rubber_band)
            self.rubber_band.reset(QGis.Polygon)
            self.map_widget.unsetMapTool(self)

    def canvasMoveEvent(self, e):
        if self.rubber_band is None:
            return
        if self.rubber_band.numberOfVertices() > 0:
            self.rubber_band.removeLastPoint(0)
            self.rubber_band.addPoint(self.toMapCoordinates(e.pos()))

    def run(self):
        self.show_message("Left Click adds point. Right click to end")
        self.map_widget.setMapTool(self)

    def deactivate(self):
        if self.polygon is None:
            return
        self.set_filter_param(self.polygon)
        self.next_tools()


class SquareTool(QgsMapTool, SelectionTool):
    def __init__(self, field, window):
        QgsMapTool.__init__(self, window.mapWidget)
        SelectionTool.__init__(self, field)
        self.cursor = QtCore.Qt.ArrowCursor

        # to be set upon first click
        self.rubber_band = None

        # to be set on selection end
        self.polygon = None
        self.center = None

    def canvasMoveEvent(self, e):
        """
        Draw a geo square where ``self.center`` is the center and the
        current point is a vertex
        """
        if self.rubber_band is None:
            return

        self.rubber_band.reset(QGis.Polygon)
        current = self.map2layer.transform(self.toMapCoordinates(e.pos()))
        point = geo.point.Point(current.x(), current.y())
        distance = point.distance(self.center)
        azimuth = point.azimuth(self.center)
        for vertex in [
                self.center.point_at(distance, 0., (azimuth + s) % 360)
                for s in [0., 90., 180., 270.]]:
            self.rubber_band.addPoint(
                self.map2layer.transform(
                    QgsPoint(vertex.longitude, vertex.latitude), 1))

    def canvasPressEvent(self, e):
        """
        Left click -> set the center
        Right click -> marks end
        """

        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.map_widget, QGis.Polygon)
            self.rubber_band.setColor(QtGui.QColor(0, 0, 0, 100))

        qgs_point = self.map2layer.transform(self.toMapCoordinates(e.pos()))
        point = geo.point.Point(qgs_point.x(), qgs_point.y())

        if e.button() == QtCore.Qt.LeftButton:
            self.rubber_band.reset(QGis.Polygon)
            self.center = point
        else:
            if self.center is not None:
                self.polygon = self._rubber_band_to_poly(self.rubber_band)
            self.rubber_band.reset(QGis.Polygon)
            self.map_widget.unsetMapTool(self)

    def run(self):
        self.show_message("Select a point on the map. Right click ends.")
        self.map_widget.setMapTool(self)

    def deactivate(self):
        if self.polygon is None:
            return
        self.set_filter_param(self.polygon)
        self.next_tools()


class DistanceTool(QgsMapTool, SelectionTool):
    def __init__(self, window):
        QgsMapTool.__init__(self, window.mapWidget)
        SelectionTool.__init__(self)
        self.cursor = QtCore.Qt.ArrowCursor

        # to be set upon first click
        self.rubber_band = None

        # to be set on selection end
        self.center = None
        self.distance = None

    def canvasMoveEvent(self, e):
        if self.rubber_band is None:
            return

        catalogue_map = self.selector.window.catalogue_map
        transform = QgsCoordinateTransform(
            catalogue_map.ol_plugin.layer.crs(),
            QgsCoordinateReferenceSystem(4326)).transform

        self.rubber_band.reset(QGis.Polygon)
        current = transform(self.toMapCoordinates(e.pos()))
        point = geo.point.Point(current.x(), current.y())
        distance = point.distance(self.center)
        circular_polygon = self.center.to_polygon(distance)
        for lon, lat in zip(circular_polygon.lons, circular_polygon.lats):
            self.rubber_band.addPoint(transform(QgsPoint(lon, lat), 1))

    def canvasPressEvent(self, e):
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.map_widget, QGis.Polygon)
            self.rubber_band.setColor(QtGui.QColor(0, 0, 0, 100))

        qgs_point = self.map2layer.transform(self.toMapCoordinates(e.pos()))
        point = geo.point.Point(qgs_point.x(), qgs_point.y())
        if e.button() == QtCore.Qt.LeftButton:
            self.rubber_band.reset(QGis.Polygon)
            self.center = point
        else:
            if self.center is not None:
                self.distance = point.distance(self.center)
            self.rubber_band.reset(QGis.Polygon)
            self.map_widget.unsetMapTool(self)

    def run(self):
        self.show_message("Select a point on the map. Right click ends.")
        self.map_widget.setMapTool(self)

    def deactivate(self):
        if self.center is None:
            return
        self.set_filter_params({'center': self.center,
                                'distance': self.distance})
        self.next_tools()


class FloatTool(QtGui.QDialog, SelectionTool):
    def __init__(self, fields):
        QtGui.QDialog.__init__(self)
        SelectionTool.__init__(self)

        self.fields = fields
        self.input_fields = dict()

        # to be set in #run
        self.layout = None
        self.button_box = None
        self.form = None

    def run(self):
        self.resize(400, 400)
        self.layout = QtGui.QVBoxLayout(self)
        self.form = QtGui.QFormLayout()

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
            ret = dict()
            for name, input_field in self.input_fields.items():
                if input_field.text():
                    ret[name] = float(input_field.text())
                else:
                    ret[name] = None
            self.set_filter_params(ret)
            self.next_tools()
        else:
            raise AbortSelection


class FloatFieldBetweenTool(QtGui.QDialog, SelectionTool):
    class Slider(QtGui.QSlider):
        def __init__(self, catalogue, field, label, field_type="min"):
            QtGui.QSlider.__init__(self, QtCore.Qt.Horizontal)
            self.catalogue = catalogue
            self.field = field

            self.label = label
            self.min_field = True
            self.field_type = field_type

        def val(self, v=None):
            v = v or self.value()
            return self.catalogue.data[self.field].min() + (
                self.catalogue.data[self.field].max() -
                self.catalogue.data[self.field].min()) / 10 * v

        def changed(self, v):
            val = self.val(v)
            self.label.setText("%s %s (%.03f)" % (
                self.field_type, self.field, val))
            return val

    def __init__(self, *fields):
        QtGui.QDialog.__init__(self)
        SelectionTool.__init__(self)

        self.fields = fields
        self.min_fields = dict()
        self.max_fields = dict()

        # to be set in #run
        self.layout = None
        self.button_box = None
        self.form = None

    def run(self):
        self.resize(400, 400)
        self.layout = QtGui.QVBoxLayout(self)
        self.form = QtGui.QFormLayout()

        catalogue = self.catalogue

        for i, name in enumerate(self.fields):
            label = QtGui.QLabel()
            label.setText("min %s" % name)
            self.form.setWidget(i * 2, QtGui.QFormLayout.LabelRole, label)
            self.min_fields[name] = self.Slider(catalogue, name, label, "min")
            self.form.setWidget(
                i * 2, QtGui.QFormLayout.FieldRole, self.min_fields[name])

            label = QtGui.QLabel()
            label.setText("max %s" % name)
            self.form.setWidget(i * 2 + 1, QtGui.QFormLayout.LabelRole, label)
            self.max_fields[name] = self.Slider(catalogue, name, label, "max")
            self.form.setWidget(
                i * 2 + 1, QtGui.QFormLayout.FieldRole, self.max_fields[name])

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
            ret = dict()
            for name in self.fields:
                ret[name] = (self.min_fields[name].val(),
                             self.max_fields[name].val())
            self.set_filter_params(ret)
            self.next_tools()
        else:
            raise AbortSelection


class DateBetweenTool(QtGui.QDialog, SelectionTool):
    def __init__(self, start_field_name, end_field_name):
        QtGui.QDialog.__init__(self)
        SelectionTool.__init__(self)

        self.start_field_name = start_field_name
        self.end_field_name = end_field_name

        # to be set in #run
        self.layout = None
        self.button_box = None
        self.field = None

    def run(self):
        self.resize(400, 400)
        self.layout = QtGui.QVBoxLayout(self)
        self.field = ExtendedDatesWidget(parent=self)
        self.layout.insertWidget(0, self.field)

        self.button_box = QtGui.QDialogButtonBox(self)
        self.button_box.setGeometry(QtCore.QRect(290, 20, 81, 341))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.insertWidget(1, self.button_box)
        self.show()

    def accept(self):
        start = self.field.get_from_min_datetime().toPyDateTime()
        end = self.field.get_from_max_datetime().toPyDateTime()
        self.set_filter_params({
            self.start_field_name: start, self.end_field_name: end})
        self.next_tools()

    def reject(self):
        pass


class Selector(object):
    def __init__(self, callback, window, tools):
        self.callback = callback
        self.window = window
        for tool in tools:
            tool.selector = self
        self.tools = iter(tools)
        self.filter_params = dict()

    def run(self):
        return self.tools.next().safe_run()


class Invert(QtGui.QListWidgetItem):
    def __init__(self, window):
        super(Invert, self).__init__("Invert selection")
        window.selection_editor.selectorList.addItem(self)
        window.update_selection()

    def apply(self, catalogue, initial_catalogue):
        return CatalogueSelector(initial_catalogue, True).select_catalogue(
            [x not in catalogue.data['eventID']
             for x in initial_catalogue.data['eventID']])


class WithinJBSource(QtGui.QListWidgetItem, Selector):
    def __init__(self, window):
        super(WithinJBSource, self).__init__("Within JB Source")
        self.selector = Selector(
            self.add,
            window,
            [SourceTool("source", window),
             FloatTool(collections.OrderedDict(
                 distance="Distance",
                 upper_depth="Upper seismogenic depth",
                 lower_depth="Lower seismogenic depth"))])
        self.window = window
        self.selector.run()

    def add(self):
        source = self.selector.filter_params['source']
        self.setText("Within %s from %s (u: %s l: %s)" % (
            self.selector.filter_params['distance'],
            source,
            self.selector.filter_params['upper_depth'],
            self.selector.filter_params['lower_depth']))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).within_joyner_boore_distance(
            self.selector.filter_params['source'],
            self.selector.filter_params['distance'],
            upper_depth=self.selector.filter_params['upper_depth'],
            lower_depth=self.selector.filter_params['lower_depth'])


class WithinRuptureDistance(WithinJBSource):
    desc = "Rupture"
    source_type = 'SimpleFaultSource'

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).within_rupture_distance(
            self.selector.filter_params['source'],
            self.selector.filter_params['distance'],
            upper_depth=self.selector.filter_params['upper_depth'],
            lower_depth=self.selector.filter_params['lower_depth'])


class WithinPolygon(QtGui.QListWidgetItem, Selector):
    def __init__(self, window, tools=None):
        super(WithinPolygon, self).__init__("Within polygon")
        tools = tools or [PolygonTool("polygon", window),
                          FloatTool(
                              collections.OrderedDict(
                                  distance="Distance",
                                  upper_depth="Upper seismogenic depth",
                                  lower_depth="Lower seismogenic depth"))]
        self.window = window
        self.selector = Selector(self.add, window, tools)
        self.selector.run()

    def add(self):
        self.setText("Within poly %s %s %s %s" % (
            ", ".join(["%.4f %.4f" % (x, y)
                       for x, y
                       in zip(self.selector.filter_params['polygon'].lons,
                              self.selector.filter_params['polygon'].lats)]),
            self.selector.filter_params.get('distance', 0),
            self.selector.filter_params.get('upper_depth'),
            self.selector.filter_params.get('lower_depth')))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).within_polygon(
            self.selector.filter_params['polygon'],
            self.selector.filter_params.get('distance', 0),
            upper_depth=self.selector.filter_params.get('upper_depth'),
            lower_depth=self.selector.filter_params.get('lower_depth'))


class WithinSquare(WithinPolygon):
    def __init__(self, window):
        super(WithinSquare, self).__init__(
            window,
            [SquareTool("polygon", window),
             FloatTool(collections.OrderedDict(
                 upper_depth="Upper seismogenic depth",
                 lower_depth="Lower seismogenic depth"))])


class WithinDistance(WithinPolygon):
    def __init__(self, window):
        super(WithinDistance, self).__init__(
            window,
            [DistanceTool(window),
             BooleanTool(
                 "Epicentral distance?", "distance_type", "epicentral")])

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).circular_distance_from_point(
            self.selector.filter_params['center'],
            self.selector.filter_params['distance'],
            distance_type=self.selector.filter_params['distance_type'])

    def add(self):
        self.setText("Within %s distance %s from %s" % (
            self.selector.filter_params['distance_type'],
            self.selector.filter_params.get('distance', 0),
            self.selector.filter_params['center']))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()


class TimeBetween(QtGui.QListWidgetItem):
    def __init__(self, window):
        super(TimeBetween, self).__init__("Time between")
        self.selector = Selector(
            self.add, window,
            [DateBetweenTool("start_time", "end_time")])
        self.window = window
        self.selector.run()

    def apply(self, catalogue, _initial_catalogue):
        return CatalogueSelector(catalogue, True).within_time_period(
            start_time=self.selector.filter_params['start_time'],
            end_time=self.selector.filter_params['end_time'])

    def add(self):
        self.setText("Time within period %s %s" % (
            self.selector.filter_params['start_time'],
            self.selector.filter_params['end_time']))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()


class FloatFieldBetween(QtGui.QListWidgetItem):
    def __init__(self, window):
        super(FloatFieldBetween, self).__init__("Float field between")
        self.window = window
        self.selector = Selector(
            self.add, window, [FloatFieldBetweenTool("depth", "magnitude")])
        self.selector.run()

    def apply(self, catalogue, _initial_catalogue):
        filter_params = self.selector.filter_params.items()
        print filter_params
        field, (min_val, max_val) = filter_params[0]

        catalogue = self.window.catalogue_model.catalogue
        is_valid = numpy.logical_and(
            catalogue.data[field] >= min_val, catalogue.data[field] <= max_val)

        for field, (min_val, max_val) in filter_params[1:]:
            is_valid = numpy.logical_and(
                is_valid,
                catalogue.data[field] >= min_val,
                catalogue.data[field] <= max_val)

        return CatalogueSelector(catalogue, True).select_catalogue(
            is_valid)

    def add(self):
        self.setText("Depth between %s %s - Magnitude between %s %s" % (
            self.selector.filter_params['depth'][0],
            self.selector.filter_params['depth'][1],
            self.selector.filter_params['magnitude'][0],
            self.selector.filter_params['magnitude'][1]))
        self.window.selection_editor.selectorList.addItem(self)
        self.window.update_selection()


SELECTORS = [Invert, WithinPolygon, WithinJBSource,
             WithinRuptureDistance, WithinSquare, WithinDistance,
             TimeBetween, FloatFieldBetween]
