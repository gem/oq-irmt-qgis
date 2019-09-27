# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2016 by GEM Foundation
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
import json
import tempfile
import zipfile
import copy
from operator import itemgetter
from uuid import uuid4

from qgis.PyQt.QtCore import (QDir,
                              Qt,
                              QTimer,
                              pyqtSlot,
                              QFileInfo,
                              QSettings)

from qgis.PyQt.QtWidgets import (QDialog,
                                 QTableWidgetItem,
                                 QPushButton,
                                 QFileDialog,
                                 QInputDialog,
                                 QMessageBox)
from qgis.PyQt.QtGui import QColor, QBrush
from qgis.gui import QgsMessageBar
from qgis.core import QgsTask, QgsApplication

from requests import Session
from requests.exceptions import (ConnectionError,
                                 InvalidSchema,
                                 MissingSchema,
                                 ReadTimeout,
                                 SSLError,
                                 )
from requests.packages.urllib3.exceptions import (
    LocationParseError)
from svir.utilities.shared import (OQ_TO_LAYER_TYPES,
                                   OQ_RST_TYPES,
                                   OQ_EXTRACT_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_VIEW_TYPES,
                                   OQ_ZIPPED_TYPES,
                                   OQ_BASIC_CSV_TO_LAYER_TYPES,
                                   )
from svir.utilities.utils import (WaitCursorManager,
                                  engine_login,
                                  log_msg,
                                  ask_for_download_destination_folder,
                                  get_ui_class,
                                  SvNetworkError,
                                  get_irmt_version,
                                  get_credentials,
                                  check_is_lockdown,
                                  ServerError,
                                  RedirectionError,
                                  )
from svir.dialogs.load_ruptures_as_layer_dialog import (
    LoadRupturesAsLayerDialog)
from svir.dialogs.load_basic_csv_as_layer_dialog import (
    LoadBasicCsvAsLayerDialog)
from svir.dialogs.load_dmg_by_asset_as_layer_dialog import (
    LoadDmgByAssetAsLayerDialog)
from svir.dialogs.load_gmf_data_as_layer_dialog import (
    LoadGmfDataAsLayerDialog)
from svir.dialogs.load_asset_risk_as_layer_dialog import (
    LoadAssetRiskAsLayerDialog)
from svir.dialogs.load_hmaps_as_layer_dialog import (
    LoadHazardMapsAsLayerDialog)
from svir.dialogs.load_hcurves_as_layer_dialog import (
    LoadHazardCurvesAsLayerDialog)
from svir.dialogs.load_uhs_as_layer_dialog import (
    LoadUhsAsLayerDialog)
from svir.dialogs.load_losses_by_asset_as_layer_dialog import (
    LoadLossesByAssetAsLayerDialog)
from svir.dialogs.load_inputs_dialog import LoadInputsDialog
from svir.dialogs.show_full_report_dialog import ShowFullReportDialog
from svir.dialogs.show_console_dialog import ShowConsoleDialog
from svir.dialogs.show_params_dialog import ShowParamsDialog
from svir.tasks.download_oq_output_task import (
    DownloadOqOutputTask, TaskCanceled)

FORM_CLASS = get_ui_class('ui_drive_engine_server.ui')


HANDLED_EXCEPTIONS = (SSLError, ConnectionError, InvalidSchema, MissingSchema,
                      ReadTimeout, SvNetworkError, LocationParseError,
                      ServerError, RedirectionError)

BUTTON_WIDTH = 75

OUTPUT_TYPE_LOADERS = {
    'ruptures': LoadRupturesAsLayerDialog,
    'realizations': LoadBasicCsvAsLayerDialog,
    'events': LoadBasicCsvAsLayerDialog,
    'dmg_by_event': LoadBasicCsvAsLayerDialog,
    'losses_by_event': LoadBasicCsvAsLayerDialog,
    'agglosses': LoadBasicCsvAsLayerDialog,
    'agg_risk': LoadBasicCsvAsLayerDialog,
    'dmg_by_asset': LoadDmgByAssetAsLayerDialog,
    'gmf_data': LoadGmfDataAsLayerDialog,
    'hmaps': LoadHazardMapsAsLayerDialog,
    'hcurves': LoadHazardCurvesAsLayerDialog,
    'uhs': LoadUhsAsLayerDialog,
    'losses_by_asset': LoadLossesByAssetAsLayerDialog,
    'avg_losses-stats': LoadLossesByAssetAsLayerDialog,
    'asset_risk': LoadAssetRiskAsLayerDialog,
    'input': LoadInputsDialog,
}
assert set(OUTPUT_TYPE_LOADERS) == OQ_TO_LAYER_TYPES, (
    OUTPUT_TYPE_LOADERS, OQ_TO_LAYER_TYPES)


class DriveOqEngineServerDialog(QDialog, FORM_CLASS):
    """
    Non-modal dialog to drive the OpenQuake Engine Server's API. Through this,
    it is possible to run calculations, delete them, list them, visualize
    their outputs and loading them as vector layers.
    """
    def __init__(self, iface, viewer_dock, hostname=None):
        self.iface = iface
        self.viewer_dock = viewer_dock  # needed to change the output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.params_dlg = None
        self.console_dlg = None
        self.full_report_dlg = None
        # keep track of the log lines acquired for each calculation
        self.calc_log_line = {}
        self.session = None
        self.hostname = hostname
        if hostname is not None:
            self.forced_hostname = True
        else:
            self.forced_hostname = False
        self.calc_list = None
        self.current_calc_id = None  # list of outputs refers to this calc_id
        self.pointed_calc_id = None  # we will scroll to it
        self.is_logged_in = False
        self.is_polling = False
        self.reconnect_btn.setEnabled(True)
        self.timer = None
        # Keep retrieving the list of calculations (especially important to
        # update the status of the calculation)
        # NOTE: start_polling() is called from outside, in order to reset
        #       the timer whenever the button to open the dialog is pressed
        self.finished.connect(self.stop_polling)
        self.reconnect_btn.clicked.connect(self.on_reconnect_btn_clicked)

        self.message_bar = QgsMessageBar(self)
        self.layout().insertWidget(0, self.message_bar)

        self.engine_version = None
        self.num_login_attempts = 0

        self.download_tasks = {}
        self.open_output_dlgs = {}

        self.is_gui_enabled = False
        self.attempt_login()

    def on_reconnect_btn_clicked(self):
        self.attempt_login()

    def attempt_login(self):
        self.num_login_attempts += 1
        try:
            self.login()
        except HANDLED_EXCEPTIONS as exc:
            # in case of disconnection, try 3 times to reconnect, before
            # displaying an error
            self.set_gui_enabled(False)
            if isinstance(exc, ConnectionError):
                if self.num_login_attempts < 3:
                    # it attempts to login after the timeout is triggered
                    return
            self._handle_exception(exc)
            return exc
        else:
            if self.is_logged_in:
                self.set_gui_enabled(True)
                self.refresh_calc_list()
                self.current_calc_id = None
                self.pointed_calc_id = None
                self.check_engine_compatibility()
                self.setWindowTitle(
                    'Drive the OpenQuake Engine v%s (%s)' % (
                        self.engine_version, self.hostname))
                self.num_login_attempts = 0
                if not self.is_polling:
                    self.start_polling()

    def check_engine_compatibility(self):
        engine_version = self.get_engine_version()
        assert engine_version is not None
        self.engine_version = engine_version.split('-')[0]
        engine_version = tuple(int(x) for x in self.engine_version.split('.'))
        irmt_version = get_irmt_version()
        irmt_version = tuple(int(x) for x in irmt_version.split('.'))
        irmt_major_minor = irmt_version[:2]
        engine_major_minor = engine_version[:2]
        if irmt_major_minor != engine_major_minor:
            msg = ('The plugin is optimized to work with OpenQuake Engine '
                   ' version %s.%s. You are currently connecting with '
                   ' OpenQuake Engine version %s.%s. This could cause some '
                   ' malfunctioning.' % (irmt_major_minor[0],
                                         irmt_major_minor[1],
                                         engine_major_minor[0],
                                         engine_major_minor[1]))
            log_msg(msg, level='W', message_bar=self.message_bar)

    def login(self):
        self.session = Session()
        if not self.forced_hostname:
            self.hostname, username, password = get_credentials('engine')
        # try without authentication (if authentication is disabled server
        # side)
        # NOTE: check_is_lockdown() can raise exceptions,
        #       to be caught from outside
        is_lockdown = check_is_lockdown(self.hostname, self.session)
        if not is_lockdown:
            self.is_logged_in = True
            return
        with WaitCursorManager('Logging in...', self.message_bar):
            # it can raise exceptions, caught by self.attempt_login
            engine_login(self.hostname, username, password, self.session)
            # if no exception occurred
            self.is_logged_in = True
            return
        self.is_logged_in = False

    def get_engine_version(self):
        engine_version_url = "%s/v1/engine_version" % self.hostname
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(
                    engine_version_url, timeout=10, verify=False,
                    allow_redirects=False, stream=True)
                if resp.status_code == 302:
                    raise RedirectionError(
                        "Error %s loading %s: please check the url" % (
                            resp.status_code, resp.url))
                if not resp.ok:
                    raise ServerError(
                        "Error %s loading %s: %s" % (
                            resp.status_code, resp.url, resp.reason))
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
            return resp.text

    def refresh_calc_list(self):
        # returns True if the list is correctly retrieved
        calc_list_url = "%s/v1/calc/list?relevant=true" % self.hostname
        try:
            # FIXME: enable the user to set verify=True
            resp = self.session.get(
                calc_list_url, timeout=10, verify=False,
                allow_redirects=False, stream=True)
            if resp.status_code == 302:
                raise RedirectionError(
                    "Error %s loading %s: please check the url" % (
                        resp.status_code, resp.url))
            if not resp.ok:
                raise ServerError(
                    "Error %s loading %s: %s" % (
                        resp.status_code, resp.url, resp.reason))
        except HANDLED_EXCEPTIONS as exc:
            if self.num_login_attempts < 3:
                self.attempt_login()
            else:
                self._handle_exception(exc)
            return False
        if not self.is_gui_enabled:
            self.set_gui_enabled(True)
        self.calc_list = json.loads(resp.text)
        selected_keys = [
            'description', 'id', 'calculation_mode', 'owner', 'status']
        col_names = [
            'Description', 'Job ID', 'Calculation Mode', 'Owner', 'Status']
        col_widths = [340, 60, 135, 70, 80]
        if not self.calc_list:
            self.calc_list_tbl.blockSignals(True)
            if self.calc_list_tbl.rowCount() > 0:
                self.calc_list_tbl.clearContents()
                self.calc_list_tbl.setRowCount(0)
            else:
                self.calc_list_tbl.setRowCount(0)
                self.calc_list_tbl.setColumnCount(len(col_names))
                self.calc_list_tbl.setHorizontalHeaderLabels(col_names)
                self.calc_list_tbl.horizontalHeader().setStyleSheet(
                    "font-weight: bold;")
                self.set_calc_list_widths(col_widths)
            self.calc_list_tbl.blockSignals(False)
            return False
        actions = [
            {'label': 'Console', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Remove', 'bg_color': '#d9534f', 'txt_color': 'white'},
            {'label': 'Outputs', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Continue', 'bg_color': 'white', 'txt_color': 'black'},
            {'label': 'Abort', 'bg_color': '#d9534f', 'txt_color': 'white'},
        ]
        self.calc_list_tbl.blockSignals(True)
        self.calc_list_tbl.clearContents()
        self.calc_list_tbl.setRowCount(len(self.calc_list))
        self.calc_list_tbl.setColumnCount(len(selected_keys) + len(actions))
        for row, calc in enumerate(self.calc_list):
            calc_status = calc['status']
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                try:
                    value = self.calc_list[row][key]
                except KeyError:
                    # from engine2.5 to engine2.6, job_type was changed into
                    # calculation_mode. This check prevents the plugin to break
                    # wnen using an old version of the engine.
                    if key == 'calculation_mode':
                        value = 'unknown'
                    else:
                        # if any other unexpected keys are used, it is safer to
                        # raise a KeyError
                        raise
                item.setData(Qt.DisplayRole, value)
                # set default colors
                row_bg_color = Qt.white
                row_txt_color = Qt.black
                if calc_status == 'failed':
                    row_bg_color = QColor('#f2dede')
                elif calc_status == 'complete':
                    row_bg_color = QColor('#dff0d8')
                item.setBackground(row_bg_color)
                item.setForeground(QBrush(row_txt_color))
                self.calc_list_tbl.setItem(row, col, item)
            for col, action in enumerate(actions, len(selected_keys)):
                btn_lbl = action['label']

                # Do not display the Abort button unless the calc is running
                if btn_lbl == 'Abort' and not calc['is_running']:
                    continue

                # Display the Remove button only if calc is failed or complete
                if btn_lbl == 'Remove' and calc_status not in ('failed',
                                                               'complete'):
                    continue

                # Display the Outputs and Continue buttons
                # only if the calc is complete
                if (btn_lbl in ('Outputs', 'Continue') and
                        calc_status != 'complete'):
                    continue

                button = QPushButton()
                button.setText(btn_lbl)
                style = 'background-color: %s; color: %s' % (
                    action['bg_color'], action['txt_color'])
                button.setStyleSheet(style)
                button.clicked.connect(lambda checked=False, calc_id=calc['id'], action=btn_lbl: (  # NOQA
                    self.on_calc_action_btn_clicked(calc_id, action)))
                self.calc_list_tbl.setCellWidget(row, col, button)
                self.calc_list_tbl.setColumnWidth(col, BUTTON_WIDTH)
        empty_col_names = [''] * len(actions)
        headers = col_names + empty_col_names
        self.calc_list_tbl.setHorizontalHeaderLabels(headers)
        self.calc_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.set_calc_list_widths(col_widths)
        # if a running calculation is selected, the corresponding outputs will
        # be displayed (once) automatically at completion
        if (self.pointed_calc_id and
                self.output_list_tbl.rowCount() == 0):
            self.update_output_list(self.pointed_calc_id)
        self.calc_list_tbl.blockSignals(False)
        return True

    def get_row_by_calc_id(self, calc_id):
        # find QTableItem corresponding to that calc_id
        calc_id_col_idx = 1
        for row in range(self.calc_list_tbl.rowCount()):
            item_calc_id = self.calc_list_tbl.item(row, calc_id_col_idx)
            if int(item_calc_id.text()) == calc_id:
                return row
        return None

    def set_calc_list_widths(self, widths):
        for i, width in enumerate(widths):
            self.calc_list_tbl.setColumnWidth(i, width)
        self.calc_list_tbl.resizeRowsToContents()

    def clear_output_list(self):
        self.output_list_tbl.clearContents()
        self.output_list_tbl.setRowCount(0)
        self.output_list_tbl.setColumnCount(0)
        self.list_of_outputs_lbl.setText('List of outputs')
        self.download_datastore_btn.setEnabled(False)
        self.download_datastore_btn.setText(
            'Download HDF5 datastore')
        self.show_calc_params_btn.setEnabled(False)
        self.show_calc_params_btn.setText(
            'Show calculation parameters')

    def get_calc_info(self, calc_id):
        # NOTE: while a calc is incomplete, this returns None
        for calc_info in self.calc_list:
            if calc_info['id'] == calc_id:
                return calc_info

    def update_output_list(self, calc_id):
        calc_status = self.get_calc_status(calc_id)
        if isinstance(calc_status, Exception):
            # NOTE: the exception is managed by self._handle_exception
            return
        self.clear_output_list()
        if calc_status['status'] != 'complete':
            return
        output_list = self.get_output_list(calc_id)
        self.list_of_outputs_lbl.setText(
            'List of outputs for calculation %s' % calc_id)
        # from engine2.5 to engine2.6, job_type was changed into
        # calculation_mode. This check prevents the plugin to break wnen
        # using an old version of the engine.
        self.show_output_list(
            output_list, calc_status.get('calculation_mode', 'unknown'))
        calc_info = self.get_calc_info(calc_id)
        size_mb = calc_info['size_mb']
        btn_text = 'Download HDF5 datastore'
        if size_mb is not None:
            btn_text += 'for calculation %s (%.2f MB)' % (calc_id, size_mb)
        self.download_datastore_btn.setEnabled(size_mb is not None)
        self.download_datastore_btn.setText(btn_text)
        self.show_calc_params_btn.setEnabled(True)
        self.show_calc_params_btn.setText(
            'Show parameters for calculation %s' % calc_id)

    def on_calc_action_btn_clicked(self, calc_id, action):
        # NOTE: while scrolling through the list of calculations, the tool
        # keeps polling and refreshing the list, without losing the current
        # scrolling.  But if you click on any button, at the next refresh, the
        # view is scrolled to the top. Therefore we need to keep track of which
        # line was selected, in order to scroll to that line.
        self.current_calc_id = self.pointed_calc_id = calc_id
        self._set_show_calc_params_btn()
        self.highlight_and_scroll_to_calc_id(calc_id)
        if action == 'Console':
            self.update_output_list(calc_id)
            self.console_dlg = ShowConsoleDialog(self, calc_id)
            self.console_dlg.setWindowTitle(
                'Console log of calculation %s' % calc_id)
            self.console_dlg.show()
        elif action == 'Abort':
            confirmed = QMessageBox.question(
                self,
                'Abort calculation?',
                'The calculation will be aborted. Are you sure?',
                QMessageBox.Yes | QMessageBox.No)
            if confirmed == QMessageBox.Yes:
                self.remove_calc(calc_id, abort=True)
                if self.current_calc_id == calc_id:
                    self.clear_output_list()
        elif action == 'Remove':
            confirmed = QMessageBox.question(
                self,
                'Remove calculation?',
                'The calculation will be removed permanently. Are you sure?',
                QMessageBox.Yes | QMessageBox.No)
            if confirmed == QMessageBox.Yes:
                self.remove_calc(calc_id)
                if self.current_calc_id == calc_id:
                    self.clear_output_list()
        elif action == 'Outputs':
            self.update_output_list(calc_id)
        elif action == 'Continue':
            self.update_output_list(calc_id)
            self.run_calc(calc_id)
        else:
            raise NotImplementedError(action)

    def get_calc_log(self, calc_id):
        if calc_id not in self.calc_log_line:
            self.calc_log_line[calc_id] = 0
        start = self.calc_log_line[calc_id]
        stop = ''  # get until the end
        calc_log_url = "%s/v1/calc/%s/log/%s:%s" % (
            self.hostname, calc_id, start, stop)
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(
                    calc_log_url, timeout=10, verify=False, stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
            except Exception as exc:
                log_msg('Unhandled exception: %s' % exc,
                        level='C', exception=exc)
            calc_log = json.loads(resp.text)
            self.calc_log_line[calc_id] = start + len(calc_log)
            return '\n'.join([','.join(row) for row in calc_log])

    def get_calc_status(self, calc_id):
        calc_status_url = "%s/v1/calc/%s/status" % (self.hostname, calc_id)
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(
                    calc_status_url, timeout=10, verify=False, stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
            calc_status = json.loads(resp.text)
        return calc_status

    def remove_calc(self, calc_id, abort=False):
        method = 'abort' if abort else 'remove'
        url = "%s/v1/calc/%s/%s" % (self.hostname, calc_id, method)
        msg = 'Aborting calculation...' if abort else 'Removing calculation...'
        with WaitCursorManager(msg, self.message_bar):
            try:
                resp = self.session.post(url, timeout=10, stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
        if resp.ok:
            verb = 'aborted' if abort else 'removed'
            msg = 'Calculation %s successfully %s' % (calc_id, verb)
            log_msg(msg, level='S', message_bar=self.message_bar)
            if self.current_calc_id == calc_id:
                self.current_calc_id = None
                self.clear_output_list()
            if self.pointed_calc_id == calc_id:
                self.pointed_calc_id = None
                self.clear_output_list()
            self.refresh_calc_list()
        else:
            msg = 'Unable to %s calculation %s: %s' % (method, calc_id, resp)
            log_msg(msg, level='C', message_bar=self.message_bar)
        return

    def run_calc(self, calc_id=None, file_names=None, directory=None,
                 use_default_ini=False):
        """
        Run a calculation. If `calc_id` is given, it means we want to run
        a calculation re-using the output of the given calculation
        """
        text = self.tr('Select the files needed to run the calculation,'
                       ' or the zip archive containing those files.')
        if directory is None:
            default_dir = QSettings().value('irmt/run_oqengine_calc_dir',
                                            QDir.homePath())
        else:
            default_dir = directory
        if not file_names:
            file_names, __ = QFileDialog.getOpenFileNames(
                self, text, default_dir)
        if not file_names:
            return
        if directory is None:
            selected_dir = QFileInfo(file_names[0]).dir().path()
            QSettings().setValue('irmt/run_oqengine_calc_dir', selected_dir)
        else:
            file_names = [os.path.join(directory, os.path.basename(file_name))
                          for file_name in file_names]
        if len(file_names) == 1:
            file_full_path = file_names[0]
            _, file_ext = os.path.splitext(file_full_path)
            if file_ext == '.zip':
                zipped_file_name = file_full_path
            else:
                # NOTE: an alternative solution could be to check if the single
                # file is .ini, to look for all the files specified in the .ini
                # and to build a zip archive with all them
                msg = "Please select all the files needed, or a zip archive"
                log_msg(msg, level='C', message_bar=self.message_bar)
                return
        else:
            _, zipped_file_name = tempfile.mkstemp()
            with zipfile.ZipFile(zipped_file_name, 'w') as zipped_file:
                for file_name in file_names:
                    zipped_file.write(file_name)
        with zipfile.ZipFile(zipped_file_name, 'r') as f:
            input_file_names = f.namelist()
        ini_file_names = [file_name for file_name in input_file_names
                          if os.path.splitext(file_name)[1] == '.ini']
        if len(ini_file_names) > 1:
            if use_default_ini:
                job_ini_filename = None
            else:
                selected_file_name, ok_pressed = QInputDialog.getItem(
                    self, "Selection of the .ini file",
                    "Select a file or press Cancel to let the OQ-Engine pick"
                    " one by default",
                    [os.path.basename(file_name)
                     for file_name in ini_file_names],
                    0, False)
                if ok_pressed and selected_file_name:
                    job_ini_filename = selected_file_name
                else:
                    job_ini_filename = None
        elif len(ini_file_names) == 1:
            job_ini_filename = os.path.basename(ini_file_names[0])
        else:
            msg = "No .ini file was found"
            log_msg(msg, level='C', message_bar=self.message_bar)
            return
        run_calc_url = "%s/v1/calc/run" % self.hostname
        with WaitCursorManager('Starting calculation...', self.message_bar):
            if calc_id is not None:
                # FIXME: currently the web api is expecting a hazard_job_id
                # although it could be any kind of job_id. This will have to be
                # changed as soon as the web api is updated.
                data = {'hazard_job_id': calc_id}
            else:
                data = {}
            if job_ini_filename is not None:
                data['job_ini'] = job_ini_filename
            files = {'archive': open(zipped_file_name, 'rb')}
            try:
                log_msg('POST: %s, with files: %s, with data: %s' % (
                            run_calc_url, files, data),
                        level='I', print_to_stderr=True)
                resp = self.session.post(
                    run_calc_url, files=files, data=data, timeout=20,
                    stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
        if resp.ok:
            resp_dict = resp.json()
            job_id = resp_dict['job_id']
            self.pointed_calc_id = job_id
            self.refresh_calc_list()
            self.update_output_list(self.pointed_calc_id)
            return resp_dict
        else:
            log_msg(resp.text, level='C', message_bar=self.message_bar)

    def on_same_fs(self, checksum_file_path, ipt_checksum):
        on_same_fs_url = "%s/v1/on_same_fs" % self.hostname
        data = {'filename': checksum_file_path, 'checksum': str(ipt_checksum)}
        try:
            resp = self.session.post(
                on_same_fs_url, data=data, timeout=20, stream=True)
        except HANDLED_EXCEPTIONS as exc:
            self._handle_exception(exc)
            return False
        try:
            result = json.loads(resp.text)['success']
        except Exception as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            return False
        else:
            return result

    @pyqtSlot(int, int, int, int)
    def on_calc_list_tbl_currentCellChanged(
            self, curr_row, curr_column, prev_row, prev_col):
        # find QTableItem corresponding to that calc_id
        calc_id_col_idx = 1
        item_calc_id = self.calc_list_tbl.item(curr_row, calc_id_col_idx)
        if not item_calc_id:
            return
        calc_id = int(item_calc_id.text())
        self.current_calc_id = calc_id
        self.pointed_calc_id = calc_id
        self._set_show_calc_params_btn()
        self.update_output_list(calc_id)
        self._set_show_calc_params_btn()

    def _set_show_calc_params_btn(self):
        self.show_calc_params_btn.setEnabled(
            self.current_calc_id is not None)
        if self.current_calc_id is not None:
            self.show_calc_params_btn.setText(
                'Show parameters for calculation %s'
                % self.current_calc_id)
        else:
            self.show_calc_params_btn.setText('Show calculation parameters')

    @pyqtSlot()
    def on_download_datastore_btn_clicked(self):
        dest_folder = ask_for_download_destination_folder(self)
        if not dest_folder:
            return
        task_id = uuid4()
        msg = 'Downloading HDF5 datastore'
        self.download_tasks[task_id] = DownloadOqOutputTask(
            msg, QgsTask.CanCancel,
            None, None, None, dest_folder, self.session, self.hostname,
            self.notify_downloaded, self.notify_error, self.del_task, task_id,
            current_calc_id=self.current_calc_id)
        log_msg('%s starting. Watch progress in QGIS task bar' % msg,
                level='I', message_bar=self.message_bar)
        QgsApplication.taskManager().addTask(self.download_tasks[task_id])

    @pyqtSlot()
    def on_show_calc_params_btn_clicked(self):
        self.params_dlg = ShowParamsDialog()
        self.params_dlg.setWindowTitle(
            'Parameters of calculation %s' % self.current_calc_id)
        json_params = self.get_oqparam()
        indented_params = json.dumps(json_params, indent=4)
        self.params_dlg.text_browser.setText(indented_params)
        self.params_dlg.show()

    def get_oqparam(self):
        get_calc_params_url = "%s/v1/calc/%s/oqparam" % (
            self.hostname, self.current_calc_id)
        with WaitCursorManager('Getting calculation parameters...',
                               self.message_bar):
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(get_calc_params_url, timeout=10,
                                        verify=False, stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
            json_params = json.loads(resp.text)
        return json_params

    def get_output_list(self, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (self.hostname, calc_id)
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(output_list_url, timeout=10,
                                        verify=False, stream=True)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return exc
        if resp.ok:
            output_list = json.loads(resp.text)
            self.current_calc_id = calc_id
            return output_list
        else:
            return []

    def show_output_list(self, output_list, calculation_mode):
        if not output_list:
            self.clear_output_list()
            self.download_datastore_btn.setEnabled(False)
            self.download_datastore_btn.setText('Download HDF5 datastore')
            return
        output_list.sort(key=itemgetter('name'))
        exclude = ['url', 'outtypes', 'type', 'size_mb']
        selected_keys = [key for key in sorted(output_list[0].keys())
                         if key not in exclude]
        max_actions = 0
        for row in output_list:
            num_actions = len(row['outtypes'])
            if row['type'] in (OQ_TO_LAYER_TYPES |
                               OQ_RST_TYPES |
                               OQ_EXTRACT_TO_VIEW_TYPES):
                # TODO: remove check when gmf_data, dmg_by_event and
                #       losses_by_event will be loadable also for event_based
                if not (row['type'] in ['gmf_data',
                                        'dmg_by_event',
                                        'losses_by_event']
                        and 'event_based' in calculation_mode):
                    num_actions += 1  # needs additional column for loader btn
            if "%s_aggr" % row['type'] in OQ_EXTRACT_TO_VIEW_TYPES:
                num_actions += 1
            max_actions = max(max_actions, num_actions)

        self.output_list_tbl.setRowCount(len(output_list))
        self.output_list_tbl.setColumnCount(len(selected_keys) + max_actions)
        for row, output in enumerate(output_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                value = output_list[row][key]
                item.setData(Qt.DisplayRole, value)
                size_mb = output_list[row]['size_mb']
                if size_mb is None:
                    size_str = ' (size: n.a.)'
                else:
                    size_str = ' (size: ~%.2f MB)' % size_mb
                tooltip = "%s" % output_list[row]['type'] + size_str
                item.setData(Qt.ToolTipRole, tooltip)
                self.output_list_tbl.setItem(row, col, item)
            outtypes = output_list[row]['outtypes']
            for col, outtype in enumerate(outtypes, len(selected_keys)):
                additional_cols = 2  # start after "Id, Name"
                # Additional buttons with respect to the webui
                if output['type'] in (OQ_TO_LAYER_TYPES |
                                      OQ_RST_TYPES |
                                      OQ_EXTRACT_TO_VIEW_TYPES):
                    if output['type'] in (OQ_RST_TYPES |
                                          OQ_EXTRACT_TO_VIEW_TYPES):
                        action = 'Show'
                    elif output['type'] in OQ_ZIPPED_TYPES:
                        if calculation_mode == 'multi_risk':
                            action = 'Load from zip'
                        else:
                            action = 'Download'
                            button = QPushButton()
                            self.connect_button_to_action(
                                button, action, output, outtype)
                            self.output_list_tbl.setCellWidget(
                                row, additional_cols, button)
                            self.calc_list_tbl.setColumnWidth(
                                additional_cols, BUTTON_WIDTH)
                            continue
                    elif output['type'] in OQ_BASIC_CSV_TO_LAYER_TYPES:
                        action = 'Load table'
                    else:
                        action = 'Load layer'
                    # TODO: remove check when gmf_data, dmg_by_event and
                    # losses_by_event will be loadable also for event_based
                    if (output['type'] in ['gmf_data',
                                           'dmg_by_event',
                                           'losses_by_event']
                            and calculation_mode == 'event_based'):
                        continue
                    button = QPushButton()
                    self.connect_button_to_action(
                        button, action, output, outtype)
                    self.output_list_tbl.setCellWidget(
                        row, additional_cols, button)
                    additional_cols += 1
                if "%s_aggr" % output['type'] in OQ_EXTRACT_TO_VIEW_TYPES:
                    mod_output = copy.deepcopy(output)
                    mod_output['type'] = "%s_aggr" % output['type']
                    button = QPushButton()
                    self.connect_button_to_action(
                        button, 'Aggregate', mod_output, outtype)
                    self.output_list_tbl.setCellWidget(
                        row, additional_cols, button)
                    additional_cols += 1
                # For each output id, add a Download btn per each output type
                # (like in the webui)
                action = 'Download'
                button = QPushButton()
                self.connect_button_to_action(button, action, output, outtype)
                self.output_list_tbl.setCellWidget(
                    row, additional_cols, button)
                self.calc_list_tbl.setColumnWidth(
                    additional_cols, BUTTON_WIDTH)
        col_names = [key.capitalize() for key in selected_keys]
        empty_col_names = ['' for outtype in range(max_actions)]
        headers = col_names + empty_col_names
        self.output_list_tbl.setHorizontalHeaderLabels(headers)
        self.output_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.output_list_tbl.resizeColumnsToContents()
        self.output_list_tbl.resizeRowsToContents()

    def connect_button_to_action(self, button, action, output, outtype):
        if action in ('Load layer', 'Load from zip', 'Load table',
                      'Show', 'Aggregate'):
            style = 'background-color: blue; color: white;'
            if action == 'Load layer':
                button.setText("Load layer")
            elif action == 'Load from zip':
                button.setText("Load from zip")
            elif action == 'Load table':
                button.setText("Load table")
            elif action == 'Aggregate':
                button.setText("Aggregate")
            else:
                button.setText("Show")
        else:
            style = 'background-color: #3cb3c5; color: white;'
            button.setText("%s %s" % (action, outtype))
        button.setStyleSheet(style)
        button.clicked.connect(lambda checked=False, output=output, action=action, outtype=outtype: (  # NOQA
            self.on_output_action_btn_clicked(output, action, outtype)))

    def on_output_action_btn_clicked(self, output, action, outtype):
        output_id = output['id']
        output_type = output['type']
        if action in ['Show', 'Aggregate']:
            dest_folder = tempfile.gettempdir()
            if output_type in OQ_EXTRACT_TO_VIEW_TYPES:
                log_msg('Please use the OpenQuake Data Viewer to'
                        ' visualize data',
                        level='I', message_bar=self.message_bar)
                self.viewer_dock.load_no_map_output(
                    self.current_calc_id, self.session,
                    self.hostname, output_type, self.engine_version)
            elif outtype == 'rst':
                descr = ('Download full report for calculation %s'
                         % self.current_calc_id)
                task_id = uuid4()
                self.download_tasks[task_id] = DownloadOqOutputTask(
                    descr, QgsTask.CanCancel, output_id, outtype,
                    output_type, dest_folder, self.session, self.hostname,
                    self.open_full_report, self.notify_error, self.del_task,
                    task_id)
                log_msg('%s starting. Watch progress in QGIS task bar' % descr,
                        level='I', message_bar=self.message_bar)
                QgsApplication.taskManager().addTask(
                    self.download_tasks[task_id])
            else:
                raise NotImplementedError("%s %s" % (action, outtype))
        elif action in ['Load layer', 'Load table']:
            # NOTE: even when only a csv output is available, we might have to
            # ignore the csv and use the extract api instead, as in the case of
            # the asset_risk output type
            if outtype == 'npz' or output_type in (
                    OQ_EXTRACT_TO_LAYER_TYPES | OQ_EXTRACT_TO_VIEW_TYPES):
                self.open_output(output_id, output_type)
            elif outtype == 'csv':
                dest_folder = tempfile.gettempdir()
                descr = 'Download %s for calculation %s' % (
                    output_type, self.current_calc_id)
                task_id = uuid4()
                self.download_tasks[task_id] = DownloadOqOutputTask(
                    descr, QgsTask.CanCancel, output_id, outtype,
                    output_type, dest_folder, self.session, self.hostname,
                    self.open_output, self.notify_error, self.del_task,
                    task_id)
                log_msg('%s starting. Watch progress in QGIS task bar' % descr,
                        level='I', message_bar=self.message_bar)
                QgsApplication.taskManager().addTask(
                    self.download_tasks[task_id])
            else:
                raise NotImplementedError("%s %s" % (action, outtype))
        elif action in ['Download', 'Load from zip']:
            if action == 'Load from zip':
                dest_folder = tempfile.gettempdir()
            else:
                dest_folder = ask_for_download_destination_folder(self)
            if not dest_folder:
                return
            descr = 'Download %s for calculation %s' % (
                output_type, self.current_calc_id)
            task_id = uuid4()
            if action == 'Download':
                success_callback = self.notify_downloaded
            else:  # 'Load from zip'
                success_callback = self.on_zip_downloaded
            self.download_tasks[task_id] = DownloadOqOutputTask(
                descr, QgsTask.CanCancel, output_id, outtype,
                output_type, dest_folder, self.session, self.hostname,
                success_callback, self.notify_error, self.del_task,
                task_id)
            log_msg('%s starting. Watch progress in QGIS task bar' % descr,
                    level='I', message_bar=self.message_bar)
            QgsApplication.taskManager().addTask(self.download_tasks[task_id])
        else:
            raise NotImplementedError(action)

    def del_task(self, task_id):
        del(self.download_tasks[task_id])

    def del_dlg(self, dlg_id):
        del(self.open_output_dlgs[dlg_id])

    def open_full_report(
            self, output_id=None, output_type=None, filepath=None):
        assert(filepath is not None)
        # NOTE: it might be created here directly instead, but this way
        # we can use the qt-designer
        self.full_report_dlg = ShowFullReportDialog(filepath)
        self.full_report_dlg.setWindowTitle(
            'Full report of calculation %s' %
            self.current_calc_id)
        self.full_report_dlg.show()

    def open_output(
            self, output_id=None, output_type=None, filepath=None):
        assert(output_type is not None)
        if output_type not in OUTPUT_TYPE_LOADERS:
            raise NotImplementedError(output_type)
        dlg_id = uuid4()
        log_msg('Loading output started. Watch progress in QGIS task bar',
                level='I', message_bar=self.message_bar)
        open_output_dlg = OUTPUT_TYPE_LOADERS[output_type](
            self, self.iface, self.viewer_dock,
            self.session, self.hostname, self.current_calc_id,
            output_type, path=filepath,
            engine_version=self.engine_version)
        self.open_output_dlgs[dlg_id] = open_output_dlg
        open_output_dlg.finished[int].connect(
            lambda result: self.del_dlg(dlg_id))

    def notify_downloaded(
            self, output_id=None, output_type=None, filepath=None):
        assert(filepath is not None)
        if output_id is not None:
            msg = 'Calculation %s was saved as %s' % (output_id, filepath)
        else:
            msg = 'HDF5 datastore saved as %s' % filepath
        log_msg(msg, level='S', message_bar=self.message_bar)

    def on_zip_downloaded(
            self, output_id=None, output_type=None, filepath=None):
        self.notify_downloaded(output_id, output_type, filepath)
        dlg_id = uuid4()
        load_inputs_dlg = LoadInputsDialog(self, filepath, self.iface)
        self.open_output_dlgs[dlg_id] = load_inputs_dlg
        load_inputs_dlg.loading_completed.connect(lambda: self.del_dlg(dlg_id))
        load_inputs_dlg.loading_canceled.connect(lambda: self.del_dlg(dlg_id))
        load_inputs_dlg.show()

    def notify_error(self, exc):
        if isinstance(exc, TaskCanceled):
            msg = 'Download canceled'
            log_msg(msg, level='W', message_bar=self.iface.messageBar())
        else:
            msg = 'Unable to download the output'
            log_msg(
                msg, level='C', message_bar=self.message_bar, exception=exc)

    def start_polling(self):
        if not self.is_logged_in:
            try:
                self.login()
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
        if not self.is_logged_in:
            return
        self.refresh_calc_list()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_calc_list)
        self.timer.start(5000)  # refresh calc list time in milliseconds
        self.is_polling = True
        self.reconnect_btn.setEnabled(False)

    def stop_polling(self):
        # NOTE: perhaps we should disconnect the timeout signal here?
        if hasattr(self, 'timer') and self.timer is not None:
            self.timer.stop()
        # QObject.disconnect(self.timer, SIGNAL('timeout()'))
        self.is_polling = False
        self.calc_list_tbl.clearContents()
        self.clear_output_list()
        self.pointed_calc_id = None
        self.current_calc_id = None
        self.reconnect_btn.setEnabled(True)

    @pyqtSlot()
    def on_run_calc_btn_clicked(self):
        self.run_calc()

    def _handle_exception(self, exc):
        if isinstance(exc, SSLError):
            err_msg = '; '.join(exc.message.message.strerror.message[0])
            err_msg += ' (you could try prepending http:// or https://)'
            log_msg(err_msg, level='C', message_bar=self.message_bar)
        elif isinstance(exc, (ConnectionError,
                              InvalidSchema,
                              MissingSchema,
                              ReadTimeout,
                              LocationParseError,
                              ServerError,
                              RedirectionError,
                              SvNetworkError)):
            err_msg = str(exc)
            if isinstance(exc, InvalidSchema):
                err_msg += ' (you could try prepending http:// or https://)'
            elif isinstance(exc, ConnectionError):
                err_msg += (
                    ' (please make sure the OpenQuake Engine server (WebUI)'
                    ' is running)')
            elif isinstance(exc, (SvNetworkError, ServerError)):
                err_msg += (
                    ' (please make sure the username and password are'
                    ' spelled correctly)')
            elif isinstance(exc, RedirectionError):
                pass  # err_msg should already be enough
            else:
                err_msg += (
                    ' (please make sure the username and password are'
                    ' spelled correctly and that you are using the right'
                    ' url and port in the host setting)')
            log_msg(err_msg, level='C', message_bar=self.message_bar,
                    exception=exc)
        else:
            # sanity check (it should never occur)
            raise TypeError(
                'Unable to handle exception of type %s' % type(exc))
        self.is_logged_in = False
        self.set_gui_enabled(False)
        self.stop_polling()

    def set_gui_enabled(self, enabled):
        self.run_calc_btn.setEnabled(enabled)
        self.calc_list_tbl.setEnabled(enabled)
        self.output_list_tbl.setEnabled(enabled)
        if enabled:
            if self.current_calc_id is not None:
                self.download_datastore_btn.setEnabled(enabled)
                self.show_calc_params_btn.setEnabled(enabled)
        else:
            self.download_datastore_btn.setEnabled(enabled)
            self.show_calc_params_btn.setEnabled(enabled)
        self.is_gui_enabled = enabled

    def reject(self):
        self.stop_polling()
        if self.params_dlg is not None:
            self.params_dlg.reject()
        if self.console_dlg is not None:
            self.console_dlg.reject()
        if self.full_report_dlg is not None:
            self.full_report_dlg.reject()
        # NOTE: it should be safe to keep other dialogs open
        super().reject()
