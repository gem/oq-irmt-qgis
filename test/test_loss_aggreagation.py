# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
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
import qgis   # pylint: disable=W0611  # NOQA
import os.path

import unittest

from qgis.core import QgsVectorLayer

from utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from process_layer import ProcessLayer
from aggregate_loss_by_zone import calculate_zonal_stats


class AggregateLossByZoneTestCase(unittest.TestCase):

    def setUp(self):
        # Load dummy layers
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(curr_dir_name,
                                          'data/aggregation/dummy')
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points.shp')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.shp')
        orig_loss_layer = QgsVectorLayer(loss_layer_path, 'Loss points', 'ogr')
        orig_zonal_layer = QgsVectorLayer(zonal_layer_path, 'SVI zones', 'ogr')
        # Avoid modifying the original files
        self.loss_layer = ProcessLayer(orig_loss_layer).duplicate_in_memory()
        self.zonal_layer = ProcessLayer(orig_zonal_layer).duplicate_in_memory()
        self.loss_attr_names = ['FATALITIES', 'STRUCTURAL']
        self.loss_layer_is_vector = True
        self.zone_id_in_zones_attr_name = ''

    def test_aggregate_using_zone_id(self):
        # TODO aggregate
        pass

    def test_aggregate_using_geometries(self):
        # TODO: manage both with or without SAGA
        zone_id_in_losses_attr_name = None
        zone_id_in_zones_attr_name = 'ZONE_ID'

        res = calculate_zonal_stats(self.loss_layer,
                                    self.zonal_layer,
                                    self.loss_attr_names,
                                    self.loss_layer_is_vector,
                                    zone_id_in_losses_attr_name,
                                    zone_id_in_zones_attr_name,
                                    IFACE)
        (output_loss_layer, output_zonal_layer, output_loss_attrs_dict) = res

        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')

        if not ProcessLayer(output_zonal_layer).has_same_content_as(
                expected_zonal_layer):
            ProcessLayer(output_loss_layer).pprint()
            ProcessLayer(output_zonal_layer).pprint()
            ProcessLayer(expected_zonal_layer).pprint()
            raise Exception('The output layer is different than expected')

    def test_aggregate_and_purge_empty_zones(self):
        # TODO
        pass
