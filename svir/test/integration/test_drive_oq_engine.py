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
import sys
import unittest
import time

from PyQt4.QtCore import (
                          QObject,
                          SIGNAL,
                          QThread,
                          )
from PyQt4.QtGui import QAction
from svir.dialogs.drive_oq_engine_server_dialog import (
    DriveOqEngineServerDialog)
# from svir.irmt import Irmt
from svir.dialogs.viewer_dock import ViewerDock
from svir.utilities.utils import listdir_fullpath
from svir.test.utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class DriveOqEngineTestCase(unittest.TestCase):
    def setUp(self):
        IFACE.newProject()
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data')
        # FIXME: it might be passed as argument when running integration tests
        self.demos_dir = os.path.join(
            os.path.expanduser('~'), 'projects', 'oq-engine', 'demos')
        mock_action = QAction(IFACE.mainWindow())
        self.viewer_dock = ViewerDock(IFACE, mock_action)
        self.dlg = DriveOqEngineServerDialog(IFACE, self.viewer_dock)
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.start_polling()
        # self.irmt = Irmt(IFACE)
        # self.irmt.drive_oq_engine_server()
        # self.driver_dlg = self.irmt.drive_oq_engine_server_dlg

    def test_run_calculation_separate_input_files(self):
        area_source_dir = os.path.join(
            self.demos_dir, 'hazard', 'AreaSourceClassicalPSHA')
        file_names = listdir_fullpath(area_source_dir)
        # self.dlg.run_calc(file_names=file_names)

        # import pdb
        # pdb.set_trace()
        # print 'ciao'
        # self.calc_status = None
        # QObject.connect(
        #     self.dlg.timer, SIGNAL('timeout()'), self._get_calc_status)
        # self._get_calc_status()
        # while self.calc_status != 'complete':
        #     time.sleep(1)
        #     sys.stderr.write(self.status)
        #     sys.stderr.write('\n')

        # thread = QThread()
        # while True:
        #     thread.sleep(2000)
        #     self._get_calc_status()
        # while True:
        #     time.sleep(2)
        #     try:
        #         status = self.dlg.calc_list_tbl.item(0, 4).text()
        #         sys.stderr.write(status)
        #         sys.stderr.write('\n')
        #     except:
        #         pass
        #     if status == 'complete':
        #         break
        # import pdb
        # pdb.set_trace()
        # remove_btn = self.dlg.calc_list_tbl.item(0, 6)
        # remove_btn.click()
        # print 'ciao'

    # def _get_calc_status(self):
    #     self.calc_status = self.dlg.calc_list_tbl.item(0, 4).text()
    #     sys.stderr.write(self.calc_status)
    #     sys.stderr.write('\n')

    def test_get_calc_log(self):
        print(self.dlg.get_calc_log(219))

    def test_get_calc_status(self):
        print(self.dlg.get_calc_status(219))

    def test_remove_calculation(self):
        # self.dlg.remove_calc(219)
        pass
