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
import zipfile
import json
import numpy

from svir.third_party.requests import Session
from svir.utilities.utils import listdir_fullpath


class DriveOqEngineTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session = Session()
        # TODO: it might be passed as argument when running integration tests
        cls.demos_dir = os.path.join(
            os.path.dirname(__file__),
            os.pardir, os.pardir, os.pardir, os.pardir,
            'oq-engine', 'demos')
        cls.hostname = 'http://localhost:8800'
        # TODO: we should run all the demos that cover the output types for
        # which we have already implemented a corresponding loader. For now,
        # we are just running the hazard AreaSource demo
        area_source_dir = os.path.join(
            cls.demos_dir, 'hazard', 'AreaSourceClassicalPSHA')
        file_names = listdir_fullpath(area_source_dir)
        resp = cls.run_calc(file_names=file_names)
        assert resp['status'] == 'created', resp['status']
        cls.calc_id = resp['job_id']

        while True:
            time.sleep(4)
            status = cls.get_calc_status(cls.calc_id)
            assert status['status'] != 'failed', status['status']
            if status['status'] == 'complete':
                break

        output_list = cls.get_output_list(cls.calc_id)
        for output in output_list:
            if output['type'] == 'hcurves':
                cls.hcurves_filepath = cls.download_output(output['id'], 'npz')
                assert cls.hcurves_filepath is not None
            elif output['type'] == 'hmaps':
                cls.hmaps_filepath = cls.download_output(output['id'], 'npz')
                assert cls.hmaps_filepath is not None
            elif output['type'] == 'uhs':
                cls.uhs_filepath = cls.download_output(output['id'], 'npz')
                assert cls.uhs_filepath is not None

    @classmethod
    def tearDownClass(cls):
        # TODO: we should remove all the calculations that were created in the
        # setUp
        cls.remove_calc(cls.calc_id)

    @classmethod
    def run_calc(cls, calc_id=None, file_names=None):
        """
        Run a calculation. If `calc_id` is given, it means we want to run
        a calculation re-using the output of the given calculation
        """
        if len(file_names) == 1:
            file_full_path = file_names[0]
            _, file_ext = os.path.splitext(file_full_path)
            if file_ext == '.zip':
                zipped_file_name = file_full_path
            else:
                raise TypeError(file_ext)
        else:
            _, zipped_file_name = tempfile.mkstemp()
            with zipfile.ZipFile(zipped_file_name, 'w') as zipped_file:
                for file_name in file_names:
                    zipped_file.write(file_name)
        run_calc_url = "%s/v1/calc/run" % cls.hostname
        if calc_id is not None:
            # FIXME: currently the web api is expecting a hazard_job_id
            # although it could be any kind of job_id. This will have to be
            # changed as soon as the web api is updated.
            data = {'hazard_job_id': calc_id}
        else:
            data = {}
        files = {'archive': open(zipped_file_name, 'rb')}
        resp = cls.session.post(
            run_calc_url, files=files, data=data, timeout=20)
        if not resp.ok:
            raise Exception(resp.text)
        return resp.json()

    @classmethod
    def remove_calc(cls, calc_id):
        calc_remove_url = "%s/v1/calc/%s/remove" % (cls.hostname, calc_id)
        resp = cls.session.post(calc_remove_url, timeout=10)
        if not resp.ok:
            raise Exception(resp.text)

    @classmethod
    def get_calc_status(cls, calc_id):
        calc_status_url = "%s/v1/calc/%s/status" % (cls.hostname, calc_id)
        # FIXME: enable the user to set verify=True
        resp = cls.session.get(calc_status_url, timeout=10, verify=False)
        calc_status = json.loads(resp.text)
        return calc_status

    @classmethod
    def get_output_list(cls, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (cls.hostname, calc_id)
        # FIXME: enable the user to set verify=True
        resp = cls.session.get(output_list_url, timeout=10, verify=False)
        if not resp.ok:
            raise Exception(resp.text)
        output_list = json.loads(resp.text)
        return output_list

    @classmethod
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

    def test_load_hmaps(self):
        npz = numpy.load(self.hmaps_filepath, 'r')
        rlz_dtype = npz['rlz-000'].dtype
        expected_rlz_dtype = numpy.dtype([
            ('lon', '<f8'),
            ('lat', '<f8'),
            ('PGA-0.1', '<f8'),
            ('PGA-0.02', '<f8'),
            ('PGV-0.1', '<f8'),
            ('PGV-0.02', '<f8'),
            ('SA(0.025)-0.1', '<f8'),
            ('SA(0.025)-0.02', '<f8'),
            ('SA(0.05)-0.1', '<f8'),
            ('SA(0.05)-0.02', '<f8'),
            ('SA(0.1)-0.1', '<f8'),
            ('SA(0.1)-0.02', '<f8'),
            ('SA(0.2)-0.1', '<f8'),
            ('SA(0.2)-0.02', '<f8'),
            ('SA(0.5)-0.1', '<f8'),
            ('SA(0.5)-0.02', '<f8'),
            ('SA(1.0)-0.1', '<f8'),
            ('SA(1.0)-0.02', '<f8'),
            ('SA(2.0)-0.1', '<f8'),
            ('SA(2.0)-0.02', '<f8')])
        self.assertEqual(rlz_dtype, expected_rlz_dtype)

    def test_load_hcurves(self):
        npz = numpy.load(self.hcurves_filepath, 'r')
        imtls_dtype = npz['imtls'].dtype
        expected_imtls_dtype = numpy.dtype([
            ('PGA', '<f8', (19,)),
            ('PGV', '<f8', (45,)),
            ('SA(0.025)', '<f8', (19,)),
            ('SA(0.05)', '<f8', (19,)),
            ('SA(0.1)', '<f8', (19,)),
            ('SA(0.2)', '<f8', (19,)),
            ('SA(0.5)', '<f8', (19,)),
            ('SA(1.0)', '<f8', (20,)),
            ('SA(2.0)', '<f8', (20,))])
        self.assertEqual(imtls_dtype, expected_imtls_dtype)
        rlz_dtype = npz['rlz-000'].dtype
        expected_rlz_dtype = numpy.dtype([
            ('lon', '<f8'),
            ('lat', '<f8'),
            ('PGA', '<f8', (19,)),
            ('PGV', '<f8', (45,)),
            ('SA(0.025)', '<f8', (19,)),
            ('SA(0.05)', '<f8', (19,)),
            ('SA(0.1)', '<f8', (19,)),
            ('SA(0.2)', '<f8', (19,)),
            ('SA(0.5)', '<f8', (19,)),
            ('SA(1.0)', '<f8', (20,)),
            ('SA(2.0)', '<f8', (20,))])
        self.assertEqual(rlz_dtype, expected_rlz_dtype)

    def test_load_uhs(self):
        npz = numpy.load(self.uhs_filepath, 'r')
        rlz_dtype = npz['rlz-000'].dtype
        expected_rlz_dtype = numpy.dtype([
            ('lon', '<f8'),
            ('lat', '<f8'),
            ('0.1', [('PGA', '<f8'),
                     ('SA(0.025)', '<f8'),
                     ('SA(0.05)', '<f8'),
                     ('SA(0.1)', '<f8'),
                     ('SA(0.2)', '<f8'),
                     ('SA(0.5)', '<f8'),
                     ('SA(1.0)', '<f8'),
                     ('SA(2.0)', '<f8')]),
            ('0.02', [('PGA', '<f8'),
                      ('SA(0.025)', '<f8'),
                      ('SA(0.05)', '<f8'),
                      ('SA(0.1)', '<f8'),
                      ('SA(0.2)', '<f8'),
                      ('SA(0.5)', '<f8'),
                      ('SA(1.0)', '<f8'),
                      ('SA(2.0)', '<f8')])])
        self.assertEqual(rlz_dtype, expected_rlz_dtype)
