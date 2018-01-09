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
from shutil import copyfile
from qgis.PyQt.QtGui import QPushButton, QLineEdit, QHBoxLayout, QFileDialog
from qgis.PyQt.QtCore import QUrl, pyqtSlot, QSettings, QDir, QFileInfo
from qgis.PyQt.QtNetwork import QNetworkRequest, QHttpMultiPart, QHttpPart
from svir.dialogs.standalone_app_dialog import StandaloneAppDialog, GemApi
from svir.utilities.shared import DEBUG, REQUEST_ATTRS


class IptDialog(StandaloneAppDialog):
    """
    Dialog that embeds the OpenQuake Input Modelling Toolkit
    standalone application
    """

    def __init__(self, ipt_dir, irmt, parent=None):
        self.irmt = irmt
        self.ipt_dir = ipt_dir
        app_name = 'ipt'
        app_descr = 'OpenQuake Input Preparation Toolkit'
        gem_header_name = "Gem--Qgis-Oq-Irmt--Ipt"
        gem_header_value = "0.1.0"
        super(IptDialog, self).__init__(
            app_name, app_descr, gem_header_name, gem_header_value, parent)
        self.gem_api = IptPythonApi(self.message_bar, self)
        self.build_gui()

    def build_gui(self):
        super(IptDialog, self).build_gui()
        if DEBUG:
            self.set_example_btn = QPushButton("Set example")
            self.set_example_btn.clicked.connect(
                self.on_set_example_btn_clicked)
            ipt_example = '%s/%s?tab_id=1&subtab_id=0&example_id=99' % (
                self.host, self.app_name)
            self.example_url = QLineEdit(ipt_example)
            self.hlayout = QHBoxLayout()
            self.hlayout.addWidget(self.example_url)
            self.hlayout.addWidget(self.set_example_btn)
            self.vlayout.addLayout(self.hlayout)

    def on_set_example_btn_clicked(self):
        qurl = QUrl(self.example_url.text())
        self.web_view.load(qurl)


class IptPythonApi(GemApi):
    """
    API methods that are specific for the IPT application
    (other shared methods are defined in the CommonApi)
    """

    @pyqtSlot(result='QVariantMap')
    def select_file(self):
        """
        Open a file browser to select a single file in the ipt_dir,
        and return the name of the selected files
        """
        try:
            ipt_dir = self.parent().ipt_dir
            file_name = QFileDialog.getOpenFileName(
                self.parent().parent(), 'Select file', ipt_dir)
            basename = os.path.basename(file_name)
        except Exception as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': basename, 'reason': 'ok'}

    @pyqtSlot(result='QVariantMap')
    def select_files(self):
        """
        Open a file browser to select multiple files in the ipt_dir,
        and return the list of names of selected files
        """
        try:
            ipt_dir = self.parent().ipt_dir
            file_names = QFileDialog.getOpenFileNames(
                self.parent().parent(), 'Select files', ipt_dir)
            ls = [os.path.basename(file_name) for file_name in file_names]
        except Exception as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': ls, 'reason': 'ok'}

    @pyqtSlot(result='QVariantMap')
    def select_and_copy_files_to_ipt_dir(self):
        """
        Open a file browser pointing to the most recently browsed directory,
        where multiple files can be selected. The selected files will be
        copied inside the ipt_dir
        """
        try:
            default_dir = QSettings().value('irmt/ipt_browsed_dir',
                                            QDir.homePath())
            text = 'The selected files will be copied to the ipt directory'
            file_paths = QFileDialog.getOpenFileNames(
                self.parent().parent(), text, default_dir)
            if not file_paths:
                return {'ret': 1, 'reason': 'No file was selected'}
            selected_dir = QFileInfo(file_paths[0]).dir().path()
            QSettings().setValue('irmt/ipt_browsed_dir', selected_dir)
            ipt_dir = self.parent().ipt_dir
            for file_path in file_paths:
                basename = os.path.basename(file_path)
                copyfile(file_path, os.path.join(ipt_dir, basename))
        except Exception as exc:
            return {'ret': 2, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    @pyqtSlot(str, str, result='QVariantMap')
    def save_str_to_file(self, content, file_name):
        """
        :param content: string to be saved in the file
        :param file_name: basename of the file to be saved into the ipt_dir
        """
        ipt_dir = self.parent().ipt_dir
        try:
            basename = os.path.basename(file_name)
            with open(os.path.join(ipt_dir, basename), "w") as f:
                f.write(content)
        except Exception as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    @pyqtSlot(result='QVariantMap')
    def ls_ipt_dir(self):
        ipt_dir = self.parent().ipt_dir
        try:
            ls = os.listdir(ipt_dir)
        except OSError as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': ls, 'reason': 'ok'}

    @pyqtSlot(str, result='QVariantMap')
    def rm_file_from_ipt_dir(self, file_name):
        """
        :param file_name: name of the file to be removed from the ipt_dir
        """
        ipt_dir = self.parent().ipt_dir
        basename = os.path.basename(file_name)
        file_path = os.path.join(ipt_dir, basename)
        try:
            os.remove(file_path)
        except OSError as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    @pyqtSlot(str, str, result='QVariantMap')
    def rename_file_in_ipt_dir(self, old_name, new_name):
        """
        :param old_name: name of the file to be renamed
        :param new_name: new name to be assigned to the file
        """
        ipt_dir = self.parent().ipt_dir
        old_basename = os.path.basename(old_name)
        new_basename = os.path.basename(new_name)
        old_path = os.path.join(ipt_dir, old_basename)
        new_path = os.path.join(ipt_dir, new_basename)
        try:
            os.rename(old_path, new_path)
        except OSError as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    @pyqtSlot('QStringList', result='QVariantMap')
    def run_oq_engine_calc(self, file_names):
        """
        It opens the dialog showing the list of calculations on the engine
        server, and automatically runs an oq-engine calculation, given a list
        of input files to be collected from the ipt_dir
        :param file_names: list of names of the input files
        :returns: a dict with a return value and a possible reason of failure
        """
        file_names = file_names if file_names else None
        try:
            self.parent().irmt.drive_oq_engine_server()
            drive_engine_dlg = self.parent().irmt.drive_oq_engine_server_dlg
            drive_engine_dlg.run_calc(file_names=file_names,
                                      directory=self.parent().ipt_dir)
        except Exception as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    # javascript objects come into python as dictionaries
    @pyqtSlot(str, str, 'QVariantList', 'QVariantList', str, str, result=bool)
    def delegate_download(self, action_url, method, headers, data,
                          js_cb_func, js_cb_object_id):
        """
        :param action_url: url to call on ipt api
        :param method: string like 'POST'
        :param headers: list of strings
        :param data: list of dictionaries {name (string) value(string)}
        :param delegate_download_js_cb: javascript callback
        :param js_cb_object_id: id of the javascript object to be called back
        """
        # TODO: Accept also methods other than POST
        if method != 'POST':
            self.call_js_cb(js_cb_func, js_cb_object_id, None, 1,
                            'Method %s not allowed' % method)
            return False
        if ':' in action_url:
            qurl = QUrl(action_url)
        elif action_url.startswith('/'):
            qurl = QUrl("%s%s" % (self.parent().host, action_url))
        else:
            url = "%s/%s" % (
                '/'.join([str(x) for x in self.parent().web_view.url(
                         ).toEncoded().split('/')[:-1]]), action_url)
            qurl = QUrl(url)
        manager = self.parent().web_view.page().networkAccessManager()
        request = QNetworkRequest(qurl)
        request.setAttribute(REQUEST_ATTRS['instance_finished_cb'],
                             self.manager_finished_cb)
        request.setAttribute(REQUEST_ATTRS['js_cb_object_id'],
                             js_cb_object_id)
        request.setAttribute(REQUEST_ATTRS['js_cb_func'],
                             js_cb_func)
        for header in headers:
            request.setRawHeader(header['name'], header['value'])
        multipart = QHttpMultiPart(QHttpMultiPart.FormDataType)
        for d in data:
            part = QHttpPart()
            part.setHeader(QNetworkRequest.ContentDispositionHeader,
                           "form-data; name=\"%s\"" % d['name'])
            part.setBody(d['value'])
            multipart.append(part)
        reply = manager.post(request, multipart)
        # NOTE: needed to avoid segfault!
        multipart.setParent(reply)  # delete the multiPart with the reply
        return True

    def manager_finished_cb(self, reply):
        file_name = None
        js_cb_object_id = reply.request().attribute(
            REQUEST_ATTRS['js_cb_object_id'], None)
        js_cb_func = reply.request().attribute(
            REQUEST_ATTRS['js_cb_func'], None)
        if js_cb_object_id is None or js_cb_object_id is None:
            self.call_js_cb(js_cb_func, js_cb_object_id, file_name, 2,
                            'Unable to extract attributes from request')
            return
        content_disposition = reply.rawHeader('Content-Disposition')
        # expected format: 'attachment; filename="exposure_model.xml"'
        # sanity check
        if 'filename' not in content_disposition:
            self.call_js_cb(js_cb_func, js_cb_object_id, file_name, 4,
                            'File name not found')
            return
        file_name = str(content_disposition.split('"')[1])
        file_content = str(reply.readAll())
        ipt_dir = self.parent().ipt_dir
        with open(os.path.join(ipt_dir, file_name), "w") as f:
            f.write(file_content)
        self.call_js_cb(js_cb_func, js_cb_object_id, file_name, 0)

    def call_js_cb(self, js_cb_func, js_cb_object_id, file_name,
                   success=1, reason='ok'):
        js_to_call = '%s("%s", "%s", %d, "%s");' % (
            js_cb_func, js_cb_object_id, file_name, success, reason)
        frame = self.parent().web_view.page().mainFrame()
        frame.evaluateJavaScript(js_to_call)
