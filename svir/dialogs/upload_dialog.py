# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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
from StringIO import StringIO
from qgis.core import QgsRuleBasedRendererV2
from qgis.gui import QgsMessageBar

from qgis.PyQt.QtCore import Qt, QUrl, QSettings, pyqtSignal
from qgis.PyQt.QtGui import QDialog, QSizePolicy, QDialogButtonBox
from qgis.PyQt.QtNetwork import QNetworkCookieJar, QNetworkCookie
from qgis.PyQt.QtWebKit import QWebSettings

from svir.thread_worker.abstract_worker import start_worker
from svir.thread_worker.upload_worker import UploadWorker
from svir.third_party.requests.sessions import Session
from svir.third_party.requests.utils import dict_from_cookiejar
from svir.utilities.sldadapter import getGsCompatibleSld
from svir.utilities.utils import (platform_login,
                                  create_progress_message_bar,
                                  clear_progress_message_bar,
                                  SvNetworkError,
                                  log_msg,
                                  get_ui_class,
                                  get_credentials,
                                  )
from svir.utilities.shared import DEBUG

FORM_CLASS = get_ui_class('ui_upload_metadata.ui')


class UploadDialog(QDialog, FORM_CLASS):
    """
    Modal dialog allowing to upload the data to the OQ-Platform
    """

    upload_successful = pyqtSignal(str)

    def __init__(self, iface, file_stem):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.message_bar = QgsMessageBar()
        self.message_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().insertWidget(0, self.message_bar)

        self.message_bar_item = None

        self.button_box = self.buttonBox

        self.hostname, self.username, self.password = get_credentials(
            'platform')

        self.web_view = self.web_view
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
                'Error', error_msg, duration=0, level=QgsMessageBar.CRITICAL)
            return

        # adding by emitting signal in different thread
        worker = UploadWorker(
            self.hostname, self.session, self.file_stem,
            self.username, self.iface.activeLayer())

        worker.successfully_finished.connect(self.upload_done)
        start_worker(worker, self.message_bar, 'Uploading data')

    def _update_layer_style(self):
        # The file stem contains the full path. We get just the basename
        layer_name = os.path.basename(self.file_stem)
        # Since the style name is set by default substituting '-' with '_',
        # tp get the right style we need to do the same substitution
        style_name = layer_name.replace('-', '_')
        print(style_name)
        try:
            sld = getGsCompatibleSld(self.iface.activeLayer(), style_name)
            # print(sld)
        except Exception as e:
            error_msg = (
                'Unable to export the styled layer descriptor: ' + e.message)
            self.message_bar.pushMessage(
                'Style error', error_msg, duration=0,
                level=QgsMessageBar.CRITICAL)
            return

        import tempfile
        fd, sld_file = tempfile.mkstemp(suffix=".sld")
        os.close(fd)
        with open(sld_file, 'w') as f:
            f.write(sld)
        # os.system('tidy -xml -i %s' % fname)
        # headers = {'content-type': 'application/vnd.ogc.sld+xml'}
        with open(sld_file, 'rb') as f:
            print(f.read())
        files = {'sld': open(sld_file, 'rb')}
        data = {'name': style_name}
        resp = self.session.put(
            self.hostname + '/gs/%s/style/upload' % style_name,
            # data=sld, headers=headers)
            data=data, files=files)
        print('resp: %s' % resp)
        # import pdb; pdb.set_trace()
        if DEBUG:
            log_msg('Style upload response: %s' % resp)
        if not resp.ok:
            error_msg = (
                'Error while styling the uploaded layer: ' + resp.reason)
            self.message_bar.pushMessage(
                'Style error', error_msg, duration=0,
                level=QgsMessageBar.CRITICAL)
        select_style_xml = """
<layer>
    <name>oqplatform:%s</name>
    <defaultStyle>
        <name>%s</name>
        <atom:link xmlns:atom="http://www.w3.org/2005/Atom" rel="alternate" href="http://127.0.0.1:8080/geoserver/rest/styles/%s.xml" type="application/xml"/>
    </defaultStyle>
</layer>
        """ % (style_name, style_name, style_name)
        print('select_style_xml:\n%s' % select_style_xml)
        headers = {'content-type': 'application/xml'}
        files = {'file': StringIO(select_style_xml)}
        resp = self.session.put(
            self.hostname + '/gs/rest/layers/%s.xml' % style_name,
            files=files,
            headers=headers)
        print('resp: %s' % resp)
        # import pdb; pdb.set_trace()
        if DEBUG:
            log_msg('Style selection response: %s' % resp)
        if not resp.ok:
            error_msg = (
                'Error while selecting the style of the loaded layer: '
                + resp.reason)
            self.message_bar.pushMessage(
                'Style error', error_msg, duration=0,
                level=QgsMessageBar.CRITICAL)

    def upload_done(self, result):
        layer_url, success = result
        # In case success == 'False', layer_url contains the error message
        if success:
            # so far, we implemented the style-converter only for the
            # rule-based styles. Only in those cases, we should add a style to
            # the layer to be uploaded. Otherwise, it's fine to use the default
            # basic geonode style.
            if isinstance(self.iface.activeLayer().rendererV2(),
                          QgsRuleBasedRendererV2):
                print('isinstance render v2')
                self._update_layer_style()
            else:
                self.message_bar.pushMessage(
                    'Info',
                    'Using the basic default style',
                    level=QgsMessageBar.INFO)
            self.message_bar_item, _ = create_progress_message_bar(
                self.message_bar, 'Loading page......', no_percentage=True)
            self.web_view.load(QUrl(layer_url))
            self.layer_url = layer_url
            self.upload_successful.emit(layer_url)
        else:
            error_msg = layer_url
            clear_progress_message_bar(self.message_bar)
            self.message_bar.pushMessage(
                'Upload error', error_msg, duration=0,
                level=QgsMessageBar.CRITICAL)

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
            '/irmt/developer_mode', True, type=bool)
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
