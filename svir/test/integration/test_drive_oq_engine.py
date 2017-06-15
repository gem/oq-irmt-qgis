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
import traceback
import unittest
import tempfile
import json
from mock import Mock

from svir.third_party.requests import Session
from svir.utilities.shared import (OQ_ALL_LOADABLE_TYPES,
                                   OQ_CSV_LOADABLE_TYPES,
                                   OQ_NPZ_LOADABLE_TYPES,
                                   )
from svir.test.utilities import get_qgis_app
from svir.dialogs.drive_oq_engine_server_dialog import OUTPUT_TYPE_LOADERS

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LoadOqEngineOutputsTestCase(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.hostname = 'http://localhost:8800'

    def get_calc_list(self):
        calc_list_url = "%s/v1/calc/list?relevant=true" % self.hostname
        resp = self.session.get(
            calc_list_url, timeout=10, verify=False)
        calc_list = json.loads(resp.text)
        return calc_list

    def get_output_list(self, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (self.hostname, calc_id)
        resp = self.session.get(output_list_url, timeout=10, verify=False)
        if not resp.ok:
            raise Exception(resp.text)
        output_list = json.loads(resp.text)
        return output_list

    def download_output(self, output_id, outtype):
        dest_folder = tempfile.gettempdir()
        output_download_url = (
            "%s/v1/calc/result/%s?export_type=%s&dload=true" % (self.hostname,
                                                                output_id,
                                                                outtype))
        # FIXME: enable the user to set verify=True
        resp = self.session.get(output_download_url, verify=False)
        if not resp.ok:
            raise Exception(resp.text)
        filename = resp.headers['content-disposition'].split(
            'filename=')[1]
        filepath = os.path.join(dest_folder, filename)
        open(filepath, "wb").write(resp.content)
        return filepath

    def load_calc_outputs(self, calc):
        calc_id = calc['id']
        output_list = self.get_output_list(calc_id)
        for output in output_list:
            try:
                output_type = output['type']
                if output_type in OQ_ALL_LOADABLE_TYPES:
                    if output_type in OQ_CSV_LOADABLE_TYPES:
                        print('\tLoading output type %s' % output_type)
                        filepath = self.download_output(output['id'], 'csv')
                        assert filepath is not None
                    elif output_type in OQ_NPZ_LOADABLE_TYPES:
                        print('\tLoading output type %s' % output_type)
                        filepath = self.download_output(output['id'], 'npz')
                    IFACE.newProject()
                    dlg = OUTPUT_TYPE_LOADERS[output_type](
                        IFACE, Mock(), output_type, filepath)
                    dlg.accept()
                else:
                    print('\tLoader for output type %s is not implemented'
                          % output_type)
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                failed_attempt = {'calc_id': calc_id,
                                  'calc_description': calc['description'],
                                  'output_type': output_type,
                                  'traceback': tb}
                self.failed_attempts.append(failed_attempt)
                traceback.print_tb(failed_attempt['traceback'])
                print(ex)

    def test_load_outputs(self):
        self.failed_attempts = []
        calc_list = self.get_calc_list()
        for calc in calc_list:
            print('\nCalculation %s: %s' % (calc['id'], calc['description']))
            self.load_calc_outputs(calc)
        if not self.failed_attempts:
            print('All outputs were successfully loaded')
        else:
            print('Failed attempts:')
            for failed_attempt in self.failed_attempts:
                print('Calculation %s: %s'
                      % (failed_attempt['calc_id'],
                         failed_attempt['calc_description']))
                print('Output type: %s' % failed_attempt['output_type'])
            raise RuntimeError(
                'At least one output was not successfully loaded')
