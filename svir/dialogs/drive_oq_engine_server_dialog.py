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
                         QPushButton,
                         QFileDialog,
                         QColor,
                         QDockWidget,
                         )
from svir.third_party.requests import Session
from svir.third_party.requests.exceptions import (ConnectionError,
                                                  InvalidSchema,
                                                  MissingSchema,
                                                  ReadTimeout,
                                                  SSLError,
                                                  )
from svir.utilities.settings import get_engine_credentials
from svir.utilities.utils import (WaitCursorManager,
                                  engine_login,
                                  log_msg,
                                  ask_for_download_destination_folder,
                                  get_ui_class,
                                  SvNetworkError,
                                  )
from svir.dialogs.load_npz_as_layer_dialog import LoadNpzAsLayerDialog
from svir.dialogs.load_geojson_as_layer_dialog import LoadGeoJsonAsLayerDialog
from svir.dialogs.load_csv_as_layer_dialog import LoadCsvAsLayerDialog

FORM_CLASS = get_ui_class('ui_drive_engine_server.ui')

HANDLED_EXCEPTIONS = (SSLError, ConnectionError, InvalidSchema, MissingSchema,
                      ReadTimeout, SvNetworkError)


class DriveOqEngineServerDialog(QDialog, FORM_CLASS):
    """
    Non-modal dialog to drive the OpenQuake Engine Server's API. Through this,
    it is possible to run calculations, delete them, list them, visualize
    their outputs and loading them as vector layers.
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # keep track of the log lines acquired for each calculation
        self.calc_log_line = {}
        self.session = None
        self.hostname = None
        self.current_output_calc_id = None
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
        # NOTE: is_lockdown() can raise exceptions, to be catched from outside
        is_lockdown = self.is_lockdown()
        if not is_lockdown:
            self.is_logged_in = True
            return
        if username and password:
            with WaitCursorManager('Logging in...', self.iface):
                # it can raise exceptions, catched by self.attempt_login
                engine_login(self.hostname, username, password, self.session)
                # if no exception occurred
                self.is_logged_in = True

    def is_lockdown(self):
        # try retrieving the engine version and see if the server
        # redirects you to the login page
        engine_version_url = "%s/engine_version" % self.hostname
        with WaitCursorManager():
            # it can raise exceptions, catched by self.attempt_login
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
        selected_keys = ['description', 'id', 'job_type', 'owner', 'status']
        col_names = ['Description', 'ID', 'Job Type', 'Owner', 'Status']
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
                self.calc_list_tbl.resizeColumnsToContents()
                self.calc_list_tbl.resizeRowsToContents()
            return
        actions = [
            {'label': 'Console', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Remove', 'bg_color': '#d9534f', 'txt_color': 'white'},
            {'label': 'Outputs', 'bg_color': '#3cb3c5', 'txt_color': 'white'},
            {'label': 'Run Risk', 'bg_color': 'white', 'txt_color': 'black'}
        ]
        self.calc_list_tbl.clearContents()
        self.calc_list_tbl.setRowCount(len(calc_list))
        self.calc_list_tbl.setColumnCount(len(selected_keys) + len(actions))
        for row, calc in enumerate(calc_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                value = calc_list[row][key]
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
                # do not display 'Run Risk' button, if this is already a risk
                # calculation or if the calculation is still incomplete
                if action['label'] == 'Run Risk':
                    if (calc['job_type'] == 'risk'
                            or calc['status'] != 'complete'):
                        continue
                # do not display the button for outputs until calc is complete
                elif action['label'] == 'Outputs':
                    if calc['status'] != 'complete':
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
        empty_col_names = [''] * len(actions)
        headers = col_names + empty_col_names
        self.calc_list_tbl.setHorizontalHeaderLabels(headers)
        self.calc_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.calc_list_tbl.resizeColumnsToContents()
        self.calc_list_tbl.resizeRowsToContents()
        return True

    def clear_output_list(self):
        self.output_list_tbl.clearContents()
        self.output_list_tbl.setRowCount(0)
        self.output_list_tbl.setColumnCount(0)

    def on_calc_action_btn_clicked(self, calc_id, action):
        if action == 'Console':
            calc_log = self.get_calc_log(calc_id)
            log_msg(calc_log, tag='Calculation %s' % calc_id)
            logDock = self.iface.mainWindow().findChild(QDockWidget,
                                                        'MessageLog')
            logDock.show()
        elif action == 'Remove':
            self.remove_calc(calc_id)
            if (self.current_output_calc_id is not None
                    and self.current_output_calc_id == calc_id):
                self.clear_output_list()
        elif action == 'Outputs':
            output_list = self.get_output_list(calc_id)
            self.list_of_outputs_lbl.setText(
                'List of outputs for calculation %s' % calc_id)
            self.clear_output_list()
            self.show_output_list(output_list)
            self.download_datastore_btn.setEnabled(True)
            self.download_datastore_btn.setText(
                'Download HDF5 datastore for calculation %s'
                % self.current_output_calc_id)
        elif action == 'Run Risk':
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
        with WaitCursorManager(
                'Getting log for output %s...' % calc_id, self.iface):
            try:
                # FIXME: enable the user to set verify=True
                resp = self.session.get(calc_log_url, timeout=10, verify=False)
            except HANDLED_EXCEPTIONS as exc:
                self._handle_exception(exc)
                return
            calc_log = json.loads(resp.text)
            self.calc_log_line[calc_id] = start + len(calc_log)
            return '\n'.join([','.join(row) for row in calc_log])

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

    def run_calc(self, calc_id=None):
        """
        Run a calculation. If `calc_id` is given, it means we want to run
        a risk calculation re-using the output of the given hazard calculation
        """
        text = self.tr('Select the files needed to run the calculation,'
                       ' or the zip archive containing those files.')
        default_dir = QSettings().value('irmt/run_oqengine_calc_dir',
                                        QDir.homePath())
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
        else:
            log_msg(resp.text, level='C', message_bar=self.iface.messageBar())

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

    def get_output_list(self, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (self.hostname, calc_id)
        with WaitCursorManager('Getting list of outputs...', self.iface):
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

    def show_output_list(self, output_list):
        if not output_list:
            self.clear_output_list()
            self.download_datastore_btn.setEnabled(False)
            self.download_datastore_btn.setText('Download HDF5 datastore')
            return
        exclude = ['url', 'outtypes']
        selected_keys = [key for key in sorted(output_list[0].keys())
                         if key not in exclude]
        max_actions = 0
        has_hmaps = False
        has_hcurves = False
        has_gmf_data = False
        has_uhs = False
        has_dmg_by_asset = False
        for row in output_list:
            if row['type'] == 'hmaps':
                has_hmaps = True
            if row['type'] == 'hcurves':
                has_hcurves = True
            if row['type'] == 'gmf_data':
                has_gmf_data = True
            if row['type'] == 'uhs':
                has_uhs = True
            if row['type'] == 'dmg_by_asset':
                has_dmg_by_asset = True
            num_actions = len(row['outtypes'])
            if num_actions > max_actions:
                max_actions = num_actions
        if (has_hmaps or has_hcurves or has_gmf_data or has_uhs or
                has_dmg_by_asset):
            max_actions += 1
        else:
            if has_dmg_by_asset:
                max_actions += 1
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
            if output['type'] in [
                    'hmaps', 'hcurves', 'gmf_data', 'uhs', 'dmg_by_asset']:
                action = 'Load as shapefile'
                button = QPushButton()
                self.connect_button_to_action(
                    button, action, output, outtype)
                self.output_list_tbl.setCellWidget(row, col + 1, button)
        col_names = [key.capitalize() for key in selected_keys]
        empty_col_names = ['' for outtype in range(max_actions)]
        headers = col_names + empty_col_names
        self.output_list_tbl.setHorizontalHeaderLabels(headers)
        self.output_list_tbl.horizontalHeader().setStyleSheet(
            "font-weight: bold;")
        self.output_list_tbl.resizeColumnsToContents()
        self.output_list_tbl.resizeRowsToContents()

    def connect_button_to_action(self, button, action, output, outtype):
        if action == 'Load as shapefile':
            style = 'background-color: blue; color: white;'
            button.setText("Load %s as shapefile" % outtype)
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
        if action == 'Load as shapefile':
            dest_folder = tempfile.gettempdir()
            if outtype == 'npz':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                dlg = LoadNpzAsLayerDialog(self.iface, output_type, filepath)
                dlg.exec_()
            elif outtype == 'geojson':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                dlg = LoadGeoJsonAsLayerDialog(self.iface, filepath)
                dlg.exec_()
            elif outtype == 'csv':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                dlg = LoadCsvAsLayerDialog(self.iface, filepath)
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
        self.timer.start(4000)  # refresh calc list time in milliseconds

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
