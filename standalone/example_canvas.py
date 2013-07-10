import sys
import uuid

from qgis.core import QgsApplication
from PyQt4 import QtGui, QtCore
from qgis.gui import QgsMapCanvas
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsField, \
    QgsGeometry, QgsFeature, QgsPoint
from ui_canvas import Ui_MainWindow


DATA = [
    (15, 15, 0.3),
    (15, 20, 0.4),
    (20, 15, 0.35)]


class MainWindow(Ui_MainWindow, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.canvas = QgsMapCanvas()
        self.canvas.setCanvasColor(QtGui.QColor(255, 255, 255))
        self.canvas.enableAntiAliasing(True)

    def create_layer(self, data):
        display_name = 'some-layer'
        uri = 'Point?crs=epsg:4326&index=yes&uuid=%s' % uuid.uuid4()
        vlayer = QgsVectorLayer(uri, display_name, 'memory')
        QgsMapLayerRegistry.instance().addMapLayer(vlayer)

        provider = vlayer.dataProvider()
        vlayer.startEditing()
        provider.addAttributes([
            QgsField('population_density', QtCore.QVariant.Double),
        ])
        features = []
        for x, y, density in data:
            feat = QgsFeature()
            geom = QgsGeometry.fromPoint(QgsPoint(x, y))
            feat.setGeometry(geom)
            feat.setAttributes([density])
            features.append(feat)
        provider.addFeatures(features)
        vlayer.commitChanges()
        vlayer.updateExtents()
        self.canvas.setExtent(vlayer.extent())
        vlayer.triggerRepaint()

    def load_countries(self):
        display_name = 'Population density'
        uri = '/home/michele/oq-eqcatalogue-tool/openquake/qgis/gemcatalogue/data/Countries.shp'
        vlayer = QgsVectorLayer(uri, display_name, 'ogr')
        QgsMapLayerRegistry.instance().addMapLayers([vlayer])


def main():
    app = QtGui.QApplication(sys.argv, True)
    # supply path to where is your qgis installed
    QgsApplication.setPrefixPath("/usr", True)
    # load providers
    QgsApplication.initQgis()
    # print QgsApplication.showSettings()
    mw = MainWindow()
    try:
        # mw.create_layer(DATA)
        mw.load_countries()
        mw.show()
        app.exec_()
    finally:
        QgsApplication.exitQgis()

if __name__ == '__main__':
    main()
    # launch with PYTHONPATH=/usr/share/qgis/python python example.py
