# -*- coding: utf-8 -*-
# /***************************************************************************
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
                         QSizePolicy,
                         QDialogButtonBox)

from svir.utilities.utils import (WaitCursorManager,
                                  SvNetworkError,
                                  get_ui_class,
                                  )
from svir.ui.list_multiselect_widget import ListMultiSelectWidget

FORM_CLASS = get_ui_class('ui_select_sv_variables.ui')


class SelectSvVariablesDialog(QDialog, FORM_CLASS):
    """
    Modal dialog giving to the user the possibility to select
    social vulnerability variables to import from the oq-platform
    """
    def __init__(self, downloader):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.country_multiselect = ListMultiSelectWidget(
            title='Select Countries')
        self.zone_multiselect = ListMultiSelectWidget(
            title='Select Zones')
        self.indicator_multiselect = ListMultiSelectWidget(
            title='Select Indicators')
        for multiselect in (self.country_multiselect,
                            self.zone_multiselect,
                            self.indicator_multiselect):
            multiselect.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.scrollAreaWidgetContents.layout().insertWidget(
            1, self.country_multiselect)
        self.scrollAreaWidgetContents.layout().insertWidget(
            3, self.zone_multiselect)
        self.scrollAreaWidgetContents.layout().insertWidget(
            8, self.indicator_multiselect)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.is_subnational_study = False  # National is the default one
        self.set_ok_button()
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = downloader
        self.indicators_info_dict = {}
        with WaitCursorManager():
            self.fill_studies()
            self.fill_themes()
        self.indicator_multiselect.unselected_widget.itemClicked.connect(
            self.update_indicator_info)
        self.indicator_multiselect.selected_widget.itemClicked.connect(
            self.update_indicator_info)
        self.indicator_multiselect.selection_changed.connect(
            self.set_ok_button)
        self.zone_multiselect.selection_changed.connect(
            self.set_ok_button)

    @pyqtSlot()
    def on_fill_zones_btn_clicked(self):
        with WaitCursorManager():
            self.fill_zones()

    @pyqtSlot(str)
    def on_theme_cbx_currentIndexChanged(self):
        theme = self.theme_cbx.currentText()
        with WaitCursorManager():
            self.fill_subthemes(theme)

    @pyqtSlot()
    def on_filter_btn_clicked(self):
        with WaitCursorManager():
            self.fill_indicators()

    @pyqtSlot(str)
    def on_study_cbx_currentIndexChanged(self):
        with WaitCursorManager():
            self.country_multiselect.clear()
            self.indicator_multiselect.clear()
            self.zone_multiselect.clear()
            self.fill_countries()
            admin_levels = self.sv_downloader.get_admin_levels_for_study(
                self.study_cbx.currentText())
            self.is_subnational_study = any(
                int(admin_level) > 0 for admin_level in admin_levels)
            if self.is_subnational_study:
                self.zone_multiselect.show()
                self.fill_zones_btn.show()
            else:
                self.zone_multiselect.hide()
                self.fill_zones_btn.hide()
            self.set_ok_button()

    def set_ok_button(self):
        if self.is_subnational_study:
            self.ok_button.setEnabled(
                self.indicator_multiselect.selected_widget.count() > 0
                and self.zone_multiselect.selected_widget.count() > 0)
        else:
            self.ok_button.setEnabled(
                self.indicator_multiselect.selected_widget.count() > 0
                and self.country_multiselect.selected_widget.count() > 0)

    def fill_studies(self):
        try:
            studies = self.sv_downloader.get_studies()
            self.study_cbx.addItems(studies)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability studies: %s" % e)

    def fill_themes(self):
        self.theme_cbx.clear()
        # load list of themes from the platform
        self.theme_cbx.addItems([None])
        try:
            themes = self.sv_downloader.get_themes()
            self.theme_cbx.addItems(themes)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability themes: %s" % e)
        # populate the subsequent combo boxes accordingly with the currently
        # selected item
        current_theme = self.theme_cbx.currentText()
        self.fill_subthemes(current_theme)

    def fill_subthemes(self, theme):
        self.subtheme_cbx.clear()
        # load list of subthemes from the platform
        self.subtheme_cbx.addItems([None])
        if theme:
            try:
                subthemes = self.sv_downloader.get_subthemes_by_theme(theme)
                self.subtheme_cbx.addItems(subthemes)
            except SvNetworkError as e:
                raise SvNetworkError(
                    "Unable to download social vulnerability"
                    " subthemes: %s" % e)

    def fill_indicators(self):
        self.indicator_multiselect.set_unselected_items([])
        # load list of social vulnerability variable names from the platform
        name_filter = self.name_filter_le.text()
        keywords = self.keywords_le.text()
        theme = self.theme_cbx.currentText()
        subtheme = self.subtheme_cbx.currentText()
        zones_count = self.zone_multiselect.selected_widget.count()
        zone_ids_list = []
        for zone_idx in range(zones_count):
            zone_id = \
                self.zone_multiselect.selected_widget.item(zone_idx).text()
            zone_ids_list.append(zone_id)
        zone_ids_string = "|".join(zone_ids_list)
        study = self.study_cbx.currentText()
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
            self.indicator_multiselect.add_unselected_items(names)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download social vulnerability names: %s" % e)

    def update_indicator_info(self, item):
        hint_text = item.text()
        indicator_code = item.text().split(':')[0]
        indicator_info_dict = self.indicators_info_dict[indicator_code]
        hint_text += '\n\n' + 'Description:\n' + indicator_info_dict[
            'description']
        self.indicator_details.setText(hint_text)

    def fill_countries(self):
        # load from platform a list of countries belonging to the
        # selected study
        study_name = self.study_cbx.currentText()
        try:
            countries_dict = self.sv_downloader.get_countries_info(study_name)
            names = sorted(
                [countries_dict[iso] + ' (' + iso + ')'
                    for iso in countries_dict])
            self.country_multiselect.set_unselected_items(names)
        except SvNetworkError as e:
            raise SvNetworkError(
                "Unable to download the list of zones: %s" % e)

    def fill_zones(self):
        # load from platform a list of zones belonging to the selected study
        study_name = self.study_cbx.currentText()
        country_count = self.country_multiselect.selected_widget.count()
        all_names = []
        for country_idx in range(country_count):
            country_item = self.country_multiselect.selected_widget.item(
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
        self.zone_multiselect.set_unselected_items(all_names)
