# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from platform_settings_dialog import PlatformSettingsDialog

from ui.ui_select_sv_indices import Ui_SelectSvIndicesDialog
from import_sv_data import SvDownloader, SvDownloadError


class SelectSvIndicesDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    social vulnerability variables to import from the oq-platform
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        # Set up the user interface from Designer.
        self.ui = Ui_SelectSvIndicesDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.hostname, self.username, self.password = self.get_credentials()
        self.fill_themes()

    @pyqtSlot(str)
    def on_theme_cbx_currentIndexChanged(self):
        self.fill_subthemes()

    @pyqtSlot(str)
    def on_subtheme_cbx_currentIndexChanged(self):
        self.fill_tags()

    @pyqtSlot(str)
    def on_tag_cbx_currentIndexChanged(self):
        self.fill_names()

    @pyqtSlot(str)
    def fill_themes(self):
        # load list of themes from the platform
        sv_downloader = SvDownloader(self.hostname)
        sv_downloader.login(self.username, self.password)
        try:
            filename, msg = sv_downloader.download()
        except SvDownloadError as e:
            # TODO: use QGIS bar to display error
            print "Unable to download social vulnerability themes: %s" % e
            return
        # FIXME: Remove DEBUG prints
        print "filename:", filename
        print "msg:", msg

        # clear the subsequent combo boxes
        self.ui.subtheme_cbx.clear()
        self.ui.tag_cbx.clear()
        self.ui.name_cbx.clear()

    def fill_subthemes(self):
        # load list of subthemes from the platform
        pass

        # clear the subsequent combo boxes
        self.ui.tag_cbx.clear()
        self.ui.name_cbx.clear()

    def fill_tags(self):
        # load list of tags from the platform
        pass

        # clear the subsequent combo box
        self.ui.name_cbx.clear()

    def fill_names(self):
        # load list of social vulnerability variable names from the platform
        pass

    def get_credentials(self):
        qs = QSettings()
        hostname = qs.value('platform_settings/hostname', '')
        username = qs.value('platform_settings/username', '')
        password = qs.value('platform_settings/password', '')
        # FIXME: forcing the user to specify settings every time
        if True or not (hostname and username and password):
            PlatformSettingsDialog(self.iface).exec_()
            hostname = qs.value('platform_settings/hostname', '')
            username = qs.value('platform_settings/username', '')
            password = qs.value('platform_settings/password', '')
        return hostname, username, password
