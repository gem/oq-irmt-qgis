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

from utilities import get_qgis_app
from svir.dialogs.load_npz_as_layer_dialog import LoadNpzAsLayerDialog

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LoadNpzAsLayerTestCase(unittest.TestCase):
    def setUp(self):
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, 'data', 'hazard')

    def test_load_hazard_map(self):
        filepath = os.path.join(self.data_dir_name, 'output-182-hmaps_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'hmaps', filepath)
        dlg.accept()

    def test_load_hazard_curves(self):
        filepath = os.path.join(self.data_dir_name,
                                'output-181-hcurves_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'hcurves', filepath)
        dlg.accept()

    def test_load_uhs(self):
        filepath = os.path.join(self.data_dir_name, 'output-184-uhs_67.npz')
        dlg = LoadNpzAsLayerDialog(IFACE, 'uhs', filepath)
        dlg.accept()
