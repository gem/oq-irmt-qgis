# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014-2015 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/
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
"""

from PyQt4.QtCore import (Qt,
                          QUrl,
                          QSettings,
                          pyqtSignal)

from PyQt4.QtGui import (QDialog, QSizePolicy, QDialogButtonBox)
from PyQt4.QtNetwork import QNetworkCookieJar, QNetworkCookie
from PyQt4.QtWebKit import QWebSettings

from qgis.gui import QgsMessageBar
from abstract_worker import start_worker
from third_party.requests.sessions import Session
from third_party.requests.utils import dict_from_cookiejar
from sldadapter import getGsCompatibleSld

from ui.ui_upload_metadata import Ui_UploadMetadataDialog
from upload_worker import UploadWorker

from utils import (get_credentials,
                   platform_login,
                   create_progress_message_bar, clear_progress_message_bar,
                   SvNetworkError)
from shared import DEBUG


class UploadDialog(QDialog):
    """
    Modal dialog allowing to upload the data to the OQ-Platform
    """

    upload_successful = pyqtSignal(str)

    def __init__(self, iface, file_stem):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_UploadMetadataDialog()
        self.ui.setupUi(self)
        self.message_bar = QgsMessageBar()
        self.message_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().insertWidget(0, self.message_bar)

        self.message_bar_item = None

        self.button_box = self.ui.buttonBox

        self.hostname, self.username, self.password = get_credentials(
            self.iface)

        self.web_view = self.ui.web_view
        self.page = self.web_view.page()
        self.frame = self.page.mainFrame()

        self.session = Session()
        self.network_access_manager = self.page.networkAccessManager()
        self.cookie_jar = QNetworkCookieJar()
        self.network_access_manager.setCookieJar(self.cookie_jar)

        self._setup_context_menu()
        self.frame.javaScriptWindowObjectCleared.connect(self._setup_js)

        self.file_stem = file_stem

        self.layout().setContentsMargins(0, 0, 0, 0)

        self.web_view.loadFinished.connect(self.load_finished)

        self.layer_url = None

    def showEvent(self, event):
        super(UploadDialog, self).showEvent(event)
        self.upload()

    def upload(self):
        try:
            self._login_to_platform()
        except SvNetworkError as e:
            error_msg = (
                'Unable to login to the platform: ' + e.message)
            self.message_bar.pushMessage(
                'Error', error_msg, level=QgsMessageBar.CRITICAL)
            return

        # adding by emitting signal in different thread
        worker = UploadWorker(
            self.hostname, self.session, self.file_stem, self.username)

        worker.successfully_finished.connect(self.upload_done)
        start_worker(worker, self.message_bar, 'Uploading data')

    def _update_layer_style(self):
        # file_stem contains also the slashes, which need to be removed
        # Since the style name is set by default substituting '-' with '_',
        # tp get the right style we need to do the same substitution
        style_name = self.file_stem.replace('/', '').replace('-', '_')
        try:
            sld = getGsCompatibleSld(self.iface.activeLayer(), style_name)
        except Exception as e:
            error_msg = (
                'Unable to export the styled layer descriptor: ' + e.message)
            self.message_bar.pushMessage(
                'Style error', error_msg, level=QgsMessageBar.CRITICAL)
            return

        if DEBUG:
            import os
            import tempfile
            fd, fname = tempfile.mkstemp(suffix=".sld")
            os.close(fd)
            with open(fname, 'w') as f:
                f.write(sld)
            os.system('tidy -xml -i %s' % fname)
        headers = {'content-type': 'application/vnd.ogc.sld+xml'}
        resp = self.session.put(
            self.hostname + '/gs/rest/styles/%s' % style_name,
            data=sld, headers=headers)
        if DEBUG:
            print 'Style upload response:', resp
        if not resp.ok:
            error_msg = (
                'Error while styling the uploaded layer: ' + resp.reason)
            self.message_bar.pushMessage(
                'Style error', error_msg, level=QgsMessageBar.CRITICAL)

    def upload_done(self, result):
        layer_url, success = result
        # In case success == 'False', layer_url contains the error message
        if success:
            self._update_layer_style()
            self.message_bar_item, _ = create_progress_message_bar(
                self.message_bar, 'Loading page......', no_percentage=True)
            self.web_view.load(QUrl(layer_url))
            self.layer_url = layer_url
            self.upload_successful.emit(layer_url)
        else:
            error_msg = layer_url
            clear_progress_message_bar(self.message_bar)
            self.message_bar.pushMessage(
                'Upload error', error_msg, level=QgsMessageBar.CRITICAL)

    def load_finished(self):
        clear_progress_message_bar(self.message_bar, self.message_bar_item)
        if not self.button_box.isEnabled():
            self.button_box.setEnabled(True)
            self.button_box.addButton('Close',
                                      QDialogButtonBox.NoRole)
            self.button_box.addButton('Close and show in browser',
                                      QDialogButtonBox.YesRole)

    def _login_to_platform(self):
        platform_login(
            self.hostname, self.username, self.password, self.session)
        sessionid = dict_from_cookiejar(self.session.cookies)['sessionid']
        sessionid_cookie = QNetworkCookie('sessionid', sessionid)
        self.cookie_jar.setCookiesFromUrl(
            [sessionid_cookie], QUrl(self.hostname))

    def _setup_context_menu(self):
        settings = QSettings()
        developer_mode = settings.value(
            '/svir/developer_mode', True, type=bool)
        if developer_mode is True:
            self.web_view.page().settings().setAttribute(
                QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

    def _setup_js(self):
        # pass a reference (called qt_page) of self to the JS world
        # to expose a member of self to js you need to declare it as property
        # see for example self.json_str()
        self.frame.addToJavaScriptWindowObject('qt_page', self)
