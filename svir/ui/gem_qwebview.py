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
from qgis.PyQt.QtCore import (QMutex,
                              QMutexLocker,
                              QSettings,
                              QByteArray,
                              pyqtSlot,
                              )
from qgis.PyQt.QtGui import QSizePolicy
from svir.utilities.shared import DEBUG, REQUEST_ATTRS


if DEBUG:
    # turn on developer tools in webkit so we can get at the
    # javascript console for debugging (it causes segfaults in tests, so it has
    # to be kept disabled while it is not used for debugging).
    QWebSettings.globalSettings().setAttribute(
        QWebSettings.DeveloperExtrasEnabled, True)


class GemQWebView(QWebView):
    """
    A modified version of QWebView, that adds to the embedded web pages a
    header that contains information about the version of the interface between
    the plugin and the standalone gem application that is embedded.
    Whenever the global window object of the Javascript environment is cleared,
    a Python API is made available to be called from the web page.

    :param gem_header_name: a name like "Gem--Qgis-Oq-Irmt--Ipt", describing
        the applications that are interacting (the plugin and the web app)
    :param gem_header_value: the version of the API, like "0.1.0"
    :param gem_api: the python API that can be used from Javascript to drive
        the QGIS GUI
    """

    def __init__(self, gem_header_name, gem_header_value, gem_api,
                 parent=None):
        self.parent = parent
        self.gem_header_name = gem_header_name
        self.gem_header_value = gem_header_value
        self.gem_api = gem_api

        super(GemQWebView, self).__init__(parent=parent)

        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,
                                       QSizePolicy.MinimumExpanding))
        manager = GemQNetworkAccessManager(self)
        self.page().setNetworkAccessManager(manager)
        manager.finished.connect(self.manager_finished_cb)
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

        # catch the signal emitted when the title of the page is changed
        self.titleChanged[str].connect(self.on_title_changed)

    def load_gem_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('gem_api', self.gem_api)

    def manager_finished_cb(self, reply):
        instance_finished_cb = reply.request().attribute(
            REQUEST_ATTRS['instance_finished_cb'], None)
        if instance_finished_cb is not None:
            instance_finished_cb(reply)

    @pyqtSlot(str)
    def on_title_changed(self, title):
        # get the changed title of the web page and set the window title of the
        # parent widget to the same string
        self.parent.setWindowTitle(title)

    # on window.open(link), force window.open(link, "_self")
    # i.e., open all links in the same page
    def createWindow(self, window_type):
        return self

    def add_header_to_request(self, request):
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request


class GemQNetworkAccessManager(QNetworkAccessManager):
    """
    A modified version of QNetworkAccessManager, that adds a header to each
    request and that uses a persistent cookie jar.
    """

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
    """
    A modified version of QNetworkCookieJar, that saves and loads cookies
    to/from a permanent storage (using QSettings as storage infrastructure)
    """

    mutex = QMutex()

    def __init__(self, parent=None):
        super(PersistentCookieJar, self).__init__(parent)
        self.load_cookies()

    def setCookiesFromUrl(self, *args, **kwargs):
        ret_val = super(PersistentCookieJar, self).setCookiesFromUrl(
            *args, **kwargs)
        self.save_cookies()
        return ret_val

    def save_cookies(self):
        with QMutexLocker(self.mutex):
            cookies = self.allCookies()
            data = QByteArray()
            for cookie in cookies:
                if not cookie.isSessionCookie():
                    data.append(cookie.toRawForm())
                    data.append("\n")
            QSettings().setValue("irmt/cookies", data)

    def load_cookies(self):
        with QMutexLocker(self.mutex):
            data = QSettings().value("irmt/cookies", "")
            cookies = QNetworkCookie.parseCookies(data)
            self.setAllCookies(cookies)
