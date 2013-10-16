import collections
from PyQt4 import QtGui

from qgis.core import (
    QGis,
    QgsSymbolV2, QgsGraduatedSymbolRendererV2,
    QgsFeatureRendererV2, QgsVectorGradientColorRampV2)


class CatalogueDepthMagnitudeRenderer(QgsGraduatedSymbolRendererV2):
    """
    Render events depending on their depth/magnitude
    """

    @classmethod
    def create_renderer(cls, layer, catalogue, display_field):
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        ramp = QgsVectorGradientColorRampV2.create(
            dict(color1='red', color2='blue'))
        # number of color classes = 8
        renderer = cls.createRenderer(
            layer, "depth", 8,
            QgsGraduatedSymbolRendererV2.Quantile, symbol, ramp)

        renderer.setSizeScaleField(display_field)

        return renderer


class CatalogueCompletenessRenderer(QgsGraduatedSymbolRendererV2):
    """
    Render events depending on their completeness attributes
    """
    @classmethod
    def create(cls, layer):
        color1 = QtGui.QColor("red")
        color2 = QtGui.QColor("blue")
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        return cls.createRenderer(
            layer, "Completeness_Flag", 3,
            QgsGraduatedSymbolRendererV2.Quantile,
            QgsSymbolV2.defaultSymbol(layer.geometryType()),
            ramp)


class CatalogueClusterRenderer(QgsFeatureRendererV2):
    """
    Render events depending on their cluster attributes
    """
    Cluster = collections.namedtuple('Cluster', 'index flag')

    def __init__(self, catalogue):
        QgsFeatureRendererV2.__init__(self, "CatalogueClusterRenderer")
        self.default_point = QgsSymbolV2.defaultSymbol(QGis.Point)
        self.default_point.setColor(QtGui.QColor(0, 0, 0))

        self.syms = {self.Cluster(0, 0, True): self.default_point}
        self.catalogue = catalogue

    def symbolForFeature(self, feature):
        index = feature["Cluster_Index"]
        flag = feature["Cluster_Flag"]

        return self.syms.get(self.Cluster(index, flag), self.default_point)

    def update_syms(self, catalogue):
        self.syms = {}

        for flag in set(catalogue.data['Cluster_Flag'].tolist()):
            for index in set(catalogue.data['Cluster_Index'].tolist()):
                point = QgsSymbolV2.defaultSymbol(QGis.Point)
                point.setColor(self.catalogue.cluster_color(index))

                point.setSize(1 + 2 * (1 - abs(flag)))
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
        return CatalogueClusterRenderer(self.catalogue)
