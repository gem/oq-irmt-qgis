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


from qgis.PyQt.QtWebKit import QWebView, QWebSettings
from qgis.PyQt.QtNetwork import (QNetworkAccessManager,
                                 QNetworkCookieJar,
                                 QNetworkCookie,
                                 )
from qgis.PyQt.QtCore import QMutex, QMutexLocker, QSettings, QByteArray

# # uncomment to turn on developer tools in webkit so we can get at the
# # javascript console for debugging (it causes segfaults in tests, so it has
# # to be kept disabled while it is not used for debugging).
# QWebSettings.globalSettings().setAttribute(
#     QWebSettings.DeveloperExtrasEnabled, True)


class GemQWebView(QWebView):

    def __init__(self, gem_header_name, gem_header_value, gem_api):
        self.gem_header_name = gem_header_name
        self.gem_header_value = gem_header_value
        self.gem_api = gem_api

        super(GemQWebView, self).__init__()

        self.page().setNetworkAccessManager(GemQNetworkAccessManager(self))
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
        self.frame.javaScriptWindowObjectCleared.connect(self.load_gem_api)

    def load_gem_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('gem_api', self.gem_api)

    # on window.open(link), force window.open(link, "_self")
    # i.e., open all links in the same page
    def createWindow(self, window_type):
        return self

    def add_header_to_request(self, request):
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request


class GemQNetworkAccessManager(QNetworkAccessManager):

    def __init__(self, parent=None):
        super(GemQNetworkAccessManager, self).__init__(parent)
        self.setCookieJar(PersistentCookieJar())

    def createRequest(self, op, req, outgoingData):
        req = self.parent().add_header_to_request(req)
        return super(GemQNetworkAccessManager, self).createRequest(
            op, req, outgoingData)


# Inspired by:
# https://stackoverflow.com/questions/13971787/how-do-i-save-cookies-with-qt
class PersistentCookieJar(QNetworkCookieJar):
    mutex = QMutex()

    def __init__(self, parent=None):
        super(PersistentCookieJar, self).__init__(parent)
        self.load()

    def cookiesForUrl(self, *args, **kwargs):
        return super(PersistentCookieJar, self).cookiesForUrl(*args, **kwargs)

    def setCookiesFromUrl(self, *args, **kwargs):
        ret_val = super(PersistentCookieJar, self).setCookiesFromUrl(
            *args, **kwargs)
        self.save()
        return ret_val

    def save(self):
        with QMutexLocker(self.mutex):
            cookies = self.allCookies()
            data = QByteArray()
            for cookie in cookies:
                if not cookie.isSessionCookie():
                    data.append(cookie.toRawForm())
                    data.append("\n")
            QSettings().setValue("Cookies", data)

    def load(self):
        with QMutexLocker(self.mutex):
            data = QSettings().value("Cookies")
            cookies = QNetworkCookie.parseCookies(data)
            self.setAllCookies(cookies)
