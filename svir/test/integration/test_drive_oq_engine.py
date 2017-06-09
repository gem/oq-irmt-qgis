# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2014-10-24
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
import time
import tempfile

from PyQt4.QtGui import QAction
from svir.dialogs.drive_oq_engine_server_dialog import (
    DriveOqEngineServerDialog)
from svir.dialogs.viewer_dock import ViewerDock
from svir.utilities.utils import listdir_fullpath
from svir.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class DriveOqEngineTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        curr_dir_name = os.path.dirname(__file__)
        cls.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data')
        # FIXME: it might be passed as argument when running integration tests
        cls.demos_dir = os.path.join(
            os.path.expanduser('~'), 'projects', 'oq-engine', 'demos')
        mock_action = QAction(IFACE.mainWindow())
        cls.viewer_dock = ViewerDock(IFACE, mock_action)
        cls.dlg = DriveOqEngineServerDialog(IFACE, cls.viewer_dock)

        # TODO: we should run all the demos that cover the output types for
        # which we have already implemented a corresponding loader. For now,
        # we are just running the hazard AreaSource demo
        area_source_dir = os.path.join(
            cls.demos_dir, 'hazard', 'AreaSourceClassicalPSHA')
        file_names = listdir_fullpath(area_source_dir)
        resp = cls.dlg.run_calc(file_names=file_names)
        assert resp['status'] == 'created', resp['status']
        cls.calc_id = resp['job_id']

        while True:
            time.sleep(4)
            status = cls.dlg.get_calc_status(cls.calc_id)
            assert status['status'] != 'failed', status['status']
            if status['status'] == 'complete':
                break

        output_list = cls.dlg.get_output_list(cls.calc_id)
        for output in output_list:
            if output['type'] == 'hcurves':
                cls.hcurves_id = output['id']
            elif output['type'] == 'hmaps':
                cls.hmaps_id = output['id']
            elif output['type'] == 'uhs':
                cls.uhs_id = output['id']

    @classmethod
    def tearDownClass(cls):
        # TODO: we should remove all the calculations that were created in the
        # setUp
        cls.dlg.remove_calc(cls.calc_id)

    def test_get_calc_log(self):
        self.dlg.get_calc_log(self.calc_id)

    def test_load_output(self):
        filepath = self.dlg.download_output(
            self.hmaps_id, 'npz', tempfile.gettempdir())
        print filepath

    def test_load_hmaps(self):
        output = dict(id=self.hmaps_id, type='hmaps')
        self.dlg.on_output_action_btn_clicked(output, 'Load as layer', 'npz')

    def test_load_hcurves(self):
        output = dict(id=self.hcurves_id, type='hcurves')
        self.dlg.on_output_action_btn_clicked(output, 'Load as layer', 'npz')

    def test_load_uhs(self):
        output = dict(id=self.uhs_id, type='uhs')
        self.dlg.on_output_action_btn_clicked(output, 'Load as layer', 'npz')
