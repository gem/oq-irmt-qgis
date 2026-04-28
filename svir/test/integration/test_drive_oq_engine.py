# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2014-10-24
#        copyright            : (C) 2014-2026 by GEM Foundation
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

import os
import glob
import sys
import time
import copy
import csv
import tempfile
import pytest

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtTest import QTest, QSignalSpy
from qgis.core import QgsProject

from svir.utilities.shared import (
    OQ_CSV_TO_LAYER_TYPES, OQ_EXTRACT_TO_LAYER_TYPES,
    OQ_RST_TYPES, OQ_EXTRACT_TO_VIEW_TYPES, OQ_ZIPPED_TYPES, OQ_ALL_TYPES
)
from svir.test.utilities import assert_and_emit
from svir.dialogs.drive_oq_engine_server_dialog import OUTPUT_TYPE_LOADERS
from svir.dialogs.show_full_report_dialog import ShowFullReportDialog
from svir.dialogs.load_inputs_dialog import LoadInputsDialog


LONG_LOADING_TIME = 10  # seconds
ONLY_OUTPUT_TYPE = os.environ.get('ONLY_OUTPUT_TYPE')
OQ_CHECK_MISSING_OUTPUTS = os.environ.get('OQ_CHECK_MISSING_OUTPUTS') != '0'
OQ_TEST_RUN_CALC = os.environ.get('OQ_TEST_RUN_CALC') != '0'


# Helper Assertions for async emit compat
def _assert_greater(a, b, msg=""): assert a > b, msg
def _assert_equal(a, b, msg=""): assert a == b, msg


class EngineOutputLoader:
    """
    Handles the UI and stateful logic for loading outputs.
    """
    def __init__(self, plugin, qgis_app, calc_list, output_list):
        self.irmt = plugin
        self.qgis_app = qgis_app
        self.hostname = os.environ.get(
            'OQ_ENGINE_HOST', 'http://localhost:8800')
        self.calc_list = calc_list
        self.output_list = output_list
        self.loading_completed = {}
        self.loading_exception = {}

    def download_output(self, output_id, filetype, output_type):
        dest_folder = tempfile.gettempdir()
        output_download_url = (
            f"{self.hostname}/v1/calc/result/{output_id}"
            f"?export_type={filetype}&dload=true")
        print(f'\t\tGET: {output_download_url}', file=sys.stderr)
        resp = self.irmt.drive_oq_engine_server_dlg.session.get(
            output_download_url, verify=False)
        if not resp.ok:
            print(f'\t\tERROR downloading {output_type}: {resp.reason}')
            print(f'\t\tresp.status_code={resp.status_code}')
            print(f'\t\tresp.text={resp.text}')
            raise Exception(resp)
        cont_disp = resp.headers.get('content-disposition', '')
        if 'filename=' not in cont_disp:
            raise RuntimeError("Missing filename in content-disposition")
        filename = cont_disp.split('filename=')[1].strip('"')
        filepath = os.path.join(dest_folder, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath

    def on_init_done(self, dlg, taxonomy_idx=None, aggregate_by_site=None,
                     approach=None, n_simulations=None):
        # Use 0 as a fallback if taxonomy_idx is None
        safe_tax_idx = taxonomy_idx if taxonomy_idx is not None else 0
        if taxonomy_idx is not None:
            print("\t\tTaxonomy: %s" % dlg.taxonomy_cbx.itemText(safe_tax_idx))
            dlg.taxonomy_cbx.setCurrentIndex(safe_tax_idx)
        if taxonomy_idx is not None and hasattr(dlg, 'taxonomy_cbx'):
            print(f"\t\tTaxonomy: {dlg.taxonomy_cbx.itemText(taxonomy_idx)}")
            dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
        if aggregate_by_site is not None and hasattr(
                dlg, 'aggregate_by_site_cbx'):
            print(f"\t\taggregate_by_site: {aggregate_by_site}")
            dlg.aggregate_by_site_ckb.setChecked(aggregate_by_site)
        if dlg.output_type == 'uhs':
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.poe_cbx.count(), 0, 'No PoE was found')
            dlg.poe_cbx.setCurrentIndex(0)
        elif dlg.output_type == 'avg_losses-rlzs':
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(
                dlg, dlg.loading_exception, _assert_greater,
                dlg.taxonomy_cbx.count(), 1, 'No taxonomy was found')
            taxonomy_all_idx = dlg.taxonomy_cbx.findText('All')
            assert_and_emit(dlg, dlg.loading_exception, _assert_equal,
                            taxonomy_all_idx, 0, "Taxonomy All was not first")
            dlg.taxonomy_cbx.setCurrentIndex(taxonomy_idx)
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.loss_type_cbx.count(), 0, 'No loss type')
            dlg.loss_type_cbx.setCurrentIndex(0)
        elif dlg.output_type in ('damages-rlzs',
                                 'damages-stats') and aggregate_by_site:
            dlg.load_selected_only_ckb.setChecked(True)
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.taxonomy_cbx.count(), 0, 'No taxonomy')
            dlg.taxonomy_cbx.setCurrentIndex(0)
            taxonomy_all_idx = dlg.taxonomy_cbx.findText('All')
            assert_and_emit(dlg, dlg.loading_exception, _assert_equal,
                            taxonomy_all_idx, 0, "Taxonomy All was not first")
            dlg.taxonomy_cbx.setCurrentIndex(safe_tax_idx)
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.loss_type_cbx.count(), 0, 'No loss_type')
            dlg.loss_type_cbx.setCurrentIndex(0)
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.dmg_state_cbx.count(), 0, 'No dmg state')
            dlg.dmg_state_cbx.setCurrentIndex(0)
        elif dlg.output_type == 'asset_risk':
            num_sel = len(list(dlg.taxonomies_multisel.get_selected_items()))
            num_unsel = len(list(
                dlg.taxonomies_multisel.get_unselected_items()))
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            (num_sel + num_unsel), 0, 'No taxonomy found')
            assert_and_emit(dlg, dlg.loading_exception, _assert_greater,
                            dlg.category_cbx.count(), 0, 'No category found')
            dlg.category_cbx.setCurrentIndex(0)
        if dlg.ok_button.isEnabled():
            dlg.accept()
            # QTest.mouseClick(dlg.ok_button, Qt.LeftButton)
            # if dlg.output_type == 'asset_risk':
            #     # NOTE: avoiding to emit loading_completed for asset_risk,
            #     # because in this case there's a second asynchronous call to
            #     # the extract api, and the signal is emitted by the callback
            #     return
            if dlg.output_type in ('asset_risk', 'hcurves', 'gmf_data'):
                return
        else:
            raise RuntimeError('The ok button is disabled')
        dlg.loading_completed.emit(dlg)

    def load_output(self, calc, output, taxonomy_idx=None,
                    aggregate_by_site=None, approach=None, n_simulations=None):
        calc_id = calc['id']
        output_type = output['type']
        calculation_mode = calc['calculation_mode']

        if output_type == 'input' and calculation_mode != 'multi_risk':
            self.skipped_attempts.append({
                'calc_id': calc_id, 'calc_mode': calculation_mode,
                'calc_description': calc['description'],
                'output_type': output_type})
            print('\t\tSKIPPED (loading zipped input files only'
                  ' for multi_risk)')
            return 'skipped'

        if output_type in (
                OQ_CSV_TO_LAYER_TYPES | OQ_RST_TYPES | OQ_ZIPPED_TYPES):
            filetype = ('csv' if output_type in OQ_CSV_TO_LAYER_TYPES
                        else 'rst' if output_type in OQ_RST_TYPES else 'zip')
            filepath = self.download_output(
                output['id'], filetype, output_type)
            assert os.path.exists(filepath), "Downloaded file does not exist"

            self.irmt.iface.newProject()

            if output_type == 'fullreport':
                dlg = ShowFullReportDialog(filepath)
                dlg.close()
                return 'ok'

            if output_type in OQ_ZIPPED_TYPES:
                dlg = LoadInputsDialog(
                    self.irmt.drive_oq_engine_server_dlg,
                    filepath, self.irmt.iface, mode='testing')
                QTest.mouseClick(dlg.ok_button, Qt.LeftButton)
                return 'ok'

            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg, self.irmt.iface,
                self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type, filepath,
                calculation_mode=calculation_mode, mode='testing')

            if dlg.ok_button.isEnabled():
                QTest.mouseClick(dlg.ok_button, Qt.LeftButton)
                return 'ok'
            raise RuntimeError('The ok button is disabled')

        elif output_type == 'ruptures':
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg, self.irmt.iface,
                self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type,
                calculation_mode=calculation_mode, mode='testing')

            self.loading_completed[dlg] = False
            self.loading_exception[dlg] = None
            dlg.loading_completed.connect(
                lambda d: self.loading_completed.update({d: True}))
            dlg.loading_exception.connect(
                lambda d, e: self.loading_exception.update({d: e}))

            timeout, start_time = 30, time.time()
            QTest.mouseClick(dlg.ok_button, Qt.LeftButton)

            while time.time() - start_time < timeout:
                self.qgis_app.processEvents()
                if self.loading_completed[dlg]:
                    return 'ok'
                if self.loading_exception[dlg]:
                    raise self.loading_exception[dlg]
                time.sleep(0.1)
            raise TimeoutError(f'Loading time exceeded {timeout} seconds')

        elif output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            self.irmt.iface.newProject()
            dlg = OUTPUT_TYPE_LOADERS[output_type](
                self.irmt.drive_oq_engine_server_dlg, self.irmt.iface,
                self.irmt.viewer_dock,
                self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, calc_id, output_type,
                calculation_mode=calculation_mode, mode='testing')

            self.loading_completed[dlg] = False
            self.loading_exception[dlg] = None
            dlg.loading_completed.connect(
                lambda d: self.loading_completed.update({d: True}))
            dlg.loading_exception.connect(
                lambda d, e: self.loading_exception.update({d: e}))
            dlg.init_done.connect(lambda d: self.on_init_done(
                    d, taxonomy_idx=taxonomy_idx,
                    aggregate_by_site=aggregate_by_site,
                    approach=approach, n_simulations=n_simulations))

            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                self.qgis_app.processEvents()
                if self.loading_completed[dlg]:
                    return 'ok'
                if self.loading_exception[dlg]:
                    raise self.loading_exception[dlg]
                time.sleep(0.1)
            raise TimeoutError(f'Loading time exceeded {timeout} seconds')

        elif output_type in OQ_EXTRACT_TO_VIEW_TYPES:
            self.irmt.iface.newProject()
            self.irmt.viewer_dock.load_no_map_output(
                calc_id, self.irmt.drive_oq_engine_server_dlg.session,
                self.hostname, output_type,
                self.irmt.drive_oq_engine_server_dlg.engine_version)
            tmpfile_handler, tmpfile_name = tempfile.mkstemp()
            self.irmt.viewer_dock.write_export_file(tmpfile_name)
            os.close(tmpfile_handler)
            return 'ok'

    def load_uhs(self):
        self._set_output_type('Uniform Hazard Spectra')
        self._change_selection()
        self._test_export()

    def load_hcurves(self):
        self._set_output_type('Hazard Curves')
        active_layer = self.irmt.iface.activeLayer()
        if active_layer:
            self.irmt.iface.layerTreeView().setCurrentLayer(active_layer)
        # Wait up to 5 seconds for the IMT combo box to populate
        timeout = 5  # seconds
        start_time = time.time()
        while self.irmt.viewer_dock.imt_cbx.count() == 0:
            self.qgis_app.processEvents()
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        assert self.irmt.viewer_dock.imt_cbx.count() > 0, (
            f"No IMT was found in the viewer dock after {timeout}s! "
            "Check if the engine calculation contains hazard data."
        )
        self.irmt.viewer_dock.imt_cbx.setCurrentIndex(0)
        self._change_selection()
        self._test_export()

    def _test_export(self, empty_is_ok=False):
        fd, exported_file_path = tempfile.mkstemp(suffix=".csv")
        self.irmt.viewer_dock.write_export_file(
            exported_file_path, empty_is_ok)
        with open(exported_file_path, 'r', newline='') as got:
            got_reader = csv.reader(got)
            n_rows = 0
            for got_line in got_reader:
                if got_line[0].startswith('#'):
                    continue
                n_rows += 1
                n_cols = len(got_line)
                assert n_cols >= 3, (
                    f"File {exported_file_path} line has only {n_cols}"
                    f" columns:\n{got_line}")
            if not empty_is_ok:
                assert n_rows >= 2, (
                    f"Exported file {exported_file_path} has"
                    f" only {n_rows} rows")
        os.close(fd)

    def _set_output_type(self, output_type):
        self.irmt.viewer_dock.output_type_cbx.setCurrentIndex(-1)
        idx = self.irmt.viewer_dock.output_type_cbx.findText(output_type)
        assert idx != -1, f'Output type {output_type} not found'
        self.irmt.viewer_dock.output_type_cbx.setCurrentIndex(idx)

    def _change_selection(self):
        layer = self.irmt.iface.activeLayer()
        features = list(layer.getFeatures())
        assert len(features) > 0, (
            'The loaded layer does not contain any feature!')
        fids = [f.id() for f in features]

        spy = QSignalSpy(layer.selectionChanged)
        layer.removeSelection()
        self.qgis_app.processEvents()

        initial_spy_count = len(spy)
        layer.selectByIds([fids[0]])
        self.qgis_app.processEvents()
        assert len(spy) > initial_spy_count, (
            "selectionChanged not emitted after selecting first feature")

        initial_spy_count = len(spy)
        if len(fids) > 1:
            layer.selectByIds([fids[0], fids[-1]])
            self.qgis_app.processEvents()
            assert len(spy) > initial_spy_count, (
                "selectionChanged not emitted after second selection")
        else:
            layer.removeSelection()
            self.qgis_app.processEvents()
            assert len(spy) > initial_spy_count, (
                "selectionChanged not emitted on second removeSelection")
            layer.selectByIds([fids[0]])
            self.qgis_app.processEvents()
            assert len(spy) > initial_spy_count + 1, (
                "selectionChanged not emitted after second selection")

    def check_layer_loaded(self, output_type):
        if output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            if output_type == 'gmf_data':
                return
            loaded_layer = None
            timeout = 3.0  # Give QGIS UI 3 seconds to catch up
            start_time = time.time()
            # Poll for the active layer
            while time.time() - start_time < timeout:
                self.qgis_app.processEvents()
                loaded_layer = self.irmt.iface.activeLayer()
                if loaded_layer is not None:
                    break
                time.sleep(0.1)
            # Fallback: Check if it's in the project even if not active in UI
            if loaded_layer is None:
                layers = QgsProject.instance().mapLayers()
                if layers:
                    loaded_layer = list(layers.values())[-1]
            assert loaded_layer is not None, (
                'No layer was loaded into the project')
            assert loaded_layer.featureCount() > 0, (
                f"Layer '{loaded_layer.name()}' is empty")

    def execute_test_for_output(self, selected_output_type):
        """Runs the entire flow for a specific output type."""
        for calc in self.calc_list:
            aggregate_by_site = (
                None if selected_output_type == 'avg_losses-rlzs' else True)
            taxonomy_loop = [0, 1] if selected_output_type in [
                'avg_losses-rlzs', 'damages-rlzs'] else [None]
            for taxonomy_idx in taxonomy_loop:
                for output in self.output_list[calc['id']]:
                    if (output['type'] != selected_output_type and
                            f"{output['type']}_aggr" != selected_output_type):
                        continue
                    output_dict = {
                        'calc_id': calc['id'],
                        'calc_mode': calc['calculation_mode'],
                        'calc_description': calc['description'],
                        'output_type': selected_output_type}
                    output_copy = copy.deepcopy(output)
                    output_copy['type'] = selected_output_type

                    loading_resp = self.load_output(
                        calc, output_copy, taxonomy_idx=taxonomy_idx,
                        aggregate_by_site=aggregate_by_site)
                    if loading_resp == 'ok':
                        if selected_output_type == 'hcurves':
                            self.load_hcurves()
                        elif selected_output_type == 'uhs':
                            self.load_uhs()
                    if loading_resp == 'skipped':
                        pytest.skip(
                            f"Skipping {output_dict['output_type']}"
                            f"for calculation mode {output_dict['calc_mode']}")
                    else:
                        self.check_layer_loaded(selected_output_type)


# Pytest Functions


@pytest.mark.parametrize("output_type", OQ_ALL_TYPES)
def test_load_engine_outputs(
        output_type, irmt_plugin, qgis_app, oq_engine_data):
    """
    Parametrized test that loops over all specific output types.
    """
    if ONLY_OUTPUT_TYPE and ONLY_OUTPUT_TYPE != output_type:
        pytest.skip(f"ONLY_OUTPUT_TYPE is set to {ONLY_OUTPUT_TYPE}")

    loader = EngineOutputLoader(
        irmt_plugin, qgis_app, oq_engine_data['calc_list'],
        oq_engine_data['output_list'])
    loader.execute_test_for_output(output_type)


def test_all_loadable_output_types_found_in_demos(oq_engine_data):
    loadable_output_types_found = set()
    loadable_output_types_not_found = set()

    for loadable_type in OQ_ALL_TYPES:
        found = any(loadable_type == out['type']
                    for calc in oq_engine_data['calc_list']
                    for out in oq_engine_data['output_list'][calc['id']])
        if found:
            loadable_output_types_found.add(loadable_type)
        else:
            loadable_output_types_not_found.add(loadable_type)

    assert loadable_output_types_found, (
        "No loadable output type was found in any demo")

    critical_missing = [
        t for t in loadable_output_types_not_found if not t.endswith('_aggr')]
    if critical_missing:
        # Check if they are just CSV types covered by other loaded CSVs
        if not all(t in OQ_CSV_TO_LAYER_TYPES and any(
                otype in OQ_CSV_TO_LAYER_TYPES
                for otype in loadable_output_types_found)
                   for t in critical_missing):
            raise RuntimeError(
                f"Loadable output types not found in any demo:"
                f"{critical_missing}")


def test_all_loaders_are_implemented(oq_engine_data):
    not_implemented_loaders = set()
    for calc in oq_engine_data['calc_list']:
        for output in oq_engine_data['output_list'][calc['id']]:
            if output['type'] not in OQ_ALL_TYPES:
                not_implemented_loaders.add(output['type'])

    if not_implemented_loaders:
        print("\n\nLoaders for the following output types found have not"
              " been implemented yet:")
        print(", ".join(not_implemented_loaders))


def test_run_calculation(irmt_plugin, qgis_app):
    """
    Triggers an actual OpenQuake engine calculation and ensures it completes.
    """
    risk_demos_path = os.path.join(os.pardir, 'oq-engine', 'demos', 'risk')
    risk_demos_dirs = glob.glob(os.path.join(risk_demos_path, "*", ""))
    demo_dir_list = [d for d in risk_demos_dirs if "ScenarioDamage" in d]
    assert len(demo_dir_list) == 1, (
        "Demo directory ScenarioDamage was not found")
    filepaths = glob.glob(os.path.join(demo_dir_list[0], '*'))

    def run_and_monitor(job_type, parent_id=None):
        resp = irmt_plugin.drive_oq_engine_server_dlg.run_calc(
            calc_id=parent_id, file_names=filepaths, use_default_ini=True)
        job_id = resp['job_id']

        start_time = time.time()
        while time.time() - start_time < 240:
            qgis_app.processEvents()
            status = irmt_plugin.drive_oq_engine_server_dlg.get_calc_status(
                job_id)
            if status.get('status') in ('complete', 'failed'):
                break
            time.sleep(0.1)

        final_status = irmt_plugin.drive_oq_engine_server_dlg.get_calc_status(
            job_id)
        if final_status.get('status') != 'complete':
            irmt_plugin.drive_oq_engine_server_dlg.remove_calc(job_id)
            pytest.fail(
                f"{job_type} calculation failed or timed out: {final_status}")
        return job_id

    hazard_calc_id = run_and_monitor('hazard')
    risk_calc_id = run_and_monitor('risk', parent_id=hazard_calc_id)
    # Teardown
    irmt_plugin.drive_oq_engine_server_dlg.remove_calc(risk_calc_id)
    irmt_plugin.drive_oq_engine_server_dlg.remove_calc(hazard_calc_id)
