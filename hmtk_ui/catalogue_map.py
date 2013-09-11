from PyQt4 import QtGui
from PyQt4.QtCore import (QVariant,)

from qgis.core import (
    QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
    QgsPoint, QgsMapLayerRegistry, QgsPluginLayerRegistry,
    QgsFeatureRendererV2, QgsSymbolV2, QGis)
from qgis.gui import QgsMapCanvasLayer

from openlayers_plugin.openlayers_plugin import (
    OpenlayersPlugin, OpenlayersPluginLayerType)

import numpy

import utils


class CatalogueMap(object):
    def __init__(self, canvas, catalogue_model):
        self.canvas = canvas
        self.catalogue_model = catalogue_model

        self.catalogue_layer = QgsVectorLayer(
            'Point?crs=epsg:4326', "catalogue", 'memory')

        QgsMapLayerRegistry.instance().addMapLayer(self.catalogue_layer)
        self.selection_layer = QgsVectorLayer(
            'Point?crs=epsg:4326', "selection", 'memory')
        QgsMapLayerRegistry.instance().addMapLayer(self.selection_layer)
        self.selection_layer.setRendererV2(CatalogueRenderer(
            self.catalogue_model))

        layer = self.load_catalogue(catalogue_model.catalogue)
        base_map = self.load_basemap()
        self.canvas.setLayerSet([layer, base_map])
        self.canvas.refresh()
        self.canvas.zoomByFactor(1.1)

    def load_catalogue(self, catalogue):
        vl = self.catalogue_layer
        self.populate_layer(vl, catalogue)
        layer = QgsMapCanvasLayer(vl)
        vl.setRendererV2(CatalogueRenderer(self.catalogue_model))
        vl.updateExtents()
        self.catalogue_layer = vl
        self.canvas.setLayerSet([layer])
        self.canvas.setExtent(vl.extent())
        self.canvas.refresh()

        return layer

    def populate_layer(self, vl, catalogue):
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

            for j, key in enumerate(sorted(catalogue.data.keys())):
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
        self.populate_layer(vl, catalogue_model.catalogue)
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

        print "select layer count %d" % selection.featureCount()
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

    @property
    def basemap_layer(self):
        return self.canvas.layer(1)

    def select(self, fid):
        self.canvas.setLayerSet(
            [QgsMapCanvasLayer(self.catalogue_layer),
             QgsMapCanvasLayer(self.basemap_layer)])
        self.catalogue_layer.select(fid)
        self.canvas.panToSelected(self.catalogue_layer)

    def update_catalogue_layer(self, attr_names):
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
    def __init__(self, catalogue):
        QgsFeatureRendererV2.__init__(self, "CatalogueRenderer")
        defaultPoint = QgsSymbolV2.defaultSymbol(QGis.Point)
        defaultPoint.setColor(QtGui.QColor(0, 0, 0))

        self.uncompletePoint = QgsSymbolV2.defaultSymbol(QGis.Point)
        self.uncompletePoint.setColor(QtGui.QColor(200, 200, 200))

        self.syms = [defaultPoint]
        self.cluster_index_idx = catalogue.field_idx('Cluster_Index')
        self.cluster_flag_idx = catalogue.field_idx('Cluster_Flag')
        self.comp_flag_idx = catalogue.field_idx('Completeness_Flag')
        self.catalogue = catalogue

    def symbolForFeature(self, feature):
        attrs = feature.attributeMap()
        if not attrs.keys():
            return
        if self.catalogue.completeness_table is not None:
            if attrs[self.comp_flag_idx].toPyObject():
                return self.uncompletePoint
            else:
                return self.syms[0]
        else:
            index = int(attrs[self.cluster_index_idx].toPyObject())
            index = index * 2
            if len(self.syms) > index:
                if attrs[self.cluster_flag_idx].toPyObject():
                    index = index - 1
            else:
                index = 0

            return self.syms[index]

    def update_syms(self, catalogue):
        cluster_nr = int(max(catalogue.data['Cluster_Index']))

        self.syms = [self.syms[0]]

        for cluster in range(cluster_nr):
            point = QgsSymbolV2.defaultSymbol(QGis.Point)
            point.setColor(self.catalogue.cluster_color(cluster))
            point.setSize(2)
            point.setAlpha(0.75)
            self.syms.append(point)

            point = QgsSymbolV2.defaultSymbol(QGis.Point)
            point.setColor(self.catalogue.cluster_color(cluster))
            point.setSize(3)
            self.syms.append(point)

    def startRender(self, context, _vlayer):
        for s in self.syms:
            s.startRender(context)

    def stopRender(self, context):
        for s in self.syms:
            s.stopRender(context)

    def usedAttributes(self):
        return ['id', 'Cluster_Index', 'Cluster_Flag', 'Completeness_Flag']

    def clone(self):
        return CatalogueRenderer(self.catalogue)
