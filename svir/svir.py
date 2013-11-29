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
import uuid
import numpy

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
from select_layers_to_join_dialog import SelectLayersToJoinDialog
from svirdialog import SvirDialog
from attribute_selection_dialog import AttributeSelectionDialog

from layer_editing_manager import LayerEditingManager
from trace_time_manager import TraceTimeManager

from utils import Utils


# Default names of the attributes, in the input loss data layer and in the
# zonal data layer, containing loss info and zone ids for aggregation
DEFAULT_LOSS_ATTR_NAME = "TOTLOSS"
DEFAULT_REGION_ID_ATTR_NAME = "MCODE"
DEFAULT_SVI_ATTR_NAME = "TOTSVI"
AGGR_LOSS_ATTR_NAME = "AGGR_LOSS"
DEBUG = False


class Svir:

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
        # Input layer specifying zones for aggregation
        self.zonal_layer = None
        # Output layer containing aggregated loss data
        self.aggregation_layer = None
        # Output layer containing aggregated loss data for non-empty zones
        self.purged_layer = None
        # Input layer containing social vulnerability data
        self.social_vulnerability_layer = None
        # Output layer containing joined data and final svir computations
        self.svir_layer = None
        # Action to activate the modal dialog to load loss data and zones
        self.initial_action = None
        # Action to activate building a new layer with loss data
        # aggregated by zone, excluding zones containing no loss points
        self.purge_empty_zones_action = None
        # Action to join SVI with loss data (both aggregated by zone)
        self.join_svi_with_losses_action = None
        # Action to calculate some common statistics combining SVI and loss
        self.calculate_svir_statistics_action = None
        # Name of the attribute containing loss values (in loss_layer)
        self.loss_attr_name = None
        # Name of the (optional) attribute containing zone id (in loss_layer)
        self.zone_id_in_losses_attr_name = None
        # Name of the attribute containing zone id (in zonal_layer)
        self.zone_id_in_zones_attr_name = None
        # Name of the attribute containing, e.g., SVI values
        self.zonal_attr_name = None
        # It can be, e.g., the aggregation_layer or the purged_layer
        self.loss_layer_to_join = None
        # Most likely, it will be the zonal layer
        self.zonal_layer_to_join = None

    def initGui(self):
        # Create action that will start plugin configuration
        self.initial_action = QAction(
            QIcon(":/plugins/svir/start_plugin_icon.png"),
            u"Aggregate loss by zone", self.iface.mainWindow())
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
                                    self.purge_empty_zones_action)
        self.iface.removeToolBarIcon(self.purge_empty_zones_action)
        self.iface.removePluginMenu(u"&SVIR",
                                    self.join_svi_with_losses_action)
        self.iface.removeToolBarIcon(self.join_svi_with_losses_action)
        self.iface.removePluginMenu(u"&SVIR",
                                    self.calculate_svir_statistics_action)
        self.iface.removeToolBarIcon(self.calculate_svir_statistics_action)
        self.clear_progress_message_bar()

    # run method that performs all the real work
    def run(self):
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # check if loss layer is raster or vector (aggregating by zone
            # is different in the two cases)
            self.loss_layer_is_vector = self.dlg.loss_map_is_vector
            self.load_layers(self.dlg.ui.zonal_layer_le.text(),
                             self.dlg.ui.loss_layer_le.text(),
                             self.loss_layer_is_vector)

            # Open dialog to ask the user to specify attributes
            # * loss from loss_layer
            # * zone_id from loss_layer
            # * svi from zonal_layer
            # * zone_id from zonal_layer
            self.attribute_selection()

            self.create_aggregation_layer()
            # aggregate losses by zone (calculate count of points in the
            # zone and sum of loss values for the same zone)
            self.calculate_stats()

            # Create and enable toolbar button and menu item for
            # purging empty zones
            self.enable_purging_empty_zones()

            # TODO: Check if it's good to use the same layer to get
            #       zones and social vulnerability data
            self.social_vulnerability_layer = Utils.duplicate_in_memory(
                self.zonal_layer, "Social vulnerability map")

            # TODO: standardize loss data before inserting it in the svir layer
            self.standardize_losses()  # it's still a placeholder

            # Create menu item and toolbar button to activate join procedure
            self.enable_joining_svi_with_aggr_losses()

    def enable_purging_empty_zones(self):
        """
        Create and enable toolbar button and menu item
        for purging empty zones
        """
        # Create action
        self.purge_empty_zones_action = QAction(
            QIcon(":/plugins/svir/purge_empty_zones_icon.png"),
            u"Purge empty zones",
            self.iface.mainWindow())
        # Connect the action to the purge_empty_zones method
        self.purge_empty_zones_action.triggered.connect(
            self.create_new_aggregation_layer_with_no_empty_zones)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.purge_empty_zones_action)
        self.iface.addPluginToMenu(u"&SVIR",
                                   self.purge_empty_zones_action)
        msg = 'Select "Purge empty zones" from SVIR plugin menu ' \
              'to create a new aggregation layer with the zones ' \
              'containing at least one loss point'
        self.iface.messageBar().pushMessage(Utils.tr("Info"),
                                            Utils.tr(msg),
                                            level=QgsMessageBar.INFO)

    def enable_joining_svi_with_aggr_losses(self):
        """
        Create and enable toolbar button and menu item
        for joining SVI with loss data (both aggregated by zone)
        """
        # Create action
        self.join_svi_with_losses_action = QAction(
            QIcon(":/plugins/svir/start_plugin_icon.png"),
            u"Join SVI with loss data",
            self.iface.mainWindow())
        # Connect the action to the join_svi_with_aggr_losses method
        self.join_svi_with_losses_action.triggered.connect(
            self.join_svi_with_aggr_losses)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.join_svi_with_losses_action)
        self.iface.addPluginToMenu(u"&SVIR",
                                   self.join_svi_with_losses_action)
        msg = 'Select "Join SVI with loss data" from SVIR plugin menu ' \
              'to join SVI and loss data (both aggregated by zone)'
        self.iface.messageBar().pushMessage(Utils.tr("Info"),
                                            Utils.tr(msg),
                                            level=QgsMessageBar.INFO)

    def enable_calculating_svir_stats(self):
        """
        Create and enable toolbar button and menu item
        for calculating common SVIR statistics
        """
        # Create action
        self.calculate_svir_statistics_action = QAction(
            QIcon(":/plugins/svir/start_plugin_icon.png"),
            u"Calculate common SVIR statistics",
            self.iface.mainWindow())
        # Connect the action to the calculate_svir_statistics method
        self.calculate_svir_statistics_action.triggered.connect(
            self.calculate_svir_statistics)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.calculate_svir_statistics_action)
        self.iface.addPluginToMenu(u"&SVIR",
                                   self.calculate_svir_statistics_action)
        msg = 'Select "Calculate common SVIR statistics" from SVIR plugin ' \
              'menu to calculate RISKPLUS, RISKMULT and RISK1F statistics'
        self.iface.messageBar().pushMessage(Utils.tr("Info"),
                                            Utils.tr(msg),
                                            level=QgsMessageBar.INFO)

    def join_svi_with_aggr_losses(self):
        if self.select_layers_to_join():
            self.create_svir_layer()
            # Create menu item and toolbar button to activate calculation
            # of common svir statistics
            self.enable_calculating_svir_stats()
        else:
            msg = 'The new layer containing SVIR data has not been built.'
            self.iface.messageBar().pushMessage(Utils.tr("Warning"),
                                                Utils.tr(msg),
                                                level=QgsMessageBar.WARNING)

    def load_layers(self, aggregation_layer_path,
                    loss_layer_path,
                    loss_layer_is_vector):
        # Load aggregation layer
        self.zonal_layer = QgsVectorLayer(aggregation_layer_path,
                                          Utils.tr('Zonal data'), 'ogr')
        # Add aggregation layer to registry
        if self.zonal_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.zonal_layer)
        else:
            raise RuntimeError('Aggregation layer invalid')
            # Load loss layer
        if loss_layer_is_vector:
            self.loss_layer = QgsVectorLayer(loss_layer_path,
                                             Utils.tr('Loss map'), 'ogr')
        else:
            self.loss_layer = QgsRasterLayer(loss_layer_path,
                                             Utils.tr('Loss map'))
            # Add loss layer to registry
        if self.loss_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.loss_layer)
        else:
            raise RuntimeError('Loss layer invalid')
            # Zoom depending on the zonal layer's extent
        self.canvas.setExtent(self.zonal_layer.extent())

    def attribute_selection(self):
        """
        Open a modal dialog containing 3 combo boxes, allowing the user
        to select what are the attribute names for
        * loss values (from loss layer)
        * zone id (from loss layer)
        * social vulnerability index (from zonal layer)
        * zone id (from zonal layer)
        """
        dlg = AttributeSelectionDialog()
        # if the loss layer does not contain an attribute specifying the ids of
        # zones, the user must not be forced to select such attribute, so we
        # add an "empty" option to the combobox
        dlg.ui.zone_id_attr_name_loss_cbox.addItem(
            Utils.tr("Use zonal geometries"))
        # populate combo boxes with field names taken by layers
        loss_dp = self.loss_layer.dataProvider()
        loss_fields = list(loss_dp.fields())
        for field in loss_fields:
            dlg.ui.loss_attr_name_cbox.addItem(field.name())
            dlg.ui.zone_id_attr_name_loss_cbox.addItem(field.name())
        zonal_dp = self.zonal_layer.dataProvider()
        zonal_fields = list(zonal_dp.fields())
        for field in zonal_fields:
            dlg.ui.zone_id_attr_name_zone_cbox.addItem(field.name())
            dlg.ui.zonal_attr_name_cbox.addItem(field.name())
        # TODO: pre-select default attribute names in the dropdown (if present)

        # if the user presses OK
        if dlg.exec_():
            # retrieve attribute names from combobox selections
            self.loss_attr_name = loss_fields[
                dlg.ui.loss_attr_name_cbox.currentIndex()].name()
            # if the loss file does not contain an attribute specifying the
            # zone id for each point, or if the zones are not compatible
            # with those specified by the layer containing svi data
            if dlg.ui.zone_id_attr_name_loss_cbox.currentIndex() == 0:
                self.zone_id_in_losses_attr_name = None
            else:
                # currentIndex() - 1 because index 0 is for "No zone ids"
                self.zone_id_in_losses_attr_name = loss_fields[
                    dlg.ui.zone_id_attr_name_loss_cbox.currentIndex()-1].name()
            self.zonal_attr_name = zonal_fields[
                dlg.ui.zonal_attr_name_cbox.currentIndex()].name()
            self.zone_id_in_zones_attr_name = zonal_fields[
                dlg.ui.zone_id_attr_name_zone_cbox.currentIndex()].name()
        else:
            # TODO: is it good to use default values, or should we stop here?
            # use default values if CANCEL is pressed
            self.loss_attr_name = DEFAULT_LOSS_ATTR_NAME
            self.zone_id_in_losses_attr_name = DEFAULT_REGION_ID_ATTR_NAME
            self.zonal_attr_name = DEFAULT_SVI_ATTR_NAME
            self.zone_id_in_zones_attr_name = DEFAULT_REGION_ID_ATTR_NAME
            msg = 'Using default attributes: {0}, {1}, {2}, {3}'.format(
                self.loss_attr_name,
                self.zone_id_in_losses_attr_name,
                self.zonal_attr_name,
                self.zone_id_in_zones_attr_name)
            self.iface.messageBar().pushMessage(Utils.tr("Warning"),
                                                Utils.tr(msg),
                                                level=QgsMessageBar.WARNING)

    def select_layers_to_join(self):
        """
        Open a modal dialog containing 2 combo boxes, allowing the user
        to select a layer containing loss data and one containing SVI data.
        The two layers will be joined (later) by zone id
        """
        dlg = SelectLayersToJoinDialog()
        reg = QgsMapLayerRegistry.instance()
        layer_list = list(reg.mapLayers())
        dlg.ui.loss_layer_cbox.addItems(layer_list)
        dlg.ui.zonal_layer_cbox.addItems(layer_list)
        if dlg.exec_():
            self.loss_layer_to_join = reg.mapLayers().values()[
                dlg.ui.loss_layer_cbox.currentIndex()]
            self.zonal_layer_to_join = reg.mapLayers().values()[
                dlg.ui.zonal_layer_cbox.currentIndex()]
            return True
        else:
            # TODO: what happens if the user presses CANCEL?
            return False

    def create_aggregation_layer(self):
        """
        Create a new aggregation layer which contains the polygons from
        the zonal layer. Two new attributes (count and sum) will represent
        the count of loss points in a zone and the sum of loss values for
        the same zone.
        """
        if DEBUG:
            print "Creating and initializing aggregation layer"

        # create layer
        self.aggregation_layer = QgsVectorLayer("Polygon",
                                                Utils.tr("Aggregated Losses"),
                                                "memory")
        pr = self.aggregation_layer.dataProvider()
        caps = pr.capabilities()

        with LayerEditingManager(self.aggregation_layer,
                                 "Layer initialization",
                                 DEBUG):

            # add count and sum fields for aggregating statistics
            pr.addAttributes(
                [QgsField(self.zone_id_in_zones_attr_name, QVariant.String),
                 QgsField("count", QVariant.Int),
                 QgsField("sum", QVariant.Double)])

            # to show the overall progress, cycling through zones
            tot_zones = len(list(self.zonal_layer.getFeatures()))
            msg = Utils.tr("Step 1 of 3: initializing aggregation layer...")
            progress = self.create_progress_message_bar(msg)

            # copy zones from zonal layer
            for current_zone, zone_feature in enumerate(
                    self.zonal_layer.getFeatures()):
                progress_perc = current_zone / float(tot_zones) * 100
                progress.setValue(progress_perc)

                feat = QgsFeature()
                # copy the polygon from the input aggregation layer
                feat.setGeometry(QgsGeometry(zone_feature.geometry()))
                # Define the count and sum fields to initialize to 0
                fields = QgsFields()
                fields.append(
                    QgsField(self.zone_id_in_zones_attr_name, QVariant.String))
                fields.append(
                    QgsField("count", QVariant.Int))
                fields.append(
                    QgsField("sum", QVariant.Double))
                # Add fields to the new feature
                feat.setFields(fields)
                feat[self.zone_id_in_zones_attr_name] = zone_feature[
                    self.zone_id_in_zones_attr_name]
                # Add the new feature to the layer
                if caps & QgsVectorDataProvider.AddFeatures:
                    pr.addFeatures([feat])

        # Add aggregation layer to registry
        if self.aggregation_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.aggregation_layer)
        else:
            raise RuntimeError('Aggregation layer invalid')

    def calculate_stats(self):
        """
        A loss_layer containing loss data points needs to be already loaded,
        and it can be a raster or vector layer.
        Another layer (zonal_layer) needs to be previously loaded as well,
        containing social vulnerability data aggregated by zone.
        This method calls other methods of the class in order to produce
        a new aggregation_layer containing, for each feature (zone):
        * a zone id attribute, that can be taken from the zonal_layer or from
          the loss_layer, if the latter contains an attribute specifying the
          zone id for each point (CAUTION! The user needs to check if the zones
          defined in the loss_layer correspond to those defined in the
          zonal_layer!)
        * a "count" attribute, specifying how many loss points are inside the
          zone
        * a "sum" attribute, summing the loss values for all the points that
          are inside the zone
        """
        if self.loss_layer_is_vector:
            # check if the user specified that the loss_layer contains an
            # attribute specifying what's the zone id for each loss point
            if self.zone_id_in_losses_attr_name:
                # then we can aggregate by zone id, instead of doing a
                # geo-spatial analysis to see in which zone each point is
                self.calculate_vector_stats_aggregating_by_zone_id()
            else:
                # otherwise we need to acquire the zones' geometries from the
                # zonal layer and check if loss points are inside those zones
                self.calculate_vector_stats_using_geometries()
        else:
            self.calculate_raster_stats()

    def calculate_vector_stats_aggregating_by_zone_id(self):
        """
        If we know the zone id of each point in the loss map, we
        don't need to use geometries while aggregating, and we can
        simply count by zone id
        """
        tot_points = len(list(self.loss_layer.getFeatures()))
        msg = Utils.tr("Step 2 of 3: aggregating losses by zone id...")
        progress = self.create_progress_message_bar(msg)
        with TraceTimeManager(msg, DEBUG):
            zone_stats = {}
            for current_point, point_feat in enumerate(
                    self.loss_layer.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                zone_id = point_feat[self.zone_id_in_losses_attr_name]
                loss_value = point_feat[self.loss_attr_name]
                if zone_id in zone_stats:
                    # increment the count by one and add the loss value
                    # to the sum
                    to_add = numpy.array([1, loss_value])
                    zone_stats[zone_id] += to_add
                else:
                    # initialize stats for the new zone found
                    zone_stats[zone_id] = numpy.array([1, loss_value])
        self.clear_progress_message_bar()

        msg = Utils.tr("Step 3 of 3: writing counts and sums on "
                       "aggregation_layer...")
        with TraceTimeManager(msg, DEBUG):
            tot_zones = len(list(self.aggregation_layer.getFeatures()))
            progress = self.create_progress_message_bar(msg)
            with LayerEditingManager(self.aggregation_layer,
                                     msg,
                                     DEBUG):
                count_index = self.aggregation_layer.fieldNameIndex('count')
                sum_index = self.aggregation_layer.fieldNameIndex('sum')
                for current_zone, zone_feat in enumerate(
                        self.aggregation_layer.getFeatures()):
                    progress_perc = current_zone / float(tot_zones) * 100
                    progress.setValue(progress_perc)
                    # get the id of the current zone
                    zone_id = zone_feat[self.zone_id_in_zones_attr_name]
                    # retrieve count and sum from the dictionary, using the
                    # zone id as key to get the values from the corresponding
                    # numpy array
                    points_count, loss_sum = zone_stats[zone_id]
                    # without casting to int and to float, it wouldn't work
                    fid = zone_feat.id()
                    self.aggregation_layer.changeAttributeValue(
                        fid, count_index, int(points_count))
                    self.aggregation_layer.changeAttributeValue(
                        fid, sum_index, float(loss_sum))
        self.clear_progress_message_bar()

    def calculate_vector_stats_using_geometries(self):
        """
        On the hypothesis that we don't know what is the zone in which
        each point was collected,
        * we create a spatial index of the loss points
        * for each zone (in the layer containing zoneally-aggregated SVI
            * we identify points that are inside the zone's bounding box
            * we check if each of these points is actually inside the
              zone's geometry; if it is:
                * add 1 to the count of points in the zone
                * add the loss value to the total loss of the zone
        Notes:
        * self.loss_layer contains the not aggregated loss points
        * self.zonal_layer contains the zone geometries
        * self.aggregation_layer is the new layer with losses aggregated by
            zone
        """
        # to show the overall progress, cycling through points
        tot_points = len(list(self.loss_layer.getFeatures()))
        msg = Utils.tr(
            "Step 2 of 3: creating spatial index for loss points...")
        progress = self.create_progress_message_bar(msg)

        # create spatial index
        with TraceTimeManager("Creating spatial index for loss points...",
                              DEBUG):
            spatial_index = QgsSpatialIndex()
            for current_point, loss_feature in enumerate(
                    self.loss_layer.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                spatial_index.insertFeature(loss_feature)

        self.clear_progress_message_bar()

        with LayerEditingManager(self.aggregation_layer,
                                 "Calculate count and sum attributes",
                                 DEBUG):
            # to show the overall progress, cycling through zones
            # Note that zones from zone layer were copied earlier into the
            # aggregation layer
            tot_zones = len(list(self.aggregation_layer.getFeatures()))
            msg = Utils.tr("Step 3 of 3: aggregating points by zone...")
            progress = self.create_progress_message_bar(msg)

            # check if there are no loss points contained in any of the zones
            # and later display a warning if that occurs
            no_loss_points_in_any_zone = True

            count_index = self.aggregation_layer.fieldNameIndex('count')
            sum_index = self.aggregation_layer.fieldNameIndex('sum')

            # We cycle through zones in the aggregation_layer, because the
            # aggregation layer contains the zones copied from the zonal
            # layer, plus it contains the attributes count and sum to populate
            for current_zone, zone_feature in enumerate(
                    self.aggregation_layer.getFeatures()):
                progress_perc = current_zone / float(tot_zones) * 100
                progress.setValue(progress_perc)
                msg = "{0}% - Zone: {1} on {2}".format(progress_perc,
                                                       zone_feature.id(),
                                                       tot_zones)
                with TraceTimeManager(msg, DEBUG):
                    points_count = 0
                    loss_sum = 0
                    zone_geometry = zone_feature.geometry()
                    # Find ids of points within the bounding box of the zone
                    point_ids = spatial_index.intersects(
                        zone_geometry.boundingBox())
                    # check if the points inside the bounding box of the zone
                    # are actually inside the zone's geometry
                    for point_id in point_ids:
                        msg = "Checking if point {0} is actually inside " \
                              "the zone".format(point_id)
                        with TraceTimeManager(msg, DEBUG):
                            # Get the point feature by the point's id
                            request = QgsFeatureRequest().setFilterFid(
                                point_id)
                            point_feature = self.loss_layer.getFeatures(
                                request).next()
                            point_geometry = QgsGeometry(
                                point_feature.geometry())
                            # check if the point is actually inside the zone
                            # and it is not only contained by its bounding box
                            if zone_geometry.contains(point_geometry):
                                points_count += 1
                                # we have found at least one loss point inside
                                # a zone
                                no_loss_points_in_any_zone = False
                                point_loss = point_feature[self.loss_attr_name]
                                loss_sum += point_loss
                    msg = "Updating count and sum for the zone..."
                    with TraceTimeManager(msg, DEBUG):
                        fid = zone_feature.id()
                        self.aggregation_layer.changeAttributeValue(
                            fid, count_index, points_count)
                        self.aggregation_layer.changeAttributeValue(
                            fid, sum_index, loss_sum)
        self.clear_progress_message_bar()
        # display a warning in case none of the loss points are inside
        # any of the zones
        if no_loss_points_in_any_zone:
            msg = "No loss points are contained by any of the zones!"
            self.iface.messageBar().pushMessage(Utils.tr("Warning"),
                                                Utils.tr(msg),
                                                level=QgsMessageBar.INFO)

    def calculate_raster_stats(self):
        """
        In case the layer containing loss data is raster, use
        QgsZonalStatistics to calculate count, sum and average loss
        values for each zone
        """
        zonal_statistics = QgsZonalStatistics(
            self.aggregation_layer,
            self.loss_layer.dataProvider().dataSourceUri())
        progress_dialog = QProgressDialog(
            Utils.tr('Calculating zonal statistics'),
            Utils.tr('Abort...'),
            0,
            0)
        zonal_statistics.calculateStatistics(progress_dialog)
        # TODO: This is not giving any warning in case no loss points are
        #       contained by any of the zones
        if progress_dialog.wasCanceled():
            QMessageBox.error(
                self, Utils.tr('ZonalStats: Error'),
                Utils.tr('You aborted aggregation, '
                         'so there are no data for analysis. Exiting...'))

    def create_new_aggregation_layer_with_no_empty_zones(self):
        """
        Create a new aggregation layer containing all the zones of the
        aggregation layer that contain at least one loss point
        """
        # create layer
        self.purged_layer = QgsVectorLayer(
            "Polygon",
            Utils.tr("Aggregated Losses (no empty zones)"),
            "memory")
        pr = self.purged_layer.dataProvider()
        caps = pr.capabilities()

        tot_zones = len(list(self.aggregation_layer.getFeatures()))
        msg = Utils.tr("Purging zones containing no loss points...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.purged_layer,
                                 "Purged layer initialization",
                                 DEBUG):
            # add count and sum fields for aggregating statistics
            pr.addAttributes(
                [QgsField(self.zone_id_in_zones_attr_name, QVariant.String),
                 QgsField("count", QVariant.Int),
                 QgsField("sum", QVariant.Double)])

            # copy zones from aggregation layer
            for current_zone, zone_feature in enumerate(
                    self.aggregation_layer.getFeatures()):
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                # copy only zones which contain at least one loss point
                if zone_feature['count'] >= 1:
                    feat = zone_feature
                    # Add the new feature to the layer
                    if caps & QgsVectorDataProvider.AddFeatures:
                        pr.addFeatures([feat])

        self.clear_progress_message_bar()

        # Add purged layer to registry
        if self.purged_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.purged_layer)
            msg = "Zones containing at least one loss point have been " \
                  "copied into a new aggregation layer."
            self.iface.messageBar().pushMessage(Utils.tr("Info"),
                                                Utils.tr(msg),
                                                level=QgsMessageBar.INFO)
        else:
            raise RuntimeError('Purged layer invalid')

    def populate_svir_layer_with_loss_values(self):
        """
        Copy loss values from the aggregation layer to the svir layer
        which already contains social vulnerability related attributes
        taken from the zonal layer.
        """
        # to show the overall progress, cycling through zones
        tot_zones = len(list(self.aggregation_layer.getFeatures()))
        msg = Utils.tr("Populating SVIR layer with loss values...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.svir_layer,
                                 "Add loss values to svir_layer",
                                 DEBUG):

            aggr_loss_index = self.svir_layer.fieldNameIndex(
                AGGR_LOSS_ATTR_NAME)

            # Begin populating "loss" attribute with data from the
            # aggregation_layer selected by the user (possibly purged from
            # zones containing no loss data
            for current_zone, svir_feat in enumerate(
                    self.svir_layer.getFeatures()):
                svir_feat_id = svir_feat.id()
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                match_found = False
                for aggr_feat in self.loss_layer_to_join.getFeatures():
                    if (svir_feat[self.zone_id_in_zones_attr_name] ==
                            aggr_feat[self.zone_id_in_zones_attr_name]):
                        self.svir_layer.changeAttributeValue(
                            svir_feat_id, aggr_loss_index, aggr_feat['sum'])
                        match_found = True
                # TODO: Check if this is the desired behavior, i.e., if we
                #       actually want to remove from svir_layer the zones that
                #       contain no loss values
                if not match_found:
                    caps = self.svir_layer.dataProvider().capabilities()
                    if caps & QgsVectorDataProvider.DeleteFeatures:
                        res = self.svir_layer.dataProvider().deleteFeatures(
                            [svir_feat.id()])
        self.clear_progress_message_bar()

    def standardize_losses(self):
        """
        Allow the user to select between a list of standardization algorithms,
        in order to make the loss data comparable with the social vulnerability
        index
        """
        # TODO: still not implemented
        pass

    def create_svir_layer(self):
        """
        Create a new layer joining (by zone id) social vulnerability
        and loss data
        """
        # Create new svir layer, duplicating social vulnerability layer
        self.svir_layer = Utils.duplicate_in_memory(
            self.social_vulnerability_layer, Utils.tr("SVIR map"))
        # Add "loss" attribute to svir_layer
        Utils.add_attributes_to_layer(self.svir_layer,
                                      [QgsField(AGGR_LOSS_ATTR_NAME,
                                                QVariant.Double)])
        # Populate "loss" attribute with data from aggregation_layer
        self.populate_svir_layer_with_loss_values()
        # Add svir layer to registry
        if self.svir_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.svir_layer)
        else:
            raise RuntimeError('SVIR layer invalid')

    def calculate_svir_statistics(self):
        """
        Calculate some common indices, combining total risk (in terms of
        losses) and social vulnerability index
        """
        # add attributes:
        # RISKPLUS = TOTRISK + TOTSVI
        # RISKMULT = TOTRISK * TOTSVI
        # RISK1F   = TOTRISK * (1 + TOTSVI)
        Utils.add_attributes_to_layer(self.svir_layer,
                                     [QgsField('RISKPLUS', QVariant.Double),
                                      QgsField('RISKMULT', QVariant.Double),
                                      QgsField('RISK1F', QVariant.Double)])
        # for each zone, calculate the value of the output attributes
        # to show the overall progress, cycling through zones
        tot_zones = len(list(self.svir_layer.getFeatures()))
        msg = Utils.tr("Calculating some common SVIR indices...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.svir_layer,
                                 "Calculate common SVIR statistics",
                                 DEBUG):
            riskplus_idx = self.svir_layer.fieldNameIndex('RISKPLUS')
            riskmult_idx = self.svir_layer.fieldNameIndex('RISKMULT')
            risk1f_idx = self.svir_layer.fieldNameIndex('RISK1F')

            for current_zone, svir_feat in enumerate(
                    self.svir_layer.getFeatures()):
                svir_feat_id = svir_feat.id()
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                self.svir_layer.changeAttributeValue(
                    svir_feat_id,
                    riskplus_idx,
                    (svir_feat[AGGR_LOSS_ATTR_NAME] +
                     svir_feat[self.zonal_attr_name]))
                self.svir_layer.changeAttributeValue(
                    svir_feat_id,
                    riskmult_idx,
                    (svir_feat[AGGR_LOSS_ATTR_NAME] *
                     svir_feat[self.zonal_attr_name]))
                self.svir_layer.changeAttributeValue(
                    svir_feat_id,
                    risk1f_idx,
                    (svir_feat[AGGR_LOSS_ATTR_NAME] *
                     (1 + svir_feat[self.zonal_attr_name])))

        self.clear_progress_message_bar()

    def create_progress_message_bar(self, msg):
        """
        Use the messageBar of QGIS to display a message describing what's going
        on (typically during a time-consuming task), and a bar showing the
        progress of the process.

        :param msg: Message to be displayed, describing the current task
        :type: str

        :returns: progress object on which we can set the percentage of
        completion of the task through progress.setValue(percentage)
        :rtype: QProgressBar
        """
        progress_message_bar = self.iface.messageBar().createMessage(msg)
        progress = QProgressBar()
        progress_message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progress_message_bar,
                                           self.iface.messageBar().INFO)
        return progress

    def clear_progress_message_bar(self):
        self.iface.messageBar().clearWidgets()
