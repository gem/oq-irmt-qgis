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

# Copyright (c) 2013-2014, GEM Foundation.
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
from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)

from ui.ui_select_sv_variables import Ui_SelectSvVariablesDialog
from import_sv_data import SvDownloadError
from utils import WaitCursorManager


class SelectSvVariablesDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    social vulnerability variables to import from the oq-platform
    """
    def __init__(self, downloader):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SelectSvVariablesDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.set_ok_button()
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = downloader
        with WaitCursorManager():
            self.fill_themes()

    @pyqtSlot(str)
    def on_theme_cbx_currentIndexChanged(self):
        theme = self.ui.theme_cbx.currentText()
        with WaitCursorManager():
            self.fill_subthemes(theme)

    @pyqtSlot()
    def on_filter_btn_clicked(self):
        with WaitCursorManager():
            self.fill_names()

    @pyqtSlot()
    def on_add_name_btn_clicked(self):
        theme = self.ui.theme_cbx.currentText()
        name = self.ui.name_cbx.currentText()
        name = '%s,%s' % (theme, name)
        if not self.ui.selected_names_lst.findItems(
                name, Qt.MatchFixedString):
                self.ui.selected_names_lst.addItem(name)
                self.set_ok_button()

    @pyqtSlot()
    def on_remove_name_btn_clicked(self):
        row = self.ui.selected_names_lst.currentRow()
        if row is not None:
            self.ui.selected_names_lst.takeItem(row)
            self.set_ok_button()

    @pyqtSlot()
    def on_clear_btn_clicked(self):
        self.ui.selected_names_lst.clear()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(self.ui.selected_names_lst.count() > 0)

    def fill_themes(self):
        self.ui.theme_cbx.clear()
        # load list of themes from the platform
        self.ui.theme_cbx.addItems([None])
        try:
            themes = self.sv_downloader.get_themes()
            self.ui.theme_cbx.addItems(themes)
        except SvDownloadError as e:
            raise SvDownloadError(
                "Unable to download social vulnerability themes: %s" % e)
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_theme = self.ui.theme_cbx.currentText()
        self.fill_subthemes(current_theme)

    def fill_subthemes(self, theme):
        self.ui.subtheme_cbx.clear()
        # load list of subthemes from the platform
        self.ui.subtheme_cbx.addItems([None])
        try:
            subthemes = self.sv_downloader.get_subthemes_by_theme(theme)
            self.ui.subtheme_cbx.addItems(subthemes)
        except SvDownloadError as e:
            raise SvDownloadError(
                "Unable to download social vulnerability subthemes: %s" % e)

    def fill_names(self):
        self.ui.name_cbx.clear()
        # load list of social vulnerability variable names from the platform

        name_filter = self.ui.name_filter_le.text()
        keywords = self.ui.keywords_le.text()
        theme = self.ui.theme_cbx.currentText()
        subtheme = self.ui.subtheme_cbx.currentText()
        try:
            names = self.sv_downloader.get_names(
                name_filter, keywords, theme, subtheme)
            self.ui.name_cbx.addItems(names)
        except SvDownloadError as e:
            raise SvDownloadError(
                "Unable to download social vulnerability names: %s" % e)
