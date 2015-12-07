# -*- coding: utf-8 -*-
#/***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)

from svir.ui.ui_select_sv_variables import Ui_SelectSvVariablesDialog
from svir.utilities.utils import WaitCursorManager, SvNetworkError


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
        self.is_subnational_study = False  # National is the default one
        self.set_ok_button()
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = downloader
        self.indicators_info_dict = {}
        with WaitCursorManager():
            self.fill_studies()
            self.fill_themes()
        self.ui.indicator_multiselect.unselected_widget.itemClicked.connect(
            self.update_indicator_info)
        self.ui.indicator_multiselect.selected_widget.itemClicked.connect(
            self.update_indicator_info)
        self.ui.indicator_multiselect.selection_changed.connect(
            self.set_ok_button)
        self.ui.zone_multiselect.selection_changed.connect(
            self.set_ok_button)

    @pyqtSlot()
    def on_fill_zones_btn_clicked(self):
        with WaitCursorManager():
            self.fill_zones()

    @pyqtSlot(str)
    def on_theme_cbx_currentIndexChanged(self):
        theme = self.ui.theme_cbx.currentText()
        with WaitCursorManager():
            self.fill_subthemes(theme)

    @pyqtSlot()
    def on_filter_btn_clicked(self):
        with WaitCursorManager():
            self.fill_indicators()

    @pyqtSlot(str)
    def on_study_cbx_currentIndexChanged(self):
        with WaitCursorManager():
            self.ui.country_multiselect.clear()
            self.ui.indicator_multiselect.clear()
            self.ui.zone_multiselect.clear()
            self.fill_countries()
            admin_levels = self.sv_downloader.get_admin_levels_for_study(
                self.ui.study_cbx.currentText())
            self.is_subnational_study = any(
                int(admin_level) > 0 for admin_level in admin_levels)
            if self.is_subnational_study:
                self.ui.zone_multiselect.show()
                self.ui.fill_zones_btn.show()
            else:
                self.ui.zone_multiselect.hide()
                self.ui.fill_zones_btn.hide()
            self.set_ok_button()

    def set_ok_button(self):
        if self.is_subnational_study:
            self.ok_button.setEnabled(
                self.ui.indicator_multiselect.selected_widget.count() > 0
                and self.ui.zone_multiselect.selected_widget.count() > 0)
        else:
            self.ok_button.setEnabled(
                self.ui.indicator_multiselect.selected_widget.count() > 0
                and self.ui.country_multiselect.selected_widget.count() > 0)

    def fill_studies(self):
        try:
            studies = self.sv_downloader.get_studies()
            self.ui.study_cbx.addItems(studies)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability studies: %s" % e)

    def fill_themes(self):
        self.ui.theme_cbx.clear()
        # load list of themes from the platform
        self.ui.theme_cbx.addItems([None])
        try:
            themes = self.sv_downloader.get_themes()
            self.ui.theme_cbx.addItems(themes)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability themes: %s" % e)
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_theme = self.ui.theme_cbx.currentText()
        self.fill_subthemes(current_theme)

    def fill_subthemes(self, theme):
        self.ui.subtheme_cbx.clear()
        # load list of subthemes from the platform
        self.ui.subtheme_cbx.addItems([None])
        if theme:
            try:
                subthemes = self.sv_downloader.get_subthemes_by_theme(theme)
                self.ui.subtheme_cbx.addItems(subthemes)
            except SvNetworkError as e:
                raise SvNetworkError(
                    "Unable to download social vulnerability"
                    " subthemes: %s" % e)

    def fill_indicators(self):
        self.ui.indicator_multiselect.set_unselected_items([])
        # load list of social vulnerability variable names from the platform
        name_filter = self.ui.name_filter_le.text()
        keywords = self.ui.keywords_le.text()
        theme = self.ui.theme_cbx.currentText()
        subtheme = self.ui.subtheme_cbx.currentText()
        zones_count = self.ui.zone_multiselect.selected_widget.count()
        zone_ids_list = []
        for zone_idx in range(zones_count):
            zone_id = \
                self.ui.zone_multiselect.selected_widget.item(zone_idx).text()
            zone_ids_list.append(zone_id)
        zone_ids_string = "|".join(zone_ids_list)
        study = self.ui.study_cbx.currentText()
        try:
            if zone_ids_string:  # filter by the selected zones
                filter_result_dict = self.sv_downloader.get_indicators_info(
                    name_filter=name_filter,
                    keywords=keywords,
                    theme=theme,
                    subtheme=subtheme,
                    zone_ids=zone_ids_string)
            else:  # filter by study
                filter_result_dict = self.sv_downloader.get_indicators_info(
                    name_filter=name_filter,
                    keywords=keywords,
                    theme=theme,
                    subtheme=subtheme,
                    study=study)
            self.indicators_info_dict.update(filter_result_dict)
            names = sorted(
                [code + ': ' + filter_result_dict[code]['name']
                    for code in filter_result_dict])
            self.ui.indicator_multiselect.add_unselected_items(names)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability names: %s" % e)

    def update_indicator_info(self, item):
        hint_text = item.text()
        indicator_code = item.text().split(':')[0]
        indicator_info_dict = self.indicators_info_dict[indicator_code]
        hint_text += '\n\n' + 'Description:\n' + indicator_info_dict[
            'description']
        self.ui.indicator_details.setText(hint_text)

    def fill_countries(self):
        # load from platform a list of countries belonging to the
        # selected study
        study_name = self.ui.study_cbx.currentText()
        try:
            countries_dict = self.sv_downloader.get_countries_info(study_name)
            names = sorted(
                [countries_dict[iso] + ' (' + iso + ')'
                    for iso in countries_dict])
            self.ui.country_multiselect.set_unselected_items(names)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download the list of zones: %s" % e)

    def fill_zones(self):
        # load from platform a list of zones belonging to the selected study
        study_name = self.ui.study_cbx.currentText()
        country_count = self.ui.country_multiselect.selected_widget.count()
        all_names = []
        for country_idx in range(country_count):
            country_item = self.ui.country_multiselect.selected_widget.item(
                country_idx)
            country_iso = country_item.text().split('(')[1].split(')')[0]
            try:
                zones_list = self.sv_downloader.get_zones_info(study_name,
                                                               country_iso)
            except SvNetworkError as e:
                raise SvNetworkError(
                    "Unable to download the list of zones: %s" % e)
            else:
                names = ['%s (%s: %s)' % (zone['name'],
                                          zone['country_iso'],
                                          zone['parent_label'])
                         for zone in zones_list]
                all_names.extend(names)
        self.ui.zone_multiselect.set_unselected_items(all_names)
