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

# FIXME: Delete the following two
PLATFORM_API_ROOT = "/exposure"
PLATFORM_API = dict(themes=PLATFORM_API_ROOT + "/export_sv_themes",
                    subthemes=PLATFORM_API_ROOT + "/export_sv_subthemes",
                    tags=PLATFORM_API_ROOT + "/export_sv_tags",
                    names=PLATFORM_API_ROOT + "/export_sv_names")


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
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = SvDownloader(self.hostname)
        self.sv_downloader.login(self.username, self.password)
        self.fill_themes()

    @pyqtSlot(str)
    def on_theme_cbx_currentIndexChanged(self):
        theme = self.ui.theme_cbx.currentText()
        self.fill_subthemes(theme)

    @pyqtSlot(str)
    def on_subtheme_cbx_currentIndexChanged(self):
        theme = self.ui.theme_cbx.currentText()
        subtheme = self.ui.subtheme_cbx.currentText()
        self.fill_tags(theme, subtheme)

    @pyqtSlot(str)
    def on_tag_cbx_currentIndexChanged(self):
        theme = self.ui.theme_cbx.currentText()
        subtheme = self.ui.subtheme_cbx.currentText()
        tag = self.ui.tag_cbx.currentText()
        self.fill_names(theme, subtheme, tag)

    @pyqtSlot(str)
    def fill_themes(self):
        self.ui.theme_cbx.clear()
        # load list of themes from the platform
        #sv_downloader = SvDownloader(self.hostname, PLATFORM_API['themes'])
        try:
            themes = self.sv_downloader.get_items()
            self.ui.theme_cbx.addItems(themes)
        except SvDownloadError as e:
            # TODO: use QGIS bar to display error
            print "Unable to download social vulnerability themes: %s" % e
            return
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_theme = self.ui.theme_cbx.currentText()
        self.fill_subthemes(current_theme)

    def fill_subthemes(self, theme):
        self.ui.subtheme_cbx.clear()
        # load list of subthemes from the platform
        try:
            subthemes = self.sv_downloader.get_items(theme)
            self.ui.subtheme_cbx.addItems(subthemes)
        except SvDownloadError as e:
            # TODO: use QGIS bar to display error
            print "Unable to download social vulnerability subthemes: %s" % e
            return
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_subtheme = self.ui.subtheme_cbx.currentText()
        self.fill_tags(theme, current_subtheme)

    def fill_tags(self, theme, subtheme):
        self.ui.tag_cbx.clear()
        # load list of tags from the platform
        try:
            tags = self.sv_downloader.get_items(theme, subtheme)
            self.ui.tag_cbx.addItems(tags)
        except SvDownloadError as e:
            # TODO: use QGIS bar to display error
            print "Unable to download social vulnerability tags: %s" % e
            return
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_tag = self.ui.tag_cbx.currentText()
        self.fill_names(theme, subtheme, current_tag)

    def fill_names(self, theme, subtheme, tag):
        self.ui.name_cbx.clear()
        # load list of social vulnerability variable names from the platform
        try:
            names = self.sv_downloader.get_items(theme, subtheme, tag)
            self.ui.name_cbx.addItems(names)
        except SvDownloadError as e:
            # TODO: use QGIS bar to display error
            print "Unable to download social vulnerability names: %s" % e
            return

    def get_credentials(self):
        qs = QSettings()
        hostname = qs.value('platform_settings/hostname', '')
        username = qs.value('platform_settings/username', '')
        password = qs.value('platform_settings/password', '')
        if not (hostname and username and password):
            PlatformSettingsDialog(self.iface).exec_()
            hostname = qs.value('platform_settings/hostname', '')
            username = qs.value('platform_settings/username', '')
            password = qs.value('platform_settings/password', '')
        return hostname, username, password
