import sys
import uuid

from qgis.core import QgsApplication
from PyQt4 import QtGui, QtCore, Qt
from qgis.gui import QgsMapCanvas, QgsMapCanvasLayer
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsField, \
    QgsGeometry, QgsFeature, QgsPoint, QgsRectangle
from ui_canvas import Ui_MainWindow


# Path to local QGIS install
QGIS_PREFIX = '/usr/local/qgis-master'
DATA_DIR = '/home/marco/dev/qgis-plugins/oq-eqcatalogue-tool/openquake/qgis/' \
           'gemcatalogue/data/'

DATA = [
    (15, 15, 0.3),
    (15, 20, 0.4),
    (20, 15, 0.35)]


class MainWindow(Ui_MainWindow, QtGui.QMainWindow):
    def __init__(self, splash):
        QtGui.QMainWindow.__init__(self)

        # required by Qt4 to initialize the UI
        self.setupUi(self)
        self.splash = splash

        # create map canvas
        self.canvas = QgsMapCanvas(self)
        self.canvas.setCanvasColor(QtGui.QColor(255, 255, 255))
        self.canvas.enableAntiAliasing(True)
        self.canvas.show()
        self.canvas.parentWin = self
        self.srs = None

        # lay our widgets out in the main window
        self.layout = QtGui.QVBoxLayout(self.widget)
        self.layout.addWidget(self.canvas)
        # We need to initialize the window sizes

        ## A place to store polygons we capture
        #self.capturedPolygons = []
        #self.capturedPolygonsPennies = []
        #self.capturedPolygonsRub = []
        #
        ## Interview info to write in shapefile
        #self.interviewInfo = []

        self.layers = []

        # Legend for displaying layers
        # self.legend = Legend(self)
        #
        # # New Map Tools
        # self.maptools = MapTools(self)
        #
        # # New Map Coords display in status bar
        # self.mapcoords = MapCoords(self)

        # self.load_countries()
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
        self.layers.insert(0, cl)
        self.canvas.setLayerSet(self.layers)
        vlayer.triggerRepaint()

    def load_countries(self):
        display_name = 'Population density'
        uri = DATA_DIR + 'Countries.shp'
        vlayer = QgsVectorLayer(uri, display_name, 'ogr')
        QgsMapLayerRegistry.instance().addMapLayers([vlayer])
        vlayer.updateExtents()
        self.canvas.setExtent(vlayer.extent())
        # set the map canvas layer set
        cl = QgsMapCanvasLayer(vlayer)
        self.layers.insert(0, cl)
        self.canvas.setLayerSet(self.layers)
        vlayer.triggerRepaint()


# Main entry to program.  Set up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv, True)

    # Set the app style
    mySplashPix = QtGui.QPixmap(QtCore.QString(DATA_DIR + '/OCEAN.png'))
    mySplashPixScaled = mySplashPix.scaled(500, 300, Qt.Qt.KeepAspectRatio)
    mySplash = QtGui.QSplashScreen(mySplashPixScaled)
    mySplash.show()

    # initialize qgis libraries
    QgsApplication.setPrefixPath(QGIS_PREFIX, True)
    QgsApplication.initQgis()

    # create main window
    wnd = MainWindow(mySplash)
    wnd.show()

    # Create signal for app finish
    app.connect(
        app, QtCore.SIGNAL('lastWindowClosed()'), app, QtCore.SLOT('quit()'))

    # Start the app up
    retval = app.exec_()

    # We got an exit signal so time to clean up
    QgsApplication.exitQgis()

    sys.exit(retval)


if __name__ == '__main__':
    main(sys.argv)
