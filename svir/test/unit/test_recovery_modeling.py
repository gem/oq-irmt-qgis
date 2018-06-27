# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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
import os
import unittest
import json
from nose.plugins.attrib import attr
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsVectorLayer
from svir.recovery_modeling.recovery_modeling import RecoveryModeling
from svir.dialogs.viewer_dock import ViewerDock
from svir.utilities.shared import DEFAULT_SETTINGS

from svir.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


def calculate_and_check_recovery_curve(
        testcase, dmg_by_asset_features, approach, expected_curve_path,
        regenerate_expected_values, seed=None, n_simulations=1):
    recovery = RecoveryModeling(dmg_by_asset_features, approach, IFACE)
    probs_field_names = [u'structural', u'structur_2', u'structur_4',
                         u'structur_6', u'structur_8']
    # NOTE: there is only one zone (i.e., 'ALL')
    zonal_dmg_by_asset_probs, zonal_asset_refs = \
        recovery.collect_zonal_data(probs_field_names)
    zone_id = 'ALL'
    recovery_curve = recovery.generate_community_level_recovery_curve(
        zone_id, zonal_dmg_by_asset_probs, zonal_asset_refs, seed=seed,
        n_simulations=n_simulations)
    if regenerate_expected_values:
        with open(expected_curve_path, 'w') as f:
            f.write(json.dumps(recovery_curve))
    with open(expected_curve_path, 'r') as f:
        expected_recovery_curve = json.loads(f.read())
    testcase.assertEqual(len(recovery_curve), len(expected_recovery_curve))
    for actual, expected in zip(recovery_curve, expected_recovery_curve):
        if seed is not None:
            testcase.assertEqual(actual, expected)
        else:
            testcase.assertAlmostEqual(actual, expected, places=2)


@unittest.skip('Temporarily disabled for QGIS3')
class DeterministicTestCase(unittest.TestCase):
    def setUp(self):
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'recovery_modeling')
        dmg_by_asset_layer_file_path = os.path.join(self.data_dir_name,
                                                    'dmg_by_asset.shp')
        self.dmg_by_asset_layer = QgsVectorLayer(dmg_by_asset_layer_file_path,
                                                 'dmg_by_asset', 'ogr')
        self.regenerate_expected_values = False
        self.initial_experimental_enabled = QSettings().value(
            '/irmt/experimental_enabled',
            DEFAULT_SETTINGS['experimental_enabled'],
            type=bool)
        QSettings().setValue('irmt/experimental_enabled', True)

    def tearDown(self):
        QSettings().setValue(
            'irmt/experimental_enabled', self.initial_experimental_enabled)

    def test_gui_building_aggregate(self):
        mock_action = QAction(IFACE.mainWindow())
        self.viewer_dock = ViewerDock(IFACE, mock_action)
        IFACE.setActiveLayer(self.dmg_by_asset_layer)
        output_type = 'Recovery Curves'
        idx = self.viewer_dock.output_type_cbx.findText(output_type)
        self.assertNotEqual(idx, -1, 'Output type %s not found' % output_type)
        self.viewer_dock.output_type_cbx.setCurrentIndex(idx)
        approach = 'Aggregate'
        idx = self.viewer_dock.approach_cbx.findText(approach)
        self.assertNotEqual(idx, -1, 'Approach %s not found' % approach)
        self.viewer_dock.approach_cbx.setCurrentIndex(idx)
        IFACE.activeLayer().select([1])

    def test_building_aggregate(self):
        approach = 'Aggregate'
        # using only 1 asset
        dmg_by_asset_features = [next(self.dmg_by_asset_layer.getFeatures())]
        expected_curve_path = os.path.join(
            self.data_dir_name, 'building_aggregate_1sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, seed=42, n_simulations=1)

    def test_community_aggregate(self):
        approach = 'Aggregate'
        # using all the 10 assets
        dmg_by_asset_features = list(self.dmg_by_asset_layer.getFeatures())
        expected_curve_path = os.path.join(
            self.data_dir_name, 'community_aggregate_1sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, seed=42, n_simulations=1)

    def test_building_disaggregate(self):
        approach = 'Disaggregate'
        # using only 1 asset
        dmg_by_asset_features = [next(self.dmg_by_asset_layer.getFeatures())]
        expected_curve_path = os.path.join(
            self.data_dir_name, 'building_disaggregate_1sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, seed=42, n_simulations=1)

    def test_community_disaggregate(self):
        approach = 'Disaggregate'
        # using all the 10 assets
        dmg_by_asset_features = list(self.dmg_by_asset_layer.getFeatures())
        expected_curve_path = os.path.join(
            self.data_dir_name, 'community_disaggregate_1sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, seed=42, n_simulations=1)


@attr('slow')
@unittest.skip('Temporarily disabled for QGIS3')
class StochasticTestCase(unittest.TestCase):

    def setUp(self):
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'recovery_modeling')
        dmg_by_asset_layer_file_path = os.path.join(self.data_dir_name,
                                                    'dmg_by_asset.shp')
        self.dmg_by_asset_layer = QgsVectorLayer(dmg_by_asset_layer_file_path,
                                                 'dmg_by_asset', 'ogr')
        self.regenerate_expected_values = False

    def test_building_aggregate(self):
        approach = 'Aggregate'
        # using only 1 asset
        dmg_by_asset_features = [next(self.dmg_by_asset_layer.getFeatures())]
        expected_curve_path = os.path.join(
            self.data_dir_name, 'building_aggregate_200sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, n_simulations=200)

    def test_community_aggregate(self):
        approach = 'Aggregate'
        # using only 1 asset
        dmg_by_asset_features = list(self.dmg_by_asset_layer.getFeatures())
        expected_curve_path = os.path.join(
            self.data_dir_name, 'community_aggregate_200sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, n_simulations=200)

    def test_building_disaggregate(self):
        approach = 'Disaggregate'
        # using only 1 asset
        dmg_by_asset_features = [next(self.dmg_by_asset_layer.getFeatures())]
        expected_curve_path = os.path.join(
            self.data_dir_name, 'building_disaggregate_200sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, n_simulations=200)

    def test_community_disaggregate(self):
        approach = 'Disaggregate'
        # using only 1 asset
        dmg_by_asset_features = list(self.dmg_by_asset_layer.getFeatures())
        expected_curve_path = os.path.join(
            self.data_dir_name, 'community_disaggregate_200sim.txt')
        calculate_and_check_recovery_curve(
            self, dmg_by_asset_features, approach, expected_curve_path,
            self.regenerate_expected_values, n_simulations=200)
