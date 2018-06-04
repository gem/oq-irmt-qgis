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
from svir.calculations.aggregate_loss_by_zone import calculate_zonal_stats
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

    def test_sum_point_values_by_zone(self):
        points_layer_path = os.path.join(
            self.data_dir_name, 'loss_points.gpkg')
        points_layer = QgsVectorLayer(
            points_layer_path, 'Loss points having zone ids', 'ogr')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.gpkg')
        zonal_layer = QgsVectorLayer(
            zonal_layer_path, 'SVI zones', 'ogr')
        output_zonal_layer = calculate_zonal_stats(
            zonal_layer, points_layer, self.loss_attr_names,
            'output', discard_nonmatching=False,
            predicates=('intersects',), summaries=('sum',))
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name,
            'svi_zones_plus_loss_stats.gpkg')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Expected zonal layer', 'ogr')
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)

    def _check_output_layer(self, output_layer, expected_layer):
        if not ProcessLayer(output_layer).has_same_content_as(
                expected_layer):
            ProcessLayer(output_layer).pprint(usage='testing')
            ProcessLayer(expected_layer).pprint(usage='testing')
            raise Exception(
                'The output layer is different than expected (see above)')
