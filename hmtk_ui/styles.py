import collections
from PyQt4 import QtGui

from qgis.core import (
    QGis,
    QgsSymbolV2, QgsGraduatedSymbolRendererV2,
    QgsMarkerSymbolV2,
    QgsFeatureRendererV2, QgsVectorGradientColorRampV2)


class CatalogueDepthMagnitudeRenderer(QgsGraduatedSymbolRendererV2):
    """
    Render events depending on their depth/magnitude
    """

    @classmethod
    def make(cls, catalogue_map):
        layer = catalogue_map.catalogue_layer
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        ramp = QgsVectorGradientColorRampV2.create(
            dict(color1='white', color2='blue'))

        symbol.setSize(0.15)
        # number of color classes = 8
        renderer = cls.createRenderer(
            layer, "depth", 8,
            QgsGraduatedSymbolRendererV2.Quantile, symbol, ramp)

        renderer.setSizeScaleField("_magnitude")
        renderer.setScaleMethod(QgsSymbolV2.ScaleDiameter)
        renderer.update_syms = lambda x: x

        return renderer


class CatalogueCompletenessRenderer(QgsFeatureRendererV2):
    """
    Render events depending on their completeness attributes
    """

    @classmethod
    def make(cls, _catalogue_map):
        return cls()

    def update_syms(self, _catalogue):
        pass

    def __init__(self):
        QgsFeatureRendererV2.__init__(self, "CatalogueCompletenessRenderer")
        complete = QgsSymbolV2.defaultSymbol(QGis.Point)
        uncomplete = QgsMarkerSymbolV2.createSimple(
            {'color': 'blue', 'name': 'triangle'})
        uncomplete.setSize(3)
        complete.setSize(1.5)
        complete.setColor(QtGui.QColor(255, 0, 0, 125))
        self.syms = [complete, uncomplete]

    def symbolForFeature(self, feature):
        return self.syms[int(feature['Completeness_Flag'])]

    def startRender(self, context, _vlayer):
        for s in self.syms:
            s.startRender(context)

    def stopRender(self, context):
        for s in self.syms:
            s.stopRender(context)

    def usedAttributes(self):
        return ['Completeness_Flag']

    def clone(self):
        return CatalogueCompletenessRenderer()


class CatalogueDefaultRenderer(QgsFeatureRendererV2):
    @classmethod
    def make(cls, _catalogue_map):
        return cls()

    def __init__(self):
        QgsFeatureRendererV2.__init__(self, "CatalogueDefaultRenderer")
        self.sym = QgsSymbolV2.defaultSymbol(QGis.Point)

    def symbolForFeature(self, _feature):
        return self.sym

    def update_syms(self, _catalogue):
        pass

    def startRender(self, context, _vlayer):
        self.sym.startRender(context)

    def stopRender(self, context):
        self.sym.stopRender(context)

    def usedAttributes(self):
        return []

    def clone(self):
        return CatalogueDefaultRenderer()


class CatalogueClusterRenderer(QgsFeatureRendererV2):
    """
    Render events depending on their cluster attributes
    """
    Cluster = collections.namedtuple('Cluster', 'index flag')

    @classmethod
    def make(cls, catalogue_map):
        return cls(catalogue_map.catalogue_model)

    def __init__(self, catalogue_model):
        QgsFeatureRendererV2.__init__(self, "CatalogueClusterRenderer")
        self.catalogue_model = catalogue_model
        self.syms = {}
        self.update_syms(catalogue_model.catalogue)

    def symbolForFeature(self, feature):
        return self.syms[
            self.Cluster(feature["Cluster_Index"], feature["Cluster_Flag"])]

    def update_syms(self, catalogue):
        self.syms = {}

        for flag in set(catalogue.data['Cluster_Flag'].tolist()):
            for index in set(catalogue.data['Cluster_Index'].tolist()):

                # main shock
                point = QgsMarkerSymbolV2.createSimple(
                    {'color': 'blue', 'name': 'square'})

                if index:  # belongs to a cluster
                    color = self.catalogue_model.cluster_color(index)

                    # non poissonian
                    if flag:
                        point = QgsMarkerSymbolV2.createSimple(
                            {'color': 'blue', 'name': 'triangle'})
                    color.setAlpha(125 + 125 * abs(flag))
                    point.setSize(3)
                    point.setColor(color)
                else:
                    point = QgsSymbolV2.defaultSymbol(QGis.Point)
                    point.setColor(QtGui.QColor("0,0,0,125"))
                    point.setSize(1.5)
                self.syms[self.Cluster(index, flag)] = point

    def startRender(self, context, _vlayer):
        for s in self.syms.values():
            s.startRender(context)

    def stopRender(self, context):
        for s in self.syms.values():
            s.stopRender(context)

    def usedAttributes(self):
        return ['Cluster_Index', 'Cluster_Flag']

    def clone(self):
        return CatalogueClusterRenderer(self.catalogue_model)
