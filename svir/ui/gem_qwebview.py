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
from builtins import str

import os
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.PyQt.QtNetwork import (QNetworkAccessManager,
                                 QNetworkCookieJar,
                                 QNetworkCookie,
                                 )
from qgis.PyQt.QtCore import (
                              QMutex,
                              QSettings,
                              QByteArray,
                              pyqtSlot,
                              QUrl,
                              QMutexLocker,
                              )
from qgis.PyQt.QtWidgets import QSizePolicy, QFileDialog
from svir.utilities.shared import DEBUG, REQUEST_ATTRS
from svir.utilities.utils import (tr,
                                  create_progress_message_bar,
                                  clear_progress_message_bar,
                                  )


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

        self.urlChanged.connect(self.on_url_changed)
        self.page().linkHovered.connect(self.on_link_hovered)
        self.loadStarted.connect(self.on_load_started)
        self.loadProgress[int].connect(self.on_load_progress)
        self.loadFinished[bool].connect(self.on_load_finished)

        # catch the signal emitted when the title of the page is changed
        self.titleChanged[str].connect(self.on_title_changed)

        self.page().setForwardUnsupportedContent(True)
        self.page().unsupportedContent.connect(
            self.downloadContent)

        # NOTE: in case we need to download a link, we need also to catch the
        #       signal downloadRequested, as described in:
        # https://github.com/mwarning/PyQt4-Examples/blob/master/webftpclient/ftpview.py     # NOQA
        # https://github.com/mwarning/PyQt4-Examples/blob/master/webftpclient/downloader.py  # NOQA

    def load_gem_api(self):
        # add pyapi to javascript window object
        # slots can be accessed in either of the following ways -
        #   1.  var obj = window.pyapi.json_decode(json);
        #   2.  var obj = pyapi.json_decode(json)
        self.frame.addToJavaScriptWindowObject('gem_api', self.gem_api)

    def manager_finished_cb(self, reply):
        # whenever the network access manager finishes satisfying a request,
        # this function is called. If a callback function was associated with
        # the request, it is then called.
        instance_finished_cb = reply.request().attribute(
            REQUEST_ATTRS['instance_finished_cb'], None)
        if instance_finished_cb is not None:
            instance_finished_cb(reply)

    def downloadContent(self, reply):
        self.stop()
        home = os.path.expanduser('~')
        downloads = os.path.join(home, 'Downloads')
        download = os.path.join(home, 'Download')
        if os.path.isdir(downloads):
            dest_dir = downloads
        if os.path.isdir(download):
            dest_dir = download
        if not dest_dir:
            dest_dir = QFileDialog.getExistingDirectory(
                self, tr("Select the destination folder"),
                home, QFileDialog.ShowDirsOnly)
        if not dest_dir:
            return
        try:
            file_name = reply.rawHeader('Content-Disposition').split('=')[1]
            file_name = str(file_name).strip('"')
        except Exception as exc:
            header_pairs = reply.rawHeaderPairs()
            self.gem_api.common.error(
                'Unable to get the file name from headers: %s\n'
                'Exception: %s' % (header_pairs, str(exc)))
            return
        file_content = str(reply.readAll())
        # From
        # http://doc.qt.io/archives/qt-4.8/qwebpage.html#unsupportedContent
        # "The receiving slot is responsible for deleting the reply"
        reply.close()
        reply.deleteLater()
        file_fullpath = os.path.join(dest_dir, file_name)
        if os.path.exists(file_fullpath):
            name, ext = os.path.splitext(file_name)
            i = 1
            while True:
                file_fullpath = os.path.join(
                    dest_dir, '%s_%s%s' % (name, i, ext))
                if not os.path.exists(file_fullpath):
                    break
                i += 1
        with open(file_fullpath, "w") as f:
            f.write(file_content)
        self.gem_api.common.info('File downloaded as: %s' % file_fullpath)

    @pyqtSlot(str)
    def on_title_changed(self, title):
        # get the changed title of the web page and set the window title of the
        # parent widget to the same string
        self.parent.setWindowTitle(title)

    @pyqtSlot()
    def on_load_started(self):
        self.progress_message_bar, self.progress = create_progress_message_bar(
            self.parent.lower_message_bar, "Loading...")

    @pyqtSlot(int)
    def on_load_progress(self, progress):
        try:
            self.progress.setValue(progress)
        except RuntimeError:
            self.gem_api.common.error("Unable to load the requested page.")

    @pyqtSlot(bool)
    def on_load_finished(self, ok):
        # NOTE: Intuitively, I would have used the value of ok to check if
        # loading failed and to display an error message. However, before
        # a failing loading finishes, the attempt to set the progress value
        # raises a RuntimeError. I am using that to display an error message,
        # which seems to be working fine.
        clear_progress_message_bar(
            self.parent.lower_message_bar, self.progress_message_bar)

    @pyqtSlot(str)
    def on_statusBarMessage(self, text):
        # it might be useful in the future
        pass

    @pyqtSlot(QUrl)
    def on_url_changed(self, url):
        # it might be useful in the future
        pass

    @pyqtSlot(str, str, str)
    def on_link_hovered(self, link, title, textContent):
        # it might be useful in the future
        pass

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
            data = QSettings().value("irmt/cookies", QByteArray())
            cookies = QNetworkCookie.parseCookies(data)
            self.setAllCookies(cookies)
