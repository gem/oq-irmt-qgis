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
from mock import Mock

from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsVectorLayer
from svir.dialogs.load_ruptures_as_layer_dialog import (
    LoadRupturesAsLayerDialog)
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
