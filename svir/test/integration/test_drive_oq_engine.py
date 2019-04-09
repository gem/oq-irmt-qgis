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
import tempfile
import copy
import csv
import time
import operator
import requests
from mock import Mock
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
from qgis.testing import unittest
from svir.utilities.shared import (
                                   OQ_CSV_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_LAYER_TYPES,
                                   OQ_RST_TYPES,
                                   OQ_EXTRACT_TO_VIEW_TYPES,
                                   OQ_ALL_TYPES,
                                   )
from svir.test.utilities import assert_and_emit
from svir.dialogs.drive_oq_engine_server_dialog import (
    OUTPUT_TYPE_LOADERS, DriveOqEngineServerDialog)
from svir.dialogs.show_full_report_dialog import ShowFullReportDialog
from svir.dialogs.viewer_dock import ViewerDock


QGIS_APP = QgsApplication([], True)
IFACE = iface

LONG_LOADING_TIME = 10  # seconds


def run_all():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(
        LoadOqEngineOutputsTestCase, 'test'))
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite)


class LoadOqEngineOutputsTestCase(unittest.TestCase):

    def setUp(self):
        self.hostname = os.environ.get('OQ_ENGINE_HOST',
                                       'http://localhost:8800')
        self.reset_gui()

    def reset_gui(self):
        mock_action = QAction(IFACE.mainWindow())
        self.viewer_dock = ViewerDock(IFACE, mock_action)
        IFACE.newProject()
        self.drive_oq_engine_server_dlg = DriveOqEngineServerDialog(
            IFACE, self.viewer_dock, hostname=self.hostname)

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
        filename = resp.headers['content-disposition'].split(
            'filename=')[1]
        filepath = os.path.join(dest_folder, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath

    def load_calc_outputs(self, calc):
        calc_id = calc['id']
        output_list = self.drive_oq_engine_server_dlg.get_output_list(calc_id)
        for output in output_list:
            output_dict = {'calc_id': calc_id,
                           'calc_description': calc['description'],
                           'output_type': output['type']}
            start_time = time.time()
            if (self.selected_otype is not None
                    and output['type'] != self.selected_otype):
                continue
            try:
                self.load_output(calc, output)
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                failed_attempt = copy.deepcopy(output_dict)
                failed_attempt['traceback'] = tb
                self.failed_attempts.append(failed_attempt)
                traceback.print_tb(failed_attempt['traceback'])
                print(ex)
            else:
                loading_time = time.time() - start_time
                print('\t\t(loading time: %.4f sec)' % loading_time)
                if loading_time > LONG_LOADING_TIME:
                    output_dict['loading_time'] = loading_time
                    self.time_consuming_outputs.append(output_dict)
                self.untested_otypes.discard(output['type'])
            output_type_aggr = "%s_aggr" % output['type']
            if output_type_aggr in OQ_EXTRACT_TO_VIEW_TYPES:
                aggr_output = copy.deepcopy(output)
                aggr_output['type'] = output_type_aggr
                aggr_output_dict = copy.deepcopy(output_dict)
                aggr_output_dict['output_type'] = aggr_output['type']
                try:
                    self.load_output(calc, aggr_output)
                except Exception:
                    ex_type, ex, tb = sys.exc_info()
                    failed_attempt = copy.deepcopy(output_dict)
                    failed_attempt['traceback'] = tb
                    self.failed_attempts.append(failed_attempt)
                    traceback.print_tb(failed_attempt['traceback'])
                    print(ex)
                else:
                    loading_time = time.time() - start_time
                    print('\t\t(loading time: %.4f sec)' % loading_time)
                    if loading_time > LONG_LOADING_TIME:
                        aggr_output_dict['loading_time'] = loading_time
                        self.time_consuming_outputs.append(aggr_output_dict)
                    self.untested_otypes.discard(output_type_aggr)

    def on_init_done(self, dlg):
        # set dialog options and accept
        if dlg.output_type == 'uhs':
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.poe_cbx.count(), 0, 'No PoE was found')
            dlg.poe_cbx.setCurrentIndex(0)
        elif dlg.output_type == 'losses_by_asset':
            # FIXME: testing only for the first taxonomy that is found
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.taxonomy_cbx.count(), 0, 'No taxonomy was found')
            dlg.taxonomy_cbx.setCurrentIndex(0)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.loss_type_cbx.count(), 0, 'No loss type was found')
            dlg.loss_type_cbx.setCurrentIndex(0)

            # # FIXME: we need to do dlg.accept() also for the case
            #          loading all taxonomies, and performing the
            #          aggregation by zone

            # # test all taxonomies
            # dlg.load_selected_only_ckb.setChecked(True)
            # taxonomy_idx = dlg.taxonomy_cbx.findText('All')
            # self.assertNotEqual(taxonomy_idx, -1,
            #                     'Taxonomy All was not found')
            # dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            # loss_type_idx = dlg.loss_type_cbx.findText('structural')
            # self.assertNotEqual(loss_type_idx, -1,
            #                     'Loss type structural was not found')
            # dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
            # dlg.accept()

            # FIXME: copied/pasted from skipped unit test
            #        that was causing segfault
            # loss_layer_path = os.path.join(
            #     self.data_dir_name, 'risk',
            #     'output-399-losses_by_asset_123.npz')
            # zonal_layer_path = os.path.join(
            #     self.data_dir_name, 'risk', 'zonal_layer.shp')
            # dlg = LoadLossesByAssetAsLayerDialog(
            #     IFACE, self.viewer_dock, Mock(), Mock(), Mock(),
            #     'losses_by_asset', loss_layer_path,
            #     zonal_layer_path=zonal_layer_path)
            # dlg.load_selected_only_ckb.setChecked(True)
            # dlg.zonal_layer_gbx.setChecked(True)
            # taxonomy_idx = dlg.taxonomy_cbx.findText('All')
            # self.assertNotEqual(taxonomy_idx, -1,
            #                    'Taxonomy All was not found')
            # dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            # loss_type_idx = dlg.loss_type_cbx.findText('structural')
            # self.assertNotEqual(loss_type_idx, -1,
            #                     'Loss type structural was not found')
            # dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
            # self.assertTrue(dlg.zonal_layer_cbx.currentText(),
            #                 'The zonal layer was not loaded')
            # dlg.accept()
            # zonal_layer_plus_stats = [
            #     layer for layer in IFACE.layers()
            #     if layer.name() == 'Zonal data (copy)'][0]
            # zonal_layer_plus_stats_first_feat = \
            #     zonal_layer_plus_stats.getFeatures().next()
            # expected_zonal_layer_path = os.path.join(
            #     self.data_dir_name, 'risk',
            #     'zonal_layer_plus_losses_by_asset_stats.shp')
            # expected_zonal_layer = QgsVectorLayer(
            #     expected_zonal_layer_path, 'Zonal data', 'ogr')
            # expected_zonal_layer_first_feat = \
            #     expected_zonal_layer.getFeatures().next()
            # assert_almost_equal(
            #     zonal_layer_plus_stats_first_feat.attributes(),
            #     expected_zonal_layer_first_feat.attributes())
        elif dlg.output_type == 'dmg_by_asset':
            # FIXME: testing only for selected taxonomy
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.taxonomy_cbx.count(), 0, 'No taxonomy was found')
            dlg.taxonomy_cbx.setCurrentIndex(0)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.loss_type_cbx.count(), 0, 'No loss_type was found')
            dlg.loss_type_cbx.setCurrentIndex(0)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.dmg_state_cbx.count(), 0, 'No damage state was found')
            dlg.dmg_state_cbx.setCurrentIndex(0)

            # # FIXME: we need to do dlg.accept() also for the case
            #          loading all taxonomies, and performing the
            #          aggregation by zone
            # dlg.load_selected_only_ckb.setChecked(True)
            # taxonomy_idx = dlg.taxonomy_cbx.findText('All')
            # self.assertNotEqual(
            #     taxonomy_idx, -1, 'Taxonomy All was not found')
            # dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            # loss_type_idx = dlg.loss_type_cbx.findText('structural')
            # self.assertNotEqual(loss_type_idx, -1,
            #                     'Loss type structural was not found')
            # dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
            # dmg_state_idx = dlg.dmg_state_cbx.findText('moderate')
            # self.assertNotEqual(
            #     dmg_state_idx, -1,
            #     'Damage state moderate was not found')
            # dlg.dmg_state_cbx.setCurrentIndex(dmg_state_idx)

            # FIXME: copied/pasted from skipped unit test
            #        that was causing segfault
            #        (test_load_dmg_by_asset_aggregate_by_zone)
            # dmg_layer_path = os.path.join(
            #     self.data_dir_name, 'risk',
            #     'output-1614-dmg_by_asset_356.npz')
            # zonal_layer_path = os.path.join(
            #     self.data_dir_name, 'risk',
            #     'zonal_layer.shp')
            # dlg.load_selected_only_ckb.setChecked(True)
            # dlg.zonal_layer_gbx.setChecked(True)
            # taxonomy_idx = dlg.taxonomy_cbx.findText('All')
            # self.assertNotEqual(
            #     taxonomy_idx, -1, 'Taxonomy All was not found')
            # dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            # loss_type_idx = dlg.loss_type_cbx.findText('structural')
            # self.assertNotEqual(loss_type_idx, -1,
            #                     'Loss type structural was not found')
            # dlg.loss_type_cbx.setCurrentIndex(loss_type_idx)
            # dmg_state_idx = dlg.dmg_state_cbx.findText('moderate')
            # self.assertNotEqual(
            #     dmg_state_idx, -1,
            #     'Damage state moderate was not found')
            # dlg.dmg_state_cbx.setCurrentIndex(dmg_state_idx)
            # dlg.accept()
            # zonal_layer_plus_stats = [
            #     layer for layer in IFACE.layers()
            #     if layer.name() == 'Zonal data (copy)'][0]
            # zonal_layer_plus_stats_first_feat = \
            #     zonal_layer_plus_stats.getFeatures().next()
            # expected_zonal_layer_path = os.path.join(
            #     self.data_dir_name, 'risk',
            #     'zonal_layer_plus_dmg_by_asset_stats.shp')
            # expected_zonal_layer = QgsVectorLayer(
            #     expected_zonal_layer_path, 'Zonal data', 'ogr')
            # expected_zonal_layer_first_feat = \
            #     expected_zonal_layer.getFeatures().next()
            # assert_almost_equal(
            #     zonal_layer_plus_stats_first_feat.attributes(),
            #     expected_zonal_layer_first_feat.attributes())
        elif dlg.output_type == 'asset_risk':
            num_selected_taxonomies = len(
                list(dlg.taxonomies_multisel.get_selected_items()))
            num_unselected_taxonomies = len(
                list(dlg.taxonomies_multisel.get_unselected_items()))
            num_taxonomies = (
                num_selected_taxonomies + num_unselected_taxonomies)
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                num_taxonomies, 0, 'No taxonomy was found')
            assert_and_emit(
                dlg.loading_exception, self.assertGreater,
                dlg.category_cbx.count(), 0, 'No category was found')
            dlg.category_cbx.setCurrentIndex(0)
        if dlg.ok_button.isEnabled():
            dlg.accept()
        else:
            raise RuntimeError('The ok button is disabled')
        if dlg.output_type == 'hcurves':
            self.load_hcurves()
        elif dlg.output_type == 'uhs':
            self._set_output_type('Uniform Hazard Spectra')
            self._change_selection()
            # test exporting the current selection to csv
            self._test_export()
        dlg.loading_completed.emit()

    def load_output(self, calc, output):
        # NOTE: resetting the Data Viewer before loading each output, prevents
        #       a segfault. For some reason, while running the actual
        #       application, the GUI is properly re-designed while opening a
        #       new output, but not in the testing environment (so widgets
        #       corresponding to previous outputs are not removed from the GUI)
        self.reset_gui()
        calc_id = calc['id']
        output_type = output['type']
        # TODO: when ebrisk becomes loadable, let's not skip this
        if calc['calculation_mode'] == 'ebrisk':
            skipped_attempt = {
                'calc_id': calc_id,
                'calc_description': calc['description'],
                'output_type': output_type}
            self.skipped_attempts.append(skipped_attempt)
            print('\t\tSKIPPED')
            return
        if output_type in (OQ_CSV_TO_LAYER_TYPES |
                           OQ_RST_TYPES):
            if output_type in OQ_CSV_TO_LAYER_TYPES:
                print('\tLoading output type %s...' % output_type)
                # TODO: we should test the actual downloader, asynchronously
                filepath = self.download_output(output['id'], 'csv')
            elif output_type in OQ_RST_TYPES:
                print('\tLoading output type %s...' % output_type)
                # TODO: we should test the actual downloader, asynchronously
                filepath = self.download_output(output['id'], 'rst')
            assert filepath is not None
            if output_type == 'fullreport':
                dlg = ShowFullReportDialog(filepath)
                dlg.accept()
                print('\t\tok')
                return
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                IFACE, Mock(), requests, self.hostname, calc_id,
                output_type, filepath)
            if dlg.ok_button.isEnabled():
                dlg.accept()
                print('\t\tok')
                return
            else:
                raise RuntimeError('The ok button is disabled')
        elif output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            print('\tLoading output type %s...' % output_type)
            # TODO: when gmf_data for event_based becomes loadable,
            #       let's not skip this
            if (output_type == 'gmf_data'
                    and calc['calculation_mode'] == 'event_based'):
                skipped_attempt = {
                    'calc_id': calc_id,
                    'calc_description': calc['description'],
                    'output_type': output_type}
                self.skipped_attempts.append(skipped_attempt)
                print('\t\tSKIPPED')
                return
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                IFACE, Mock(), requests, self.hostname, calc_id,
                output_type)
            self.loading_completed = False
            self.loading_exception = None
            dlg.loading_completed.connect(self.on_loading_completed)
            dlg.loading_exception[Exception].connect(self.on_loading_exception)
            dlg.init_done.connect(
                lambda: self.on_init_done(dlg))
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                QGIS_APP.processEvents()
                if self.loading_completed:
                    print('\t\tok')
                    return
                if self.loading_exception:
                    raise self.loading_exception
                time.sleep(0.1)
            raise TimeoutError(
                'Loading time exceeded %s seconds' % timeout)
        elif output_type in OQ_EXTRACT_TO_VIEW_TYPES:
            print('\tLoading output type %s...' % output_type)
            self.viewer_dock.load_no_map_output(
                calc_id, requests, self.hostname, output_type,
                self.drive_oq_engine_server_dlg.engine_version)
            tmpfile_handler, tmpfile_name = tempfile.mkstemp()
            self.viewer_dock.write_export_file(tmpfile_name)
            os.close(tmpfile_handler)
            print('\t\tok')
            return
        else:
            self.not_implemented_loaders.add(output_type)
            print('\tLoader for output type %s is not implemented'
                  % output_type)

    def on_loading_completed(self):
        self.loading_completed = True

    def on_loading_exception(self, exception):
        self.loading_exception = exception

    def test_load_outputs(self):
        self.failed_attempts = []
        self.skipped_attempts = []
        self.time_consuming_outputs = []
        self.not_implemented_loaders = set()
        self.untested_otypes = copy.copy(OQ_ALL_TYPES)  # it's a set
        calc_list = self.drive_oq_engine_server_dlg.calc_list
        try:
            selected_calc_id = int(os.environ.get('SELECTED_CALC_ID'))
        except (ValueError, TypeError):
            print('\n\n\tSELECTED_CALC_ID was not set or is not an integer'
                  ' value. Running tests for all the available calculations')
            selected_calc_id = None
        else:
            print('\n\n\tSELECTED_CALC_ID is set.'
                  ' Running tests only for calculation #%s'
                  % selected_calc_id)
        if selected_calc_id is not None:
            calc_list = [calc for calc in calc_list
                         if calc['id'] == selected_calc_id]
        self.selected_otype = os.environ.get('SELECTED_OTYPE')
        if (self.selected_otype not in OQ_ALL_TYPES):
            print('\n\tSELECTED_OTYPE was not set or is not valid.'
                  ' Running tests for all the available output types.')
            self.selected_otype = None
        else:
            print('\n\tSELECTED_OTYPE is set.'
                  ' Running tests only for %s' % self.selected_otype)
            self.untested_otypes = set([self.selected_otype])
        for calc in calc_list:
            print('\nCalculation %s: %s' % (calc['id'], calc['description']))
            self.load_calc_outputs(calc)
        if self.skipped_attempts:
            print('\n\nSkipped:')
            for skipped_attempt in self.skipped_attempts:
                print('\tCalculation %s: %s'
                      % (skipped_attempt['calc_id'],
                         skipped_attempt['calc_description']))
                print('\t\tOutput type: %s' % skipped_attempt['output_type'])
        if not self.failed_attempts:
            print('\n\nAll outputs were successfully loaded')
        else:
            print('\n\nFailed attempts:')
            for failed_attempt in self.failed_attempts:
                print('\tCalculation %s: %s'
                      % (failed_attempt['calc_id'],
                         failed_attempt['calc_description']))
                print('\t\tOutput type: %s' % failed_attempt['output_type'])
            raise RuntimeError(
                'At least one output was not successfully loaded')
        if self.time_consuming_outputs:
            print('\n\nSome loaders took longer than %s seconds:' %
                  LONG_LOADING_TIME)
            for output in sorted(self.time_consuming_outputs,
                                 key=operator.itemgetter('loading_time'),
                                 reverse=True):
                print('\t%s' % output)
        if self.not_implemented_loaders:
            # sanity check
            for not_implemented_loader in self.not_implemented_loaders:
                assert not_implemented_loader not in OQ_ALL_TYPES
            print('\n\nLoaders for the following output types found in the'
                  ' available calculations have not been implemented yet:')
            print(", ".join(self.not_implemented_loaders))
        if self.untested_otypes:
            raise RuntimeError('Untested output types: %s'
                               % self.untested_otypes)

    def load_hcurves(self):
        self._set_output_type('Hazard Curves')
        self._change_selection()
        # test changing intensity measure type
        layer = IFACE.activeLayer()
        # select the first 2 features (the same used to produce the reference
        # csv)
        num_feats = layer.featureCount()
        self.assertGreater(
            num_feats, 0, 'The layer does not contain any feature!')
        if num_feats > 1:
            layer.select([1, 2])
        else:
            layer.select([1])
        self.assertGreater(
            self.viewer_dock.imt_cbx.count(), 0, 'No IMT was found!')
        self.viewer_dock.imt_cbx.setCurrentIndex(0)
        # test exporting the current selection to csv
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        self._test_export()

    def _test_export(self):
        _, exported_file_path = tempfile.mkstemp(suffix=".csv")
        layer = IFACE.activeLayer()
        # select the first 2 features (the same used to produce the reference
        # csv)
        num_feats = layer.featureCount()
        self.assertGreater(
            num_feats, 0, 'The layer does not contain any feature!')
        if num_feats > 1:
            layer.select([1, 2])
        else:
            layer.select([1])
        # probably we have the wrong layer selected (uhs produce many layers)
        self.viewer_dock.write_export_file(exported_file_path)
        # NOTE: we are only checking that the exported CSV has at least 2 rows
        # and 3 columns per row. We are avoiding more precise checks, because
        # CSV tests are very fragile. On different platforms the numbers could
        # be slightly different. With different versions of
        # shapely/libgeos/numpy/etc the numbers could be slightly different.
        # The parameters of the demos could change in the future and the
        # numbers (even the number of rows and columns) could change.
        with open(exported_file_path, 'r') as got:
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
        idx = self.viewer_dock.output_type_cbx.findText(output_type)
        self.assertNotEqual(idx, -1, 'Output type %s not found' % output_type)
        self.viewer_dock.output_type_cbx.setCurrentIndex(idx)

    def _change_selection(self):
        layer = IFACE.activeLayer()
        # the behavior should be slightly different (pluralizing labels, etc)
        # depending on the amount of features selected
        num_feats = layer.featureCount()
        self.assertGreater(
            num_feats, 0, 'The layer does not contain any feature!')
        layer.select(1)
        layer.removeSelection()
        if num_feats > 1:
            layer.select(2)
        layer.selectAll()
        layer.removeSelection()
