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
from utils import reload_attrib_cbx

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
    def __init__(self, upload_size, iface, project_title=None):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_UploadSettingsDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        head_msg = ('The active layer and the current Project Definition'
                    ' will be uploaded to the Openquake Platform.\n\n'
                    '(About %s MB of data will be transmitted)'
                    % upload_size)
        self.ui.head_msg_lbl.setText(head_msg)
        if project_title:
            self.ui.title_le.setText(project_title)
        else:
            self.ui.title_le.setText(DEFAULTS['ISO19115_TITLE'])

        # if no field is selected, whe should not allow uploading
        self.zone_label_field_is_specified = False
        reload_attrib_cbx(
            self.ui.zone_label_field_cbx, iface.activeLayer(), True)

        for license, link in LICENSES:
            self.ui.license_cbx.addItem(license, link)
        self.ui.license_cbx.setCurrentIndex(
            self.ui.license_cbx.findText(DEFAULT_LICENSE[0]))

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.zone_label_field_is_specified
            and self.ui.confirm_chk.isChecked())

    @pyqtSlot(str)
    def on_zone_label_field_cbx_currentIndexChanged(self):
        zone_label_field = self.ui.zone_label_field_cbx.currentText()
        self.zone_label_field_is_specified = (zone_label_field != '')
        self.set_ok_button()

    @pyqtSlot(int)
    def on_confirm_chk_stateChanged(self):
        self.set_ok_button()

    @pyqtSlot()
    def on_license_info_btn_clicked(self):
        selected_license_index = self.ui.license_cbx.currentIndex()
        license_url = self.ui.license_cbx.itemData(selected_license_index)
        QDesktopServices.openUrl(QUrl(license_url))
