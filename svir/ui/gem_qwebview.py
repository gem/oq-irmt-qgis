# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2017-08-30
        copyright            : (C) 2017 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
"""


from qgis.PyQt.QtWebKit import QWebView, QWebPage
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl

# # uncomment to turn on developer tools in webkit so we can get at the
# # javascript console for debugging (it causes segfaults in tests, so it has
# # to be kept disabled while it is not used for debugging).
# from qgis.PyQt.QtWebKit import QWebSettings
# QWebSettings.globalSettings().setAttribute(
#     QWebSettings.DeveloperExtrasEnabled, True)


class GemQWebView(QWebView):

    def __init__(self, gem_header_name, gem_header_value, python_api,
                 message_bar):
        self.gem_header_name = gem_header_name
        self.gem_header_value = gem_header_value
        self.python_api = python_api
        self.message_bar = message_bar

        super(GemQWebView, self).__init__()

        self.clickpos = None

        self.frame = self.page().mainFrame()
        # javaScriptWindowObjectCleared is emitted whenever the global window
        # object of the JavaScript environment is cleared, e.g., before
        # starting a new load. If you intend to add QObjects to a QWebFrame
        # using addToJavaScriptWindowObject(), you should add them in a slot
        # connected to this signal. This ensures that your objects remain
        # accessible when loading new URLs.
        self.frame.javaScriptWindowObjectCleared.connect(self.load_python_api)

        # NOTE: without the following line, linkClicked is not emitted, but
        # we would need to delegate only one specific link!
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        self.page().linkClicked.connect(self.on_linkClicked)
        open_link_action = self.pageAction(QWebPage.OpenLink)
        open_link_action.triggered.disconnect()
        open_link_action.triggered.connect(self.on_OpenLink)
        open_in_new_win_action = self.pageAction(
            QWebPage.OpenLinkInNewWindow)
        open_in_new_win_action.triggered.disconnect()
        open_in_new_win_action.triggered.connect(
            self.on_OpenLinkInNewWindow)
        self.urlChanged[QUrl].connect(self.on_urlChanged)

        self.page().linkHovered.connect(self.on_linkHovered)

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

    def build_request(self, qurl):
        request = QNetworkRequest()
        request.setUrl(qurl)
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request

    def load_python_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('pyapi', self.python_api)

    def on_linkClicked(self, url):
        request = self.build_request(url)
        self.load(request)
        # print('Downloaded file:')
        # resp = requests.get(url.toString())
        # print(resp.content)

    def on_OpenLink(self):
        print('OpenLink')
        main_frame = self.page().mainFrame()
        qurl = main_frame.hitTestContent(self.clickpos).linkUrl()
        request = self.build_request(qurl)
        self.load(request)

    def on_OpenLinkInNewWindow(self):
        self.message_bar.pushMessage(
            'The requested functionality is disabled. Please use the IPT'
            ' application in a single window.')

    def on_urlChanged(self, url):
        pass
        # print(url)

    def on_linkHovered(self, link, title, text_content):
        pass
        # print(link)
