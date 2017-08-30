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
from qgis.PyQt.QtWebKit import QWebPage
# from qgis.PyQt.QtWebKit import QWebSettings  # uncomment for debugging
from qgis.PyQt.QtWebKit import QWebView
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QObject, pyqtSlot
from qgis.PyQt.QtGui import (QDialog,
                             QDialogButtonBox,
                             QVBoxLayout,
                             QPushButton,
                             )
from svir.third_party import requests

# uncomment to turn on developer tools in webkit so we can get at the
# javascript console for debugging (it causes segfaults in tests, so it has to
# be kept disabled while it is not used for debugging).
# QWebSettings.globalSettings().setAttribute(
#     QWebSettings.DeveloperExtrasEnabled, True)


class IptDialog(QDialog):
    """FIXME Docstring for IptDialog. """

    def __init__(self, message_bar):
        super(IptDialog, self).__init__()
        self.gem_header_name = "Gem--Oq-Irmt-Qgis--Ipt"
        self.gem_header_value = "0.1.0"
        self.web_view = GemQWebView(self.gem_header_name,
                                    self.gem_header_value)
        self.set_example_btn = QPushButton("Set example")
        self.set_example_btn.clicked.connect(self.on_set_example_btn_clicked)
        self.get_nrml_btn = QPushButton("Get nrml")
        self.get_nrml_btn.clicked.connect(self.on_get_nrml_btn_clicked)
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.on_back_btn_clicked)
        self.buttonBox = QDialogButtonBox()
        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.web_view)
        self.vlayout.addWidget(self.set_example_btn)
        self.vlayout.addWidget(self.get_nrml_btn)
        self.vlayout.addWidget(self.back_btn)
        self.vlayout.addWidget(self.buttonBox)
        self.setLayout(self.vlayout)
        self.setWindowTitle("Input Preparation Toolkit")

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.message_bar = message_bar
        qurl = QUrl(
            # FIXME: loading a page that offers a link to download a small txt
            # 'http://www.sample-videos.com/download-sample-text-file.php')
            # 'https://platform.openquake.org/ipt')
            'http://localhost:8800/ipt?tab_id=1&example_id=99')
        request = self.build_request(qurl)
        self.web_view.load(request)
        self.api = PythonAPI(self.message_bar)
        self.frame = self.web_view.page().mainFrame()

        # javaScriptWindowObjectCleared is emitted whenever the global window
        # object of the JavaScript environment is cleared, e.g., before
        # starting a new load. If you intend to add QObjects to a QWebFrame
        # using addToJavaScriptWindowObject(), you should add them in a slot
        # connected to this signal. This ensures that your objects remain
        # accessible when loading new URLs.
        self.frame.javaScriptWindowObjectCleared.connect(self.load_api)

        # downloadRequested(QNetworkRequest) is a signal that is triggered in
        # the web page when the user right-clicks on a link and chooses "save
        # link as". Instead of proceeding with the normal workflow (asking the
        # user where to save the file) the control is passed to
        # self.handle_downhandle_downloadRequested, that retrieves the file and
        # prints its contents
        self.web_view.page().downloadRequested.connect(
            self.handle_downloadRequested)

        # NOTE: without the following line, linkClicked is not emitted, but
        # we would need to delegate only one specific link!
        self.web_view.page().setLinkDelegationPolicy(
            QWebPage.DelegateAllLinks)
        self.web_view.page().linkClicked.connect(self.handle_linkClicked)
        # self.web_view.page().OpenLink.connect(self.handle_OpenLink)
        open_link_action = self.web_view.pageAction(QWebPage.OpenLink)
        open_link_action.triggered.disconnect()
        open_link_action.triggered.connect(self.handle_OpenLink)
        open_in_new_win_action = self.web_view.pageAction(
            QWebPage.OpenLinkInNewWindow)
        open_in_new_win_action.triggered.disconnect()
        open_in_new_win_action.triggered.connect(
            self.handle_OpenLinkInNewWindow)
        self.web_view.urlChanged[QUrl].connect(self.handle_urlChanged)

        self.web_view.page().linkHovered.connect(self.handle_linkHovered)

    def load_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('pyapi', self.api)

    def handle_downloadRequested(self, request):
        print('Downloaded file:')
        resp = requests.get(request.url().toString())
        print(resp.content)

    def handle_linkClicked(self, url):
        request = self.build_request(url)
        self.web_view.load(request)
        # print('Downloaded file:')
        # resp = requests.get(url.toString())
        # print(resp.content)

    def handle_OpenLink(self):
        print('OpenLink')
        main_frame = self.web_view.page().mainFrame()
        qurl = main_frame.hitTestContent(self.web_view.clickpos).linkUrl()
        request = self.build_request(qurl)
        self.web_view.load(request)

    def handle_OpenLinkInNewWindow(self):
        self.message_bar.pushMessage(
            'The requested functionality is disabled. Please use the IPT'
            ' application in a single window.')

    def handle_urlChanged(self, url):
        pass
        # print(url)

    def handle_linkHovered(self, link, title, text_content):
        pass
        # print(link)

    def on_set_example_btn_clicked(self):
        qurl = QUrl(
            'http://localhost:8800/ipt?tab_id=1&example_id=99')
        request = self.build_request(qurl)
        self.web_view.load(request)

    def on_get_nrml_btn_clicked(self):
        main_frame = self.web_view.page().mainFrame()
        nrml_textarea = main_frame.findFirstElement("#textareaex")
        nrml = nrml_textarea.evaluateJavaScript("this.value")
        print(nrml)

    def on_back_btn_clicked(self):
        self.web_view.back()

    def build_request(self, qurl):
        request = QNetworkRequest()
        request.setUrl(qurl)
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request


class PythonAPI(QObject):

    def __init__(self, message_bar):
        super(PythonAPI, self).__init__()
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


class GemQWebView(QWebView):

    def __init__(self, gem_header_name, gem_header_value):
        self.gem_header_name = gem_header_name
        self.gem_header_value = gem_header_value
        self.clickpos = None
        super(GemQWebView, self).__init__()

    def load(self, *args, **kwargs):
        print("FIXME Inside GemQWebView.load")
        super(GemQWebView, self).load(*args, **kwargs)

    # def load(self, url_request, operation=QNetworkAccessManager.GetOperation,
    #          body=QByteArray()):
    #     if isinstance(url_request, QUrl):
    #         request = self.build_request(url_request)
    #     elif isinstance(url_request, QNetworkRequest):
    #         request = self.build_header(url_request)
    #     else:
    #         raise TypeError(
    #             "load accepts a QUrl or a QNetworkRequest; got %s instead."
    #             % type(url_request))
    #     super(GemQWebView, self).load(request, operation, body)

    # def acceptNavigationRequest(self, frame, request, type):
    #     print('Navigation Request:', request.url())
    #     return False

    def contextMenuEvent(self, event):
        self.clickpos = event.pos()
        super(GemQWebView, self).contextMenuEvent(event)

    # def build_request(self, qurl):
    #     request = QNetworkRequest()
    #     request.setUrl(qurl)
    #     request = request.setRawHeader(self.gem_header_name,
    #                                    self.gem_header_value)
    #     return request
