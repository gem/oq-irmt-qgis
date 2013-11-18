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

# Default names of the attributes, in the input loss data layer and in the
# regions data layer, containing loss info and region ids for aggregation
DEFAULT_LOSS_ATTR_NAME = "TOTLOSS"
DEFAULT_REGION_ID_ATTR_NAME = "MCODE"
DEFAULT_SVI_ATTR_NAME = "TOTSVI"
AGGR_LOSS_ATTR_NAME = "TOTLOSS"
DEBUG = False


class Svir:
    @staticmethod
    def tr(message):
        return QApplication.translate('Svir', message)

    @staticmethod
    def add_attributes_to_layer(layer, attribute_list):
        """
        Add attributes to a layer

        :param layer: QgsVectorLayer that needs to be modified
        :type layer: QgsVectorLayer

        :param attribute_list: list of QgsField to add to the layer
        :type attribute_list: list of QgsField
        """
        with LayerEditingManager(layer, 'Add attributes', DEBUG):
            # add attributes
            layer_pr = layer.dataProvider()
            layer_pr.addAttributes(attribute_list)

    @staticmethod
    def create_memory_copy_of_layer(layer, new_name='', add_to_registry=False):
        """
        TODO: TAKEN FROM INASAFE PLUGIN AND SLIGHTLY MODIFIED.
              IT WOULD BE USEFUL TO PUT IT INTO A SEPARATE MODULE,
              BECAUSE MANY DIFFERENT PLUGINS MIGHT NEED IT

        Return a memory copy of a layer

        :param layer: QgsVectorLayer that shall be copied to memory.
        :type layer: QgsVectorLayer

        :param new_name: The name of the copied layer.
        :type new_name: str

        :param add_to_registry: if True, the new layer will be added to
        the QgsMapRegistry
        :type: bool

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
        self.loss_attr_name = None
        self.reg_id_in_losses_attr_name = None
        self.reg_id_in_regions_attr_name = None
        self.svi_attr_name = None
        self.loss_layer_to_join = None
        self.svi_layer_to_join = None

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
        self.clear_progress_message_bar()

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # check if loss layer is raster or vector (aggregating by region
            # is different in the two cases)
            self.loss_layer_is_vector = self.dlg.loss_map_is_vector
            self.load_layers(self.dlg.ui.regions_layer_le.text(),
                             self.dlg.ui.loss_layer_le.text(),
                             self.loss_layer_is_vector)

            # Open dialog to ask the user to specify attributes
            # * loss from loss_layer
            # * region_id from loss_layer
            # * svi from regions_layer
            # * region_id from regions_layer
            self.attribute_selection()

            self.create_aggregation_layer()
            # aggregate losses by region (calculate count of points in the
            # region and sum of loss values for the same region)
            self.calculate_stats()

            self.enable_purging_empty_regions()

            # TODO: Check if it's good to use the same layer to get
            #       regions and social vulnerability data
            self.social_vulnerability_layer = self.create_memory_copy_of_layer(
                self.regions_layer, "Social vulnerability map")
            # TODO: standardize loss data before inserting it in the svir layer
            self.standardize_losses()  # it's still a placeholder
            # TODO: let the user select a loss layer and a svi layer to join
            self.select_layers_to_join()

            self.create_svir_layer()
            self.calculate_svir_statistics()

    def enable_purging_empty_regions(self):
        # Create and enable toolbar button and menu item
        # for purging empty regions
        # Create action
        self.purge_empty_regions_action = QAction(
            QIcon(":/plugins/svir/purge_empty_regions_icon.png"),
            u"Purge empty regions",
            self.iface.mainWindow())
        # Connect the action to the purge_empty_regions method
        self.purge_empty_regions_action.triggered.connect(
            self.create_new_aggregation_layer_with_no_empty_regions)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.purge_empty_regions_action)
        self.iface.addPluginToMenu(u"&SVIR",
                                   self.purge_empty_regions_action)
        msg = 'Select "Purge empty regions" from SVIR plugin menu ' \
              'to create a new aggregation layer with the regions ' \
              'containing at least one loss point'
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

    def attribute_selection(self):
        """
        Open a modal dialog containing 3 combo boxes, allowing the user
        to select what are the attribute names for
        * loss values (from loss layer)
        * region id (from loss layer)
        * social vulnerability index (from regions layer)
        * region id (from regions layer)
        """
        # FIXME: Loss layer might not have a region_id attribute!
        #        (we need to aggregate data in different ways, depending
        #         on this!)

        dlg = AttributeSelectionDialog()
        # if the loss layer does not contain an attribute specifying the ids of
        # regions, the user must not be forced to select such attribute, so we
        # add an "empty" option to the combobox
        dlg.ui.reg_id_attr_name_loss_cbox.addItem(self.tr("No region ids"))
        # populate combo boxes with field names taken by layers
        loss_dp = self.loss_layer.dataProvider()
        loss_fields = list(loss_dp.fields())
        for field in loss_fields:
            dlg.ui.loss_attr_name_cbox.addItem(field.name())
            dlg.ui.reg_id_attr_name_loss_cbox.addItem(field.name())
        regions_dp = self.regions_layer.dataProvider()
        regions_fields = list(regions_dp.fields())
        for field in regions_fields:
            dlg.ui.reg_id_attr_name_region_cbox.addItem(field.name())
            dlg.ui.svi_attr_name_cbox.addItem(field.name())
        # TODO: pre-select default attribute names in the dropdown (if present)

        # if the user presses OK
        if dlg.exec_():
            # retrieve attribute names from combobox selections
            self.loss_attr_name = loss_fields[
                dlg.ui.loss_attr_name_cbox.currentIndex()].name()
            # if the loss file does not contain an attribute specifying the
            # region id for each point, or if the regions are not compatible
            # with those specified by the layer containing svi data
            if dlg.ui.reg_id_attr_name_loss_cbox.currentIndex() == 0:
                self.reg_id_in_losses_attr_name = None
            else:
                # currentIndex() - 1 because index 0 is for "No region ids"
                self.reg_id_in_losses_attr_name = loss_fields[
                    dlg.ui.reg_id_attr_name_loss_cbox.currentIndex()-1].name()
            self.svi_attr_name = regions_fields[
                dlg.ui.svi_attr_name_cbox.currentIndex()].name()
            self.reg_id_in_regions_attr_name = regions_fields[
                dlg.ui.reg_id_attr_name_region_cbox.currentIndex()].name()
        else:
            # TODO: is it good to use default values, or should we stop here?
            # use default values if CANCEL is pressed
            self.loss_attr_name = DEFAULT_LOSS_ATTR_NAME
            self.reg_id_in_losses_attr_name = DEFAULT_REGION_ID_ATTR_NAME
            self.svi_attr_name = DEFAULT_SVI_ATTR_NAME
            self.reg_id_in_regions_attr_name = DEFAULT_REGION_ID_ATTR_NAME

    def select_layers_to_join(self):
        """
        Open a modal dialog containing 2 combo boxes, allowing the user
        to select a layer containing loss data and one containing SVI data.
        The two layers will be joined (later) by region id
        """
        dlg = SelectLayersToJoinDialog()
        reg = QgsMapLayerRegistry.instance()
        layer_list = list(reg.mapLayers())
        dlg.ui.loss_layer_cbox.addItems(layer_list)
        dlg.ui.svi_layer_cbox.addItems(layer_list)
        if dlg.exec_():
            self.loss_layer_to_join = reg.mapLayers().get(
                dlg.ui.loss_layer_cbox.currentIndex())
            self.svi_layer_to_join = reg.mapLayers().get(
                dlg.ui.svi_layer_cbox.currentIndex())
        else:
            # TODO: what happens if the user presses CANCEL?
            pass

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
                                                self.tr("Aggregated Losses"),
                                                "memory")
        pr = self.aggregation_layer.dataProvider()
        caps = pr.capabilities()

        with LayerEditingManager(self.aggregation_layer,
                                 "Layer initialization",
                                 DEBUG):

            # add count and sum fields for aggregating statistics
            pr.addAttributes(
                [QgsField(self.reg_id_in_regions_attr_name, QVariant.String),
                 QgsField("count", QVariant.Int),
                 QgsField("sum", QVariant.Double)])

            # to show the overall progress, cycling through regions
            tot_regions = len(list(self.regions_layer.getFeatures()))
            msg = self.tr("Step 1 of 5: initializing aggregation layer...")
            progress = self.create_progress_message_bar(msg)

            # copy regions from regions layer
            for current_region, region_feature in enumerate(
                    self.regions_layer.getFeatures()):
                progress_perc = current_region / float(tot_regions) * 100
                progress.setValue(progress_perc)

                feat = QgsFeature()
                # copy the polygon from the input aggregation layer
                feat.setGeometry(QgsGeometry(region_feature.geometry()))
                # Define the count and sum fields to initialize to 0
                fields = QgsFields()
                fields.append(
                    QgsField(self.reg_id_in_regions_attr_name, QVariant.String))
                fields.append(
                    QgsField("count", QVariant.Int))
                fields.append(
                    QgsField("sum", QVariant.Double))
                # Add fields to the new feature
                feat.setFields(fields)
                feat[self.reg_id_in_regions_attr_name] = region_feature[
                    self.reg_id_in_regions_attr_name]
                feat['count'] = 0
                feat['sum'] = 0.0
                # Add the new feature to the layer
                if caps & QgsVectorDataProvider.AddFeatures:
                    pr.addFeatures([feat])
                    # Update the layer including the new feature
                self.aggregation_layer.updateFeature(feat)

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
        # TODO: If we know the region id of each point in the loss map, we
        #       don't need to use geometries while aggregating, and we can
        #       simply count by region id!
        #       We need to implement this as well
        """
        On the hypothesis that we don't know what is the region in which
        each point was collected,
        * we create a spatial index of the loss points
        * for each region (in the layer containing regionally-aggregated SVI
            * we identify points that are inside the region's bounding box
            * we check if each of these points is actually inside the
              region's geometry; if it is:
                * add 1 to the count of points in the region
                * add the loss value to the total loss of the region
        Notes:
        * self.loss_layer contains the not aggregated loss points
        * self.regions_layer contains the region geometries
        * self.aggregation_layer is the new layer with losses aggregated by
            region
        """
        # to show the overall progress, cycling through points
        tot_points = len(list(self.loss_layer.getFeatures()))
        msg = self.tr("Step 2 of 5: creating spatial index for loss points...")
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
            # to show the overall progress, cycling through regions
            # Note that regions from region layer were copied earlier into the
            # aggregation layer
            tot_regions = len(list(self.aggregation_layer.getFeatures()))
            msg = self.tr("Step 3 of 5: aggregating points by region...")
            progress = self.create_progress_message_bar(msg)

            # check if there are no loss points contained in any of the regions
            # and later display a warning if that occurs
            no_loss_points_in_any_region = True
            # We cycle through regions in the aggregation_layer, because the
            # aggregation layer contains the regions copied from the regions
            # layer, plus it contains the attributes count and sum to populate
            for current_region, region_feature in enumerate(
                    self.aggregation_layer.getFeatures()):
                progress_perc = current_region / float(tot_regions) * 100
                progress.setValue(progress_perc)
                msg = "{0}% - Region: {1} on {2}".format(progress_perc,
                                                         region_feature.id(),
                                                         tot_regions)
                with TraceTimeManager(msg, DEBUG):
                    points_count = 0
                    loss_sum = 0
                    region_geometry = region_feature.geometry()
                    # Find ids of points within the bounding box of the region
                    point_ids = spatial_index.intersects(
                        region_geometry.boundingBox())
                    # check if the points inside the bounding box of the region
                    # are actually inside the region's geometry
                    for point_id in point_ids:
                        msg = "Checking if point {0} is actually inside " \
                              "the region".format(point_id)
                        with TraceTimeManager(msg, DEBUG):
                            # Get the point feature by the point's id
                            request = QgsFeatureRequest().setFilterFid(
                                point_id)
                            point_feature = self.loss_layer.getFeatures(
                                request).next()
                            point_geometry = QgsGeometry(
                                point_feature.geometry())
                            # check if the point is actually inside the region
                            # and it is not only contained by its bounding box
                            if region_geometry.contains(point_geometry):
                                points_count += 1
                                # we have found at least one loss point inside
                                # a region
                                no_loss_points_in_any_region = False
                                point_loss = point_feature[self.loss_attr_name]
                                loss_sum += point_loss
                    msg = "Updating count and sum for the region..."
                    with TraceTimeManager(msg, DEBUG):
                        region_feature['count'] = points_count
                        region_feature['sum'] = loss_sum
                        self.aggregation_layer.updateFeature(region_feature)
                        # End updating count and sum attributes
                #raw_input("Press Enter to continue...")
        self.clear_progress_message_bar()
        # display a warning in case none of the loss points are inside
        # any of the regions
        if no_loss_points_in_any_region:
            msg = "No loss points are contained by any of the regions!"
            self.iface.messageBar().pushMessage(self.tr("Warning"),
                                                self.tr(msg),
                                                level=QgsMessageBar.INFO)

    def calculate_raster_stats(self):
        """
        In case the layer containing loss data is raster, use
        QgsZonalStatistics to calculate count, sum and average loss
        values for each region
        """
        zonal_statistics = QgsZonalStatistics(
            self.aggregation_layer,
            self.loss_layer.dataProvider().dataSourceUri())
        progress_dialog = QProgressDialog(
            self.tr('Calculating zonal statistics'),
            self.tr('Abort...'),
            0,
            0)
        zonal_statistics.calculateStatistics(progress_dialog)
        # TODO: This is not giving any warning in case no loss points are
        #       contained by any of the regions
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
            self.tr("Aggregated Losses (no empty regions)"),
            "memory")
        pr = self.purged_layer.dataProvider()
        caps = pr.capabilities()

        tot_regions = len(list(self.aggregation_layer.getFeatures()))
        msg = self.tr("Purging regions containing no loss points...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.purged_layer,
                                 "Purged layer initialization",
                                 DEBUG):
            # add count and sum fields for aggregating statistics
            pr.addAttributes(
                [QgsField(self.reg_id_in_regions_attr_name, QVariant.String),
                 QgsField("count", QVariant.Int),
                 QgsField("sum", QVariant.Double)])

            # copy regions from aggregation layer
            for current_region, region_feature in enumerate(
                    self.aggregation_layer.getFeatures()):
                progress_percent = current_region / float(tot_regions) * 100
                progress.setValue(progress_percent)
                # copy only regions which contain at least one loss point
                if region_feature['count'] >= 1:
                    feat = region_feature
                    # Add the new feature to the layer
                    if caps & QgsVectorDataProvider.AddFeatures:
                        pr.addFeatures([feat])
                        # Update the layer including the new feature
                    self.aggregation_layer.updateFeature(feat)

        self.clear_progress_message_bar()

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
        self.iface.messageBar().clearWidgets()

    #def load_social_vulnerability_layer(self, social_vulnerability_layer_path):
    #    # Load social vulnerability layer
    #    self.social_vulnerability_layer = QgsVectorLayer(
    #        social_vulnerability_layer_path,
    #        self.tr('Social vulnerability'),
    #        'ogr')
    #    # Add social vulnerability layer to registry
    #    if self.social_vulnerability_layer.isValid():
    #        QgsMapLayerRegistry.instance().addMapLayer(
    #            self.social_vulnerability_layer)
    #    else:
    #        raise RuntimeError('Social vulnerability layer invalid')

    def populate_svir_layer_with_loss_values(self):
        """
        Copy loss values from the aggregation layer to the svir layer
        which already contains social vulnerability related attributes
        taken from the regions layer.
        """
        # to show the overall progress, cycling through regions
        tot_regions = len(list(self.aggregation_layer.getFeatures()))
        msg = self.tr("Step 4 of 5: populating SVIR layer with loss values...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.svir_layer,
                                 "Add loss values to svir_layer",
                                 DEBUG):
            # Begin populating "loss" attribute with data from the
            # aggregation_layer selected by the user (possibly purged from
            # regions containing no loss data
            for current_region, svir_feat in enumerate(
                    self.svir_layer.getFeatures()):
                progress_percent = current_region / float(tot_regions) * 100
                progress.setValue(progress_percent)
                match_found = False
                for aggr_feat in self.loss_layer_to_join.getFeatures():
                    if svir_feat[self.reg_id_in_regions_attr_name] == \
                            aggr_feat[self.reg_id_in_regions_attr_name]:
                        svir_feat[AGGR_LOSS_ATTR_NAME] = aggr_feat['sum']
                        self.svir_layer.updateFeature(svir_feat)
                        match_found = True
            # TODO: Check if this is the desired behavior, i.e., if we actually
            #       want to remove from svir_layer the regions that contain no
            #       loss values
            if not match_found:
                caps = self.svir_layer.dataProvider().capabilities()
                if caps & QgsVectorDataProvider.DeleteFeatures:
                    res = self.svir_layer.dataProvider().deleteFeatures(
                        [aggr_feat.id()])
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
        Create a new layer joining (by region id) social vulnerability
        and loss data
        """
        # Create new svir layer, duplicating social vulnerability layer
        self.svir_layer = self.create_memory_copy_of_layer(
            self.social_vulnerability_layer, self.tr("SVIR map"))
        # Add "loss" attribute to svir_layer
        self.add_attributes_to_layer(self.svir_layer,
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
        self.add_attributes_to_layer(self.svir_layer,
                                     [QgsField('RISKPLUS', QVariant.Double),
                                      QgsField('RISKMULT', QVariant.Double),
                                      QgsField('RISK1F', QVariant.Double)])
        # for each region, calculate the value of the output attributes
        # to show the overall progress, cycling through regions
        tot_regions = len(list(self.svir_layer.getFeatures()))
        msg = self.tr("Step 5 of 5: calculating SVIR statistics...")
        progress = self.create_progress_message_bar(msg)

        with LayerEditingManager(self.svir_layer,
                                 "Calculate common SVIR statistics",
                                 DEBUG):
            for current_region, svir_feat in enumerate(
                    self.svir_layer.getFeatures()):
                progress_percent = current_region / float(tot_regions) * 100
                progress.setValue(progress_percent)
                svir_feat['RISKPLUS'] = (svir_feat[AGGR_LOSS_ATTR_NAME] +
                                         svir_feat[self.svi_attr_name])
                svir_feat['RISKMULT'] = (svir_feat[AGGR_LOSS_ATTR_NAME] *
                                         svir_feat[self.svi_attr_name])
                svir_feat['RISK1F'] = (svir_feat[AGGR_LOSS_ATTR_NAME] *
                                       (1 + svir_feat[self.svi_attr_name]))
                self.svir_layer.updateFeature(svir_feat)

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
