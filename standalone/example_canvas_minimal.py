import os
import sys
import uuid

from PyQt4 import QtGui, QtCore
from qgis.gui import QgsMapCanvasLayer
from qgis.core import QgsApplication, QgsVectorLayer, QgsMapLayerRegistry, \
    QgsField, QgsGeometry, QgsFeature, QgsPoint
from ui_mainwindowminimal import Ui_MainWindowMinimal


QGIS_PREFIX_PATH = os.environ['QGIS_PREFIX_PATH']

DATA = [
    (15, 15, 0.3),
    (15, 20, 0.4),
    (20, 15, 0.35)]


class MainWindow(Ui_MainWindowMinimal, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        # required by Qt4 to initialize the UI
        self.setupUi(self)

        # map canvas is created in UI file
        self.canvas.setCanvasColor(QtGui.QColor(255, 255, 255))
        self.canvas.enableAntiAliasing(True)

        self.create_layer(DATA)

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
        cl = QgsMapCanvasLayer(vlayer)
        self.canvas.setLayerSet([cl])
        vlayer.triggerRepaint()


# Main entry to program.  Set up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv, True)

    # Set the app style

    # initialize qgis libraries
    QgsApplication.setPrefixPath(QGIS_PREFIX_PATH, True)
    QgsApplication.initQgis()

    # create main window
    wnd = MainWindow()
    wnd.show()

    # Start the app up
    retval = app.exec_()

    # We got an exit signal so time to clean up
    QgsApplication.exitQgis()

    sys.exit(retval)


if __name__ == '__main__':
    main(sys.argv)
