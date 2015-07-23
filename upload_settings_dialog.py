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

from PyQt4.QtCore import pyqtSlot, QUrl
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox,
                         QDesktopServices)
from ui.ui_upload_settings import Ui_UploadSettingsDialog
from defaults import DEFAULTS
from utils import reload_attrib_cbx, tr

LICENSES = (
    ('CC0', 'http://creativecommons.org/about/cc0'),
    ('CC BY 3.0 ', 'http://creativecommons.org/licenses/by/3.0/'),
    ('CC BY-SA 3.0', 'http://creativecommons.org/licenses/by-sa/3.0/'),
    ('CC BY-NC-SA 3.0', 'http://creativecommons.org/licenses/by-nc-sa/3.0/'),
)
DEFAULT_LICENSE = LICENSES[2]  # CC BY-SA 3.0


class UploadSettingsDialog(QDialog):
    """
    Dialog allowing the user to set some of the fields that will be written
    into the metadata xml, including the selection of one of the available
    licenses. The user must click on a confirmation checkbox, before the
    uploading of the layer can be started.
    """
    def __init__(self, iface, suppl_info):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_UploadSettingsDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.suppl_info = suppl_info
        selected_idx = self.suppl_info['selected_project_definition_idx']
        proj_defs = self.suppl_info['project_definitions']
        project_definition = proj_defs[selected_idx]
        if 'title' in project_definition:
            self.ui.title_le.setText(project_definition['title'])
        else:
            self.ui.title_le.setText(DEFAULTS['ISO19115_TITLE'])

        if 'description' in project_definition:
            self.ui.description_te.setPlainText(project_definition[
                'description'])

        # if no field is selected, we should not allow uploading
        self.zone_label_field_is_specified = False
        reload_attrib_cbx(
            self.ui.zone_label_field_cbx, iface.activeLayer(), True)
        # pre-select the field if it's specified in the project definition
        if 'zone_label_field' in project_definition:
            zone_label_idx = self.ui.zone_label_field_cbx.findText(
                project_definition['zone_label_field'])
            if zone_label_idx != -1:
                self.ui.zone_label_field_cbx.setCurrentIndex(zone_label_idx)
                self.zone_label_field_is_specified = True

        for license_name, license_link in LICENSES:
            self.ui.license_cbx.addItem(license_name, license_link)
        if 'license' in project_definition:
            license_name = project_definition['license'].split(
                '(')[0].strip()
            license_idx = self.ui.license_cbx.findText(license_name)
            if license_idx != -1:
                self.ui.license_cbx.setCurrentIndex(license_idx)
            else:
                self.ui.license_cbx.setCurrentIndex(
                    self.ui.license_cbx.findText(DEFAULT_LICENSE[0]))
        else:
            self.ui.license_cbx.setCurrentIndex(
                self.ui.license_cbx.findText(DEFAULT_LICENSE[0]))

        self.exists_on_platform = 'platform_layer_id' in self.suppl_info
        self.do_update = False

        self.ui.update_radio.setEnabled(self.exists_on_platform)
        self.ui.update_radio.setChecked(self.exists_on_platform)
        self.set_labels()

    def set_labels(self):
        self.ui.situation_lbl.setVisible(self.exists_on_platform)
        self.ui.question_lbl.setVisible(self.exists_on_platform)
        for button in self.ui.upload_action.buttons():
            button.setVisible(self.exists_on_platform)

        if self.ui.update_radio.isChecked():
            explaination_lbl = tr(
                'The current project definition will be added to the '
                'OpenQuake Platform project\nidentified as "%s"'
                % self.suppl_info['platform_layer_id'])
            title_lbl = tr('Project title')
            description_lbl = tr('Project description')
        else:
            explaination_lbl = tr(
                'A new layer will be created on the OpenQuake Platform.')
            title_lbl = tr('New layer title')
            description_lbl = tr('New layer abstract')

        self.ui.title_lbl.setText(title_lbl)
        self.ui.description_lbl.setText(description_lbl)
        self.ui.explaination_lbl.setText(explaination_lbl)

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.ui.title_le.text() and
            self.ui.confirm_chk.isChecked() and
            self.zone_label_field_is_specified)

    @pyqtSlot(bool)
    def on_update_radio_toggled(self, on):
        self.do_update = on
        self.set_labels()

    @pyqtSlot(int)
    def on_confirm_chk_stateChanged(self):
        self.set_ok_button()

    @pyqtSlot(str)
    def on_zone_label_field_cbx_currentIndexChanged(self):
        zone_label_field = self.ui.zone_label_field_cbx.currentText()
        self.zone_label_field_is_specified = (zone_label_field != '')
        self.set_ok_button()

    @pyqtSlot()
    def on_license_info_btn_clicked(self):
        selected_license_index = self.ui.license_cbx.currentIndex()
        license_url = self.ui.license_cbx.itemData(selected_license_index)
        QDesktopServices.openUrl(QUrl(license_url))
