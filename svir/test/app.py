import sys

from PyQt4 import QtGui, QtCore
from qgis.core import QgsApplication
from qgis.gui import QgsMapCanvas

from PyQt4.QtCore import QObject, SIGNAL, pyqtSlot
from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMapCanvasLayer


class QgisInterface(QObject):
    """Class to expose qgis objects and functionalities to plugins.

    This class is here for enabling us to run unit tests only,
    so most methods are simply stubs.
    """

    def __init__(self, canvas):
        QObject.__init__(self)
        self.canvas = canvas
        # Set up slots so we can mimick the behaviour of QGIS when layers
        # are added.
        QObject.connect(QgsMapLayerRegistry.instance(),
                        SIGNAL('layersAdded(QList<QgsMapLayer *>)'),
                        self.addLayers)
        QObject.connect(QgsMapLayerRegistry.instance(),
                        SIGNAL('layerWasAdded(QgsMapLayer *)'),
                        self.addLayer)

    @pyqtSlot(list)
    def addLayers(self, theLayers):
        """Handle layers being added to the registry so they show up in canvas.

        .. note: The QgsInterface api does not include this method, it is added
                 here as a helper to facilitate testing.

        Args:
            theLayers: list<QgsMapLayer> list of map layers that were added

        Returns:
            None

        Raises:
            None
        """
        myLayers = self.canvas.layers()
        myCanvasLayers = []
        for myLayer in myLayers:
            myCanvasLayers.append(QgsMapCanvasLayer(myLayer))
        for myLayer in theLayers:
            myCanvasLayers.append(QgsMapCanvasLayer(myLayer))

        self.canvas.setLayerSet(myCanvasLayers)

    @pyqtSlot('QgsMapLayer')
    def addLayer(self, theLayer):
        """Handle a layer being added to the registry so it shows up in canvas.

        .. note: The QgsInterface api does not include this method, it is added
                 here as a helper to facilitate testing.

        .. note: The addLayer method was deprecated in QGIS 1.8 so you should
                 not need this method much.

        Args:
            theLayers: list<QgsMapLayer> list of map layers that were added

        Returns:
            None

        Raises:
            None
        """
        pass

    # ---------------- API Mock for QgsInterface follows -------------------

    def zoomFull(self):
        """Zoom to the map full extent"""
        pass

    def zoomToPrevious(self):
        """Zoom to previous view extent"""
        pass

    def zoomToNext(self):
        """Zoom to next view extent"""
        pass

    def zoomToActiveLayer(self):
        """Zoom to extent of active layer"""
        pass

    def addVectorLayer(self, vectorLayerPath, baseName, providerKey):
        """Add a vector layer"""
        pass

    def addRasterLayer(self, rasterLayerPath, baseName):
        """Add a raster layer given a raster layer file name"""
        pass

    def activeLayer(self):
        """Get pointer to the active layer (layer selected in the legend)"""
        myLayers = QgsMapLayerRegistry.instance().mapLayers()
        for myItem in myLayers:
            return myLayers[myItem]

    def addToolBarIcon(self, qAction):
        """Add an icon to the plugins toolbar"""
        pass

    def removeToolBarIcon(self, qAction):
        """Remove an action (icon) from the plugin toolbar"""
        pass

    def addToolBar(self, name):
        """Add toolbar with specified name"""
        pass

    def mapCanvas(self):
        """Return a pointer to the map canvas"""
        return self.canvas

    def mainWindow(self):
        """Return a pointer to the main window

        In case of QGIS it returns an instance of QgisApp
        """
        pass


QGISAPP = None
CANVAS = None
IFACE = None
PARENT = None


def getTestApp():
    """
    Start one QGis application to test agaist.
    If QGis is already running the handle to that app will be returned
    """

    global QGISAPP  # pylint: disable=W0603

    if QGISAPP is None:
        myGuiFlag = True  # All test will run qgis in safe_qgis mode
        QGISAPP = QgsApplication(sys.argv, myGuiFlag)
        QGISAPP.initQgis()
        # print QGISAPP.showSettings()

    global PARENT  # pylint: disable=W0603
    if PARENT is None:
        PARENT = QtGui.QWidget()

    global CANVAS  # pylint: disable=W0603
    if CANVAS is None:
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QtCore.QSize(400, 400))

    global IFACE  # pylint: disable=W0603
    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        IFACE = QgisInterface(CANVAS)

    return QGISAPP, CANVAS, IFACE, PARENT
