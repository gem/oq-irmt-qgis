# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Integrated Risk Modelling Toolkit
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2015 by GEM Foundation
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

import unittest
import os.path

from oq_irmt.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from collections import namedtuple
from oq_irmt.dialogs.select_input_layers_dialog import SelectInputLayersDialog


class ImportLossFromCsvTestCase(unittest.TestCase):

    def test_import_loss_from_dummy_csv(self):
        curr_dir_name = os.path.dirname(__file__)
        data_dir_name = os.path.join(curr_dir_name, 'data/loss/dummy')
        csv_file_path = os.path.join(
            data_dir_name, 'dummy_loss_data.csv')
        dest_shp_file_path = os.path.join(
            data_dir_name, 'output/dummy_loss_layer.shp')

        dlg = SelectInputLayersDialog(IFACE)
        shp_layer = dlg.import_loss_layer_from_csv([csv_file_path],
                                                   dest_shp_file_path,
                                                   from_oqengine=False)
        expected_field_names = ('PT_ID', 'AAL', 'DEATH')
        Feature = namedtuple('Feature', expected_field_names)
        expected_rows = [Feature('A', 32, 5),
                         Feature('B', 14, 7),
                         Feature('C', 10, 3),
                         Feature('D', 16, 4)]
        dp = shp_layer.dataProvider()
        actual_field_names = tuple(field.name() for field in dp.fields())
        self.assertEqual(actual_field_names, expected_field_names)
        for i, feat in enumerate(dp.getFeatures()):
            actual_row = Feature(*feat.attributes())
            self.assertEqual(actual_row, expected_rows[i])

    def test_import_loss_from_csv_exported_by_oqengine(self):
        curr_dir_name = os.path.dirname(__file__)
        data_dir_name = os.path.join(curr_dir_name, 'data/loss/from_oqengine')
        csv_file_paths = []
        csv_file_paths.append(os.path.join(
            data_dir_name, 'loss-curves-4.csv'))
        csv_file_paths.append(os.path.join(
            data_dir_name, 'loss-curves-5.csv'))
        csv_file_paths.append(os.path.join(
            data_dir_name, 'loss-curves-6.csv'))
        dest_shp_file_path = os.path.join(
            data_dir_name, 'output/loss_layer.shp')
        dlg = SelectInputLayersDialog(IFACE)
        shp_layer = dlg.import_loss_layer_from_csv(csv_file_paths,
                                                   dest_shp_file_path,
                                                   from_oqengine=True)
        dp = shp_layer.dataProvider()
        expected_len = 9144
        actual_len = len(list(dp.getFeatures()))
        self.assertEqual(expected_len, actual_len)
        expected_field_names = ('FATALITIES', 'NONSTRUCTU', 'STRUCTURAL')
        Feature = namedtuple('Feature', expected_field_names)
        expected_first_row = Feature(5.83469376E-03,
                                     4.50043433E+02,
                                     1.96053179E+02)
        dp = shp_layer.dataProvider()
        actual_field_names = tuple(field.name() for field in dp.fields())
        self.assertEqual(actual_field_names, expected_field_names)
        features = dp.getFeatures()
        actual_attribute_values = features.next().attributes()
        actual_first_row = Feature(*actual_attribute_values)
        self.assertEqual(actual_first_row, expected_first_row)
