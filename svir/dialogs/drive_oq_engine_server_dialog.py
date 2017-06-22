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

from PyQt4.QtCore import (QDir,
                          Qt,
                          QObject,
                          SIGNAL,
                          QTimer,
                          pyqtSlot,
                          QFileInfo,
                          QSettings,
                          )

from PyQt4.QtGui import (QDialog,
                         QTableWidgetItem,
                         QAbstractItemView,
                         QPushButton,
                         QFileDialog,
                         QColor,
                         QMessageBox,
                         )
from svir.third_party.requests import Session
from svir.third_party.requests.exceptions import (ConnectionError,
                                                  InvalidSchema,
                                                  MissingSchema,
                                                  ReadTimeout,
                                                  SSLError,
                                                  )
from svir.utilities.settings import get_engine_credentials
from svir.utilities.shared import OQ_ALL_LOADABLE_TYPES
from svir.utilities.utils import (WaitCursorManager,
                                  engine_login,
                                  log_msg,
                                  ask_for_download_destination_folder,
                                  get_ui_class,
                                  SvNetworkError,
                                  )
from svir.dialogs.load_ruptures_as_layer_dialog import (
    LoadRupturesAsLayerDialog)
from svir.dialogs.load_dmg_by_asset_as_layer_dialog import (
    LoadDmgByAssetAsLayerDialog)
from svir.dialogs.load_gmf_data_as_layer_dialog import (
    LoadGmfDataAsLayerDialog)
from svir.dialogs.load_hmaps_as_layer_dialog import (
    LoadHazardMapsAsLayerDialog)
from svir.dialogs.load_hcurves_as_layer_dialog import (
    LoadHazardCurvesAsLayerDialog)
from svir.dialogs.load_uhs_as_layer_dialog import (
    LoadUhsAsLayerDialog)
from svir.dialogs.load_losses_by_asset_as_layer_dialog import (
    LoadLossesByAssetAsLayerDialog)
from svir.dialogs.show_full_report_dialog import ShowFullReportDialog
from svir.dialogs.show_console_dialog import ShowConsoleDialog
from svir.dialogs.show_params_dialog import ShowParamsDialog

FORM_CLASS = get_ui_class('ui_drive_engine_server.ui')

HANDLED_EXCEPTIONS = (SSLError, ConnectionError, InvalidSchema, MissingSchema,
                      ReadTimeout, SvNetworkError)

BUTTON_WIDTH = 75

OUTPUT_TYPE_LOADERS = {
    'ruptures': LoadRupturesAsLayerDialog,
    'dmg_by_asset': LoadDmgByAssetAsLayerDialog,
    'gmf_data': LoadGmfDataAsLayerDialog,
    'hmaps': LoadHazardMapsAsLayerDialog,
    'hcurves': LoadHazardCurvesAsLayerDialog,
    'uhs': LoadUhsAsLayerDialog,
    'losses_by_asset': LoadLossesByAssetAsLayerDialog}
assert set(OUTPUT_TYPE_LOADERS) == OQ_ALL_LOADABLE_TYPES


class DriveOqEngineServerDialog(QDialog, FORM_CLASS):
    """
    Non-modal dialog to drive the OpenQuake Engine Server's API. Through this,
    it is possible to run calculations, delete them, list them, visualize
    their outputs and loading them as vector layers.
    """
    def __init__(self, iface, viewer_dock):
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
        self.hostname = None
        self.current_output_calc_id = None
        self.current_pointed_calc_id = None  # we will scroll to it
        self.is_logged_in = False
        self.timer = None
        # Keep retrieving the list of calculations (especially important to
        # update the status of the calculation)
        # NOTE: start_polling() is called from outside, in order to reset
        #       the timer whenever the button to open the dialog is pressed
        self.finished.connect(self.stop_polling)
        self.attempt_login()

    def attempt_login(self):
        try:
            self.login()
        except HANDLED_EXCEPTIONS as exc:
            self._handle_exception(exc)
        else:
            self.refresh_calc_list()

    def login(self):
        self.session = Session()
        self.hostname, username, password = get_engine_credentials(self.iface)
        # try without authentication (if authentication is disabled server
        # side)
        # NOTE: is_lockdown() can raise exceptions, to be caught from outside
        is_lockdown = self.is_lockdown()
        if not is_lockdown:
            self.is_logged_in = True
            return
        if username and password:
            with WaitCursorManager('Logging in...', self.iface):
                # it can raise exceptions, caught by self.attempt_login
                engine_login(self.hostname, username, password, self.session)
                # if no exception occurred
                self.is_logged_in = True

    def is_lockdown(self):
        # try retrieving the engine version and see if the server
        # redirects you to the login page
        engine_version_url = "%s/engine_version" % self.hostname
        with WaitCursorManager():
            # it can raise exceptions, caught by self.attempt_login
            # FIXME: enable the user to set verify=True
            resp = self.session.get(
                engine_version_url, timeout=10, verify=False)
            # handle case of redirection to the login page
            if not resp.ok:
                raise ConnectionError(
                    "%s %s: %s" % (resp.status_code, resp.url, resp.reason))
            if resp.url != engine_version_url and 'login' in resp.url:
                return True
        return False

    def refresh_calc_list(self):
        # returns True if the list is correctly retrieved
        calc_list_url = "%s/v1/calc/list?relevant=true" % self.hostname
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(
                    calc_list_url, timeout=10, verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            # handle case of redirection to the login page
            if resp.url != calc_list_url and 'login' in resp.url:
                msg = ("Please check OpenQuake Engine connection settings and"
                       " credentials. The call to %s was redirected to %s."
                       % (calc_list_url, resp.url))
                log_msg(msg, level='C',
                        message_bar=self.iface.messageBar())
                self.is_logged_in = False
                self.reject()
                return
            calc_list = json.loads(resp.text)
        selected_keys = [
            'description', 'id', 'calculation_mode', 'owner', 'status']
        col_names = [
            'Description', 'Job ID', 'Calculation Mode', 'Owner', 'Status']
        col_widths = [340, 60, 135, 70, 80]
        if not calc_list:
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
            return
        actions = [
            {'label': 'Console', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Remove', 'bg_color': '#d9534f', 'txt_color': 'white'},
            {'label': 'Outputs', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Continue', 'bg_color': 'white', 'txt_color': 'black'}
        ]
        self.calc_list_tbl.clearContents()
        self.calc_list_tbl.setRowCount(len(calc_list))
        self.calc_list_tbl.setColumnCount(len(selected_keys) + len(actions))
        for row, calc in enumerate(calc_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                try:
                    value = calc_list[row][key]
                except KeyError:
                    # from engine2.4 to engine2.5, job_type was changed into
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
                if calc['status'] == 'failed':
                    row_bg_color = QColor('#f2dede')
                elif calc['status'] == 'complete':
                    row_bg_color = QColor('#dff0d8')
                item.setBackgroundColor(row_bg_color)
                item.setTextColor(row_txt_color)
                self.calc_list_tbl.setItem(row, col, item)
            for col, action in enumerate(actions, len(selected_keys)):
                # display the Continue and Output buttons only if the
                # computation is completed
                if (calc['status'] != 'complete' and
                        action['label'] in ('Continue', 'Outputs')):
                    continue
                button = QPushButton()
                button.setText(action['label'])
                style = 'background-color: %s; color: %s' % (
                    action['bg_color'], action['txt_color'])
                button.setStyleSheet(style)
                QObject.connect(
                    button, SIGNAL("clicked()"),
                    lambda calc_id=calc['id'], action=action['label']: (
                        self.on_calc_action_btn_clicked(calc_id, action)))
                self.calc_list_tbl.setCellWidget(row, col, button)
                self.calc_list_tbl.setColumnWidth(col, BUTTON_WIDTH)
        empty_col_names = [''] * len(actions)
        headers = col_names + empty_col_names
        self.calc_list_tbl.setHorizontalHeaderLabels(headers)
        self.calc_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.set_calc_list_widths(col_widths)
        if self.current_pointed_calc_id:
            self.highlight_and_scroll_to_calc_id(self.current_pointed_calc_id)
        return True

    def get_row_by_calc_id(self, calc_id):
        # find QTableItem corresponding to that calc_id
        calc_id_col_idx = 1
        for row in xrange(self.calc_list_tbl.rowCount()):
            item_calc_id = self.calc_list_tbl.item(row, calc_id_col_idx)
            if int(item_calc_id.text()) == calc_id:
                return row
        return None

    def highlight_and_scroll_to_calc_id(self, calc_id):
        row = self.get_row_by_calc_id(calc_id)
        if row is not None:
            self.calc_list_tbl.selectRow(row)
            calc_id_col_idx = 1
            item_calc_id = self.calc_list_tbl.item(row, calc_id_col_idx)
            self.calc_list_tbl.scrollToItem(
                item_calc_id, QAbstractItemView.PositionAtCenter)
        else:
            self.current_pointed_calc_id = None
            self.calc_list_tbl.clearSelection()

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
            'Download HDF5 datastore for calculation')

    def update_output_list(self, calc_id):
        calc_status = self.get_calc_status(calc_id)
        if calc_status['status'] == 'complete':
            self.clear_output_list()
            output_list = self.get_output_list(calc_id)
            self.list_of_outputs_lbl.setText(
                'List of outputs for calculation %s' % calc_id)
            # from engine2.4 to engine2.5, job_type was changed into
            # calculation_mode. This check prevents the plugin to break wnen
            # using an old version of the engine.
            self.show_output_list(
                output_list, calc_status.get('calculation_mode', 'unknown'))
            self.download_datastore_btn.setEnabled(True)
            self.download_datastore_btn.setText(
                'Download HDF5 datastore for calculation %s'
                % self.current_output_calc_id)
        else:
            self.clear_output_list()

    def on_calc_action_btn_clicked(self, calc_id, action):
        # NOTE: while scrolling through the list of calculations, the tool
        # keeps polling and refreshing the list, without losing the current
        # scrolling.  But if you click on any button, at the next refresh, the
        # view is scrolled to the top. Therefore we need to keep track of which
        # line was selected, in order to scroll to that line.
        self.current_pointed_calc_id = calc_id
        self._set_show_calc_params_btn()
        self.highlight_and_scroll_to_calc_id(calc_id)
        if action == 'Console':
            self.update_output_list(calc_id)
            self.console_dlg = ShowConsoleDialog(self, calc_id)
            self.console_dlg.setWindowTitle(
                'Console log of calculation %s' % calc_id)
            self.console_dlg.show()
        elif action == 'Remove':
            confirmed = QMessageBox.question(
                self,
                'Remove calculation?',
                'The calculation will be removed permanently. Are you sure?',
                QMessageBox.Yes | QMessageBox.No)
            if confirmed == QMessageBox.Yes:
                self.remove_calc(calc_id)
                if self.current_output_calc_id == calc_id:
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
                resp = self.session.get(calc_log_url, timeout=10, verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            calc_log = json.loads(resp.text)
            self.calc_log_line[calc_id] = start + len(calc_log)
            return '\n'.join([','.join(row) for row in calc_log])

    def get_calc_status(self, calc_id):
        calc_status_url = "%s/v1/calc/%s/status" % (self.hostname, calc_id)
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(
                    calc_status_url, timeout=10, verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            calc_status = json.loads(resp.text)
            return calc_status

    def remove_calc(self, calc_id):
        calc_remove_url = "%s/v1/calc/%s/remove" % (self.hostname, calc_id)
        with WaitCursorManager('Removing calculation...', self.iface):
            try:
                resp = self.session.post(calc_remove_url, timeout=10)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
        if resp.ok:
            msg = 'Calculation %s successfully removed' % calc_id
            log_msg(msg, level='I', message_bar=self.iface.messageBar())
            self.refresh_calc_list()
        else:
            msg = 'Unable to remove calculation %s' % calc_id
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
        return

    def run_calc(self, calc_id=None, file_names=None):
        """
        Run a calculation. If `calc_id` is given, it means we want to run
        a calculation re-using the output of the given calculation
        """
        text = self.tr('Select the files needed to run the calculation,'
                       ' or the zip archive containing those files.')
        default_dir = QSettings().value('irmt/run_oqengine_calc_dir',
                                        QDir.homePath())
        if not file_names:
            file_names = QFileDialog.getOpenFileNames(self, text, default_dir)
        if not file_names:
            return
        selected_dir = QFileInfo(file_names[0]).dir().path()
        QSettings().setValue('irmt/run_oqengine_calc_dir', selected_dir)
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
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
                return
        else:
            _, zipped_file_name = tempfile.mkstemp()
            with zipfile.ZipFile(zipped_file_name, 'w') as zipped_file:
                for file_name in file_names:
                    zipped_file.write(file_name)
        run_calc_url = "%s/v1/calc/run" % self.hostname
        with WaitCursorManager('Starting calculation...', self.iface):
            if calc_id is not None:
                # FIXME: currently the web api is expecting a hazard_job_id
                # although it could be any kind of job_id. This will have to be
                # changed as soon as the web api is updated.
                data = {'hazard_job_id': calc_id}
            else:
                data = {}
            files = {'archive': open(zipped_file_name, 'rb')}
            try:
                resp = self.session.post(
                    run_calc_url, files=files, data=data, timeout=20)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
        if resp.ok:
            self.refresh_calc_list()
            return resp.json()
        else:
            log_msg(resp.text, level='C', message_bar=self.iface.messageBar())

    @pyqtSlot(int, int)
    def on_calc_list_tbl_cellClicked(self, row, column):
        self.calc_list_tbl.selectRow(row)
        # find QTableItem corresponding to that calc_id
        calc_id_col_idx = 1
        item_calc_id = self.calc_list_tbl.item(row, calc_id_col_idx)
        calc_id = int(item_calc_id.text())
        if self.current_pointed_calc_id == calc_id:
            self.current_pointed_calc_id = None
            self.calc_list_tbl.clearSelection()
        else:
            self.current_pointed_calc_id = calc_id
            self._set_show_calc_params_btn()
        self._set_show_calc_params_btn()
        self.update_output_list(calc_id)

    def _set_show_calc_params_btn(self):
        self.show_calc_params_btn.setEnabled(
            self.current_pointed_calc_id is not None)
        if self.current_pointed_calc_id is not None:
            self.show_calc_params_btn.setText(
                'Show parameters for calculation %s'
                % self.current_pointed_calc_id)
        else:
            self.show_calc_params_btn.setText('Show calculation parameters')

    @pyqtSlot()
    def on_download_datastore_btn_clicked(self):
        dest_folder = ask_for_download_destination_folder(self)
        if not dest_folder:
            return
        datastore_url = "%s/v1/calc/%s/datastore" % (
            self.hostname, self.current_output_calc_id)
        with WaitCursorManager('Getting HDF5 datastore...', self.iface):
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(datastore_url, timeout=10,
                                        verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            filename = resp.headers['content-disposition'].split(
                'filename=')[1]
            filepath = os.path.join(dest_folder, os.path.basename(filename))
            open(filepath, "wb").write(resp.content)
            log_msg('The datastore has been saved as %s' % filepath,
                    level='I', message_bar=self.iface.messageBar())

    @pyqtSlot()
    def on_show_calc_params_btn_clicked(self):
        self.params_dlg = ShowParamsDialog()
        self.params_dlg.setWindowTitle(
            'Parameters of calculation %s' % self.current_pointed_calc_id)
        get_calc_params_url = "%s/v1/calc/%s/oqparam" % (
            self.hostname, self.current_pointed_calc_id)
        with WaitCursorManager('Getting calculation parameters...',
                               self.iface):
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(get_calc_params_url, timeout=10,
                                        verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            json_params = json.loads(resp.text)
            indented_params = json.dumps(json_params, indent=4)
            self.params_dlg.text_browser.setText(indented_params)
        self.params_dlg.show()

    def get_output_list(self, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (self.hostname, calc_id)
        with WaitCursorManager():
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(output_list_url, timeout=10,
                                        verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
        if resp.ok:
            output_list = json.loads(resp.text)
            self.current_output_calc_id = calc_id
            return output_list
        else:
            return []

    def show_output_list(self, output_list, calculation_mode):
        if not output_list:
            self.clear_output_list()
            self.download_datastore_btn.setEnabled(False)
            self.download_datastore_btn.setText('Download HDF5 datastore')
            return
        exclude = ['url', 'outtypes']
        selected_keys = [key for key in sorted(output_list[0].keys())
                         if key not in exclude]
        max_actions = 0
        for row in output_list:
            num_actions = len(row['outtypes'])
            if (row['type'] in OQ_ALL_LOADABLE_TYPES
                    or row['type'] == 'fullreport'):
                # TODO: remove check when gmf_data will be loadable also for
                #       event_based
                if not (row['type'] == 'gmf_data'
                        and 'event_based' in calculation_mode):
                    num_actions += 1  # needs additional column for loader btn
            max_actions = max(max_actions, num_actions)

        self.output_list_tbl.setRowCount(len(output_list))
        self.output_list_tbl.setColumnCount(
            len(selected_keys) + max_actions)
        for row, output in enumerate(output_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                value = output_list[row][key]
                item.setData(Qt.DisplayRole, value)
                self.output_list_tbl.setItem(row, col, item)
            outtypes = output_list[row]['outtypes']
            for col, outtype in enumerate(outtypes, len(selected_keys)):
                action = 'Download'
                button = QPushButton()
                self.connect_button_to_action(button, action, output, outtype)
                self.output_list_tbl.setCellWidget(row, col, button)
                self.calc_list_tbl.setColumnWidth(col, BUTTON_WIDTH)
            if (output['type'] in OQ_ALL_LOADABLE_TYPES
                    or output['type'] == 'fullreport'):
                if output['type'] == 'fullreport':
                    action = 'Show'
                else:
                    action = 'Load as layer'
                # TODO: remove check when gmf_data will be loadable also for
                #       event_based
                if (output['type'] == 'gmf_data'
                        and 'event_based' in calculation_mode):
                    continue
                button = QPushButton()
                self.connect_button_to_action(
                    button, action, output, outtype)
                self.output_list_tbl.setCellWidget(row, col + 1, button)
                self.calc_list_tbl.setColumnWidth(col, BUTTON_WIDTH)
        col_names = [key.capitalize() for key in selected_keys]
        empty_col_names = ['' for outtype in range(max_actions)]
        headers = col_names + empty_col_names
        self.output_list_tbl.setHorizontalHeaderLabels(headers)
        self.output_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.output_list_tbl.resizeColumnsToContents()
        self.output_list_tbl.resizeRowsToContents()

    def connect_button_to_action(self, button, action, output, outtype):
        if action in ('Load as layer', 'Show'):
            style = 'background-color: blue; color: white;'
            if action == 'Load as layer':
                button.setText("Load %s as layer" % outtype)
            else:
                button.setText("Show")
        else:
            style = 'background-color: #3cb3c5; color: white;'
            button.setText("%s %s" % (action, outtype))
        button.setStyleSheet(style)
        QObject.connect(
            button, SIGNAL("clicked()"),
            lambda output=output, action=action, outtype=outtype: (
                self.on_output_action_btn_clicked(output, action, outtype))
        )

    def on_output_action_btn_clicked(self, output, action, outtype):
        output_id = output['id']
        output_type = output['type']
        if action == 'Show':
            dest_folder = tempfile.gettempdir()
            if outtype == 'rst':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                if not filepath:
                    return
                # NOTE: it might be created here directly instead, but this way
                # we can use the qt-designer
                self.full_report_dlg = ShowFullReportDialog(filepath)
                self.full_report_dlg.setWindowTitle(
                    'Full report of calculation %s' %
                    self.current_output_calc_id)
                self.full_report_dlg.show()
            else:
                raise NotImplementedError("%s %s" % (action, outtype))
        elif action == 'Load as layer':
            dest_folder = tempfile.gettempdir()
            if outtype in ('npz', 'csv'):
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                if not filepath:
                    return
                if output_type not in OUTPUT_TYPE_LOADERS:
                    raise NotImplementedError(output_type)
                dlg = OUTPUT_TYPE_LOADERS[output_type](
                    self.iface, self.viewer_dock, output_type, filepath)
                dlg.exec_()
            else:
                raise NotImplementedError("%s %s" % (action, outtype))
        elif action == 'Download':
            filepath = self.download_output(output_id, outtype)
            if not filepath:
                return
            msg = 'Calculation %s was saved as %s' % (output_id, filepath)
            log_msg(msg, level='I', message_bar=self.iface.messageBar())
        else:
            raise NotImplementedError(action)

    def download_output(self, output_id, outtype, dest_folder=None):
        if not dest_folder:
            dest_folder = ask_for_download_destination_folder(self)
            if not dest_folder:
                return
        output_download_url = (
            "%s/v1/calc/result/%s?export_type=%s&dload=true" % (self.hostname,
                                                                output_id,
                                                                outtype))
        with WaitCursorManager('Downloading output...', self.iface):
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(output_download_url, verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            if not resp.ok:
                err_msg = (
                    'Unable to download the output.\n%s: %s.\n%s'
                    % (resp.status_code, resp.reason, resp.text))
                log_msg(err_msg, level='C',
                        message_bar=self.iface.messageBar())
                return
            filename = resp.headers['content-disposition'].split(
                'filename=')[1]
            filepath = os.path.join(dest_folder, filename)
            open(filepath, "wb").write(resp.content)
        return filepath

    def start_polling(self):
        if not self.is_logged_in:
            self.login()
        if not self.is_logged_in:
            return
        self.refresh_calc_list()
        self.timer = QTimer()
        QObject.connect(
            self.timer, SIGNAL('timeout()'), self.refresh_calc_list)
        self.timer.start(5000)  # refresh calc list time in milliseconds

    def stop_polling(self):
        # NOTE: perhaps we should disconnect the timeout signal here?
        if hasattr(self, 'timer') and self.timer is not None:
            self.timer.stop()
        # QObject.disconnect(self.timer, SIGNAL('timeout()'))

    @pyqtSlot()
    def on_run_calc_btn_clicked(self):
        self.run_calc()

    def _handle_exception(self, exc):
        if isinstance(exc, SSLError):
            err_msg = '; '.join(exc.message.message.strerror.message[0])
            err_msg += ' (you could try prepending http:// or https://)'
            log_msg(err_msg, level='C', message_bar=self.iface.messageBar())
        elif isinstance(exc, (ConnectionError,
                              InvalidSchema,
                              MissingSchema,
                              ReadTimeout,
                              SvNetworkError)):
            err_msg = str(exc)
            if isinstance(exc, InvalidSchema):
                err_msg += ' (you could try prepending http:// or https://)'
            elif isinstance(exc, SvNetworkError):
                err_msg += (
                    ' (please make sure the username and password are'
                    ' spelled correctly)')
            else:
                err_msg += (
                    ' (please make sure the username and password are'
                    ' spelled correctly and that you are using the right'
                    ' url and port in the host setting)')
            log_msg(err_msg, level='C',
                    message_bar=self.iface.messageBar())
        else:
            # sanity check (it should never occur)
            raise TypeError(
                'Unable to handle exception of type %s' % type(exc))
        self.is_logged_in = False
        self.reject()

    def reject(self):
        self.stop_polling()
        super(DriveOqEngineServerDialog, self).reject()
