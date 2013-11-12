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
from PyQt4 import Qt
import os.path
import uuid

from PyQt4.QtCore import (QSettings,
                          QTranslator,
                          QCoreApplication,
                          qVersion,
                          QVariant)

from PyQt4.QtGui import (QApplication,
                         QAction,
                         QIcon,
                         QProgressDialog,
                         QMessageBox,
                         QProgressBar)

from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsRasterLayer,
                       QgsField,
                       QgsFeature,
                       QgsGeometry,
                       QgsFields,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       QgsVectorDataProvider,
                       QgsMapLayer,
                       QGis)

from qgis.gui import QgsMessageBar

from qgis.analysis import QgsZonalStatistics

import resources_rc

# Import the code for the dialog
from svirdialog import SvirDialog

from time import time

# Name of the attribute, in the input loss data layer, containing loss info
LOSS_ATTRIBUTE_NAME = "TOTLOSS"  # "POP2010"  # "RSCORE"  # "loss"
REGION_ID_ATTRIBUTE_NAME = "MCODE"  # "ISO"  # "STFID"
DEBUG = False


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
        # Output layer containing aggregated loss data for non-empty regions
        self.purged_layer = None
        # Input layer containing social vulnerability data
        self.social_vulnerability_layer = None
        # Output layer containing joined data and final svir computations
        self.svir_layer = None
        # Action to activate the modal dialog to load loss data and regions
        self.initial_action = None
        # Action to activate building a new layer with loss data
        # aggregated by region, excluding regions containing no loss points
        self.purge_empty_regions_action = None

    def initGui(self):
        # Create action that will start plugin configuration
        self.initial_action = QAction(
            QIcon(":/plugins/svir/start_plugin_icon.png"),
            u"Aggregate loss by region", self.iface.mainWindow())
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
            ## Create and enable toolbar button and menu item
            ## for purging empty regions
            ## Create action
            #self.purge_empty_regions_action = QAction(
            #    QIcon(":/plugins/svir/purge_empty_regions_icon.png"),
            #    u"Purge empty regions",
            #    self.iface.mainWindow())
            ## Connect the action to the purge_empty_regions method
            #self.purge_empty_regions_action.triggered.connect(
            #    self.create_new_aggregation_layer_with_no_empty_regions)
            ## Add toolbar button and menu item
            #self.iface.addToolBarIcon(self.purge_empty_regions_action)
            #self.iface.addPluginToMenu(u"&SVIR",
            #                           self.purge_empty_regions_action)
            #msg = 'Select "Purge empty regions" from SVIR plugin menu ' \
            #      'to create a new aggregation layer with the regions ' \
            #      'containing at least one loss point'
            #self.iface.messageBar().pushMessage(self.tr("Info"),
            #                                    self.tr(msg),
            #                                    level=QgsMessageBar.INFO)
            # FIXME: Same layer to get regions and social vulnerability data
            #social_vulnerability_layer_path = "/home/paolo/prove/mappe/Chris/varie/Integrated Risk Example_Portugal/Aggregated_Social_Vulnerability.shp"
            #self.load_social_vulnerability_layer(
            #    social_vulnerability_layer_path)
            # Create social vulnerability layer, duplicating regions layer
            self.social_vulnerability_layer = self.create_memory_layer(
                self.regions_layer, "Social vulnerability map")
            self.create_svir_layer()
            self.calculate_svir_statistics()

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
        if DEBUG:
            print "Creating and initializing aggregation layer"
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
             QgsField("sum", QVariant.Double)])

        # copy regions from regions layer
        for region_feature in self.regions_layer.getFeatures():
            if DEBUG:
                print "Copying feature ", region_feature.id(), "from regions_layer"
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
            feat[REGION_ID_ATTRIBUTE_NAME] = region_feature[
                REGION_ID_ATTRIBUTE_NAME]
            feat['count'] = 0
            feat['sum'] = 0.0
            # Add the new feature to the layer
            if caps & QgsVectorDataProvider.AddFeatures:
                pr.addFeatures([feat])
                # Update the layer including the new feature
            self.aggregation_layer.updateFeature(feat)
            if DEBUG:
                print "done"

        # End layer initialization
        self.aggregation_layer.endEditCommand()
        self.aggregation_layer.commitChanges()

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.aggregation_layer.updateExtents()

        if DEBUG:
            print "Adding aggregation layer to registry"
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
        if DEBUG:
            print "Creating spatial index for loss points..."
            t_start = time()
        spatial_index = QgsSpatialIndex()
        for loss_feature in loss_features:
            spatial_index.insertFeature(loss_feature)
        loss_features.rewind()      # reset iterator
        if DEBUG:
            t_stop = time()
            print "Completed in %f" % (t_stop - t_start)

        # Begin updating count and sum attributes
        if DEBUG:
            print "Starting to count points in regions"
        self.aggregation_layer.startEditing()
        self.aggregation_layer.beginEditCommand(
            "Edit count and sum attributes")
        # to show the overall progress, cycling through regions
        tot_regions = len(list(self.aggregation_layer.getFeatures()))
        current_region = 0
        msg = self.tr("Aggregating points by region...")
        progress_message_bar = self.iface.messageBar().createMessage(msg)
        progress = QProgressBar()
        progress_message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progress_message_bar,
                                           self.iface.messageBar().INFO)
        # check if there are no loss points contained in any of the regions
        # and later display a warning if that occurs
        no_loss_points_in_any_region = True
        for region_feature in region_features:
            progress_perc = current_region / float(tot_regions) * 100
            progress.setValue(progress_perc)
            if DEBUG:
                print "*" * 50
                print "*" * 50
                print progress, "% - Region:", region_feature.id(), "on", tot_regions
                print "*" * 50
                print "*" * 50
                t_region_start = time()
            current_region += 1
            points_count = 0
            loss_sum = 0
            region_geometry = region_feature.geometry()
            # Find ids of points within the bounding box of the region
            if DEBUG:
                print "Find ids of points within the region's bounding box..."
                t_start = time()
            point_ids = spatial_index.intersects(region_geometry.boundingBox())
            if DEBUG:
                t_stop = time()
                print "Completed in %f" % (t_stop - t_start)
            if len(point_ids) > 0:  # at least one point in bounding box
                # For points that are within the bounding box of the region
                for point_id in point_ids:
                    if DEBUG:
                        print "Checking if point", point_id, \
                            "is actually inside the region"
                        print "Retrieving point geometry..."
                        t_start = time()
                        # Get the point feature by the point's id
                    request = QgsFeatureRequest().setFilterFid(point_id)
                    point_feature = self.loss_layer.getFeatures(request).next()
                    point_geometry = QgsGeometry(point_feature.geometry())
                    if DEBUG:
                        t_stop = time()
                        print "Completed in %f" % (t_stop - t_start)
                        print "Check if region geometry contains the point..."
                        t_start = time()
                        # check if the point is actually inside the region and
                    # it is not only contained by its bounding box
                    if region_geometry.contains(point_geometry):
                        points_count += 1
                        # we have found at least one loss point inside a region
                        no_loss_points_in_any_region = False
                        point_loss = point_feature[LOSS_ATTRIBUTE_NAME]
                        loss_sum += point_loss
                    if DEBUG:
                        t_stop = time()
                        print "Completed in %f" % (t_stop - t_start)
                if DEBUG:
                    print "Updating count and sum for the region..."
                    t_start = time()
                region_feature['count'] = points_count
                region_feature['sum'] = loss_sum
                self.aggregation_layer.updateFeature(region_feature)
                # End updating count and sum attributes
                if DEBUG:
                    t_stop = time()
                    print "Completed in %f" % (t_stop - t_start)
                    t_region_stop = time()
                    print "Region completed in %f" % (t_region_stop - t_region_start)
                    #raw_input("Press Enter to continue...")
        self.aggregation_layer.endEditCommand()
        self.aggregation_layer.commitChanges()
        self.iface.messageBar().clearWidgets()
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

    def create_new_aggregation_layer_with_no_empty_regions(self):
        """
        Create a new aggregation layer containing all the regions of the
        aggregation layer that contain at least one loss point
        """
        # create layer
        self.purged_layer = QgsVectorLayer(
            "Polygon",
            "Aggregated Losses (no empty regions)",
            "memory")
        pr = self.purged_layer.dataProvider()
        caps = pr.capabilities()

        # Begin layer initialization
        self.purged_layer.startEditing()
        self.purged_layer.beginEditCommand("Layer initialization")

        # add count and sum fields for aggregating statistics
        pr.addAttributes(
            [QgsField(REGION_ID_ATTRIBUTE_NAME, QVariant.String),
             QgsField("count", QVariant.Int),
             QgsField("sum", QVariant.Double)])

        # copy regions from aggregation layer
        for region_feature in self.aggregation_layer.getFeatures():
            # copy only regions which contain at least one loss point
            if region_feature['count'] >= 1:
                feat = region_feature
                # Add the new feature to the layer
                if caps & QgsVectorDataProvider.AddFeatures:
                    pr.addFeatures([feat])
                    # Update the layer including the new feature
                self.aggregation_layer.updateFeature(feat)

        # End layer initialization
        self.purged_layer.endEditCommand()
        self.purged_layer.commitChanges()

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.purged_layer.updateExtents()

        # Add purged layer to registry
        if self.purged_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.purged_layer)
            msg = "Regions containing at least one loss point have been " \
                  "copied into a new aggregation layer."
            self.iface.messageBar().pushMessage(self.tr("Info"),
                                                self.tr(msg),
                                                level=QgsMessageBar.INFO)
        else:
            raise RuntimeError('Purged layer invalid')

    def load_social_vulnerability_layer(self, social_vulnerability_layer_path):
        # Load social vulnerability layer
        self.social_vulnerability_layer = QgsVectorLayer(
            social_vulnerability_layer_path,
            self.tr('Social vulnerability'),
            'ogr')
        # Add social vulnerability layer to registry
        if self.social_vulnerability_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(
                self.social_vulnerability_layer)
        else:
            raise RuntimeError('Social vulnerability layer invalid')

    def populate_svir_layer_with_loss_values(self):
        # to show the overall progress, cycling through regions
        tot_regions = len(list(self.aggregation_layer.getFeatures()))
        current_region = 0
        msg = self.tr("Populating svir layer with loss values...")
        progress_message_bar = self.iface.messageBar().createMessage(msg)
        progress = QProgressBar()
        progress_message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progress_message_bar,
                                           self.iface.messageBar().INFO)
        # Begin populating "loss" attribute with data from aggregation_layer
        self.svir_layer.startEditing()
        self.svir_layer.beginEditCommand("Add loss values")
        for svir_feat in self.svir_layer.getFeatures():
            progress_percent = current_region / float(tot_regions) * 100
            progress.setValue(progress_percent)
            current_region += 1
            for aggr_feat in self.aggregation_layer.getFeatures():
                if svir_feat[REGION_ID_ATTRIBUTE_NAME] == aggr_feat[REGION_ID_ATTRIBUTE_NAME]:
                    svir_feat['TOTLOSS'] = aggr_feat['sum']
                    self.svir_layer.updateFeature(svir_feat)
        # End adding loss attribute
        self.svir_layer.endEditCommand()
        self.svir_layer.commitChanges()
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.svir_layer.updateExtents()
        self.iface.messageBar().clearWidgets()

    def create_svir_layer(self):
        """
        Create a new layer joining (by region id) social vulnerability
        and loss data
        """
        # Create new svir layer, duplicating social vulnerability layer
        self.svir_layer = self.create_memory_layer(
            self.social_vulnerability_layer, "SVIR map")
        # Add "loss" attribute to svir_layer
        self.add_attributes_to_layer(self.svir_layer,
                                     [QgsField('TOTLOSS', QVariant.Double)])
        # Populate "loss" attribute with data from aggregation_layer
        self.populate_svir_layer_with_loss_values()
        # Add svir layer to registry
        if self.svir_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.svir_layer)
        else:
            raise RuntimeError('SVIR layer invalid')

    def calculate_svir_statistics(self):
        # add attributes:
        # RISKPLUS = TOTRISK + TOTSVI
        # RISKMULT = TOTRISK * TOTSVI
        # RISK1F   = TOTRISK * (1 + TOTSVI)
        self.add_attributes_to_layer(self.svir_layer,
                                     [QgsField('RISKPLUS', QVariant.Double),
                                      QgsField('RISKMULT', QVariant.Double),
                                      QgsField('RISK1F', QVariant.Double)])
        # for each region, calculate the value of the output attributes
        # to show the overall progress, cycling through regions
        tot_regions = len(list(self.svir_layer.getFeatures()))
        current_region = 0
        msg = self.tr("Calculating SVIR statistics...")
        progress_message_bar = self.iface.messageBar().createMessage(msg)
        progress = QProgressBar()
        progress_message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progress_message_bar,
                                           self.iface.messageBar().INFO)
        # Begin calculating RISKPLUS
        self.svir_layer.startEditing()
        self.svir_layer.beginEditCommand("Calculate RISKPLUS values")
        for svir_feat in self.svir_layer.getFeatures():
            progress_percent = current_region / float(tot_regions) * 100
            progress.setValue(progress_percent)
            current_region += 1
            svir_feat['RISKPLUS'] = svir_feat['TOTLOSS'] + svir_feat["TOTSVI"]
            svir_feat['RISKMULT'] = svir_feat['TOTLOSS'] * svir_feat["TOTSVI"]
            svir_feat['RISK1F'] = svir_feat['TOTLOSS']*(1+svir_feat["TOTSVI"])
            self.svir_layer.updateFeature(svir_feat)
        # End adding loss attribute
        self.svir_layer.endEditCommand()
        self.svir_layer.commitChanges()
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.svir_layer.updateExtents()
        self.iface.messageBar().clearWidgets()

    def add_attributes_to_layer(self, layer, attribute_list):
        layer.startEditing()
        layer.beginEditCommand("Add attributes")
        # add attributes
        layer_pr = layer.dataProvider()
        layer_pr.addAttributes(attribute_list)
        # End adding attributes
        layer.endEditCommand()
        layer.commitChanges()
        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        layer.updateExtents()

    def create_memory_layer(self, layer, new_name='', add_to_registry=False):
        """
        FIXME: TAKEN BY INASAFE PLUGIN.
        IT WOULD BE USEFUL TO PUT IT INTO A SEPARATE MODULE,
        BECAUSE MANY DIFFERENT PLUGINS MIGHT NEED IT

        Return a memory copy of a layer

        :param layer: QgsVectorLayer that shall be copied to memory.
        :type layer: QgsVectorLayer

        :param new_name: The name of the copied layer.
        :type new_name: str

        :returns: An in-memory copy of a layer.
        :rtype: QgsMapLayer
        """
        if new_name is '':
            new_name = layer.name() + ' TMP'

        if layer.type() == QgsMapLayer.VectorLayer:
            v_type = layer.geometryType()
            if v_type == QGis.Point:
                type_str = 'Point'
            elif v_type == QGis.Line:
                type_str = 'Line'
            elif v_type == QGis.Polygon:
                type_str = 'Polygon'
            else:
                raise RuntimeError('Layer is whether Point nor '
                                   'Line nor Polygon')
        else:
            raise RuntimeError('Layer is not a VectorLayer')

        crs = layer.crs().authid().lower()
        my_uuid = str(uuid.uuid4())
        uri = '%s?crs=%s&index=yes&uuid=%s' % (type_str, crs, my_uuid)
        mem_layer = QgsVectorLayer(uri, new_name, 'memory')
        mem_provider = mem_layer.dataProvider()

        provider = layer.dataProvider()
        v_fields = provider.fields()

        fields = []
        for i in v_fields:
            fields.append(i)

        mem_provider.addAttributes(fields)

        for ft in provider.getFeatures():
            mem_provider.addFeatures([ft])

        if add_to_registry:
            if mem_layer.isValid():
                QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
            else:
                raise RuntimeError('Layer invalid')

        return mem_layer