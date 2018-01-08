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
from numpy.testing import assert_almost_equal

from PyQt4.QtGui import QAction
from qgis.core import QgsVectorLayer
from svir.dialogs.load_dmg_by_asset_as_layer_dialog import (
    LoadDmgByAssetAsLayerDialog)
from svir.dialogs.load_ruptures_as_layer_dialog import (
    LoadRupturesAsLayerDialog)
from svir.dialogs.load_hmaps_as_layer_dialog import (
    LoadHazardMapsAsLayerDialog)
from svir.dialogs.load_hcurves_as_layer_dialog import (
    LoadHazardCurvesAsLayerDialog)
from svir.dialogs.load_gmf_data_as_layer_dialog import (
    LoadGmfDataAsLayerDialog)
from svir.dialogs.load_uhs_as_layer_dialog import (
    LoadUhsAsLayerDialog)
from svir.dialogs.load_losses_by_asset_as_layer_dialog import (
    LoadLossesByAssetAsLayerDialog)
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

    def test_load_hazard_map(self):
        filepath = os.path.join(
            self.data_dir_name, 'hazard', 'output-3-hmaps_1.npz')
        dlg = LoadHazardMapsAsLayerDialog(
            IFACE, self.viewer_dock, 'hmaps', filepath)
        dlg.accept()
        # hazard maps have nothing to do with the Data Viewer

    def test_load_gmf(self):
        filepath = os.path.join(self.data_dir_name, 'hazard',
                                'output-195-gmf_data_70.npz')
        dlg = LoadGmfDataAsLayerDialog(
            IFACE, self.viewer_dock, 'gmf_data', filepath)
        dlg.accept()
        # ground motion fields have nothing to do with the Data Viewer

    def test_load_hazard_curves(self):
        filepath = os.path.join(self.data_dir_name, 'hazard',
                                'output-121-hcurves_27.npz')
        dlg = LoadHazardCurvesAsLayerDialog(
            IFACE, self.viewer_dock, 'hcurves', filepath)
        dlg.accept()
        self._set_output_type('Hazard Curves')
        self._change_selection()
        # test changing intensity measure type
        layer = IFACE.activeLayer()
        # select the first 2 features (the same used to produce the reference
        # csv)
        layer.select([1, 2])
        imt = 'SA(0.1)'
        idx = self.viewer_dock.imt_cbx.findText(imt)
        self.assertNotEqual(idx, -1, 'IMT %s not found' % imt)
        self.viewer_dock.imt_cbx.setCurrentIndex(idx)
        # test exporting the current selection to csv
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        self._test_export()

    def test_load_uhs_only_selected_poe(self):
        filepath = os.path.join(self.data_dir_name, 'hazard',
                                'output-125-uhs_27.npz')
        dlg = LoadUhsAsLayerDialog(
            IFACE, self.viewer_dock, 'uhs', filepath)
        dlg.load_selected_only_ckb.setChecked(True)
        idx = dlg.poe_cbx.findText('0.1')
        self.assertEqual(idx, 0, 'POE 0.1 was not found')
        dlg.poe_cbx.setCurrentIndex(idx)
        dlg.accept()
        self._set_output_type('Uniform Hazard Spectra')
        self._change_selection()
        # test exporting the current selection to csv
        self._test_export()

    def test_load_ruptures(self):
        filepath = os.path.join(
            self.data_dir_name, 'hazard', 'ruptures',
            'output-607-ruptures_162.csv')
        dlg = LoadRupturesAsLayerDialog(
            IFACE, self.viewer_dock, 'ruptures', filepath, mode='testing')
        dlg.save_as_shp_ckb.setChecked(True)
        dlg.accept()
        current_layer = IFACE.activeLayer()
        reference_path = os.path.join(
            self.data_dir_name, 'hazard', 'ruptures',
            'output-607-ruptures_162.shp')
        reference_layer = QgsVectorLayer(
            reference_path, 'reference_ruptures', 'ogr')
        ProcessLayer(current_layer).has_same_content_as(reference_layer)

    def test_load_losses_by_asset_only_selected_taxonomy_and_loss_type(self):
        filepath = os.path.join(self.data_dir_name, 'risk',
                                'output-399-losses_by_asset_123.npz')
        dlg = LoadLossesByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'losses_by_asset', filepath)
        dlg.load_selected_only_ckb.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('"Concrete"')
        self.assertNotEqual(taxonomy_idx, -1,
                            'Taxonomy "Concrete" was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        dlg.accept()

    def test_load_losses_by_asset_all_taxonomies_only_selected_loss_type(self):
        filepath = os.path.join(self.data_dir_name, 'risk',
                                'output-399-losses_by_asset_123.npz')
        dlg = LoadLossesByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'losses_by_asset', filepath)
        dlg.load_selected_only_ckb.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('All')
        self.assertNotEqual(taxonomy_idx, -1, 'Taxonomy All was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        dlg.accept()

    @unittest.skip("Causing segfault")
    def test_load_losses_by_asset_aggregate_by_zone(self):
        loss_layer_path = os.path.join(self.data_dir_name, 'risk',
                                       'output-399-losses_by_asset_123.npz')
        zonal_layer_path = os.path.join(self.data_dir_name, 'risk',
                                        'zonal_layer.shp')
        dlg = LoadLossesByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'losses_by_asset', loss_layer_path,
            zonal_layer_path=zonal_layer_path)
        dlg.load_selected_only_ckb.setChecked(True)
        dlg.zonal_layer_gbx.setChecked(True)
        taxonomy_idx = dlg.taxonomy_cbx.findText('All')
        self.assertNotEqual(taxonomy_idx, -1, 'Taxonomy All was not found')
        dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        loss_type_idx = dlg.loss_type_cbx.findText('structural')
        self.assertNotEqual(loss_type_idx, -1,
                            'Loss type structural was not found')
        dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
        self.assertTrue(dlg.zonal_layer_cbx.currentText(),
                        'The zonal layer was not loaded')
        dlg.accept()
        zonal_layer_plus_stats = [layer for layer in IFACE.layers()
                                  if layer.name() == 'Zonal data (copy)'][0]
        zonal_layer_plus_stats_first_feat = \
            zonal_layer_plus_stats.getFeatures().next()
        expected_zonal_layer_path = os.path.join(
            self.data_dir_name, 'risk',
            'zonal_layer_plus_losses_by_asset_stats.shp')
        expected_zonal_layer = QgsVectorLayer(
            expected_zonal_layer_path, 'Zonal data', 'ogr')
        expected_zonal_layer_first_feat = \
            expected_zonal_layer.getFeatures().next()
        assert_almost_equal(
            zonal_layer_plus_stats_first_feat.attributes(),
            expected_zonal_layer_first_feat.attributes())

    def test_load_dmg_by_asset_only_selected_taxonomy(self):
        filepath = os.path.join(self.data_dir_name, 'risk',
                                'output-1614-dmg_by_asset_356.npz')
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'dmg_by_asset', filepath)
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
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'dmg_by_asset', filepath)
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
        dlg = LoadDmgByAssetAsLayerDialog(
            IFACE, self.viewer_dock, 'dmg_by_asset', dmg_layer_path,
            zonal_layer_path=zonal_layer_path)
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
