# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-02-23
#        copyright            : (C) 2015 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
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

import tempfile
from qgis.core import (QgsVectorLayer,
                       QgsProject,
                       QgsField,
                       QgsGeometry,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       Qgis,
                       edit,
                       NULL,
                       )
from qgis.analysis import QgsZonalStatistics

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QProgressDialog

import processing

from svir.calculations.process_layer import ProcessLayer

from svir.utilities.utils import (
                                  tr,
                                  TraceTimeManager,
                                  clear_progress_message_bar,
                                  create_progress_message_bar,
                                  log_msg,
                                  save_layer_as_shapefile,
                                  )
from svir.utilities.shared import (INT_FIELD_TYPE_NAME,
                                   DOUBLE_FIELD_TYPE_NAME,
                                   DEBUG,
                                   )


# TODO: use new processing algorithm instead. See:
# https://gis.stackexchange.com/questions/209596/replicating-join-attributes-by-location-using-pyqgis  # NOQA
# https://anitagraser.com/2018/03/24/revisiting-point-polygon-joins/  # NOQA
def calculate_zonal_stats(loss_layer,
                          zonal_layer,
                          loss_attr_names,
                          loss_layer_is_vector,
                          zone_id_in_losses_attr_name,
                          zone_id_in_zones_attr_name,
                          iface,
                          extra=True):
    """
    :param loss_layer: vector or raster layer containing loss data points
    :param zonal_layer: vector layer containing zonal data
    :param loss_attr_names: names of the loss layer fields to be aggregated
    :param loss_layer_is_vector: True if the loss layer is a vector layer
    :param zone_id_in_losses_attr_name:
        name of the field containing the zone id where each loss point belongs
        (or None)
    :param zone_id_in_zones_attr_name:
        name of the field containing the id of each zone (or None)
    :param iface: QGIS interface
    :param extra:
        if True, also NUM_POINTS and AVG will be added

    At the end of the workflow, we will have, for each feature (zone):

    * a "NUM_POINTS" attribute, specifying how many points are
      inside the zone (added if extra=True)
    * for each variable:
        * a "SUM" attribute, summing the values for all the
          points that are inside the zone
        * a "AVG" attribute, averaging for each zone (added if extra=True)
    """

    # add count, sum and avg fields for aggregating statistics
    # (one new attribute for the count of points, then a sum and an average
    # for all the other loss attributes)
    # TODO remove debugging trace
    loss_attrs_dict = {}
    if extra:  # adding also NUM_POINTS and AVG
        count_field = QgsField(
                'NUM_POINTS', QVariant.Int)
        count_field.setTypeName(INT_FIELD_TYPE_NAME)
        count_added = \
            ProcessLayer(zonal_layer).add_attributes([count_field])
        # add_attributes returns a dict
        #     proposed_attr_name -> assigned_attr_name
        # so the actual count attribute name is the first value of the dict
        loss_attrs_dict['count'] = list(count_added.values())[0]
    for loss_attr_name in loss_attr_names:
        loss_attrs_dict[loss_attr_name] = {}
        sum_field = QgsField('SUM_%s' % loss_attr_name, QVariant.Double)
        sum_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        sum_added = \
            ProcessLayer(zonal_layer).add_attributes([sum_field])
        # see comment above
        loss_attrs_dict[loss_attr_name]['sum'] = list(sum_added.values())[0]
        if extra:  # adding also NUM_POINTS and AVG
            avg_field = QgsField('AVG_%s' % loss_attr_name, QVariant.Double)
            avg_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            avg_added = \
                ProcessLayer(zonal_layer).add_attributes([avg_field])
            # see comment above
            loss_attrs_dict[loss_attr_name]['avg'] = list(
                avg_added.values())[0]
    if loss_layer_is_vector:
        # check if the user specified that the loss_layer contains an
        # attribute specifying what's the zone id for each loss point
        if zone_id_in_losses_attr_name:
            # then we can aggregate by zone id, instead of doing a
            # geo-spatial analysis to see in which zone each point is
            res = calculate_vector_stats_aggregating_by_zone_id(
                    loss_layer, zonal_layer, zone_id_in_losses_attr_name,
                    zone_id_in_zones_attr_name, loss_attr_names,
                    loss_attrs_dict, iface, extra=extra)
            (loss_layer, zonal_layer, loss_attrs_dict) = res
        else:
            if not zone_id_in_zones_attr_name:
                # we need to acquire the zones' geometries from the
                # zonal layer and check if loss points are inside those zones
                # In order to be sure to avoid duplicate zone names, we add to
                # the zonal layer an additional field and copy into that the
                # unique id of each feature
                proposed_attr_name = 'ZONE_ID'
                new_attr = QgsField(proposed_attr_name, QVariant.Int)
                new_attr.setTypeName(INT_FIELD_TYPE_NAME)
                attr_dict = \
                    ProcessLayer(zonal_layer).add_attributes([new_attr])
                # we get a dict, from which we find the actual attribute name
                # in the only dict value
                zone_id_in_zones_attr_name = list(attr_dict.values())[0]
                with edit(zonal_layer):
                    unique_id_idx = zonal_layer.fields().indexOf(
                            zone_id_in_zones_attr_name)
                    for feat in zonal_layer.getFeatures():
                        zonal_layer.changeAttributeValue(
                                feat.id(), unique_id_idx, feat.id())

            (_, loss_layer_plus_zones,
             zone_id_in_losses_attr_name) = add_zone_id_to_points(
                    iface, loss_layer, zonal_layer, zone_id_in_zones_attr_name)

            old_field_to_new_field = {}
            for idx, field in enumerate(loss_layer.fields()):
                old_field_to_new_field[field.name()] = \
                    loss_layer_plus_zones.fields()[idx].name()

            res = calculate_vector_stats_aggregating_by_zone_id(
                    loss_layer_plus_zones, zonal_layer,
                    zone_id_in_losses_attr_name,
                    zone_id_in_zones_attr_name,
                    loss_attr_names, loss_attrs_dict, iface,
                    old_field_to_new_field, extra=extra)
            (loss_layer, zonal_layer, loss_attrs_dict) = res

    else:
        (loss_layer, zonal_layer) = \
            calculate_raster_stats(loss_layer, zonal_layer)
    return loss_layer, zonal_layer, loss_attrs_dict


def add_zone_id_to_points(iface, point_layer, zonal_layer, zones_id_attr_name):
    """
    Given a layer with points and a layer with zones, add to the points layer a
    new field containing the id of the zone inside which it is located.

    :param iface: QGIS interface
    :param point_layer: a QgsVectorLayer containing points
    :param zonal_layer: a QgsVectorLayer containing polygons
    :param zones_id_attr_name:
        name of the field of the zonal_layer that contains the zone id
    :returns:
        * point_attrs_dict: a dictionary mapping the original field names
          of the point_layer with the possibly laundered ones,
        * point_layer_plus_zones: the points layer with the additional field
          containing the zone id
        * points_zone_id_attr_name: the id of the new field added to the
          points layer, containing the zone id
    """
    orig_fieldnames = [field.name() for field in point_layer.fields()]
    point_layer_plus_zones, points_zone_id_attr_name = \
        _add_zone_id_to_points_internal(
            iface, point_layer, zonal_layer, zones_id_attr_name)
    # fieldnames might have been laundered to max 10 characters
    final_fieldnames = [
        field.name() for field in point_layer_plus_zones.fields()]
    # NOTE: final_fieldnames contains an additional field with the id, so I
    #       can't use zip on lists of different length
    point_attrs_dict = {orig_fieldnames[i]: final_fieldnames[i]
                        for i in range(len(orig_fieldnames))}
    return (point_attrs_dict, point_layer_plus_zones,
            points_zone_id_attr_name)


def _add_zone_id_to_points_internal(iface, loss_layer, zonal_layer,
                                    zone_id_in_zones_attr_name):
    """
       On the hypothesis that we don't know what is the zone in which
       each point was collected we use an alternative implementation of what
       SAGA does, i.e.,
       we add a field to the loss layer, containing the id of the zone
       to which it belongs. In order to achieve that:
       * we create a spatial index of the loss points
       * for each zone (in the layer containing zonally-aggregated SVI
           * we identify points that are inside the zone's bounding box
           * we check if each of these points is actually inside the
               zone's geometry; if it is:
               * copy the zone id into the new field of the loss point
       Notes:
       * loss_layer contains the not aggregated loss points
       * zonal_layer contains the zone geometries
       """
    # make a copy of the loss layer and use that from now on
    add_to_registry = True if DEBUG else False
    loss_layer_plus_zones = \
        ProcessLayer(loss_layer).duplicate_in_memory(
                new_name='Loss plus zone labels',
                add_to_registry=add_to_registry)
    # add to it the new attribute that will contain the zone id
    # and to do that we need to know the type of the zone id field
    zonal_layer_fields = zonal_layer.fields()
    zone_id_field_variant, zone_id_field_type_name = [
        (field.type(), field.typeName()) for field in zonal_layer_fields
        if field.name() == zone_id_in_zones_attr_name][0]
    zone_id_field = QgsField(
            zone_id_in_zones_attr_name, zone_id_field_variant)
    zone_id_field.setTypeName(zone_id_field_type_name)
    assigned_attr_names_dict = \
        ProcessLayer(loss_layer_plus_zones).add_attributes(
                [zone_id_field])
    zone_id_in_losses_attr_name = list(assigned_attr_names_dict.values())[0]
    # get the index of the new attribute, to be used to update its values
    zone_id_attr_idx = loss_layer_plus_zones.fields().indexOf(
            zone_id_in_losses_attr_name)
    # to show the overall progress, cycling through points
    tot_points = loss_layer_plus_zones.featureCount()
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
    with edit(loss_layer_plus_zones):
        # to show the overall progress, cycling through zones
        tot_zones = zonal_layer.featureCount()
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
                        point_feature = next(loss_layer_plus_zones.getFeatures(
                                request))
                        point_geometry = QgsGeometry(
                                point_feature.geometry())
                        # check if the point is actually inside the zone
                        # and it is not only contained by its bounding box
                        if zone_geometry.contains(point_geometry):
                            zone_id = zone_feature[
                                zone_id_in_zones_attr_name]
                            loss_layer_plus_zones.changeAttributeValue(
                                point_id, zone_id_attr_idx, zone_id)
        # for consistency with the SAGA algorithm, remove points that don't
        # belong to any zone
        for point_feature in loss_layer_plus_zones.getFeatures():
            if not point_feature[zone_id_in_losses_attr_name]:
                loss_layer_plus_zones.deleteFeature(point_feature.id())
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    return loss_layer_plus_zones, zone_id_in_losses_attr_name


def calculate_vector_stats_aggregating_by_zone_id(
        loss_layer, zonal_layer, zone_id_in_losses_attr_name,
        zone_id_in_zones_attr_name, loss_attr_names, loss_attrs_dict,
        iface, old_field_to_new_field=None, extra=True):
    """
    Once we know the zone id of each point in the loss map, we
    can count how many points are in each zone, sum and average their values
    """
    tot_points = loss_layer.featureCount()
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
                if old_field_to_new_field:
                    loss_value = point_feat[
                        old_field_to_new_field[loss_attr_name]]
                else:
                    loss_value = point_feat[loss_attr_name]
                zone_stats[zone_id][loss_attr_name]['count'] += 1
                zone_stats[zone_id][loss_attr_name]['sum'] += loss_value
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    if extra:
        msg = tr("Step 3 of 3: writing point counts, loss sums and averages"
                 " into the zonal layer...")
    else:
        msg = tr("Step 3 of 3: writing sums into the zonal layer...")
    with TraceTimeManager(msg, DEBUG):
        tot_zones = zonal_layer.featureCount()
        msg_bar_item, progress = create_progress_message_bar(
                iface.messageBar(), msg)
        with edit(zonal_layer):
            if extra:
                count_idx = zonal_layer.fields().indexOf(
                        loss_attrs_dict['count'])
                avg_idx = {}
            sum_idx = {}
            for loss_attr_name in loss_attr_names:
                sum_idx[loss_attr_name] = zonal_layer.fields().indexOf(
                        loss_attrs_dict[loss_attr_name]['sum'])
                if extra:
                    avg_idx[loss_attr_name] = zonal_layer.fields().indexOf(
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
                if extra:
                    loss_avg = {}
                loss_sum = {}
                for loss_attr_name in loss_attr_names:
                    loss_sum[loss_attr_name] = 0.0
                    if extra:
                        loss_avg[loss_attr_name] = 0.0
                # retrieve count and sum from the dictionary, using
                # the zone id as key to get the values from the
                # corresponding dict (otherwise, keep zero values)
                if zone_id in zone_stats:
                    for loss_attr_name in loss_attr_names:
                        loss_sum[loss_attr_name] = \
                            zone_stats[zone_id][loss_attr_name]['sum']
                        points_count = \
                            zone_stats[zone_id][loss_attr_name]['count']
                        if extra:
                            # division by zero should be impossible, because
                            # we are computing this only for zones containing
                            # at least one point (otherwise we keep all zeros)
                            loss_avg[loss_attr_name] = (
                                loss_sum[loss_attr_name] / points_count)
                            # NOTE: The following line looks redundant
                            zone_stats[zone_id][loss_attr_name]['avg'] = (
                                loss_avg[loss_attr_name])
                # without casting to int and to float, it wouldn't work
                fid = zone_feat.id()
                if extra:
                    zonal_layer.changeAttributeValue(
                            fid, count_idx, int(points_count))
                for loss_attr_name in loss_attr_names:
                    if points_count:
                        zonal_layer.changeAttributeValue(
                                fid, sum_idx[loss_attr_name],
                                float(loss_sum[loss_attr_name]))
                        if extra:
                            zonal_layer.changeAttributeValue(
                                    fid, avg_idx[loss_attr_name],
                                    float(loss_avg[loss_attr_name]))
                    else:
                        # if no points were found in that region, let both
                        # sum and average be NULL instead of 0
                        zonal_layer.changeAttributeValue(
                                fid, sum_idx[loss_attr_name],
                                NULL)
                        if extra:
                            zonal_layer.changeAttributeValue(
                                    fid, avg_idx[loss_attr_name],
                                    NULL)
    clear_progress_message_bar(iface.messageBar(), msg_bar_item)
    notify_loss_aggregation_by_zone_complete(
            loss_attrs_dict, loss_attr_names, iface, extra=extra)
    return (loss_layer, zonal_layer, loss_attrs_dict)


def notify_loss_aggregation_by_zone_complete(
        loss_attrs_dict, loss_attr_names, iface, extra=True):
    added_attrs = []
    if extra:
        added_attrs.append(loss_attrs_dict['count'])
    for loss_attr_name in loss_attr_names:
        added_attrs.extend(list(loss_attrs_dict[loss_attr_name].values()))
    msg = "New attributes [%s] have been added to the zonal layer" % (
        ', '.join(added_attrs))
    log_msg(msg, level='S', message_bar=iface.messageBar())


def calculate_raster_stats(loss_layer, zonal_layer, iface):
    """
    In case the layer containing loss data is raster, use
    QgsZonalStatistics to calculate NUM_POINTS, SUM and AVG
    values for each zone
    """
    zonal_statistics = QgsZonalStatistics(
            zonal_layer,
            loss_layer)
    progress_dialog = QProgressDialog(
            tr('Calculating zonal statistics'),
            tr('Abort...'),
            0,
            0)
    zonal_statistics.calculateStatistics(progress_dialog)
    # TODO: This is not giving any warning in case no loss points are
    #       contained by any of the zones
    if progress_dialog.wasCanceled():
        msg = ("You aborted aggregation, so there are"
               " no data for analysis. Exiting...")
        log_msg(msg, level='C', message_bar=iface.messageBar())
    # FIXME: We probably need to return something more
    return (loss_layer, zonal_layer)


def purge_zones_without_loss_points(
        zonal_layer, loss_attrs_dict, iface):
    """
    Delete from the zonal layer the zones that contain no loss points
    """
    tot_zones = zonal_layer.featureCount()
    msg = tr("Purging zones containing no loss points...")
    msg_bar_item, progress = create_progress_message_bar(
            iface.messageBar(), msg)

    with edit(zonal_layer):
        for current_zone, zone_feature in enumerate(zonal_layer.getFeatures()):
            progress_percent = current_zone / float(tot_zones) * 100
            progress.setValue(progress_percent)
            # save the ids of the zones to purge (which contain no loss
            # points)
            if zone_feature[loss_attrs_dict['count']] == 0:
                zonal_layer.deleteFeature(zone_feature.id())

    clear_progress_message_bar(iface.messageBar(), msg_bar_item)

    msg = "Zones containing no loss points were deleted"
    log_msg(msg, level='W', message_bar=iface.messageBar())
    return zonal_layer
