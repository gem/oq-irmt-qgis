# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
import os.path

from PyQt4.QtCore import (QSettings,
                          QTranslator,
                          QCoreApplication,
                          qVersion,
                          QVariant)

from PyQt4.QtGui import (QApplication,
                         QAction,
                         QIcon,
                         QProgressDialog,
                         QMessageBox)

from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsRasterLayer,
                       QgsField,
                       QgsVectorDataProvider,
                       QgsFeature,
                       QgsGeometry,
                       QgsPoint,
                       QGis,
                       QgsFields)
from qgis.analysis import QgsZonalStatistics

import resources_rc

# Import the code for the dialog
from svirdialog import SvirDialog


class Svir:

    @staticmethod
    def tr(message):
        return QApplication.translate('Svir', message)

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'svir_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SvirDialog()

        self.loss_layer_is_vector = True
        # Input layer containing loss data
        self.loss_layer = None
        # Input layer specifying regions for aggregation
        self.aggregation_layer = None
        # Output layer containing aggregated loss data
        self.aggregation_loss_layer = None

    def initGui(self):
        # Create action that will start plugin configuration
        # PAOLO: test_action should probably be renamed into something
        # more meaningful
        self.test_action = QAction(
            QIcon(":/plugins/svir/icon.png"),
            u"Load data", self.iface.mainWindow())
        # connect the action to the run method
        self.test_action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.test_action)
        self.iface.addPluginToMenu(u"&SVIR", self.test_action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&SVIR", self.test_action)
        self.iface.removeToolBarIcon(self.test_action)

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.loss_layer_is_vector = self.dlg.loss_map_is_vector
            self.load_layers(self.dlg.ui.aggregation_layer_le.text(),
                             self.dlg.ui.loss_layer_le.text(),
                             self.loss_layer_is_vector)
            self.create_aggregation_loss_layer()
            self.calculate_stats()

    def load_layers(self, aggregation_layer_path,
                    loss_layer_path,
                    loss_layer_is_vector):
        # Load loss layer
        if loss_layer_is_vector:
            self.loss_layer = QgsVectorLayer(loss_layer_path,
                                             self.tr('Loss map'), 'ogr')
        else:
            self.loss_layer = QgsRasterLayer(loss_layer_path,
                                             self.tr('Loss map'))
        # Add loss layer to registry
        if self.loss_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.loss_layer)
        else:
            raise RuntimeError('Loss layer invalid')
        # Load aggregation layer
        self.aggregation_layer = QgsVectorLayer(aggregation_layer_path,
                                                self.tr('Regions'),
                                                'ogr')
        # Add aggregation layer to registry
        if self.aggregation_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.aggregation_layer)
        else:
            raise RuntimeError('Aggregation layer invalid')
        # Zoom depending on the aggregation layer's extent
        self.canvas.setExtent(self.aggregation_layer.extent())

    def create_aggregation_loss_layer(self):
        """
        Create a new aggregation loss layer which contains the polygons from
        the aggregation layer. Two new attributes (count and sum) are
        initialized to 0 and will represent the count of loss points in a
        region and the sum of loss values for the same region.
        """
        # create layer
        self.aggregation_loss_layer = QgsVectorLayer("Polygon",
                                                     "Aggregated Losses",
                                                     "memory")
        pr = self.aggregation_loss_layer.dataProvider()

        # Begin layer initialization
        self.aggregation_loss_layer.beginEditCommand("Layer initialization")

        # add count and sum fields for aggregate statistics
        pr.addAttributes(
            [QgsField("count", QVariant.Int),
             QgsField("sum",  QVariant.Double)])

        # copy regions from aggregation layer
        for region in self.aggregation_layer.getFeatures():
            feat = QgsFeature()
            # copy the polygon from the input aggregation layer
            feat.setGeometry(QgsGeometry(region.geometry()))
            # Define the count and sum fields to initialize to 0
            fields = QgsFields()
            fields.append(QgsField(QgsField("count", QVariant.Int)))
            fields.append(QgsField(QgsField("sum", QVariant.Double)))
            # Add fields to the new feature
            feat.setFields(fields)
            feat['count'] = 0
            feat['sum'] = 0.0
            # Add the new feature to the layer
            pr.addFeatures([feat])
            # Update the layer including the new feature
            self.aggregation_loss_layer.updateFeature(feat)

        # End layer initialization
        self.aggregation_loss_layer.endEditCommand()

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.aggregation_loss_layer.updateExtents()

        # Add aggregation loss layer to registry
        #if self.aggregation_loss_layer.isValid():
        if self.aggregation_loss_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(
                self.aggregation_loss_layer)
        else:
            raise RuntimeError('Aggregation loss layer invalid')

    def calculate_stats(self):
        if self.loss_layer_is_vector:
            self.calculate_vector_stats()
        else:
            self.calculate_raster_stats()

    def calculate_vector_stats(self):
        # get points from loss layer
        loss_features = self.loss_layer.getFeatures()
        # get regions from aggregation loss layer
        region_features = self.aggregation_loss_layer.getFeatures()
        dp = self.aggregation_loss_layer.dataProvider()
        caps = dp.capabilities()
        # For each region, check if loss points are inside the region and,
        # if so, increase attributes count and sum
        for region_feature in region_features:
            region_geometry = region_feature.geometry()
            for loss_feature in loss_features:
                point_geometry = loss_feature.geometry()
                print region_geometry.asPolygon()[0][0:3], \
                    point_geometry.asPoint()
                if region_geometry.contains(point_geometry):
                    # FIXME: Strangely it never enters here
                    print 'Here'
                    # TODO: Increase attributes count and sum for the region

    def calculate_raster_stats(self):
        zonal_statistics = QgsZonalStatistics(
            self.aggregation_layer,
            self.loss_layer.dataProvider().dataSourceUri())
        progress_dialog = QProgressDialog(
            self.tr('Calculating zonal statistics'),
            self.tr('Abort...'),
            0,
            0)
        zonal_statistics.calculateStatistics(progress_dialog)
        if progress_dialog.wasCanceled():
            QMessageBox.error(
                self, self.tr('ZonalStats: Error'),
                self.tr('You aborted aggregation, '
                        'so there are no data for analysis. Exiting...'))