import os
import collections
import tempfile

import numpy

from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import scalerel
from openquake.hazardlib import source

from openquake.nrmllib import models as nrml_models
from shapely import wkt

from PyQt4.QtCore import QVariant, QFileInfo

from osgeo import gdal, osr
import math

from qgis.core import (
    QgsVectorLayer, QgsRasterLayer, QgsRaster,
    QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPoint,
    QgsMapLayerRegistry, QgsPluginLayerRegistry,
    QgsRectangle, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsFeatureRequest,
    QgsRasterShader, QgsColorRampShader, QgsStyleV2,
    QgsFillSymbolV2, QgsSingleSymbolRendererV2, QgsLabel)
from qgis.gui import QgsMapCanvasLayer

from openlayers_plugin.openlayers_plugin import (
    OpenlayersPlugin, OpenlayersPluginLayerType)

import utils
import styles


class CatalogueMap(object):
    """
    Model a map suitable to hold information about a seismic event catalogue

    :attr canvas:
       a :class:`QgsMapCanvas` instance that hold the QGIS map

    :attr catalogue_model:
       a :class:`hmtk_ui.catalogue_model.CatalogueModel` instance holding
       the event catalogue

    :attr catalogue_layer:
       a :class:`QgsVectorLayer` instance holding map features related to
       a catalogue model

    :attr ol_plugin:
       a instance of the QGIS OpenLayer plugin

    :attr basemap_layer:
       a Layer used to show the base map

    :attr raster_layer:
       A QGIS raster layer used to display smoothed seismicity data

    :attr dict event_feature_ids:
       A dict of QgsFeatureIDs keyed by eventID string
    """
    def __init__(self, canvas, catalogue_model):
        """
        Create and initialize a layer for catalogue events, an empty
        temporary layer and the basemap openlayer-based layer.
        """
        self.canvas = canvas
        self.catalogue_model = catalogue_model
        self.event_feature_ids = None
        self.sources = dict()

        self.catalogue_layer = make_inmemory_layer("catalogue")
        self.populate_catalogue_layer(catalogue_model.catalogue)
        self.set_catalogue_style("cluster")

        # XXX: QGIS require to set FIRST the vector layer to get the
        # proper projection transformation
        self.canvas.setLayerSet([QgsMapCanvasLayer(self.catalogue_layer)])
        self.canvas.setExtent(self.catalogue_layer.extent())

        self.basemap_layer = self.load_basemap()
        self.ol_plugin = self.load_osm_plugin()

        # initialized later
        self.raster_layer = None
        self.source_layers = dict()

        # Initialize Map
        self.reset_map()

    def load_basemap(self):
        layer_path = os.path.join(
            os.path.dirname(__file__),
            "data", "Countries.shp")
        layer = QgsVectorLayer(
            layer_path, "World Countries", "ogr")
        if not layer.isValid():
            raise RuntimeError("Basemap layer is not valid!!!")
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        return layer

    def reset_map(self):
        """
        Reset the map by loading the catalogue and the basemap layers
        """
        catalogue = []
        if self.raster_layer:
            catalogue.append(QgsMapCanvasLayer(self.raster_layer))
        catalogue.append(QgsMapCanvasLayer(self.catalogue_layer))
        self.canvas.setLayerSet(
            catalogue +
            [QgsMapCanvasLayer(s) for s in self.source_layers.values()] +
            [QgsMapCanvasLayer(self.basemap_layer)])
        self.canvas.refresh()

    def set_catalogue_style(self, style):
        layer = self.catalogue_layer

        if style == "depth-magnitude":
            renderer = styles.CatalogueDepthMagnitudeRenderer
        elif style == "completeness":
            renderer = styles.CatalogueCompletenessRenderer
        elif style == "cluster":
            renderer = styles.CatalogueClusterRenderer
        elif style == "default":
            renderer = styles.CatalogueDefaultRenderer
        else:
            raise NotImplementedError("Unsupported style %s" % style)

        layer.setRendererV2(renderer.make(self))
        layer.triggerRepaint()

    def populate_catalogue_layer(self, catalogue):
        """
        Populate the catalogue vector layer with data got from `catalogue`

        :param catalogue:
            a :class:`hmtk.seismicity.catalogue.Catalogue` instance
        """
        vl = self.catalogue_layer
        pr = vl.dataProvider()
        vl.startEditing()

        # Set field types (the schema of the vector layer)
        fields = []
        mock_attributes = ["_magnitude"]

        for key in catalogue.data.keys() + mock_attributes:
            if key in mock_attributes:
                key_norm = key[1:]
            else:
                key_norm = key
            if isinstance(key_norm, numpy.ndarray):
                fields.append(QgsField(key, QVariant.Double))
            else:
                fields.append(QgsField(key, QVariant.String))

        pr.addAttributes(fields)

        qgs_fields = QgsFields()
        for f in fields:
            qgs_fields.append(f)

        # Create the features
        features = []
        for i in range(catalogue.get_number_events()):
            fet = QgsFeature()
            fet.setFields(qgs_fields)

            x = catalogue.data['longitude'][i]
            y = catalogue.data['latitude'][i]
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(x, y)))

            for key in catalogue.data:
                event_data = catalogue.data[key]
                if len(event_data):
                    if isinstance(catalogue.data[key], numpy.ndarray):
                        fet[key] = float(event_data[i])
                    else:
                        fet[key] = str(event_data[i])
            fet['_magnitude'] = fet['magnitude'] ** 2
            features.append(fet)
        pr.addFeatures(features)
        vl.commitChanges()

        self.event_feature_ids = dict([
            (f['eventID'], f.id()) for f in vl.getFeatures()])

        # Set the canvas extent to avoid projection problems and to
        # pan to the loaded events
        vl.updateExtents()

    @staticmethod
    def magnitude_to_display_size(x):
        return math.exp(x)/10

    def change_catalogue_model(self, catalogue_model):
        """
        Load a new catalogue model (replace the old one)
        """
        self.catalogue_model = catalogue_model
        self.clear_features(self.catalogue_layer)
        self.populate_catalogue_layer(catalogue_model.catalogue)
        self.reset_map()

    def load_osm_plugin(self):
        """
        Initialize the QGIS OpenLayer plugin and load the basemap
        layer
        """
        canvas = self.canvas

        class IFace(object):
            def mapCanvas(self):
                return canvas

        iface = IFace()
        olplugin = OpenlayersPlugin(iface)

        # hacked from #OpenlayersPlugin#initGui
        if not olplugin._OpenlayersPlugin__setCoordRSGoogle():
            utils.alert("Error in setting coordinate system")
        oltype = OpenlayersPluginLayerType(
            iface, olplugin.setReferenceLayer,
            olplugin._OpenlayersPlugin__coordRSGoogle,
            olplugin.olLayerTypeRegistry)
        QgsPluginLayerRegistry.instance().addPluginLayerType(oltype)

        return olplugin

    def load_osm(self, olplugin):
        # 4 is OpenStreetMap
        ol_gphyslayertype = olplugin.olLayerTypeRegistry.getById(4)
        olplugin.addLayer(ol_gphyslayertype)

        if not olplugin.layer.isValid():
            utils.alert("Failed to load basemap")

        return olplugin.layer

    def set_osm(self):
        # we keep a reference of the OpenLayer Plugin (instead of a
        # layer) such that the underlying basemap layer data is not
        # garbage collected
        self.basemap_layer = self.load_osm(self.ol_plugin)
        self.reset_map()

        # This zoom is required to initialize the map canvas
        self.canvas.zoomByFactor(1.1)

    def center_on(self, field, value, comparator=cmp):
        """
        Pan and zoom to the features with `field` equal to `value` by
        using a custom comparator function `cmp`
        """
        # Select all the features that fulfill the given condition
        selected_features = self.catalogue_layer.selectedFeatures()
        features = []

        catalogue = self.catalogue_model.catalogue
        for i, event_id in enumerate(catalogue.data['eventID']):
            expected = catalogue.data[field][i]
            if not comparator(expected, value):
                features.append(event_id)
        self.select(features)
        self.canvas.panToSelected(self.catalogue_layer)
        self.canvas.zoomToSelected(self.catalogue_layer)
        self.canvas.zoomByFactor(1.1)
        self.catalogue_layer.removeSelection()
        self.catalogue_layer.select([f.id() for f in selected_features])

    def clear_features(self, layer):
        """
        Delete all the features from `layer`
        """
        layer.startEditing()
        for feat in layer.getFeatures():
            layer.deleteFeature(feat.id())
        layer.commitChanges()

    def select(self, event_ids):
        """
        Select features with Feature ID `fids` and center the map on
        them
        """
        fids = [self.event_feature_ids[event_id] for event_id in event_ids]
        self.catalogue_layer.removeSelection()
        self.catalogue_layer.select(fids)

    def update_catalogue_layer(self, attr_names):
        """
        Update layer as in catalogue columns `attr_names` are changed
        """
        layer = self.catalogue_layer
        layer.startEditing()

        for i, event_id in enumerate(
                self.catalogue_model.catalogue.data['eventID']):
            feature = self.catalogue_layer.getFeatures(
                QgsFeatureRequest(self.event_feature_ids[event_id])).next()
            for attr in attr_names:
                feature[attr] = self.catalogue_model.catalogue.data[attr][i]
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.rendererV2().update_syms(self.catalogue_model.catalogue)
        layer.triggerRepaint()
        self.canvas.refresh()

    def show_tip(self, point):
        rectangle = QgsRectangle()
        radius = self.canvas.extent().width() / 100 * 5  # 5% of the map width
        rectangle.setXMinimum(point.x() - radius)
        rectangle.setYMinimum(point.y() - radius)
        rectangle.setXMaximum(point.x() + radius)
        rectangle.setYMaximum(point.y() + radius)

        layer_rectangle = self.canvas.mapRenderer().mapToLayerCoordinates(
            self.catalogue_layer, rectangle)

        features = self.catalogue_layer.getFeatures(
            QgsFeatureRequest().setFilterRect(layer_rectangle))

        # assume the first one is the closest
        try:
            feat = features.next()
            msg_lines = ["Event Found"]
            for k in self.catalogue_model.catalogue_keys():
                msg_lines.append("%s=%s" % (k, feat[k]))
        except StopIteration:
            msg_lines = ["No Event found"]

        if self.raster_layer is not None:
            src = self.basemap_layer.crs()
            dst = QgsCoordinateReferenceSystem(4326)
            trans = QgsCoordinateTransform(src, dst)
            point = trans.transform(point)

            raster_data = self.raster_layer.dataProvider().identify(
                point, QgsRaster.IdentifyFormatValue)

            for k, v in raster_data.results().items():
                msg_lines.append("Smoothed=%s" % str(v))

        utils.alert('\n'.join(msg_lines))

    def set_raster(self, matrix):
        layer = create_raster_layer(matrix)
        if self.raster_layer is not None:
            QgsMapLayerRegistry.instance().removeMapLayer(
                self.raster_layer.id())
        self.raster_layer = layer
        layer.reload()
        self.reset_map()

    def add_source_layers(self, sources):
        """
        :param list sources:
            a list of nrmllib Source Models (e.g. SimpleFaultSource)
        """
        source_type = collections.namedtuple(
            'SourceType', 'layer_type transform color')

        geometries = {
            'PointSource': source_type(
                'Point', lambda x: x.geometry.wkt, "255,255,255,185"),
            'AreaSource': source_type(
                'Polygon', lambda x: x.geometry.wkt, '0,255,255,185'),
            'SimpleFaultSource': source_type(
                'Polygon',
                lambda x: simple_surface_from_source(x).wkt,
                '0,50,255,185'),
            'ComplexFaultSource': source_type(
                'MultiPolygon', lambda _: NotImplementedError, '50,50,50,185')}

        source_dict = collections.defaultdict(list)

        for s in sources:
            source_dict[s.__class__.__name__].append(s)

        for stype, sources in source_dict.items():
            layer = QgsVectorLayer(
                '%s?crs=epsg:4326' % (
                    geometries[stype].layer_type),
                stype, 'memory')
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            pr = layer.dataProvider()
            layer.startEditing()

            fields = [QgsField("source_id", QVariant.String)]
            pr.addAttributes(fields)

            qgs_fields = QgsFields()
            for field in fields:
                qgs_fields.append(field)

            features = []
            for src in sources:
                fet = QgsFeature()
                fet.setFields(qgs_fields)
                fet['source_id'] = src.id
                if stype == 'SimpleFaultSource':
                    self.sources[src.id] = _nrml_to_hazardlib(src, 1.)
                fet.setGeometry(QgsGeometry.fromWkt(
                    geometries[stype].transform(src)))
                features.append(fet)
            pr.addFeatures(features)
            layer.commitChanges()
            layer.updateExtents()

            symbol = QgsFillSymbolV2.createSimple(
                {'style': 'diagonal_x',
                 'color': geometries[stype].color,
                 'style_border': 'solid'})
            layer.setRendererV2(QgsSingleSymbolRendererV2(symbol))

            self.source_layers[stype] = layer

        self.reset_map()

    def toggle_catalogue_labels(self):
        label = self.catalogue_layer.label()
        attributes = label.labelAttributes()
        attributes.setOffset(0, 15, 1)
        label.setLabelField(
            QgsLabel.Text, self.catalogue_layer.fieldNameIndex("eventID"))
        self.catalogue_layer.enableLabels(
            not self.catalogue_layer.hasLabelsEnabled())
        self.reset_map()

    def toggle_sources_labels(self):
        for layer in self.source_layers.values():
            label = layer.label()
            label.setLabelField(QgsLabel.Text, layer.fieldNameIndex("eventID"))
            layer.enableLabels(not layer.hasLabelsEnabled())
        self.reset_map()


def create_raster_layer(matrix):
    driver = gdal.GetDriverByName("GTiff")

    filename = tempfile.mktemp(prefix="hmtk", suffix=".tif")

    # sort the data by lon, lat
    gridded_data = numpy.array(
        sorted(matrix, key=lambda row: (90 + row[1]) * 180 + (180 + row[0])))

    # extract it into separate vars
    lons, lats, vals = (
        gridded_data[:, 0], gridded_data[:, 1], gridded_data[:, 3])

    ncols = lons[lons == lons[0]].size
    nrows = lats[lats == lats[0]].size

    # put values in a grid
    gridded_vals = vals.reshape((ncols, nrows)).T

    dataset = driver.Create(filename, ncols, nrows, 1, gdal.GDT_Float32)

    dataset.SetGeoTransform((
        min(lons),
        (max(lons) - min(lons)) / ncols,
        0,
        max(lats),
        0,
        -(max(lats) - min(lats)) / nrows))

    out_srs = osr.SpatialReference()
    out_srs.ImportFromEPSG(4326)
    dataset.SetProjection(out_srs.ExportToWkt())

    out_band = dataset.GetRasterBand(1)
    out_band.WriteArray(gridded_vals)
    out_band.SetNoDataValue(0)
    out_band.FlushCache()
    out_band = None
    dataset = None

    fileInfo = QFileInfo(filename)
    baseName = fileInfo.baseName()
    layer = QgsRasterLayer(filename, baseName)

    stat = layer.dataProvider().bandStatistics(1)

    minVal = stat.minimumValue
    maxVal = stat.maximumValue
    entries_nr = 20

    colorRamp = QgsStyleV2().defaultStyle().colorRamp("Spectral")
    currentValue = float(minVal)
    intervalDiff = float(maxVal - minVal) / float(entries_nr - 1)

    colorRampItems = []
    for i in reversed(xrange(entries_nr)):
        item = QgsColorRampShader.ColorRampItem()
        item.value = currentValue
        item.label = unicode(currentValue)
        currentValue += intervalDiff
        item.color = colorRamp.color(float(i) / float(entries_nr))
        item.color.setAlphaF(0.75)
        colorRampItems.append(item)

    rasterShader = QgsRasterShader()
    colorRampShader = QgsColorRampShader()

    colorRampShader.setColorRampItemList(colorRampItems)
    colorRampShader.setColorRampType(QgsColorRampShader.INTERPOLATED)
    rasterShader.setRasterShaderFunction(colorRampShader)

    layer.setDrawingStyle('SingleBandPseudoColor')
    layer.renderer().setShader(rasterShader)

    QgsMapLayerRegistry.instance().addMapLayer(layer)

    return layer


def make_inmemory_layer(name):
    layer = QgsVectorLayer('Point?crs=epsg:4326', name, 'memory')
    QgsMapLayerRegistry.instance().addMapLayer(layer)
    return layer


def simple_surface_from_source(src):
    return geo.surface.SimpleFaultSurface.surface_projection_from_fault_data(
        geo.Line([geo.Point(x[0], x[1])
                  for x in wkt.loads(src.geometry.wkt).coords]),
        upper_seismogenic_depth=src.geometry.upper_seismo_depth,
        lower_seismogenic_depth=src.geometry.lower_seismo_depth,
        dip=src.geometry.dip)


def _nrml_to_hazardlib(src, mesh_spacing=1.):
    """
    Convert a NRML source object into the HazardLib representation.
    """
    if not isinstance(src, nrml_models.SimpleFaultSource):
        raise NotImplementedError

    return geo.surface.SimpleFaultSurface.from_fault_data(
        geo.Line([geo.Point(*x) for x in wkt.loads(src.geometry.wkt).coords]),
        src.geometry.upper_seismo_depth,
        src.geometry.lower_seismo_depth,
        src.geometry.dip,
        mesh_spacing)
