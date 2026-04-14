# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2026 by GEM Foundation
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

import os
import shutil
import time
import gc
import pytest

from qgis.core import QgsVectorLayer
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import calculate_zonal_stats


@pytest.fixture
def data_dir():
    """Fixture to provide the path to the dummy data directory."""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir, 'data', 'aggregation', 'dummy'
        )
    )


def test_sum_point_values_by_zone(qgis_app, data_dir, tmp_path):
    """Test the aggregation of point values into zones."""
    loss_attr_names = ['PEOPLE', 'STRUCTURAL']

    # Define paths
    points_src = os.path.join(data_dir, 'loss_points.gpkg')
    zones_src = os.path.join(data_dir, 'svi_zones.gpkg')
    expected_src = os.path.join(data_dir, 'svi_zones_plus_loss_stats.gpkg')

    # Create temporary copies using tmp_path (pytest handles cleanup)
    points_path = str(tmp_path / "loss_points.gpkg")
    zones_path = str(tmp_path / "svi_zones.gpkg")
    expected_path = str(tmp_path / "expected.gpkg")

    shutil.copyfile(points_src, points_path)
    shutil.copyfile(zones_src, zones_path)
    shutil.copyfile(expected_src, expected_path)

    # Load layers
    points_layer = QgsVectorLayer(points_path, 'Loss points', 'ogr')
    zonal_layer = QgsVectorLayer(zones_path, 'SVI zones', 'ogr')
    expected_layer = QgsVectorLayer(expected_path, 'Expected', 'ogr')

    # Shared state for the callback
    state = {'is_complete': False, 'output_layer': None}

    def on_finished(output_zonal_layer):
        state['output_layer'] = output_zonal_layer
        state['is_complete'] = True

    # Run calculation
    calculate_zonal_stats(
        on_finished,
        zonal_layer,
        points_layer,
        loss_attr_names,
        'output',
        discard_nonmatching=False,
        predicates=('intersects',),
        summaries=('sum',)
    )

    # Wait for the async process to finish
    timeout = 5
    start_time = time.time()
    while time.time() - start_time < timeout:
        qgis_app.processEvents()
        if state['is_complete']:
            break
        time.sleep(0.01)

    assert state['is_complete'], f"Aggregation timed out after {timeout}s"

    output_layer = state['output_layer']
    assert output_layer is not None
    has_same_content = ProcessLayer(output_layer).has_same_content_as(
        expected_layer
    )
    assert has_same_content, "Output layer content mismatch."

    # Clear references and force garbage collection
    # before the session-scoped qgis_app fixture begins its teardown,
    # in order to avoid 139 segementation fault.
    del points_layer
    del zonal_layer
    del expected_layer
    if 'output_layer' in state:
        del state['output_layer']
    gc.collect()
