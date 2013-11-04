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
                       QgsFeature,
                       QgsGeometry,
                       QgsFields,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       QgsVectorDataProvider)

from qgis.gui import QgsMessageBar

from qgis.analysis import QgsZonalStatistics

import resources_rc

# Import the code for the dialog
from svirdialog import SvirDialog

# Name of the attribute, in the input loss data layer, containing loss info
LOSS_ATTRIBUTE_NAME = "RSCORE"  # "loss"
REGION_ID_ATTRIBUTE_NAME = "STFID"


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
        self.regions_layer = None
        # Output layer containing aggregated loss data
        self.aggregation_layer = None
        self.initial_action = None
        self.purge_empty_regions_action = None

    def initGui(self):
        # Create action that will start plugin configuration
        self.initial_action = QAction(
            QIcon(":/plugins/svir/icon.png"),
            u"Load data", self.iface.mainWindow())
        # connect the action to the run method
        self.initial_action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.initial_action)
        self.iface.addPluginToMenu(u"&SVIR", self.initial_action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&SVIR", self.initial_action)
        self.iface.removeToolBarIcon(self.initial_action)
        self.iface.removePluginMenu(u"&SVIR",
                                    self.purge_empty_regions_action)
        self.iface.removeToolBarIcon(self.purge_empty_regions_action)

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.loss_layer_is_vector = self.dlg.loss_map_is_vector
            self.load_layers(self.dlg.ui.regions_layer_le.text(),
                             self.dlg.ui.loss_layer_le.text(),
                             self.loss_layer_is_vector)
            self.create_aggregation_layer()
            self.calculate_stats()
            # Create and enable toolbar button and menu item
            # for purging empty regions
            # Create action
            self.purge_empty_regions_action = QAction(
                QIcon(":/plugins/svir/icon.png"),
                u"Purge empty regions",
                self.iface.mainWindow())
            # Connect the action to the purge_empty_regions method
            self.purge_empty_regions_action.triggered.connect(
                self.purge_empty_regions)
            # Add toolbar button and menu item
            self.iface.addToolBarIcon(self.purge_empty_regions_action)
            self.iface.addPluginToMenu(u"&SVIR",
                                       self.purge_empty_regions_action)
            msg = 'Select "Purge empty regions" from SVIR plugin menu ' \
                  'to remove regions containing no loss points'
            self.iface.messageBar().pushMessage(self.tr("Info"),
                                            self.tr(msg),
                                            level=QgsMessageBar.INFO)

    def load_layers(self, aggregation_layer_path,
                    loss_layer_path,
                    loss_layer_is_vector):
        # Load aggregation layer
        self.regions_layer = QgsVectorLayer(aggregation_layer_path,
                                            self.tr('Regions'), 'ogr')
        # Add aggregation layer to registry
        if self.regions_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.regions_layer)
        else:
            raise RuntimeError('Aggregation layer invalid')
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
        # Zoom depending on the regions layer's extent
        self.canvas.setExtent(self.regions_layer.extent())

    def create_aggregation_layer(self):
        """
        Create a new aggregation layer which contains the polygons from
        the regions layer. Two new attributes (count and sum) are
        initialized to 0 and will represent the count of loss points in a
        region and the sum of loss values for the same region.
        """
        # create layer
        self.aggregation_layer = QgsVectorLayer("Polygon",
                                                "Aggregated Losses",
                                                "memory")
        pr = self.aggregation_layer.dataProvider()
        caps = pr.capabilities()

        # Begin layer initialization
        self.aggregation_layer.startEditing()
        self.aggregation_layer.beginEditCommand("Layer initialization")

        # add count and sum fields for aggregating statistics
        pr.addAttributes(
            [QgsField(REGION_ID_ATTRIBUTE_NAME, QVariant.String),
             QgsField("count", QVariant.Int),
             QgsField("sum",  QVariant.Double)])

        # copy regions from aggregation layer
        for region_feature in self.regions_layer.getFeatures():
            feat = QgsFeature()
            # copy the polygon from the input aggregation layer
            feat.setGeometry(QgsGeometry(region_feature.geometry()))
            # Define the count and sum fields to initialize to 0
            fields = QgsFields()
            fields.append(QgsField(QgsField(REGION_ID_ATTRIBUTE_NAME,
                                             QVariant.String)))
            fields.append(QgsField(QgsField("count", QVariant.Int)))
            fields.append(QgsField(QgsField("sum", QVariant.Double)))
            # Add fields to the new feature
            feat.setFields(fields)
            feat[REGION_ID_ATTRIBUTE_NAME] = region_feature[REGION_ID_ATTRIBUTE_NAME]
            feat['count'] = 0
            feat['sum'] = 0.0
            # Add the new feature to the layer
            if caps & QgsVectorDataProvider.AddFeatures:
                pr.addFeatures([feat])
            # Update the layer including the new feature
            self.aggregation_layer.updateFeature(feat)

        # End layer initialization
        self.aggregation_layer.endEditCommand()
        self.aggregation_layer.commitChanges()

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.aggregation_layer.updateExtents()

        # Add aggregation layer to registry
        if self.aggregation_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.aggregation_layer)
        else:
            raise RuntimeError('Aggregation layer invalid')

    def calculate_stats(self):
        if self.loss_layer_is_vector:
            self.calculate_vector_stats()
        else:
            self.calculate_raster_stats()

    def calculate_vector_stats(self):
        # get points from loss layer
        loss_features = self.loss_layer.getFeatures()
        # get regions from aggregation layer
        region_features = self.aggregation_layer.getFeatures()

        # create spatial index
        spatial_index = QgsSpatialIndex()
        for loss_feature in loss_features:
            spatial_index.insertFeature(loss_feature)
        loss_features.rewind()      # reset iterator

        # Begin updating count and sum attributes
        self.aggregation_layer.startEditing()
        self.aggregation_layer.beginEditCommand(
            "Edit count and sum attributes")

        # check if there are no loss points contained in any of the regions
        # and later display a warning if that occurs
        no_loss_points_in_any_region = True
        for region_feature in region_features:
            points_count = 0
            loss_sum = 0
            has_intersections = False
            region_geometry = region_feature.geometry()
            # Find ids of points within the bounding box of the region
            point_ids = spatial_index.intersects(region_geometry.boundingBox())
            if len(point_ids) > 0:
                has_intersections = True
            if has_intersections:
                # For points that are within the bounding box of the region
                for point_id in point_ids:
                    # Get the point feature by the point's id
                    request = QgsFeatureRequest().setFilterFid(point_id)
                    point_feature = self.loss_layer.getFeatures(request).next()
                    point_geometry = QgsGeometry(point_feature.geometry())
                    # check if the point is actually inside the region and
                    # it is not only contained by its bounding box
                    if region_geometry.contains(point_geometry):
                        points_count += 1
                        # we have found at least one loss point inside a region
                        no_loss_points_in_any_region = False
                        point_loss = point_feature[LOSS_ATTRIBUTE_NAME]
                        loss_sum += point_loss
                region_feature['count'] = points_count
                region_feature['sum'] = loss_sum
                self.aggregation_layer.updateFeature(region_feature)
        # End updating count and sum attributes
        self.aggregation_layer.endEditCommand()
        self.aggregation_layer.commitChanges()
        # display a warning in case none of the loss points are inside
        # any of the regions
        if no_loss_points_in_any_region:
            msg = "No loss points are contained by any of the regions!"
            self.iface.messageBar().pushMessage(self.tr("Warning"),
                                                self.tr(msg),
                                                level=QgsMessageBar.INFO)

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

    def purge_empty_regions(self):
        region_features = self.aggregation_layer.getFeatures()
        pr = self.aggregation_layer.dataProvider()
        caps = pr.capabilities()
        # Begin purging empty regions
        self.aggregation_layer.startEditing()
        self.aggregation_layer.beginEditCommand(
            "Purge empty regions")
        problems_purging = False
        for region_feature in region_features:
            if region_feature['count'] == 0:
                if caps & QgsVectorDataProvider.DeleteFeatures:
                    deletion_is_ok = pr.deleteFeatures([region_feature.id()])
                    if not deletion_is_ok:
                        problems_purging = True
        if problems_purging:
            msg = "Problems occurred while attempting to purge empty regions!"
            self.iface.messageBar().pushMessage(self.tr("Error"),
                                    self.tr(msg),
                                    level=QgsMessageBar.CRITICAL)
        else:
            msg = "Empty regions have been successfully purged. " \
                  "Hide and show aggregation layer to display the result."
            self.iface.messageBar().pushMessage(self.tr("Success"),
                                    self.tr(msg),
                                    level=QgsMessageBar.INFO)
        # End updating count and sum attributes
        self.aggregation_layer.endEditCommand()
        self.aggregation_layer.commitChanges()
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.aggregation_layer.updateExtents()
