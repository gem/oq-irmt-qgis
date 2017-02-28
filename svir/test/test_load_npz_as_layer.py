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
import os
import unittest
import tempfile
import filecmp

from PyQt4.QtGui import QAction
from qgis.core import QgsMapLayerRegistry
from svir.dialogs.load_npz_as_layer_dialog import LoadNpzAsLayerDialog
from svir.dialogs.viewer_dock import ViewerDock
from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LoadNpzAsLayerTestCase(unittest.TestCase):
    def setUp(self):
        IFACE.newProject()
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, 'data', 'hazard')
        mock_action = QAction(IFACE.mainWindow())
        self.viewer_dock = ViewerDock(IFACE, mock_action)

    def tearDown(self):
        # the following line removes all the existing map layers
        IFACE.newProject()

    def test_load_hazard_map(self):
        filepath = os.path.join(self.data_dir_name, 'output-182-hmaps_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'hmaps', filepath)
        dlg.accept()
        # hazard maps have nothing to do with the Data Viewer

    def test_load_gmf(self):
        filepath = os.path.join(self.data_dir_name,
                                'output-195-gmf_data_70.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'gmf_data', filepath)
        dlg.accept()
        # ground motion fields have nothing to do with the Data Viewer

    def test_load_hazard_curves(self):
        filepath = os.path.join(self.data_dir_name,
                                'output-181-hcurves_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'hcurves', filepath)
        dlg.accept()
        self._set_output_type('Hazard Curves')
        expected_layer_name = 'hazard_curves_rlz-rlz-000'
        layer = self._get_layer_by_name(expected_layer_name)
        self._change_selection(layer)
        # test changing intensity measure type
        # select the first 2 features (the same used to produce the reference
        # csv)
        layer.select([1, 2])
        imt = 'SA(0.2)'
        idx = self.viewer_dock.imt_cbx.findText(imt)
        self.assertNotEqual(idx, -1, 'IMT %s not found' % imt)
        self.viewer_dock.imt_cbx.setCurrentIndex(idx)
        # test exporting the current selection to csv
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        self._test_export(layer, 'hazard_curves_SA(0.2).csv')

    def test_load_uhs(self):
        filepath = os.path.join(self.data_dir_name, 'output-184-uhs_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'uhs', filepath)
        dlg.accept()
        expected_layer_name = 'uhs_rlz-rlz-000_poe-0.02'
        layer = self._get_layer_by_name(expected_layer_name)
        self._set_output_type('Uniform Hazard Spectra')
        self._change_selection(layer)
        # test exporting the current selection to csv
        self._test_export(layer, 'uniform_hazard_spectra.csv')

    def _test_export(self, layer, expected_file_name):
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        # select the first 2 features (the same used to produce the reference
        # csv)
        layer.select([1, 2])
        self.viewer_dock.write_export_file(exported_file_path)
        expected_file_path = os.path.join(
            self.data_dir_name, expected_file_name)
        self.assertTrue(
            filecmp.cmp(exported_file_path, expected_file_path),
            'The exported file (%s) is different with respect to the'
            ' reference one (%s)' % (exported_file_path, expected_file_path))

    def _set_output_type(self, output_type):
        idx = self.viewer_dock.output_type_cbx.findText(output_type)
        self.assertNotEqual(idx, -1, 'Output type %s not found' % output_type)
        self.viewer_dock.output_type_cbx.setCurrentIndex(idx)

    def _change_selection(self, layer):
        # the behavior should be slightly different (pluralizing labels, etc)
        # depending on the amount of features selected
        layer.select(1)
        layer.select(2)
        layer.selectAll()
        layer.removeSelection()

    def _get_layer_by_name(self, layer_name):
        layers = QgsMapLayerRegistry.instance().mapLayersByName(
            layer_name)
        self.assertEqual(
            len(layers), 1, 'Layer %s found %s times.' % (layer_name,
                                                          len(layers)))
        layer = layers[0]
        IFACE.setActiveLayer(layer)
        return layer
