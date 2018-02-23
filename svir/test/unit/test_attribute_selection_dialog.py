# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-06-15
#        copyright            : (C) 2015 by GEM Foundation
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

__author__ = 'devops@openquake.org'
__date__ = '2014-09-10'
__copyright__ = 'Copyright 2014, GEM Foundation'

import unittest
import os.path

from qgis.PyQt.QtGui import QDialogButtonBox, QDialog

from qgis.core import QgsVectorLayer

from svir.dialogs.attribute_selection_dialog import AttributeSelectionDialog
from svir.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class AttributeSelectionDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'aggregation', 'dummy')
        loss_layer_path = os.path.join(
            self.data_dir_name, 'loss_points_having_zone_ids.shp')
        loss_layer = QgsVectorLayer(loss_layer_path,
                                    'Loss points having zone ids',
                                    'ogr')
        zonal_layer_path = os.path.join(
            self.data_dir_name, 'svi_zones.shp')
        zonal_layer = QgsVectorLayer(zonal_layer_path, 'SVI zones', 'ogr')
        self.dialog = AttributeSelectionDialog(loss_layer, zonal_layer)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""

        ok_button = self.dialog.buttonBox.button(QDialogButtonBox.Ok)
        ok_button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)
        self.dialog.loss_attrs_multisel.select_all_btn.click()
        ok_button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Accepted)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        button = self.dialog.buttonBox.button(QDialogButtonBox.Cancel)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)

if __name__ == "__main__":
    suite = unittest.makeSuite(AttributeSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
