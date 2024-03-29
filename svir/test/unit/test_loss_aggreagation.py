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
import tempfile
import shutil
import time
from qgis.core import QgsVectorLayer
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import calculate_zonal_stats

from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

QGIS_APP = start_app()
IFACE = get_iface()


class AggregateLossByZoneTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        # Load dummy layers
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'aggregation', 'dummy')
        self.loss_attr_names = ['PEOPLE', 'STRUCTURAL']
        self.loss_layer_is_vector = True

    def test_sum_point_values_by_zone(self):
        # NOTE: it shouldn't be necessary to make copies of gpkg files, because
        # they are not modified by the test. However, when QGIS opens a gpkg
        # (and it's not protected from writing), it modifies the file even if
        # no changes are made and if it's not saved afterwards. It seems like a
        # bug in QGIS.
        points_layer_path = os.path.join(
            self.data_dir_name, 'loss_points.gpkg')
        self.points_copy_path = tempfile.NamedTemporaryFile(
            suffix='.gpkg').name
        shutil.copyfile(points_layer_path, self.points_copy_path)
        points_layer = QgsVectorLayer(
            self.points_copy_path, 'Loss points having zone ids', 'ogr')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.gpkg')
        self.zonal_copy_path = tempfile.NamedTemporaryFile(suffix='.gpkg').name
        shutil.copyfile(zonal_layer_path, self.zonal_copy_path)
        zonal_layer = QgsVectorLayer(
            self.zonal_copy_path, 'SVI zones', 'ogr')
        self.is_test_complete = False
        calculate_zonal_stats(
            self.on_calculate_zonal_stats_finished,
            zonal_layer, points_layer, self.loss_attr_names,
            'output', discard_nonmatching=False,
            predicates=('intersects',), summaries=('sum',))
        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            QGIS_APP.processEvents()
            time.sleep(0.01)
            print(self.is_test_complete)
            if self.is_test_complete:
                return
        raise TimeoutError(
            'Unable to run the aggregation within %s seconds' % timeout)

    def on_calculate_zonal_stats_finished(self, output_zonal_layer):
        if output_zonal_layer is None:
            raise RuntimeError('Unable to produce the output zonal layer')
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name,
            'svi_zones_plus_loss_stats.gpkg')
        expected_copy_path = tempfile.NamedTemporaryFile(suffix='.gpkg').name
        shutil.copyfile(expected_zonal_layer_path, expected_copy_path)
        expected_zonal_layer = QgsVectorLayer(
            expected_copy_path, 'Expected zonal layer', 'ogr')
        self._check_output_layer(output_zonal_layer, expected_zonal_layer)
        os.remove(self.points_copy_path)
        os.remove(self.zonal_copy_path)
        os.remove(expected_copy_path)
        self.is_test_complete = True

    def _check_output_layer(self, output_layer, expected_layer):
        if not ProcessLayer(output_layer).has_same_content_as(
                expected_layer):
            ProcessLayer(output_layer).pprint(usage='testing')
            ProcessLayer(expected_layer).pprint(usage='testing')
            raise Exception(
                'The output layer is different than expected (see above)')
