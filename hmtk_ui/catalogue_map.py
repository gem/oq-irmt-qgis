import collections
import tempfile

import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant, QFileInfo

from osgeo import gdal, osr

from qgis.core import (
    QgsVectorLayer, QgsRasterLayer, QgsField, QgsFeature, QgsGeometry,
    QgsPoint, QgsMapLayerRegistry, QgsPluginLayerRegistry,
    QgsFeatureRendererV2, QgsSymbolV2, QGis, QgsRectangle,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform)
from qgis.gui import QgsMapCanvasLayer

from openlayers_plugin.openlayers_plugin import (
    OpenlayersPlugin, OpenlayersPluginLayerType)

import utils


class CatalogueMap(object):
    def __init__(self, canvas, catalogue_model):
        self.canvas = canvas
        self.catalogue_model = catalogue_model

        self.catalogue_layer = QgsVectorLayer(
            'Point?crs=epsg:4326', "catalogue", 'memory')
        self.raster_layer = None

        QgsMapLayerRegistry.instance().addMapLayer(self.catalogue_layer)
        self.selection_layer = QgsVectorLayer(
            'Point?crs=epsg:4326', "selection", 'memory')
        QgsMapLayerRegistry.instance().addMapLayer(self.selection_layer)
        self.selection_layer.setRendererV2(CatalogueRenderer(
            self.catalogue_model))

        layer = self.load_catalogue()
        self.basemap_layer = self.load_basemap()
        self.canvas.setLayerSet([layer, self.basemap_layer])
        self.canvas.refresh()
        self.canvas.zoomByFactor(1.1)

    def set_raster(self, matrix):
        layer = create_raster_layer(matrix)
        if self.raster_layer is not None:
            QgsMapLayerRegistry.instance().removeMapLayer(
                self.raster_layer.layer().id())
        self.raster_layer = QgsMapCanvasLayer(layer)

        self.canvas.setLayerSet(
            [QgsMapCanvasLayer(self.catalogue_layer),
             self.raster_layer,
             QgsMapCanvasLayer(self.basemap_layer)])
        layer.reload()
        self.canvas.refresh()
        self.canvas.zoomByFactor(1.1)

    def load_catalogue(self):
        vl = self.catalogue_layer
        self.populate_layer(vl)
        layer = QgsMapCanvasLayer(vl)
        vl.setRendererV2(CatalogueRenderer(self.catalogue_model))
        vl.updateExtents()
        self.catalogue_layer = vl
        self.canvas.setLayerSet([layer])
        self.canvas.setExtent(vl.extent())
        self.canvas.refresh()

        return layer

    def populate_layer(self, vl):
        catalogue = self.catalogue_model.catalogue
        pr = vl.dataProvider()
        vl.startEditing()

        fields = []
        for key in catalogue.data:
            if isinstance(catalogue.data[key], numpy.ndarray):
                fields.append(QgsField(key, QVariant.Double))
            else:
                fields.append(QgsField(key, QVariant.String))
        pr.addAttributes(fields)

        features = []
        for i in range(catalogue.get_number_events()):
            fet = QgsFeature(int(catalogue.data['eventID'][i]))
            event_values = {}

            for j, key in enumerate(self.catalogue_model.catalogue_keys()):
                event_data = catalogue.data[key]
                if len(event_data):
                    event_values[j] = QVariant(event_data[i])
                else:
                    event_values[j] = QVariant("NA")

            x = catalogue.data['longitude'][i]
            y = catalogue.data['latitude'][i]
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(x, y)))
            fet.setAttributeMap(event_values)
            features.append(fet)
        pr.addFeatures(features)
        vl.commitChanges()

    def change_catalogue_model(self, catalogue_model):
        vl = self.catalogue_layer
        self.clear_features(vl)
        self.catalogue_model = catalogue_model
        self.populate_layer(vl)
        vl.updateExtents()
        self.canvas.setLayerSet(
            [QgsMapCanvasLayer(vl),
             QgsMapCanvasLayer(self.basemap_layer)])
        self.canvas.refresh()
        # TODO. recenter map

    def load_basemap(self):
        canvas = self.canvas

        class IFace(object):
            def mapCanvas(self):
                return canvas

        iface = IFace()
        olplugin = OpenlayersPlugin(iface)

        if not olplugin._OpenlayersPlugin__setCoordRSGoogle():
            utils.alert("Error in setting coordinate system")
        oltype = OpenlayersPluginLayerType(
            iface, olplugin.setReferenceLayer,
            olplugin._OpenlayersPlugin__coordRSGoogle,
            olplugin.olLayerTypeRegistry)
        QgsPluginLayerRegistry.instance().addPluginLayerType(oltype)
        ol_gphyslayertype = olplugin.olLayerTypeRegistry.getById(4)
        olplugin.addLayer(ol_gphyslayertype)
        if not olplugin.layer.isValid():
            utils.alert("Failed to load basemap")
        return QgsMapCanvasLayer(olplugin.layer)

    def filter(self, field, value, comparator=cmp):
        layer = self.catalogue_layer

        fids = layer.selectedFeaturesIds()
        for fid in fids:
            layer.deselect(fid)

        catalogue = self.catalogue_model.catalogue
        for i, fid in enumerate(catalogue.data['eventID']):
            if not comparator(catalogue.data[field][i], value):
                layer.select(fid)

        l = self.make_selection_layer()

        self.canvas.setLayerSet([l, QgsMapCanvasLayer(self.basemap_layer)])
        self.canvas.panToSelected(layer)

    def make_selection_layer(self):
        layer = self.catalogue_layer
        selection = self.selection_layer
        self.clear_features(selection)
        selection.startEditing()
        selection.addFeatures(layer.selectedFeatures())
        selection.commitChanges()
        selection.rendererV2().update_syms(self.catalogue_model.catalogue)

        return QgsMapCanvasLayer(selection)

    def clear_features(self, layer):
        layer.startEditing()

        if layer.featureCount():
            feat = QgsFeature()
            provider = layer.dataProvider()
            allAttrs = provider.attributeIndexes()
            provider.select(allAttrs)
            while provider.nextFeature(feat):
                layer.deleteFeature(feat.id())
        layer.commitChanges()

        assert layer.featureCount() == 0

    def select(self, fid):
        self.canvas.setLayerSet(
            [QgsMapCanvasLayer(self.catalogue_layer),
             QgsMapCanvasLayer(self.basemap_layer)])
        self.catalogue_layer.select(fid)
        self.canvas.panToSelected(self.catalogue_layer)

    def update_catalogue_layer(self, attr_names):
        """
        Update layer as in catalogue columns `attr_names` are changed
        """
        layer = self.catalogue_layer
        layer.startEditing()
        provider = layer.dataProvider()
        feat = QgsFeature()
        allAttrs = provider.attributeIndexes()
        provider.select(allAttrs)
        i = 0
        while provider.nextFeature(feat):
            attrs = {}
            for attr in attr_names:
                attrs[self.catalogue_model.field_idx(attr)] = QVariant(
                    self.catalogue_model.catalogue.data[attr][i])
            provider.changeAttributeValues({feat.id(): attrs})
            i = i + 1
        layer.commitChanges()
        layer.rendererV2().update_syms(self.catalogue_model.catalogue)
        layer.triggerRepaint()
        self.canvas.refresh()

    def show_tip(self, point):
        r = QgsRectangle()
        radius = self.canvas.extent().width() / 100 * 5  # 5% of the map width
        r.setXMinimum(point.x() - radius)
        r.setYMinimum(point.y() - radius)
        r.setXMaximum(point.x() + radius)
        r.setYMaximum(point.y() + radius)

        r = self.canvas.mapRenderer().mapToLayerCoordinates(
            self.catalogue_layer, r)

        feat = QgsFeature()
        self.catalogue_layer.select([0], r, True, True)
        self.catalogue_layer.nextFeature(feat)

        if feat.id():
            msg_lines = ["Event Found"]
            keys = self.catalogue_model.catalogue_keys()
            for k, v in feat.attributeMap().items():
                msg_lines.append("%s=%s" % (keys[k], v.toPyObject()))
        else:
            msg_lines = ["No Event found"]

        if self.raster_layer is not None:
            src = self.basemap_layer.layer().crs()
            dst = QgsCoordinateReferenceSystem(4326)
            trans = QgsCoordinateTransform(src, dst)
            point = trans.transform(point)

            ret, raster_data = self.raster_layer.layer().identify(point)

            if ret:
                for k, v in raster_data.items():
                    msg_lines.append("Smoothed=%s" % str(v))

        utils.alert('\n'.join(msg_lines))

    def dump(self, layer):
        provider = layer.dataProvider()
        feat = QgsFeature()
        allAttrs = provider.attributeIndexes()
        provider.select(allAttrs)
        while provider.nextFeature(feat):
            for k, v in feat.attributeMap().items():
                if k == 1 or k == 2:
                    print "Feature: %s" % feat.id()
                    print k, v.toPyObject()


class CatalogueRenderer(QgsFeatureRendererV2):
    SymbolKey = collections.namedtuple(
        'SymbolKey', 'cluster_index, cluster_flag, completeness_flag')

    def __init__(self, catalogue):
        QgsFeatureRendererV2.__init__(self, "CatalogueRenderer")
        self.default_point = QgsSymbolV2.defaultSymbol(QGis.Point)
        self.default_point.setColor(QtGui.QColor(0, 0, 0))

        self.syms = {self.SymbolKey(0, 0, True): self.default_point}

        self.cluster_index_idx = catalogue.field_idx('Cluster_Index')
        self.cluster_flag_idx = catalogue.field_idx('Cluster_Flag')
        self.comp_flag_idx = catalogue.field_idx('Completeness_Flag')
        self.catalogue = catalogue

    def symbolForFeature(self, feature):
        attrs = feature.attributeMap()
        if not attrs.keys():
            return

        cluster_index = int(attrs[self.cluster_index_idx].toPyObject())
        cluster_flag = int(attrs[self.cluster_flag_idx].toPyObject())
        comp_flag = not bool(attrs[self.comp_flag_idx].toPyObject())

        return self.syms.get(
            self.SymbolKey(cluster_index, cluster_flag, comp_flag),
            self.default_point)

    def update_syms(self, catalogue):
        self.syms = {}

        for cluster_flag in set(catalogue.data['Cluster_Flag'].tolist()):
            for cluster_index in set(catalogue.data['Cluster_Index'].tolist()):
                point = QgsSymbolV2.defaultSymbol(QGis.Point)
                point.setColor(self.catalogue.cluster_color(cluster_index))
                point.setSize(1)
                point.setAlpha(1 - 0.25 * cluster_flag)
                self.syms[
                    self.SymbolKey(cluster_index, cluster_flag, False)] = (
                        point)

                point = QgsSymbolV2.defaultSymbol(QGis.Point)
                point.setColor(self.catalogue.cluster_color(cluster_index))
                point.setSize(2)
                point.setAlpha(1 - 0.25 * cluster_flag)
                self.syms[
                    self.SymbolKey(cluster_index, cluster_flag, True)] = (
                        point)

    def startRender(self, context, _vlayer):
        for s in self.syms.values():
            s.startRender(context)

    def stopRender(self, context):
        for s in self.syms.values():
            s.stopRender(context)

    def usedAttributes(self):
        return ['id', 'Cluster_Index', 'Cluster_Flag', 'Completeness_Flag']

    def clone(self):
        return CatalogueRenderer(self.catalogue)


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
    gridded_vals = vals.reshape((nrows, ncols))

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
    layer.setDrawingStyle(QgsRasterLayer.SingleBandPseudoColor)
    layer.setColorShadingAlgorithm(QgsRasterLayer.PseudoColorShader)
    QgsMapLayerRegistry.instance().addMapLayer(layer)

    return layer
