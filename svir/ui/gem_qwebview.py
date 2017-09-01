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


from qgis.PyQt.QtWebKit import QWebView, QWebPage, QWebSettings
# from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkAccessManager
# from qgis.PyQt.QtCore import QUrl

# # uncomment to turn on developer tools in webkit so we can get at the
# # javascript console for debugging (it causes segfaults in tests, so it has
# # to be kept disabled while it is not used for debugging).
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

        self.webpage = QWebPage()
        self.network_access_manager = GemQNetworkAccessManager(self)
        self.setPage(self.webpage)
        self.webpage.setNetworkAccessManager(self.network_access_manager)
        self.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        self.settings().setAttribute(
            QWebSettings.JavascriptCanOpenWindows, True)

        self.frame = self.page().mainFrame()
        # javaScriptWindowObjectCleared is emitted whenever the global window
        # object of the JavaScript environment is cleared, e.g., before
        # starting a new load. If you intend to add QObjects to a QWebFrame
        # using addToJavaScriptWindowObject(), you should add them in a slot
        # connected to this signal. This ensures that your objects remain
        # accessible when loading new URLs.
        self.frame.javaScriptWindowObjectCleared.connect(self.load_python_api)

    def load_python_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('pyapi', self.python_api)

    # on window.open(link), force window.open(link, "_self")
    # i.e., open all links in the same page
    def createWindow(self, window_type):
        return self

    def add_header_to_request(self, request):
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request


class GemQNetworkAccessManager(QNetworkAccessManager):

    def createRequest(self, op, req, outgoingData):
        req = self.parent().add_header_to_request(req)
        return super(GemQNetworkAccessManager, self).createRequest(
            op, req, outgoingData)
