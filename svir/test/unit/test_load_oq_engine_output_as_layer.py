# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 201-10-24
#        copyright            : (C) 2014-2017 by GEM Foundation
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
import qgis  # NOQA

import os
import unittest
import tempfile
import csv
from mock import Mock
from numpy.testing import assert_almost_equal

from qgis.PyQt.QtGui import QAction
from qgis.core import QgsVectorLayer
from svir.dialogs.load_dmg_by_asset_as_layer_dialog import (
    LoadDmgByAssetAsLayerDialog)
from svir.dialogs.load_ruptures_as_layer_dialog import (
    LoadRupturesAsLayerDialog)
from svir.dialogs.load_gmf_data_as_layer_dialog import (
    LoadGmfDataAsLayerDialog)
from svir.dialogs.viewer_dock import ViewerDock
from svir.calculations.process_layer import ProcessLayer
from svir.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LoadOQEngineOutputAsLayerTestCase(unittest.TestCase):
    def setUp(self):
        IFACE.newProject()
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data')
        mock_action = QAction(IFACE.mainWindow())
        self.viewer_dock = ViewerDock(IFACE, mock_action)

    def test_load_gmf(self):
        filepath = os.path.join(self.data_dir_name, 'hazard',
                                'output-195-gmf_data_70.npz')
        # TODO: in the future, we will move this to integration tests, using
        #       session, hostname  and calc_id and the extract api, instead of
        #       mocking
        dlg = LoadGmfDataAsLayerDialog(
            IFACE, self.viewer_dock,
            Mock(), Mock(), Mock(), 'gmf_data', filepath)
        dlg.accept()
        # ground motion fields have nothing to do with the Data Viewer

    def test_load_ruptures(self):
        filepath = os.path.join(
            self.data_dir_name, 'hazard', 'ruptures',
            'output-607-ruptures_162.csv')
        # TODO: in the future, we will move this to integration tests, using
        #       session, hostname  and calc_id and the extract api, instead of
        #       mocking
        dlg = LoadRupturesAsLayerDialog(
            IFACE, self.viewer_dock, Mock(), Mock(), Mock(), 'ruptures',
            filepath, mode='testing')
        dlg.save_as_shp_ckb.setChecked(True)
        dlg.accept()
        current_layer = IFACE.activeLayer()
        reference_path = os.path.join(
            self.data_dir_name, 'hazard', 'ruptures',
            'output-607-ruptures_162.shp')
        reference_layer = QgsVectorLayer(
            reference_path, 'reference_ruptures', 'ogr')
        ProcessLayer(current_layer).has_same_content_as(reference_layer)

    def test_load_dmg_by_asset_only_selected_taxonomy(self):
        filepath = os.path.join(self.data_dir_name, 'risk',
                                'output-1614-dmg_by_asset_356.npz')
        # TODO: in the future, we will move this to integration tests, using
        #       session, hostname  and calc_id and the extract api, instead of
        #       mocking
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, Mock(), Mock(), Mock(), 'dmg_by_asset',
            filepath)
        dlg.load_selected_only_ckb.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('"Concrete"')
        self.assertNotEqual(taxonomy_idx, -1,
                            'Taxonomy "Concrete" was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        dmg_state_idx = dlg.dmg_state_cbx.findText('moderate')
        self.assertNotEqual(dmg_state_idx, -1,
                            'Damage state moderate was not found')
        dlg.dmg_state_cbx.setCurrentIndex(dmg_state_idx)
        dlg.accept()

    def test_load_dmg_by_asset_all_taxonomies(self):
        filepath = os.path.join(self.data_dir_name, 'risk',
                                'output-1614-dmg_by_asset_356.npz')
        # TODO: in the future, we will move this to integration tests, using
        #       session, hostname  and calc_id and the extract api, instead of
        #       mocking
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, Mock(), Mock(), Mock(), 'dmg_by_asset',
            filepath)
        dlg.load_selected_only_ckb.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('All')
        self.assertNotEqual(taxonomy_idx, -1, 'Taxonomy All was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        dmg_state_idx = dlg.dmg_state_cbx.findText('moderate')
        self.assertNotEqual(dmg_state_idx, -1,
                            'Damage state moderate was not found')
        dlg.dmg_state_cbx.setCurrentIndex(dmg_state_idx)
        dlg.accept()

    @unittest.skip("Causing segfault")
    def test_load_dmg_by_asset_aggregate_by_zone(self):
        dmg_layer_path = os.path.join(self.data_dir_name, 'risk',
                                      'output-1614-dmg_by_asset_356.npz')
        zonal_layer_path = os.path.join(self.data_dir_name, 'risk',
                                        'zonal_layer.shp')
        # TODO: in the future, we will move this to integration tests, using
        #       session, hostname  and calc_id and the extract api, instead of
        #       mocking
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, Mock(), Mock(), Mock(), 'dmg_by_asset',
            dmg_layer_path, zonal_layer_path=zonal_layer_path)
        dlg.load_selected_only_ckb.setChecked(True)
        dlg.zonal_layer_gbx.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('All')
        self.assertNotEqual(taxonomy_idx, -1, 'Taxonomy All was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        dmg_state_idx = dlg.dmg_state_cbx.findText('moderate')
        self.assertNotEqual(dmg_state_idx, -1,
                            'Damage state moderate was not found')
        dlg.dmg_state_cbx.setCurrentIndex(dmg_state_idx)
        dlg.accept()
        zonal_layer_plus_stats = [layer for layer in IFACE.layers()
                                  if layer.name() == 'Zonal data (copy)'][0]
        zonal_layer_plus_stats_first_feat = \
            zonal_layer_plus_stats.getFeatures().next()
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'risk',
            'zonal_layer_plus_dmg_by_asset_stats.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Zonal data', 'ogr')
        expected_zonal_layer_first_feat = \
            expected_zonal_layer.getFeatures().next()
        assert_almost_equal(
            zonal_layer_plus_stats_first_feat.attributes(),
            expected_zonal_layer_first_feat.attributes())

    def _test_export(self):
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        layer = IFACE.activeLayer()
        # select the first 2 features (the same used to produce the reference
        # csv)
        layer.select([1, 2])
        # probably we have the wrong layer selected (uhs produce many layers)
        self.viewer_dock.write_export_file(exported_file_path)
        # NOTE: we are only checking that the exported CSV has at least 3 rows
        # and 3 columns per row. We are avoiding more precise checks, because
        # CSV tests are very fragile. On different platforms the numbers could
        # be slightly different. With different versions of
        # shapely/libgeos/numpy/etc the numbers could be slightly different.
        # The parameters of the demos could change in the future and the
        # numbers (even the number of rows and columns) could change.
        with open(exported_file_path, 'r') as got:
            got_reader = csv.reader(got)
            n_rows = 0
            for got_line in got_reader:
                n_rows += 1
                n_cols = 0
                for got_element in got_line:
                    n_cols += 1
                self.assertGreaterEqual(
                    n_cols, 3,
                    "The following line of the exported file %s has"
                    " only %s columns:\n%s" % (
                        exported_file_path, n_cols, got_line))
            self.assertGreaterEqual(
                n_rows, 3,
                "The exported file %s has only %s rows" % (
                    exported_file_path, n_rows))

    def _set_output_type(self, output_type):
        idx = self.viewer_dock.output_type_cbx.findText(output_type)
        self.assertNotEqual(idx, -1, 'Output type %s not found' % output_type)
        self.viewer_dock.output_type_cbx.setCurrentIndex(idx)

    def _change_selection(self):
        layer = IFACE.activeLayer()
        # the behavior should be slightly different (pluralizing labels, etc)
        # depending on the amount of features selected
        layer.select(1)
        layer.removeSelection()
        layer.select(2)
        layer.selectAll()
        layer.removeSelection()
