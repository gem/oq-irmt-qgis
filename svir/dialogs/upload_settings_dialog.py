# -*- coding: utf-8 -*-
#/***************************************************************************
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

from PyQt4.QtCore import pyqtSlot, QUrl
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox,
                         QDesktopServices)
from qgis.gui import QgsMessageBar
from svir.dialogs.upload_dialog import UploadDialog
from svir.metadata.metadata_utilities import write_iso_metadata_file
from svir.third_party.requests.sessions import Session

from svir.ui.ui_upload_settings import Ui_UploadSettingsDialog
from svir.utilities.defaults import DEFAULTS
from svir.calculations.process_layer import ProcessLayer
from svir.utilities.shared import (IRMT_PLUGIN_VERSION,
                                   SUPPLEMENTAL_INFORMATION_VERSION,
                                   DEBUG,
                                   )
from svir.utilities.utils import (reload_attrib_cbx,
                                  tr,
                                  WaitCursorManager,
                                  platform_login,
                                  SvNetworkError,
                                  get_credentials,
                                  update_platform_project,
                                  write_layer_suppl_info_to_qgs,
                                  insert_platform_layer_id,
                                  )

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
    def __init__(self, iface, suppl_info, file_stem):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_UploadSettingsDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.iface = iface
        self.vertices_count = None
        self.file_stem = file_stem
        self.xml_file = file_stem + '.xml'
        self.suppl_info = suppl_info
        self.selected_idx = self.suppl_info['selected_project_definition_idx']
        self.project_definition = self.suppl_info['project_definitions'][
            self.selected_idx]
        if 'title' in self.project_definition:
            self.ui.title_le.setText(self.project_definition['title'])
        else:
            self.ui.title_le.setText(DEFAULTS['ISO19115_TITLE'])

        if 'description' in self.project_definition:
            self.ui.description_te.setPlainText(self.project_definition[
                'description'])

        # if no field is selected, we should not allow uploading
        self.zone_label_field_is_specified = False
        reload_attrib_cbx(
            self.ui.zone_label_field_cbx, iface.activeLayer(), True)

        self.set_zone_label_field()
        self.set_license()

        self.exists_on_platform = 'platform_layer_id' in self.suppl_info
        self.do_update = False

        self.ui.update_radio.setEnabled(self.exists_on_platform)
        self.ui.update_radio.setChecked(self.exists_on_platform)
        self.set_labels()

        with WaitCursorManager("Counting layer's vertices", iface):
            self.vertices_count = ProcessLayer(
                iface.activeLayer()).count_vertices()

    def set_zone_label_field(self):
        # pre-select the field if it's specified in the supplemental info
        if 'zone_label_field' in self.suppl_info:
            zone_label_idx = self.ui.zone_label_field_cbx.findText(
                self.suppl_info['zone_label_field'])
            if zone_label_idx != -1:
                self.ui.zone_label_field_cbx.setCurrentIndex(zone_label_idx)
                self.zone_label_field_is_specified = True
        else:
            self.ui.zone_label_field_cbx.setCurrentIndex(-1)
            self.zone_label_field_is_specified = False

    def set_license(self):
        for license_name, license_link in LICENSES:
            self.ui.license_cbx.addItem(license_name, license_link)
        if 'license' in self.suppl_info:
            license_name = self.suppl_info['license'].split(
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
            self.ui.title_le.setEnabled(False)
            self.ui.description_te.setEnabled(False)
            self.ui.zone_label_field_cbx.setEnabled(False)
            self.ui.license_cbx.setEnabled(False)
            self.set_zone_label_field()
            self.set_license()
        else:
            explaination_lbl = tr(
                'A new layer will be created on the OpenQuake Platform.')
            title_lbl = tr('New layer title')
            description_lbl = tr('New layer abstract')
            self.ui.title_le.setEnabled(True)
            self.ui.description_te.setEnabled(True)
            self.ui.zone_label_field_cbx.setEnabled(True)
            self.ui.license_cbx.setEnabled(True)

        self.ui.title_lbl.setText(title_lbl)
        self.ui.description_lbl.setText(description_lbl)
        self.ui.explaination_lbl.setText(explaination_lbl)

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.ui.title_le.text() and
            self.ui.confirm_chk.isChecked() and
            self.zone_label_field_is_specified)

    def accept(self):
        self.suppl_info['title'] = self.ui.title_le.text()
        if 'title' not in self.project_definition:
            self.project_definition['title'] = self.suppl_info['title']
        self.suppl_info['abstract'] = self.ui.description_te.toPlainText()
        if 'description' not in self.project_definition:
            self.project_definition['description'] = self.suppl_info[
                'abstract']
        zone_label_field = self.ui.zone_label_field_cbx.currentText()
        self.suppl_info['zone_label_field'] = zone_label_field

        license_name = self.ui.license_cbx.currentText()
        license_idx = self.ui.license_cbx.currentIndex()
        license_url = self.ui.license_cbx.itemData(license_idx)
        license_txt = '%s (%s)' % (license_name, license_url)
        self.suppl_info['license'] = license_txt
        self.suppl_info['irmt_plugin_version'] = IRMT_PLUGIN_VERSION
        self.suppl_info['supplemental_information_version'] = \
            SUPPLEMENTAL_INFORMATION_VERSION
        self.suppl_info['vertices_count'] = self.vertices_count

        self.suppl_info['project_definitions'][self.selected_idx] = \
            self.project_definition
        active_layer_id = self.iface.activeLayer().id()
        write_layer_suppl_info_to_qgs(active_layer_id, self.suppl_info)

        if self.do_update:
            with WaitCursorManager(
                    'Updating project on the OpenQuake Platform',
                    self.iface):
                hostname, username, password = get_credentials(self.iface)
                session = Session()
                try:
                    platform_login(hostname, username, password, session)
                except SvNetworkError as e:
                    error_msg = (
                        'Unable to login to the platform: ' + e.message)
                    self.iface.messageBar().pushMessage(
                        'Error', error_msg, level=QgsMessageBar.CRITICAL)
                    return
                if 'platform_layer_id' not in self.suppl_info:
                    error_msg = ('Unable to retrieve the id of'
                                 'the layer on the Platform')
                    self.iface.messageBar().pushMessage(
                        'Error', error_msg, level=QgsMessageBar.CRITICAL)
                    return
                response = update_platform_project(
                    hostname, session, self.project_definition,
                    self.suppl_info['platform_layer_id'])
                if response.ok:
                    self.iface.messageBar().pushMessage(
                        tr("Info"),
                        tr(response.text),
                        level=QgsMessageBar.INFO)
                else:
                    self.iface.messageBar().pushMessage(
                        tr("Error"),
                        tr(response.text),
                        level=QgsMessageBar.CRITICAL)
        else:
            if DEBUG:
                print 'xml_file:', self.xml_file
            # do not upload the selected_project_definition_idx
            self.suppl_info.pop('selected_project_definition_idx', None)
            write_iso_metadata_file(self.xml_file,
                                    self.suppl_info)
            metadata_dialog = UploadDialog(
                self.iface, self.file_stem)
            metadata_dialog.upload_successful.connect(
                lambda layer_url: insert_platform_layer_id(
                    layer_url,
                    active_layer_id,
                    self.suppl_info))
            if metadata_dialog.exec_():
                QDesktopServices.openUrl(QUrl(metadata_dialog.layer_url))
            elif DEBUG:
                print "metadata_dialog cancelled"

        super(UploadSettingsDialog, self).accept()

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
