# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2015-02-23
        copyright            : (C) 2015 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QProgressDialog
from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsField,
                       QgsGeometry,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       )

from qgis.gui import QgsMessageBar

from qgis.analysis import QgsZonalStatistics
import processing as p

try:
    from processing.algs.saga import SagaUtils
    saga_was_imported = True
except:
    print "Unable to import SagaUtils module from processing.algs.saga"
    saga_was_imported = False

from process_layer import ProcessLayer

import resources_rc  # pylint: disable=W0611  # NOQA

from utils import (LayerEditingManager,
                   tr,
                   TraceTimeManager,
                   clear_progress_message_bar,
                   create_progress_message_bar,
                   )
from shared import (INT_FIELD_TYPE_NAME,
                    DOUBLE_FIELD_TYPE_NAME,
                    DEBUG,
                    )


def calculate_zonal_stats(loss_layer,
                          zonal_layer,
                          loss_attr_names,
                          loss_layer_is_vector,
                          zone_id_in_losses_attr_name,
                          zone_id_in_zones_attr_name,
                          iface):
    """
    The loss_layer containing loss data points, can raster or vector.
    The zonal_layer has to be a vector layer containing socioeconomic
    data aggregated by zone.
    At the end of the workflow, we will have, for each feature (zone):
    * a "LOSS_PTS" attribute, specifying how many loss points are
        inside the zone
    * for each loss variable:
        * a "SUM" attribute, summing the loss values for all the
        points that are inside the zone
        * a "AVG" attribute, averaging losses for each zone
    """
    # add count, sum and avg fields for aggregating statistics
    # (one new attribute for the count of points, then a sum and an average
    # for all the other loss attributes)
    loss_attrs_dict = {}
    count_field = QgsField(
        'LOSS_PTS', QVariant.Int)
    count_field.setTypeName(INT_FIELD_TYPE_NAME)
    count_added = \
        ProcessLayer(zonal_layer).add_attributes([count_field])
    # add_attributes returns a dict
    #     proposed_attr_name -> assigned_attr_name
    # so the actual count attribute name is the first value of the dict
    loss_attrs_dict['count'] = count_added.values()[0]
    for loss_attr_name in loss_attr_names:
        loss_attrs_dict[loss_attr_name] = {}
        sum_field = QgsField('SUM_%s' % loss_attr_name, QVariant.Double)
        sum_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        sum_added = \
            ProcessLayer(zonal_layer).add_attributes([sum_field])
        # see comment above
        loss_attrs_dict[loss_attr_name]['sum'] = sum_added.values()[0]
        avg_field = QgsField('AVG_%s' % loss_attr_name, QVariant.Double)
        avg_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        avg_added = \
            ProcessLayer(zonal_layer).add_attributes([avg_field])
        # see comment above
        loss_attrs_dict[loss_attr_name]['avg'] = avg_added.values()[0]
    if loss_layer_is_vector:
        # check if the user specified that the loss_layer contains an
        # attribute specifying what's the zone id for each loss point
        if zone_id_in_losses_attr_name:
            # then we can aggregate by zone id, instead of doing a
            # geo-spatial analysis to see in which zone each point is
            res = calculate_vector_stats_aggregating_by_zone_id(
                loss_layer, zonal_layer, zone_id_in_losses_attr_name,
                zone_id_in_zones_attr_name, loss_attr_names,
                loss_attrs_dict, iface)
            (loss_layer, zonal_layer) = res
        else:
            # otherwise we need to acquire the zones' geometries from the
            # zonal layer and check if loss points are inside those zones
            alg_name = 'saga:clippointswithpolygons'
            # if SAGA is not installed, the check will return a error msg
            err_msg = None
            if saga_was_imported:
                try:
                    saga_version = SagaUtils.getSagaInstalledVersion()
                    if saga_version is None:
                        err_msg = 'SAGA is not installed.'
                except AttributeError:
                    err_msg = 'Unable to get the SAGA installed version.'
            else:
                err_msg = 'SagaUtils was not imported.'
            if err_msg is not None:
                err_msg += tr(" In order to cope with complex geometries, "
                              "a working installation of SAGA is "
                              "recommended.")
                iface.messageBar().pushMessage(
                    tr("Warning"),
                    tr(err_msg),
                    level=QgsMessageBar.WARNING)
                calculate_vector_stats_using_geometries(
                    loss_layer, zonal_layer, zone_id_in_zones_attr_name,
                    zone_id_in_losses_attr_name, loss_attr_names,
                    loss_attrs_dict, iface)
            else:
                # using SAGA to find out in which zone each point is
                # (it does not compute any other statistics)
                # NOTE: The algorithm builds a new loss layer, in which
                #       each point will have an additional attribute,
                #       indicating the zone to which the point belongs. Be
                #       aware that such attribute is not actually the id of
                #       the zone, but the value of the attribute
                #       zone_id_in_zones_attr_name, which might
                #       possibly be not unique, causing later the grouping
                #       of points with the same value, even if
                #       geographically belonging to different polygons. For
                #       this reason, the user MUST select carefully the
                #       attribute in the zonal layer!
                res = p.runalg(alg_name,
                               loss_layer,
                               zonal_layer,
                               zone_id_in_zones_attr_name,
                               0,
                               None)
                if res is None:
                    msg = "An error occurred while attempting to " \
                          "compute zonal statistics with SAGA"
                    iface.messageBar().pushMessage(
                        tr("Error"),
                        tr(msg),
                        level=QgsMessageBar.CRITICAL)
                else:
                    loss_layer_plus_zones = QgsVectorLayer(
                        res['CLIPS'],
                        'Points labeled by zone',
                        'ogr')
                    if DEBUG:
                        QgsMapLayerRegistry.instance().addMapLayer(
                            loss_layer_plus_zones)
                    # If the zone id attribute name was already taken in
                    # the loss layer, when SAGA added the new attribute, it
                    # was given a different name by default. We need to get
                    # the new attribute name (as the difference between the
                    # loss_layer and the loss_layer_plus_zones)
                    new_fields = set(
                        field.name() for field in
                        loss_layer_plus_zones.dataProvider().fields())
                    orig_fields = set(
                        field.name() for field in
                        loss_layer.dataProvider().fields())
                    zone_field_name = (new_fields - orig_fields).pop()
                    if zone_field_name:
                        zone_id_in_losses_attr_name = zone_field_name
                    else:
                        zone_id_in_losses_attr_name = \
                            zone_id_in_zones_attr_name
                    calculate_vector_stats_aggregating_by_zone_id(
                        loss_layer_plus_zones, zonal_layer,
                        zone_id_in_losses_attr_name,
                        zone_id_in_zones_attr_name,
                        loss_attr_names, loss_attrs_dict, iface)
    else:
        (loss_layer, zonal_layer) = \
            calculate_raster_stats(loss_layer, zonal_layer)
    return (loss_layer, zonal_layer, loss_attrs_dict)


def calculate_vector_stats_aggregating_by_zone_id(
        loss_layer, zonal_layer, zone_id_in_losses_attr_name,
        zone_id_in_zones_attr_name, loss_attr_names, loss_attrs_dict, iface):
    """
    Once we know the zone id of each point in the loss map, we
    can count how many points are in each zone, sum and average their values
    """
    tot_points = len(list(loss_layer.getFeatures()))
    msg = tr("Step 2 of 3: aggregating losses by zone id...")
    msg_bar_item, progress = create_progress_message_bar(
        iface.messageBar(), msg)
    # if the user picked an attribute from the loss layer, to be
    # used as zone id, use that; otherwise, use the attribute
    # copied from the zonal layer
    if not zone_id_in_losses_attr_name:
        zone_id_in_losses_attr_name = zone_id_in_zones_attr_name
    with TraceTimeManager(msg, DEBUG):
        zone_stats = {}
        for current_point, point_feat in enumerate(
                loss_layer.getFeatures()):
            progress_perc = current_point / float(tot_points) * 100
            progress.setValue(progress_perc)
            zone_id = point_feat[zone_id_in_losses_attr_name]
            if zone_id not in zone_stats:
                zone_stats[zone_id] = {}
            for loss_attr_name in loss_attr_names:
                if loss_attr_name not in zone_stats[zone_id]:
                    zone_stats[zone_id][loss_attr_name] = {
                        'count': 0, 'sum': 0.0}
                loss_value = point_feat[loss_attr_name]
                zone_stats[zone_id][loss_attr_name]['count'] += 1
                zone_stats[zone_id][loss_attr_name]['sum'] \
                    += loss_value
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    msg = tr(
        "Step 3 of 3: writing point counts, loss sums and averages into "
        "the zonal layer...")
    with TraceTimeManager(msg, DEBUG):
        tot_zones = len(list(zonal_layer.getFeatures()))
        msg_bar_item, progress = create_progress_message_bar(
            iface.messageBar(), msg)
        with LayerEditingManager(zonal_layer,
                                 msg,
                                 DEBUG):
            count_idx = zonal_layer.fieldNameIndex(
                loss_attrs_dict['count'])
            sum_idx = {}
            avg_idx = {}
            for loss_attr_name in loss_attr_names:
                sum_idx[loss_attr_name] = zonal_layer.fieldNameIndex(
                    loss_attrs_dict[loss_attr_name]['sum'])
                avg_idx[loss_attr_name] = zonal_layer.fieldNameIndex(
                    loss_attrs_dict[loss_attr_name]['avg'])
            for current_zone, zone_feat in enumerate(
                    zonal_layer.getFeatures()):
                progress_perc = current_zone / float(tot_zones) * 100
                progress.setValue(progress_perc)
                # get the id of the current zone
                zone_id = zone_feat[zone_id_in_zones_attr_name]
                # initialize points_count, loss_sum and loss_avg
                # to zero, and update them afterwards only if the zone
                # contains at least one loss point
                points_count = 0
                loss_sum = {}
                loss_avg = {}
                for loss_attr_name in loss_attr_names:
                    loss_sum[loss_attr_name] = 0.0
                    loss_avg[loss_attr_name] = 0.0
                # retrieve count and sum from the dictionary, using
                # the zone id as key to get the values from the
                # corresponding dict (otherwise, keep zero values)
                if zone_id in zone_stats:
                    for loss_attr_name in loss_attr_names:
                        points_count = \
                            zone_stats[zone_id][loss_attr_name]['count']
                        loss_sum[loss_attr_name] = \
                            zone_stats[zone_id][loss_attr_name]['sum']
                        # division by zero should be impossible, because
                        # we are computing this only for zones containing
                        # at least one point (otherwise we keep all zeros)
                        loss_avg[loss_attr_name] = (
                            loss_sum[loss_attr_name] / points_count)
                        zone_stats[zone_id][loss_attr_name]['avg'] = \
                            loss_avg
                # without casting to int and to float, it wouldn't work
                fid = zone_feat.id()
                zonal_layer.changeAttributeValue(
                    fid, count_idx, int(points_count))
                for loss_attr_name in loss_attr_names:
                    zonal_layer.changeAttributeValue(
                        fid, sum_idx[loss_attr_name],
                        float(loss_sum[loss_attr_name]))
                    zonal_layer.changeAttributeValue(
                        fid, avg_idx[loss_attr_name],
                        float(loss_avg[loss_attr_name]))
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    notify_loss_aggregation_by_zone_complete(
        loss_attrs_dict, loss_attr_names, iface)
    return (loss_layer, zonal_layer)


def notify_loss_aggregation_by_zone_complete(
        loss_attrs_dict, loss_attr_names, iface):
    added_attrs = []
    added_attrs.append(loss_attrs_dict['count'])
    for loss_attr_name in loss_attr_names:
        added_attrs.extend(loss_attrs_dict[loss_attr_name].values())
    msg = "New attributes [%s] have been added to the zonal layer" % (
        ', '.join(added_attrs))
    iface.messageBar().pushMessage(
        tr("Info"),
        tr(msg),
        level=QgsMessageBar.INFO,
        duration=8)


def calculate_vector_stats_using_geometries(
        loss_layer, zonal_layer, zone_id_in_zones_attr_name,
        zone_id_in_losses_attr_name, loss_attr_names, loss_attrs_dict, iface):
    """
    On the hypothesis that we don't know what is the zone in which
    each point was collected (and if we can't use SAGA),
    we use an alternative implementation of what SAGA does, i.e.,
    we add a field to the loss layer, containing the id of the zone
    to which it belongs. In order to achieve that:
    * we create a spatial index of the loss points
    * for each zone (in the layer containing zonally-aggregated SVI
        * we identify points that are inside the zone's bounding box
        * we check if each of these points is actually inside the
            zone's geometry; if it is:
            * copy the zone id into the new field of the loss point
    * then we calculate_vector_stats_aggregating_by_zone_id
    Notes:
    * loss_layer contains the not aggregated loss points
    * zonal_layer contains the zone geometries
    """
    # make a copy of the loss layer and use that from now on
    add_to_registry = True if DEBUG else False
    loss_layer_plus_zones = \
        ProcessLayer(loss_layer).duplicate_in_memory(
            new_name='Loss plus zone labels', add_to_registry=add_to_registry)
    # add to it the new attribute that will contain the zone id
    # and to do that we need to know the type of the zone id field
    zonal_layer_fields = zonal_layer.dataProvider().fields()
    zone_id_field_variant = [
        field.type() for field in zonal_layer_fields
        if field.name() == zone_id_in_zones_attr_name][0]
    zone_id_field = QgsField(
        zone_id_in_zones_attr_name, zone_id_field_variant)
    assigned_attr_names_dict = \
        ProcessLayer(loss_layer_plus_zones).add_attributes(
            [zone_id_field])
    zone_id_in_losses_attr_name = assigned_attr_names_dict.values()[0]
    # get the index of the new attribute, to be used to update its values
    zone_id_attr_idx = loss_layer_plus_zones.fieldNameIndex(
        zone_id_in_losses_attr_name)
    # to show the overall progress, cycling through points
    tot_points = len(list(loss_layer_plus_zones.getFeatures()))
    msg = tr(
        "Step 2 of 3: creating spatial index for loss points...")
    msg_bar_item, progress = create_progress_message_bar(
        iface.messageBar(), msg)

    # create spatial index
    with TraceTimeManager(tr("Creating spatial index for loss points..."),
                          DEBUG):
        spatial_index = QgsSpatialIndex()
        for current_point, loss_feature in enumerate(
                loss_layer_plus_zones.getFeatures()):
            progress_perc = current_point / float(tot_points) * 100
            progress.setValue(progress_perc)
            spatial_index.insertFeature(loss_feature)

    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    with LayerEditingManager(loss_layer_plus_zones,
                             tr("Label each point with the zone id"),
                             DEBUG):
        # to show the overall progress, cycling through zones
        tot_zones = len(list(zonal_layer.getFeatures()))
        msg = tr("Step 3 of 3: labeling points by zone id...")
        msg_bar_item, progress = create_progress_message_bar(
            iface.messageBar(), msg)
        for current_zone, zone_feature in enumerate(
                zonal_layer.getFeatures()):
            progress_perc = current_zone / float(tot_zones) * 100
            progress.setValue(progress_perc)
            msg = "{0}% - Zone: {1} on {2}".format(progress_perc,
                                                   zone_feature.id(),
                                                   tot_zones)
            with TraceTimeManager(msg, DEBUG):
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
                        point_feature = loss_layer_plus_zones.getFeatures(
                            request).next()
                        point_geometry = QgsGeometry(
                            point_feature.geometry())
                        # check if the point is actually inside the zone
                        # and it is not only contained by its bounding box
                        if zone_geometry.contains(point_geometry):
                            zone_id = zone_feature[
                                zone_id_in_zones_attr_name]
                            loss_layer_plus_zones.changeAttributeValue(
                                point_id, zone_id_attr_idx, zone_id)
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    calculate_vector_stats_aggregating_by_zone_id(
        loss_layer_plus_zones,
        zonal_layer, zone_id_in_losses_attr_name,
        zone_id_in_zones_attr_name, loss_attr_names,
        loss_attrs_dict, iface)


def calculate_raster_stats(loss_layer, zonal_layer, iface):
    """
    In case the layer containing loss data is raster, use
    QgsZonalStatistics to calculate PTS_COUNT, sum and average loss
    values for each zone
    """
    zonal_statistics = QgsZonalStatistics(
        zonal_layer,
        loss_layer.dataProvider().dataSourceUri())
    progress_dialog = QProgressDialog(
        tr('Calculating zonal statistics'),
        tr('Abort...'),
        0,
        0)
    zonal_statistics.calculateStatistics(progress_dialog)
    # TODO: This is not giving any warning in case no loss points are
    #       contained by any of the zones
    if progress_dialog.wasCanceled():
        iface.messageBar().pushMessage(
            tr("ZonalStats Error"),
            tr('You aborted aggregation, so there are '
                'no data for analysis. Exiting...'),
            level=QgsMessageBar.CRITICAL)
    # FIXME: We probably need to return something more
    return (loss_layer, zonal_layer)
