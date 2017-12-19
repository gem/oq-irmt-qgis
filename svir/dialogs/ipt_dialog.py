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
from qgis.PyQt.QtGui import QPushButton, QLineEdit, QHBoxLayout, QFileDialog
from qgis.PyQt.QtCore import QUrl, pyqtSlot
from qgis.PyQt.QtNetwork import QNetworkRequest, QHttpMultiPart, QHttpPart
from svir.dialogs.standalone_app_dialog import StandaloneAppDialog, GemApi
from svir.utilities.shared import DEBUG, REQUEST_ATTRS


class IptDialog(StandaloneAppDialog):
    """
    Dialog that embeds the OpenQuake Input Modelling Toolkit
    standalone application
    """

    def __init__(self, ipt_dir, parent=None):
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

    @pyqtSlot(result=str)
    def select_file(self):
        """
        Open a file browser to select a single file in the local filesystem,
        and return the name of the selected files
        """
        ipt_dir = self.parent().ipt_dir
        file_name = QFileDialog.getOpenFileName(
            self.parent().parent(), 'Select file', ipt_dir)
        return os.path.basename(file_name)

    @pyqtSlot(result='QStringList')
    def select_files(self):
        """
        Open a file browser to select multiple files in the local filesystem,
        and return the list of names of selected files
        """
        ipt_dir = self.parent().ipt_dir
        file_names = QFileDialog.getOpenFileNames(
            self.parent().parent(), 'Select files', ipt_dir)
        return [os.path.basename(file_name) for file_name in file_names]

    # javascript objects come into python as dictionaries
    @pyqtSlot(str, str, 'QVariantList', 'QVariantList', str, str, result=bool)
    def delegate_download(self, action_url, method, headers, data,
                          delegate_download_js_cb, js_cb_object_id):
        """
        :param action_url: url to call on ipt api
        :param method: string like 'POST'
        :param headers: list of strings
        :param data: list of dictionaries {name (string) value(string)}
        :param delegate_download_js_cb: javascript callback
        :param js_cb_object_id: id of the javascript object to be called back
        """
        # TODO: Accept also methods other than POST
        assert method == 'POST', method
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
        js_cb_object_id = reply.request().attribute(
            REQUEST_ATTRS['js_cb_object_id'], None)
        assert js_cb_object_id is not None  # sanity check
        content_type = reply.rawHeader('Content-Type')
        assert content_type == 'application/xml', content_type  # sanity check
        content_disposition = reply.rawHeader('Content-Disposition')
        # expected format: 'attachment; filename="exposure_model.xml"'
        # sanity check
        assert 'filename' in content_disposition, content_disposition
        file_name = str(content_disposition.split('"')[1])
        file_content = str(reply.readAll())
        ipt_dir = self.parent().ipt_dir
        with open(os.path.join(ipt_dir, file_name), "w") as f:
            f.write(file_content)
        frame = self.parent().web_view.page().mainFrame()
        frame.evaluateJavaScript(
            'manager_finished_cb("%s");' % js_cb_object_id)
