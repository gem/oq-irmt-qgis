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

import json
from qgis.PyQt.QtCore import QUrl, QObject, pyqtSlot
from qgis.PyQt.QtGui import (QDialog,
                             QDialogButtonBox,
                             QVBoxLayout,
                             QPushButton,
                             QSizePolicy,
                             )
from qgis.gui import QgsMessageBar
from svir.third_party import requests
from svir.ui.gem_qwebview import GemQWebView


class StandaloneAppDialog(QDialog):
    """FIXME Docstring for StandaloneAppDialog. """

    def __init__(self, app_name, app_descr):
        super(StandaloneAppDialog, self).__init__()

        self.message_bar = QgsMessageBar(self)
        self.app_name = app_name
        self.app_descr = app_descr
        if app_name == 'ipt':
            self.python_api = IptPythonApi(self.message_bar)
            self.gem_header_name = "Gem--Oq-Irmt-Qgis--Ipt"
            self.gem_header_value = "0.1.0"
        elif app_name == 'taxtweb':
            self.python_api = TaxtwebPythonApi(self.message_bar)
            self.gem_header_name = "Gem--Oq-Irmt-Qgis--Taxtweb"
            self.gem_header_value = "0.1.0"
        elif app_name == 'taxonomy':
            self.python_api = TaxonomyPythonApi(self.message_bar)
            self.gem_header_name = "Gem--Oq-Irmt-Qgis--Taxonomy"
            self.gem_header_value = "0.1.0"
        else:
            raise NotImplementedError(app_name)

        self.resize(1200, self.width())
        self.web_view = GemQWebView(self.gem_header_name,
                                    self.gem_header_value,
                                    self.python_api,
                                    self.message_bar)
        self.web_view.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,
                                                QSizePolicy.MinimumExpanding))
        self.set_example_btn = QPushButton("Set example")
        self.set_example_btn.clicked.connect(self.on_set_example_btn_clicked)
        # self.get_nrml_btn = QPushButton("Get nrml")
        # self.get_nrml_btn.clicked.connect(self.on_get_nrml_btn_clicked)
        self.buttonBox = QDialogButtonBox()
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.message_bar)
        self.vlayout.addWidget(self.web_view)
        if app_name == 'ipt':
            self.vlayout.addWidget(self.set_example_btn)
        # self.vlayout.addWidget(self.get_nrml_btn)
        self.vlayout.addWidget(self.buttonBox)
        self.setLayout(self.vlayout)
        self.setWindowTitle(self.app_descr)

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        qurl = QUrl(
            # FIXME: loading a page that offers a link to download a small txt
            # 'http://www.sample-videos.com/download-sample-text-file.php')
            # 'https://platform.openquake.org/ipt')
            'http://localhost:8800/%s' % self.app_name)
        self.web_view.load(qurl)

        # downloadRequested(QNetworkRequest) is a signal that is triggered in
        # the web page when the user right-clicks on a link and chooses "save
        # link as". Instead of proceeding with the normal workflow (asking the
        # user where to save the file) the control is passed to
        # self.on_downloadRequested, that retrieves the file and
        # prints its contents
        self.web_view.page().downloadRequested.connect(
            self.on_downloadRequested)

    def on_downloadRequested(self, request):
        print('Downloaded file:')
        resp = requests.get(request.url().toString())
        print(resp.content)

    def on_set_example_btn_clicked(self):
        qurl = QUrl(
            'http://localhost:8800/ipt?tab_id=1&example_id=99')
        self.web_view.load(qurl)

    # def on_get_nrml_btn_clicked(self):
    #     main_frame = self.web_view.page().mainFrame()
    #     nrml_textarea = main_frame.findFirstElement("#textareaex")
    #     nrml = nrml_textarea.evaluateJavaScript("this.value")
    #     print(nrml)


class IptPythonApi(QObject):

    def __init__(self, message_bar):
        super(IptPythonApi, self).__init__()
        self.message_bar = message_bar

    @pyqtSlot(int, int, result=int)
    def add(self, a, b):
        return a + b

    @pyqtSlot()
    def notify_click(self):
        self.message_bar.pushMessage('Clicked!')

    # take a list of strings and return a string
    # because of setapi line above, we get a list of python strings as input
    @pyqtSlot('QStringList', result=str)
    def concat(self, strlist):
        return ''.join(strlist)

    # take a javascript object and return string
    # javascript objects come into python as dictionaries
    # functions are represented by an empty dictionary
    @pyqtSlot('QVariantMap', result=str)
    def json_encode(self, jsobj):
        # import is here to keep it separate from 'required' import
        return json.dumps(jsobj)

    # take a string and return an object (which is represented in python
    # by a dictionary
    @pyqtSlot(str, result='QVariantMap')
    def json_decode(self, jsstr):
        return json.loads(jsstr)


class TaxtwebPythonApi(QObject):
    def __init__(self, message_bar):
        super(TaxtwebPythonApi, self).__init__()
        self.message_bar = message_bar

    @pyqtSlot()
    def notify_click(self):
        self.message_bar.pushMessage('Clicked!')


class TaxonomyPythonApi(QObject):
    def __init__(self, message_bar):
        super(TaxonomyPythonApi, self).__init__()
        self.message_bar = message_bar

    @pyqtSlot()
    def notify_click(self):
        self.message_bar.pushMessage('Clicked!')
