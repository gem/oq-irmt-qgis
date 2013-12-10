# -*- coding: utf-8 -*-
# Copyright (c) 2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
# Import the PyQt and QGIS libraries
from PyQt4 import QtCore, QtGui
from qgis.core import *
# Initialize Qt resources from file resources.py, used for side-effects
import resources_rc
# Import the code for the dialog
from download_exposure import ExposureDownloader, ExposureDownloadError
from platform_settings import PlatformSettingsDialog
from extentSelector import ExtentSelector


class Dock(QtGui.QDockWidget):
    def __init__(self, iface, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.extentSelector = ExtentSelector(self.canvas)
        self.extentSelector.tool.rectangleCreated.connect(self.polygonCreated)
        self.setupUi()

    def setupUi(self):
        self.resize(200, 200)
        self.setWindowTitle('Exposure')
        self.drawBtn = QtGui.QPushButton(self)
        self.drawBtn.setObjectName('drawBtn')
        self.drawBtn.setText('Draw')

        self.downloadBtn = QtGui.QPushButton(self)
        self.downloadBtn.setObjectName('downloadBtn')
        self.downloadBtn.setText('Download')

        self.clearBtn = QtGui.QPushButton(self)
        self.clearBtn.setObjectName('clearBtn')
        self.clearBtn.setText('Clear')

        self.contents = QtGui.QGroupBox(self)
        self.layout = QtGui.QVBoxLayout(self.contents)
        self.layout.addWidget(self.drawBtn)
        self.layout.addWidget(self.downloadBtn)
        self.layout.addWidget(self.clearBtn)
        self.setWidget(self.contents)

        QtCore.QMetaObject.connectSlotsByName(self)

    def enableBusyCursor(self):
        """Set the hourglass enabled and stop listening for layer changes."""
        QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

    def disableBusyCursor(self):
        """Disable the hourglass cursor and listen for layer changes."""
        QtGui.qApp.restoreOverrideCursor()

    @QtCore.pyqtSlot()
    def on_downloadBtn_clicked(self):
        qs = QtCore.QSettings()
        hostname = qs.value('download_exposure/hostname', '')
        username = qs.value('download_exposure/username', '')
        password = qs.value('download_exposure/password', '')
        if not (hostname and username and password):
            dialog = PlatformSettingsDialog(self.iface)
            if dialog.exec_():
                self.show_exposure(hostname, username, password)
        else:
            self.show_exposure(hostname, username, password)
        self.extentSelector.stop()

    @QtCore.pyqtSlot()
    def on_drawBtn_clicked(self):
        self.extentSelector.start()
        self.extentSelector.getExtent()

    @QtCore.pyqtSlot()
    def on_clearBtn_clicked(self):
        self.extentSelector.stop()
        self.downloadBtn.setEnabled(False)

    def polygonCreated(self):
        self.downloadBtn.setEnabled(True)

    def selectedExtent(self):
        return self.extentSelector.getExtent()

    def show_exposure(self, hostname, username, password):
        self.enableBusyCursor()
        try:
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
            xform = QgsCoordinateTransform(
                crs, QgsCoordinateReferenceSystem(4326))
            extent = xform.transform(self.selectedExtent())
            lon_min, lon_max = extent.xMinimum(), extent.xMaximum()
            lat_min, lat_max = extent.yMinimum(), extent.yMaximum()

            # download data
            ed = ExposureDownloader(hostname)
            ed.login(username, password)
            try:
                fname = ed.download(lat_min, lon_min, lat_max, lon_max)
            except ExposureDownloadError as e:
                QtGui.QMessageBox.warning(
                    self, 'Exposure Download Error', str(e))
                return
            # don't remove the file, otherwise there will concurrency problems
            uri = 'file://%s?delimiter=%s&xField=%s&yField=%s&crs=epsg:4326&' \
                'skipLines=25&trimFields=yes' % (fname, ',', 'lon', 'lat')
            vlayer = QgsVectorLayer(uri, 'exposure_export', 'delimitedtext')
            QgsMapLayerRegistry.instance().addMapLayer(vlayer)
        finally:
            self.disableBusyCursor()


class ExposureTool(QtGui.QWidget):
    def __init__(self, iface, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.iface = iface
        self.plugin_dir = QtCore.QFileInfo(
            QgsApplication.qgisUserDbFilePath()
        ).path() + "/python/plugins/download_exposure"
        localePath = ""
        locale = str(QtCore.QSettings().value("locale/userLocale"))[0:2]
        if QtCore.QFileInfo(self.plugin_dir).exists():
            localePath = (self.plugin_dir + "/i18n/download_exposure_" +
                          locale + ".qm")

        if QtCore.QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.dock = Dock(self.iface)
        self.dock.setVisible(True)
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

    def initGui(self):
        self.get_platform_settings = QtGui.QAction(
            QtGui.QIcon(":/plugins/download_exposure/icon.png"),
            u"Settings for the GEM platform", self.iface.mainWindow())
        self.get_platform_settings.triggered.connect(self.platform_settings)

        # Add toolbar button and menu item
        self.iface.addPluginToMenu(
            u"&download_exposure", self.get_platform_settings)

        # display world map
        QtCore.QObject.connect(
            self.iface, QtCore.SIGNAL('initializationCompleted()'),
            self.load_countries)

    def unload(self):
        self.iface.removePluginMenu(
            u"&download_exposure", self.get_platform_settings)

    def platform_settings(self):
        dialog = PlatformSettingsDialog(self.iface)
        dialog.exec_()

    def closeEvent(self, event):
        self.emit(QtCore.SIGNAL("closed()"), self)
        return QtGui.QDockWidget.closeEvent(self, event)

    def load_countries(self):
        display_name = 'Population density'
        uri = os.path.join(self.data_dir, 'Countries.shp')
        vlayer = QgsVectorLayer(uri, display_name, 'ogr')
        QgsMapLayerRegistry.instance().addMapLayers([vlayer])
