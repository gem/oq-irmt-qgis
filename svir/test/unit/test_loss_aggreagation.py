# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

# import qgis libs so that we set the correct sip api version
import os.path
import unittest
import tempfile
from qgis.core import QgsVectorLayer
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats,
    purge_zones_without_loss_points,
    )
from svir.utilities.utils import save_layer_as_shapefile
from svir.test.utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class AggregateLossByZoneTestCase(unittest.TestCase):

    def setUp(self):
        # Load dummy layers
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'aggregation', 'dummy')
        self.loss_attr_names = ['FATALITIES', 'STRUCTURAL']
        self.loss_layer_is_vector = True

    def test_aggregate_using_zone_id(self):
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points_having_zone_ids.shp')
        orig_loss_layer = QgsVectorLayer(
            loss_layer_path, 'Loss points having zone ids', 'ogr')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.shp')
        orig_zonal_layer = QgsVectorLayer(
            zonal_layer_path, 'SVI zones', 'ogr')
        # avoid modifying the original layers
        copied_loss_layer = ProcessLayer(orig_loss_layer).duplicate_in_memory()
        copied_zonal_layer = ProcessLayer(
            orig_zonal_layer).duplicate_in_memory()
        zone_id_in_zones_attr_name = 'ZONE_NAME'
        zone_id_in_losses_attr_name = 'ZONE_NAME'
        res = calculate_zonal_stats(copied_loss_layer,
                                    copied_zonal_layer,
                                    self.loss_attr_names,
                                    self.loss_layer_is_vector,
                                    zone_id_in_losses_attr_name,
                                    zone_id_in_zones_attr_name,
                                    IFACE)
        (output_loss_layer, output_zonal_layer, output_loss_attrs_dict) = res
        _, output_loss_layer_shp_path = tempfile.mkstemp(suffix='.shp')
        _, output_zonal_layer_shp_path = tempfile.mkstemp(suffix='.shp')
        save_layer_as_shapefile(output_loss_layer, output_loss_layer_shp_path)
        save_layer_as_shapefile(output_zonal_layer,
                                output_zonal_layer_shp_path)
        output_loss_layer = QgsVectorLayer(
            output_loss_layer_shp_path, 'Loss points having zone ids', 'ogr')
        output_zonal_layer = QgsVectorLayer(
            output_zonal_layer_shp_path, 'Zonal layer', 'ogr')

        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones_plus_loss_stats_zone_names.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)

    def _aggregate_using_geometries(
            self, force_saga=False, force_fallback=False, sum_only=False):
        # TODO: manage both with or without SAGA
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points.shp')
        orig_loss_layer = QgsVectorLayer(loss_layer_path, 'Loss points', 'ogr')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.shp')
        orig_zonal_layer = QgsVectorLayer(
            zonal_layer_path, 'SVI zones', 'ogr')
        # avoid modifying the original layers
        copied_loss_layer = ProcessLayer(orig_loss_layer).duplicate_in_memory()
        copied_zonal_layer = ProcessLayer(
            orig_zonal_layer).duplicate_in_memory()
        zone_id_in_losses_attr_name = None
        zone_id_in_zones_attr_name = None

        res = calculate_zonal_stats(copied_loss_layer,
                                    copied_zonal_layer,
                                    self.loss_attr_names,
                                    self.loss_layer_is_vector,
                                    zone_id_in_losses_attr_name,
                                    zone_id_in_zones_attr_name,
                                    IFACE,
                                    force_saga,
                                    force_fallback,
                                    sum_only=sum_only)
        (output_loss_layer, output_zonal_layer, output_loss_attrs_dict) = res
        _, output_loss_layer_shp_path = tempfile.mkstemp(suffix='.shp')
        _, output_zonal_layer_shp_path = tempfile.mkstemp(suffix='.shp')
        save_layer_as_shapefile(output_loss_layer, output_loss_layer_shp_path)
        save_layer_as_shapefile(output_zonal_layer,
                                output_zonal_layer_shp_path)
        output_loss_layer = QgsVectorLayer(
            output_loss_layer_shp_path, 'Loss points plus zone ids', 'ogr')
        output_zonal_layer = QgsVectorLayer(
            output_zonal_layer_shp_path, 'Zonal layer', 'ogr')
        expected_loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points_added_zone_ids.shp')
        expected_loss_layer = QgsVectorLayer(expected_loss_layer_path,
                                             'Loss points plus zone ids',
                                             'ogr')
        if sum_only:
            expected_zonal_layer_path = os.path.join(
                self.data_dir_name,
                'svi_zones_plus_loss_stats_zone_ids_sum_only.shp')
        else:
            expected_zonal_layer_path = os.path.join(
                self.data_dir_name, 'svi_zones_plus_loss_stats_zone_ids.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')
        self._check_output_layer(output_loss_layer, expected_loss_layer)
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)

    def test_aggregate_using_geometries(self):
        self._aggregate_using_geometries()

    def test_aggregate_using_geometries_forcing_saga(self):
        self._aggregate_using_geometries(force_saga=True)

    def test_aggregate_using_geometries_forcing_fallback(self):
        self._aggregate_using_geometries(force_fallback=True)

    def test_aggregate_using_geometries_sum_only(self):
        self._aggregate_using_geometries(sum_only=True)

    def test_purge_empty_zones(self):
        loss_attrs_dict = {
            'count': u'NUM_POINTS',
            'FATALITIES': {'sum': u'SUM_FATALITIES',
                           'avg': u'AVG_FATALITIES'},
            'STRUCTURAL': {'sum': u'SUM_STRUCTURAL',
                           'avg': u'AVG_STRUCTURAL'}}
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
            ProcessLayer(output_layer).pprint(usage='testing')
            ProcessLayer(expected_layer).pprint(usage='testing')
            raise Exception(
                'The output layer is different than expected (see above)')
