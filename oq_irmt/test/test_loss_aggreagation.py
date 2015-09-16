# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
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
# import qgis libs so that we set the correct sip api version
import os.path
import unittest
from qgis.core import QgsVectorLayer

from oq_irmt.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from oq_irmt.calculations.process_layer import ProcessLayer
from oq_irmt.calculations.aggregate_loss_by_zone import (calculate_zonal_stats,
                                    purge_zones_without_loss_points,)


class AggregateLossByZoneTestCase(unittest.TestCase):

    def setUp(self):
        # Load dummy layers
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(curr_dir_name,
                                          'data/aggregation/dummy')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.shp')
        orig_zonal_layer = QgsVectorLayer(zonal_layer_path, 'SVI zones', 'ogr')
        # Avoid modifying the original files
        self.copied_zonal_layer = \
            ProcessLayer(orig_zonal_layer).duplicate_in_memory()
        self.loss_attr_names = ['FATALITIES', 'STRUCTURAL']
        self.loss_layer_is_vector = True

    def test_aggregate_using_zone_id(self):
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points_having_zone_ids.shp')
        orig_loss_layer = QgsVectorLayer(loss_layer_path,
                                         'Loss points having zone ids',
                                         'ogr')
        # avoid modifying the original layers
        copied_loss_layer = ProcessLayer(orig_loss_layer).duplicate_in_memory()
        zone_id_in_zones_attr_name = 'ZONE_NAME'
        zone_id_in_losses_attr_name = 'ZONE_NAME'
        res = calculate_zonal_stats(copied_loss_layer,
                                    self.copied_zonal_layer,
                                    self.loss_attr_names,
                                    self.loss_layer_is_vector,
                                    zone_id_in_losses_attr_name,
                                    zone_id_in_zones_attr_name,
                                    IFACE)
        (output_loss_layer, output_zonal_layer, output_loss_attrs_dict) = res

        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats_zone_names.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')

        self._check_output_layer(output_zonal_layer, expected_zonal_layer)
        # just to make sure that we can manage correctly the attributes that
        # were added, attempt to delete them
        added_attrs = []
        added_attrs.append(output_loss_attrs_dict['count'])
        for loss_attr in self.loss_attr_names:
            added_attrs.extend(output_loss_attrs_dict[loss_attr].values())
        ProcessLayer(output_zonal_layer).delete_attributes(
            added_attrs)

    def test_aggregate_using_geometries(self):
        # TODO: manage both with or without SAGA
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points.shp')
        orig_loss_layer = QgsVectorLayer(loss_layer_path, 'Loss points', 'ogr')
        # avoid modifying the original layers
        copied_loss_layer = ProcessLayer(orig_loss_layer).duplicate_in_memory()
        zone_id_in_losses_attr_name = None
        zone_id_in_zones_attr_name = None

        res = calculate_zonal_stats(copied_loss_layer,
                                    self.copied_zonal_layer,
                                    self.loss_attr_names,
                                    self.loss_layer_is_vector,
                                    zone_id_in_losses_attr_name,
                                    zone_id_in_zones_attr_name,
                                    IFACE)
        (output_loss_layer, output_zonal_layer, output_loss_attrs_dict) = res
        expected_loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points_added_zone_ids.shp')
        expected_loss_layer = QgsVectorLayer(expected_loss_layer_path,
                                             'Loss points plus zone ids',
                                             'ogr')
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats_zone_ids.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')
        self._check_output_layer(output_loss_layer, expected_loss_layer)
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)

    def test_purge_empty_zones(self):
        loss_attrs_dict = {
            'count': u'LOSS_PTS',
            'FATALITIES': {'sum': u'SUM_FATALI',
                           'avg': u'AVG_FATALI'},
            'STRUCTURAL': {'sum': u'SUM_STRUCT',
                           'avg': u'AVG_STRUCT'}}
        orig_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats_zone_ids.shp')
        orig_zonal_layer = QgsVectorLayer(
            orig_zonal_layer_path, 'Zonal layer plus stats', 'ogr')
        # avoid modifying the original layers
        copied_zonal_layer = \
            ProcessLayer(orig_zonal_layer).duplicate_in_memory()
        output_zonal_layer = purge_zones_without_loss_points(
            copied_zonal_layer, loss_attrs_dict, IFACE)
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats_purged.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal purged layer', 'ogr')
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)

    def _check_output_layer(self, output_layer, expected_layer):
        if not ProcessLayer(output_layer).has_same_content_as(
                expected_layer):
            ProcessLayer(output_layer).pprint()
            ProcessLayer(expected_layer).pprint()
            raise Exception(
                'The output layer is different than expected')
