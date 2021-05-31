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
import glob
import sys
import traceback
import tempfile
import copy
import csv
import time
import operator
import requests
from qgis.core import QgsApplication
from qgis.utils import iface
from qgis.testing import unittest, start_app, stop_app
from qgis.PyQt.QtCore import QTimer, QSettings
from svir.irmt import Irmt
from svir.utilities.shared import (
                                   OQ_CSV_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_LAYER_TYPES,
                                   OQ_RST_TYPES,
                                   OQ_EXTRACT_TO_VIEW_TYPES,
                                   OQ_ZIPPED_TYPES,
                                   OQ_ALL_TYPES,
                                   DEFAULT_SETTINGS,
                                   )
from svir.test.utilities import assert_and_emit
from svir.dialogs.drive_oq_engine_server_dialog import OUTPUT_TYPE_LOADERS
from svir.dialogs.show_full_report_dialog import ShowFullReportDialog
from svir.dialogs.load_inputs_dialog import LoadInputsDialog


# QgsApplication([], True)
QGIS_APP = start_app()

LONG_LOADING_TIME = 10  # seconds
ONLY_OUTPUT_TYPE = os.environ.get('ONLY_OUTPUT_TYPE')


def run_all():
    suite = unittest.TestSuite()
    # OQ_CSV_TO_LAYER_TYPES
    suite.addTest(unittest.makeSuite(LoadAggRiskTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAggLossesStatsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadDmgByEventTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadEventsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAggLossTableTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadRealizationsTestCase, 'test'))
    # OQ_EXTRACT_TO_LAYER_TYPES
    suite.addTest(unittest.makeSuite(LoadAssetRiskTestCase, 'test'))
    # NOTE: testing recovery curves starting from damages-rlzs
    suite.addTest(unittest.makeSuite(LoadDamagesRlzsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAvgLossesRlzsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAvgLossesStatsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadGmfDataTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadHcurvesTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadHmapsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadRupturesTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadUhsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadDisaggTestCase, 'test'))
    # OQ_ZIPPED_TYPES
    suite.addTest(unittest.makeSuite(LoadInputTestCase, 'test'))
    # OQ_RST_TYPES
    suite.addTest(unittest.makeSuite(LoadFullReportTestCase, 'test'))
    # OQ_EXTRACT_TO_VIEW_TYPES
    suite.addTest(unittest.makeSuite(LoadAggCurvesRlzsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAggCurvesStatsTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadDamagesRlzsAggrTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAvgLossesRlzsAggrTestCase, 'test'))
    suite.addTest(unittest.makeSuite(LoadAvgLossesStatsAggrTestCase, 'test'))

    # Other tests and checks
    suite.addTest(unittest.makeSuite(RunCalculationTestCase, 'test'))
    suite.addTest(unittest.makeSuite(
        AllLoadableOutputsFoundInDemosTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AllLoadersAreImplementedTestCase, 'test'))
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite)


class FailedAttempts(Exception):
    pass


class LoadOqEngineOutputsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # NOTE: recovery modeling is an exprimental feature
        cls.initial_experimental_enabled = QSettings().value(
            '/irmt/experimental_enabled',
            DEFAULT_SETTINGS['experimental_enabled'],
            type=bool)
        QSettings().setValue('irmt/experimental_enabled', True)
        cls.irmt = Irmt(iface)
        cls.irmt.initGui()
        cls.hostname = os.environ.get('OQ_ENGINE_HOST',
                                      'http://localhost:8800')
        cls.global_failed_attempts = []
        cls.global_skipped_attempts = []
        cls.global_time_consuming_outputs = []
        cls.loading_completed = {}
        cls.loading_exception = {}
        cls.irmt.drive_oq_engine_server(show=False, hostname=cls.hostname)
        # NOTE: calc_list must be retrieved BEFORE starting any test
        cls.calc_list = cls.irmt.drive_oq_engine_server_dlg.calc_list
        if isinstance(cls.calc_list, Exception):
            raise cls.calc_list
        cls.output_list = {}
        try:
            cls.only_calc_id = int(os.environ.get('ONLY_CALC_ID'))
        except (ValueError, TypeError):
            print('ONLY_CALC_ID was not set or is not an integer'
                  ' value. Running tests for all the available calculations')
            cls.only_calc_id = None
        else:
            print('ONLY_CALC_ID is set.'
                  ' Running tests only for calculation #%s'
                  % cls.only_calc_id)
        if cls.only_calc_id is not None:
            cls.calc_list = [calc for calc in cls.calc_list
                             if calc['id'] == cls.only_calc_id]
        cls.only_output_type = os.environ.get('ONLY_OUTPUT_TYPE')
        if not cls.only_output_type:
            print('ONLY_OUTPUT_TYPE was not set. Running tests for all'
                  ' the available output types')
        else:
            print('ONLY_OUTPUT_TYPE is set. Running tests only for'
                  ' output type: %s' % cls.only_output_type)

    @classmethod
    def tearDownClass(cls):
        QSettings().setValue(
            'irmt/experimental_enabled', cls.initial_experimental_enabled)
        # print("\n\nGLOBAL SUMMARY OF TESTING OQ-ENGINE OUTPUT LOADERS")
        # print("==================================================\n")
        # if cls.global_skipped_attempts:
        #     print('\nSkipped:')
        #     for skipped_attempt in cls.global_skipped_attempts:
        #         print('\tCalculation %s: %s'
        #               % (skipped_attempt['calc_id'],
        #                  skipped_attempt['calc_description']))
        #         print('\t\tOutput type: %s' % skipped_attempt['output_type'])
        # if not cls.global_failed_attempts:
        #     print("All the outputs were loaded successfully")
        # else:
        #     print('\nFailed attempts:')
        #     for failed_attempt in cls.global_failed_attempts:
        #         print('\tCalculation %s (%s): %s'
        #               % (failed_attempt['calc_id'],
        #                  failed_attempt['calc_mode'],
        #                  failed_attempt['calc_description']))
        #         print('\t\tOutput type: %s' % failed_attempt['output_type'])
        # if cls.global_time_consuming_outputs:
        #     print('\n\nSome loaders took longer than %s seconds:' %
        #           LONG_LOADING_TIME)
        #     for output in sorted(cls.global_time_consuming_outputs,
        #                          key=operator.itemgetter('loading_time'),
        #                          reverse=True):
        #         print('\t%s' % output)
        # stop_app()

    def list_calculations_and_outputs(self):
        print("\n\tList of tested OQ-Engine demo calculations:")
        for calc in self.calc_list:
            print('\tCalculation %s (%s): %s' % (calc['id'],
                                                 calc['calculation_mode'],
                                                 calc['description']))
            calc_output_list = \
                self.irmt.drive_oq_engine_server_dlg.get_output_list(
                    calc['id'])
            if isinstance(calc_output_list, Exception):
                raise calc_output_list
            self.output_list[calc['id']] = calc_output_list
            print('\t\tOutput types: %s' % ', '.join(
                [output['type'] for output in calc_output_list]))

    def get_output_list(self):
        for calc in self.calc_list:
            calc_output_list = \
                self.irmt.drive_oq_engine_server_dlg.get_output_list(
                    calc['id'])
            if isinstance(calc_output_list, Exception):
                raise calc_output_list
            self.output_list[calc['id']] = calc_output_list

    def run_calc(self, input_files, job_type='hazard', calc_id=None):
        if hasattr(self, 'timer'):
            self.timer.stop()
            delattr(self, 'timer')
        resp = self.irmt.drive_oq_engine_server_dlg.run_calc(
            calc_id=calc_id, file_names=input_files, use_default_ini=True)
        calc_id = resp['job_id']
        print("Running %s calculation #%s" % (job_type, calc_id))
        self.timer = QTimer()
        self.timer.timeout.connect(
            lambda: self.refresh_calc_log(calc_id))
        self.timer.start(3000)  # refresh time in milliseconds
        timeout = 240
        start_time = time.time()
        while time.time() - start_time < timeout:
            QGIS_APP.processEvents()
            if not self.timer.isActive():
                self.timer.timeout.disconnect()
                break
            time.sleep(0.1)
        calc_status = self.get_calc_status(calc_id)
        if isinstance(calc_status, Exception):
            print('Removing calculation #%s' % calc_id)
            resp = self.irmt.drive_oq_engine_server_dlg.remove_calc(calc_id)
            print('After reaching the timeout of %s seconds, the %s'
                  ' calculation raised the exception "%s", and it was deleted'
                  % (timeout, job_type, calc_status))
            raise calc_status
        if not calc_status['status'] == 'complete':
            print('Removing calculation #%s' % calc_id)
            resp = self.irmt.drive_oq_engine_server_dlg.remove_calc(calc_id)
            raise TimeoutError(
                'After reaching the timeout of %s seconds, the %s'
                ' calculation was in the state "%s", and it was deleted'
                % (timeout, job_type, calc_status))
        else:
            print('Calculation #%s was completed' % calc_id)
        return calc_id

    def get_calc_status(self, calc_id):
        calc_status = self.irmt.drive_oq_engine_server_dlg.get_calc_status(
            calc_id)
        return calc_status

    def refresh_calc_log(self, calc_id):
        calc_status = self.get_calc_status(calc_id)
        if isinstance(calc_status, Exception):
            print("An exception occurred: %s" % calc_status)
            print("Trying to continue anyway")
            return
        if calc_status['status'] in ('complete', 'failed'):
            self.timer.stop()
            if calc_status['status'] == 'falied':
                print('Calculation #%s failed' % calc_id)
        calc_log = self.irmt.drive_oq_engine_server_dlg.get_calc_log(calc_id)
        if isinstance(calc_log, Exception):
            print("An exception occurred: %s" % calc_log)
            return
        if calc_log:
            print(calc_log)

    def download_output(self, output_id, outtype):
        dest_folder = tempfile.gettempdir()
        output_download_url = (
            "%s/v1/calc/result/%s?export_type=%s&dload=true" % (self.hostname,
                                                                output_id,
                                                                outtype))
        print('\t\tGET: %s' % output_download_url, file=sys.stderr)
        # FIXME: enable the user to set verify=True
        resp = requests.get(output_download_url, verify=False)
        if not resp.ok:
            raise Exception(resp.text)
        filename = resp.headers['content-disposition'].split('filename=')[1]
        filepath = os.path.join(dest_folder, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath

    def _on_loading_ko(self, output_dict):
        ex_type, ex, tb = sys.exc_info()
        failed_attempt = copy.deepcopy(output_dict)
        failed_attempt['traceback'] = tb
        self.failed_attempts.append(failed_attempt)
        self.global_failed_attempts.append(failed_attempt)
        traceback.print_tb(failed_attempt['traceback'])
        print(ex)

    def _on_loading_ok(self, start_time, output_dict):
        loading_time = time.time() - start_time
        print('\t\t(loading time: %.4f sec)' % loading_time)
        if loading_time > LONG_LOADING_TIME:
            output_dict['loading_time'] = loading_time
            self.time_consuming_outputs.append(output_dict)
            self.global_time_consuming_outputs.append(output_dict)
        output_type = output_dict['output_type']
        if output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            loaded_layer = self.irmt.iface.activeLayer()
            if output_type == 'gmf_data':
                if loaded_layer is None:
                    print('\t\tWARNING: no layer was loaded. It should mean '
                          'that no data could be loaded for the chosen eid')
            else:
                self.assertIsNotNone(loaded_layer, 'No layer was loaded')
                num_feats = loaded_layer.featureCount()
                self.assertGreater(
                    num_feats, 0,
                    'The loaded layer does not contain any feature!')

    def load_calc_output(
            self, calc, selected_output_type,
            taxonomy_idx=None, aggregate_by_site=None, approach=None,
            n_simulations=None):
        calc_id = calc['id']
        for output in self.output_list[calc_id]:
            if (output['type'] != selected_output_type and
                    "%s_aggr" % output['type'] != selected_output_type):
                continue
            output_dict = {'calc_id': calc_id,
                           'calc_mode': calc['calculation_mode'],
                           'calc_description': calc['description'],
                           'output_type': selected_output_type}
            start_time = time.time()
            print('\n\tCalculation %s (%s): %s' % (
                calc['id'], calc['calculation_mode'], calc['description']))
            # NOTE: aggregated outputs use an existing OQ-Engine output and
            #       virtually transforms it postfixing its type with '_aggr'
            output_copy = copy.deepcopy(output)
            output_copy['type'] = selected_output_type
            try:
                loading_resp = self.load_output(
                    calc, output_copy, taxonomy_idx=taxonomy_idx,
                    aggregate_by_site=aggregate_by_site, approach=approach,
                    n_simulations=n_simulations)
            except Exception:
                self._on_loading_ko(output_dict)
            else:
                if loading_resp != 'skipped':
                    self._on_loading_ok(start_time, output_dict)

    def on_init_done(self, dlg, taxonomy_idx=None, aggregate_by_site=None,
                     approach=None, n_simulations=None):
        if taxonomy_idx is not None:
            print("\t\tTaxonomy: %s" % dlg.taxonomy_cbx.itemText(taxonomy_idx))
            dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        if aggregate_by_site is not None:
            print("\t\taggregate_by_site: %s" % aggregate_by_site)
            dlg.aggregate_by_site_ckb.setChecked(aggregate_by_site)
        # NOTE: approach and n_simulations have to be set in the viewer_dock
        if approach is not None:
            print("\t\tRecovery modeling with parameters:")
            print("\t\t\tApproach: %s" % approach)
        if n_simulations is not None:
            print("\t\t\tn_simulations: %s" % n_simulations)
        # set dialog options and accept
        if dlg.output_type == 'uhs':
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.poe_cbx.count(), 0, 'No PoE was found')
            dlg.poe_cbx.setCurrentIndex(0)
        elif dlg.output_type == 'avg_losses-rlzs':
            dlg.load_selected_only_ckb.setChecked(True)
            # Taxonomies should be at least 'All' and a single one
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.taxonomy_cbx.count(), 1, 'No taxonomy was found')
            # 'All' (inserted on top)
            taxonomy_all_idx = dlg.taxonomy_cbx.findText('All')
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertEqual,
                taxonomy_all_idx, 0,
                "Taxonomy All was not the first in selector")
            dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.loss_type_cbx.count(), 0, 'No loss type was found')
            dlg.loss_type_cbx.setCurrentIndex(0)
            # FIXME: we need to do dlg.accept() also for the case
            #        performing the aggregation by zone
        elif dlg.output_type == 'damages-rlzs' and aggregate_by_site:
            # FIXME: testing only for selected taxonomy
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.taxonomy_cbx.count(), 0, 'No taxonomy was found')
            dlg.taxonomy_cbx.setCurrentIndex(0)
            taxonomy_all_idx = dlg.taxonomy_cbx.findText('All')
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertEqual,
                taxonomy_all_idx, 0,
                "Taxonomy All was not the first in selector")
            dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.loss_type_cbx.count(), 0, 'No loss_type was found')
            dlg.loss_type_cbx.setCurrentIndex(0)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.dmg_state_cbx.count(), 0, 'No damage state was found')
            dlg.dmg_state_cbx.setCurrentIndex(0)
            # FIXME: we need to do dlg.accept() also for the case
            #        performing the aggregation by zone
        elif dlg.output_type == 'asset_risk':
            num_selected_taxonomies = len(
                list(dlg.taxonomies_multisel.get_selected_items()))
            num_unselected_taxonomies = len(
                list(dlg.taxonomies_multisel.get_unselected_items()))
            num_taxonomies = (
                num_selected_taxonomies + num_unselected_taxonomies)
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                num_taxonomies, 0, 'No taxonomy was found')
            assert_and_emit(
                dlg,
                dlg.loading_exception, self.assertGreater,
                dlg.category_cbx.count(), 0, 'No category was found')
            dlg.category_cbx.setCurrentIndex(0)
        if dlg.ok_button.isEnabled():
            dlg.accept()
            if dlg.output_type == 'asset_risk':
                # NOTE: avoiding to emit loading_completed for asset_risk,
                # because in this case there's a second asynchronous call to
                # the extract api, and the signal is emitted by the callback
                return
        else:
            raise RuntimeError('The ok button is disabled')
        if dlg.output_type == 'hcurves':
            self.load_hcurves()
        elif dlg.output_type == 'uhs':
            self.load_uhs()
        elif dlg.output_type == 'damages-rlzs' and not aggregate_by_site:
            self.load_recovery_curves(dlg, approach, n_simulations)
            return
        dlg.loading_completed.emit(dlg)

    def _store_skipped_attempt(self, id, calculation_mode, description, type):
        skipped_attempt = {
            'calc_id': id,
            'calc_mode': calculation_mode,
            'calc_description': description,
            'output_type': type}
        self.skipped_attempts.append(skipped_attempt)
        self.global_skipped_attempts.append(skipped_attempt)

    def load_output(
            self, calc, output, taxonomy_idx=None, aggregate_by_site=None,
            approach=None, n_simulations=None):
        # NOTE: it is better to avoid resetting the project here, because some
        # outputs might be skipped, therefore it would not be needed
        calc_id = calc['id']
        output_type = output['type']
        calculation_mode = calc['calculation_mode']
        # NOTE: loading zipped input files only for multi_risk
        if output_type == 'input' and calculation_mode != 'multi_risk':
            self._store_skipped_attempt(
                calc_id, calculation_mode,
                calc['description'], output_type)
            print('\t\tSKIPPED (loading zipped input files only for'
                  ' multi_risk)')
            return 'skipped'
        if output_type in (OQ_CSV_TO_LAYER_TYPES |
                           OQ_RST_TYPES | OQ_ZIPPED_TYPES):
            if output_type in OQ_CSV_TO_LAYER_TYPES:
                filetype = 'csv'
            elif output_type in OQ_RST_TYPES:
                filetype = 'rst'
            else:  # OQ_ZIPPED_TYPES
                filetype = 'zip'
            # TODO: we should test the actual downloader, asynchronously
            filepath = self.download_output(output['id'], filetype)
            assert filepath is not None
            self.irmt.iface.newProject()
            if output_type == 'fullreport':
                dlg = ShowFullReportDialog(filepath)
                dlg.accept()
                print('\t\tok')
                return 'ok'
            if output_type in OQ_ZIPPED_TYPES:
                dlg = LoadInputsDialog(
                    self.irmt.drive_oq_engine_server_dlg,
                    filepath, self.irmt.iface,
                    mode='testing')
                dlg.accept()
                print('\t\tok')
                return 'ok'
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg, self.irmt.iface,
                self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type, filepath,
                calculation_mode=calculation_mode,
                mode='testing')
            if dlg.ok_button.isEnabled():
                dlg.accept()
                print('\t\tok')
                return 'ok'
            else:
                raise RuntimeError('The ok button is disabled')
                return 'ko'
        elif output_type == 'ruptures':
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg, self.irmt.iface,
                self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type, min_mag=6.5,
                calculation_mode=calculation_mode,
                mode='testing')
            self.loading_completed[dlg] = False
            self.loading_exception[dlg] = None
            dlg.loading_completed.connect(
                lambda dlg: self.on_loading_completed(dlg))
            dlg.loading_exception.connect(
                lambda dlg, exception: self.on_loading_exception(
                    dlg, exception))
            timeout = 10
            start_time = time.time()
            dlg.accept()
            while time.time() - start_time < timeout:
                QGIS_APP.processEvents()
                if self.loading_completed[dlg]:
                    print('\t\tok')
                    return 'ok'
                if self.loading_exception[dlg]:
                    raise self.loading_exception
                    return 'ko'
                time.sleep(0.1)
            raise TimeoutError(
                'Loading time exceeded %s seconds' % timeout)
            return 'ko'
        elif output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            self.irmt.iface.newProject()
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg,
                self.irmt.iface, self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type,
                calculation_mode=calculation_mode,
                mode='testing')
            self.loading_completed[dlg] = False
            self.loading_exception[dlg] = None
            dlg.loading_completed.connect(
                lambda dlg: self.on_loading_completed(dlg))
            dlg.loading_exception.connect(
                lambda dlg, exception: self.on_loading_exception(
                    dlg, exception))
            dlg.init_done.connect(
                lambda dlg: self.on_init_done(
                    dlg,
                    taxonomy_idx=taxonomy_idx,
                    aggregate_by_site=aggregate_by_site,
                    approach=approach,
                    n_simulations=n_simulations))
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                QGIS_APP.processEvents()
                if self.loading_completed[dlg]:
                    print('\t\tok')
                    return 'ok'
                if self.loading_exception[dlg]:
                    raise self.loading_exception
                    return 'ko'
                time.sleep(0.1)
            raise TimeoutError(
                'Loading time exceeded %s seconds' % timeout)
            return 'ko'
        elif output_type in OQ_EXTRACT_TO_VIEW_TYPES:
            self.irmt.iface.newProject()
            self.irmt.viewer_dock.load_no_map_output(
                calc_id, self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, output_type,
                self.irmt.drive_oq_engine_server_dlg.engine_version)
            tmpfile_handler, tmpfile_name = tempfile.mkstemp()
            self.irmt.viewer_dock.write_export_file(tmpfile_name)
            os.close(tmpfile_handler)
            print('\t\tok')
            return 'ok'

    def on_loading_completed(self, dlg):
        self.loading_completed[dlg] = True

    def on_loading_exception(self, dlg, exception):
        self.loading_exception[dlg] = exception

    def load_output_type(self, selected_output_type):
        self.get_output_list()
        if (self.only_output_type and
                self.only_output_type != selected_output_type):
            print('\nSkipped output type: %s' % selected_output_type)
            return
        self.failed_attempts = []
        self.skipped_attempts = []
        self.time_consuming_outputs = []
        for calc in self.calc_list:
            if selected_output_type in ['avg_losses-rlzs', 'damages-rlzs']:
                # TODO: keep track of taxonomy in test summary
                aggregate_by_site = (
                    None if selected_output_type == 'avg_losses-rlzs'
                    else True)
                for taxonomy_idx in [0, 1]:
                    self.load_calc_output(
                        calc, selected_output_type, taxonomy_idx=taxonomy_idx,
                        aggregate_by_site=aggregate_by_site)
                # for damages-rlzs also test recovery modeling
                if selected_output_type == 'damages-rlzs':
                    for approach in ['Disaggregate', 'Aggregate']:
                        self.load_calc_output(
                            calc, selected_output_type,
                            aggregate_by_site=False,
                            approach=approach,
                            n_simulations=2)
            else:
                self.load_calc_output(calc, selected_output_type)
        if self.skipped_attempts:
            print('\nSkipped:')
            for skipped_attempt in self.skipped_attempts:
                print('\tCalculation %s: %s'
                      % (skipped_attempt['calc_id'],
                         skipped_attempt['calc_description']))
                print('\t\tOutput type: %s' % skipped_attempt['output_type'])
        if not self.failed_attempts:
            print('\n%s successfully loaded for all calculations' %
                  selected_output_type)
        else:
            failing_summary = ''
            for failed_attempt in self.failed_attempts:
                # NOTE: we avoid printing the error also at the end, because:
                #       1) it would be a duplicate
                #       2) it would not contain the traceback from the engine
                failing_summary += ('\n\tCalculation %s (%s): %s'
                                    '\n\t\t(please check traceback ahead)') % (
                    failed_attempt['calc_id'],
                    failed_attempt['calc_mode'],
                    failed_attempt['calc_description'])
            raise FailedAttempts(failing_summary)
        if self.time_consuming_outputs:
            print('\n\nSome loaders took longer than %s seconds:' %
                  LONG_LOADING_TIME)
            for output in sorted(self.time_consuming_outputs,
                                 key=operator.itemgetter('loading_time'),
                                 reverse=True):
                print('\t%s' % output)

    def load_recovery_curves(self, dlg, approach, n_simulations):
        self._set_output_type('Recovery Curves')
        self.irmt.viewer_dock.approach_cbx.setCurrentIndex(
            self.irmt.viewer_dock.approach_cbx.findText(approach))
        self.irmt.viewer_dock.n_simulations_sbx.setValue(n_simulations)
        self._change_selection()
        self._test_export()
        dlg.loading_completed.emit(dlg)

    def load_uhs(self):
        self._set_output_type('Uniform Hazard Spectra')
        self._change_selection()
        self._test_export()

    def load_hcurves(self):
        self._set_output_type('Hazard Curves')
        self.assertGreater(
            self.irmt.viewer_dock.imt_cbx.count(), 0, 'No IMT was found!')
        self.irmt.viewer_dock.imt_cbx.setCurrentIndex(0)
        self._change_selection()
        self._test_export()

    def _test_export(self):
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        self.irmt.viewer_dock.write_export_file(exported_file_path)
        # NOTE: we are only checking that the exported CSV has at least 2 rows
        # and 3 columns per row. We are avoiding more precise checks, because
        # CSV tests are very fragile. On different platforms the numbers could
        # be slightly different. With different versions of
        # shapely/libgeos/numpy/etc the numbers could be slightly different.
        # The parameters of the demos could change in the future and the
        # numbers (even the number of rows and columns) could change.
        with open(exported_file_path, 'r', newline='') as got:
            got_reader = csv.reader(got)
            n_rows = 0
            for got_line in got_reader:
                if got_line[0].startswith('#'):
                    continue
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
                n_rows, 2,
                "The exported file %s has only %s rows" % (
                    exported_file_path, n_rows))

    def _set_output_type(self, output_type):
        self.irmt.viewer_dock.output_type_cbx.setCurrentIndex(-1)
        idx = self.irmt.viewer_dock.output_type_cbx.findText(output_type)
        self.assertNotEqual(idx, -1, 'Output type %s not found' % output_type)
        self.irmt.viewer_dock.output_type_cbx.setCurrentIndex(idx)

    def _change_selection(self):
        layer = self.irmt.iface.activeLayer()
        # the behavior should be slightly different (pluralizing labels, etc)
        # depending on the amount of features selected
        num_feats = layer.featureCount()
        self.assertGreater(
            num_feats, 0, 'The loaded layer does not contain any feature!')
        # select first feature only
        layer.select(1)
        layer.removeSelection()
        # select first and last features (just one if there is only one)
        layer.select([1, num_feats])
        # NOTE: in the past, we were also selecting all features, but it was
        # not necessary ant it made tests much slower in case of many features


# OQ_CSV_TO_LAYER_TYPES

class LoadAggRiskTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'agg_risk',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_agg_risk(self):
        self.load_output_type('agg_risk')


class LoadAggLossesStatsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'agg_losses-stats',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_agg_losses_stats(self):
        self.load_output_type('agg_losses-stats')


class LoadDmgByEventTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'risk_by_event',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_risk_by_event(self):
        self.load_output_type('risk_by_event')


class LoadEventsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'events',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_events(self):
        self.load_output_type('events')


class LoadAggLossTableTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'agg_loss_table',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_agg_loss_table(self):
        self.load_output_type('agg_loss_table')


class LoadRealizationsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'realizations',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_realizations(self):
        self.load_output_type('realizations')


# OQ_EXTRACT_TO_LAYER_TYPES

class LoadAssetRiskTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'asset_risk',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_asset_risk(self):
        self.load_output_type('asset_risk')


class LoadDamagesRlzsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'damages-rlzs',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_damages_rlzs(self):
        self.load_output_type('damages-rlzs')


class LoadAvgLossesRlzsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'avg_losses-rlzs',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_avg_losses_rlzs(self):
        self.load_output_type('avg_losses-rlzs')


class LoadAvgLossesStatsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'avg_losses-stats',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_avg_losses_stats(self):
        self.load_output_type('avg_losses-stats')


class LoadGmfDataTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'gmf_data',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_gmf_data(self):
        self.load_output_type('gmf_data')


class LoadHcurvesTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'hcurves',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_hcurves(self):
        self.load_output_type('hcurves')


class LoadHmapsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'hmaps',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_hmaps(self):
        self.load_output_type('hmaps')


class LoadRupturesTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'ruptures',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_ruptures(self):
        self.load_output_type('ruptures')


class LoadUhsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'uhs',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_uhs(self):
        self.load_output_type('uhs')


class LoadDisaggTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'disagg',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_disagg(self):
        self.load_output_type('disagg')


# OQ_ZIPPED_TYPES

class LoadInputTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'input',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_input(self):
        self.load_output_type('input')


# OQ_RST_TYPES

class LoadFullReportTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'full_report',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_full_report(self):
        self.load_output_type('full_report')


# OQ_EXTRACT_TO_VIEW_TYPES

class LoadAggCurvesRlzsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'agg_curves-rlzs',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_agg_curves_rlzs(self):
        self.load_output_type('agg_curves-rlzs')


class LoadAggCurvesStatsTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'agg_curves-stats',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_agg_curves_stats(self):
        self.load_output_type('agg_curves-stats')


class LoadDamagesRlzsAggrTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'damages-rlzs_aggr',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_damages_rlzs_aggr(self):
        self.load_output_type('damages-rlzs_aggr')


class LoadAvgLossesRlzsAggrTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'avg_losses-rlzs_aggr',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_avg_losses_rlzs_aggr(self):
        self.load_output_type('avg_losses-rlzs_aggr')


class LoadAvgLossesStatsAggrTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(
        ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != 'avg_losses-stats_aggr',
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_load_avg_losses_stats_aggr(self):
        self.load_output_type('avg_losses-stats_aggr')


# Other tests and checks

class AllLoadableOutputsFoundInDemosTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(ONLY_OUTPUT_TYPE,
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_all_loadable_output_types_found_in_demos(self):
        self.list_calculations_and_outputs()
        if self.only_calc_id or self.only_output_type:
            print('Skipping test checking if all loadable outputs are found'
                  ' in demos')
            return
        loadable_output_types_found = set()
        loadable_output_types_not_found = set()
        for loadable_output_type in OQ_ALL_TYPES:
            loadable_output_type_found = False
            for calc in self.calc_list:
                for output in self.output_list[calc['id']]:
                    if loadable_output_type == output['type']:
                        loadable_output_type_found = True
                        loadable_output_types_found.add(loadable_output_type)
                        break
                if loadable_output_type_found:
                    break
            if not loadable_output_type_found:
                loadable_output_types_not_found.add(loadable_output_type)
        if loadable_output_types_found:
            print("\nOutput_types found at least in one demo:\n\t%s" %
                  "\n\t".join(loadable_output_types_found))
        else:
            raise RuntimeError("No loadable output type was found in any demo")
        if loadable_output_types_not_found:
            print("\nOutput_types not found in any demo:\n\t%s" %
                  "\n\t".join(loadable_output_types_not_found))
            if all([output_type.endswith('_aggr')
                    for output_type in loadable_output_types_not_found]):
                print("\nThe only missing output types are '_aggr', which are"
                      " not actual outputs exposed by the engine, but"
                      " derived outputs accessed through the extract API."
                      " Therefore, is is ok.")
            else:
                print("\nSome missing output types are '_aggr', which are"
                      " not actual outputs exposed by the engine, but"
                      " derived outputs accessed through the extract API."
                      " Therefore, is is ok:\n\t%s" % "\n\t".join([
                          output_type
                          for output_type in loadable_output_types_not_found
                          if output_type.endswith('_aggr')]))
                raise RuntimeError(
                    "\nThe following loadable output types were not found in"
                    " any demo:\n%s" % "\n\t".join([
                        output_type
                        for output_type in loadable_output_types_not_found
                        if not output_type.endswith('_aggr')]))


class AllLoadersAreImplementedTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(ONLY_OUTPUT_TYPE,
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_all_loaders_are_implemented(self):
        self.list_calculations_and_outputs()
        if self.only_calc_id or self.only_output_type:
            print('Skipping test checking if any loaders are not implemented')
            return
        not_implemented_loaders = set()
        for calc in self.calc_list:
            for output in self.output_list[calc['id']]:
                if output['type'] not in OQ_ALL_TYPES:
                    not_implemented_loaders.add(output['type'])
        if not_implemented_loaders:
            print('\n\nLoaders for the following output types found in the'
                  ' available calculations have not been implemented yet:')
            print(", ".join(not_implemented_loaders))
        else:
            print("All outputs in the demos have a corresponding loader")
        # NOTE: We want green tests even when loaders are still missing


class RunCalculationTestCase(LoadOqEngineOutputsTestCase):
    @unittest.skipIf(ONLY_OUTPUT_TYPE,
        'only testing output type %s' % ONLY_OUTPUT_TYPE)
    def test_run_calculation(self):
        if self.only_calc_id or self.only_output_type:
            print('Skipping test running a new calculation')
            return
        risk_demos_path = os.path.join(
            os.pardir, 'oq-engine', 'demos', 'risk')
        risk_demos_dirs = glob.glob(os.path.join(risk_demos_path, "*", ""))
        # NOTE: assuming to find ScenarioDamage folder
        demo_dir_list = [demo_dir
                         for demo_dir in risk_demos_dirs
                         if "ScenarioDamage" in demo_dir]
        self.assertEqual(len(demo_dir_list), 1,
                         "Demo directory ScenarioDamage was not found")
        demo_dir = demo_dir_list[0]
        filepaths = glob.glob(os.path.join(demo_dir, '*'))
        hazard_calc_id = self.run_calc(filepaths, 'hazard')
        risk_calc_id = self.run_calc(filepaths, 'risk', hazard_calc_id)
        print('Removing calculation #%s' % risk_calc_id)
        self.irmt.drive_oq_engine_server_dlg.remove_calc(risk_calc_id)
        print('Removing calculation #%s' % hazard_calc_id)
        self.irmt.drive_oq_engine_server_dlg.remove_calc(hazard_calc_id)
