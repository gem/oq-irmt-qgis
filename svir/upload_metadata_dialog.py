# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2014-03-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
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
                          pyqtProperty,
                          pyqtSignal)

from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from PyQt4.QtNetwork import QNetworkCookieJar, QNetworkCookie
from PyQt4.QtWebKit import QWebSettings
from metadata_utilities import write_iso_metadata_file
from third_party.requests.sessions import Session
from third_party.requests.utils import dict_from_cookiejar

from ui.ui_upload_metadata import Ui_UploadMetadataDialog

from utils import get_credentials, platform_login, upload_shp


class UploadMetadataDialog(QDialog):
    """
    Modal dialog allowing to upload the data to a platform
    """

    def __init__(self, iface, file_stem, project_definition):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_UploadMetadataDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

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
        self.project_definition = project_definition
        self.upload()

    def upload(self):
        xml_file = self.file_stem + '.xml'
        write_iso_metadata_file(xml_file, self.project_definition)
        self._login_to_platform()
        layer_url = upload_shp(self.hostname, self.session, self.file_stem)
        if layer_url:
            self._load_metadata_page(layer_url)

    def _login_to_platform(self):
        platform_login(
            self.hostname, self.username, self.password, self.session)
        sessionid = dict_from_cookiejar(self.session.cookies)['sessionid']
        sessionid_cookie = QNetworkCookie('sessionid', sessionid)
        self.cookie_jar.setCookiesFromUrl(
            [sessionid_cookie], QUrl(self.hostname))

    def _load_metadata_page(self, url):
        self.web_view.load(QUrl(url))

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
