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


from PyQt4.QtCore import QDir, QSettings, pyqtSlot
from PyQt4.QtGui import QFileDialog, QDialog
from svir.utilities.utils import get_ui_class
from svir.utilities.shared import PLATFORM_REGISTRATION_URL

FORM_CLASS = get_ui_class('ui_settings.ui')


class SettingsDialog(QDialog, FORM_CLASS):
    """
    Dialog used to specify the connection settings used to interact with the
    OpenQuake Platform or the OpenQuake Engine, and to toggle the
    developer mode option.
    """
    def __init__(self, iface, irmt_main=None, parent=None):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        # in order to reset login when new credentials are saved
        self.irmt_main = irmt_main
        # Set up the user interface from Designer.
        self.setupUi(self)
        link_text = ('<a href="%s">Register to the OpenQuake Platform</a>'
                     % PLATFORM_REGISTRATION_URL)
        self.registration_link_lbl.setText(link_text)
        self.restoreState()

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QSettings()

        platform_username = mySettings.value('irmt/platform_username', '')
        platform_password = mySettings.value('irmt/platform_password', '')
        platform_hostname = mySettings.value(
                'irmt/platform_hostname', 'https://platform.openquake.org')

        engine_username = mySettings.value('irmt/engine_username', '')
        engine_password = mySettings.value('irmt/engine_password', '')
        engine_hostname = mySettings.value(
                'irmt/engine_hostname', 'http://localhost:8800')

        # hack for strange mac behaviour
        if not platform_username:
            platform_username = ''
        if not platform_password:
            platform_password = ''
        if not platform_hostname:
            platform_hostname = ''
        if not engine_username:
            engine_username = ''
        if not engine_password:
            engine_password = ''
        if not engine_hostname:
            engine_hostname = ''

        self.platformUsernameEdit.setText(platform_username)
        self.platformPasswordEdit.setText(platform_password)
        self.platformHostnameEdit.setText(platform_hostname)
        self.engineUsernameEdit.setText(engine_username)
        self.enginePasswordEdit.setText(engine_password)
        self.engineHostnameEdit.setText(engine_hostname)

        self.developermodeCheck.setChecked(
                mySettings.value('irmt/developer_mode', False, type=bool))
        self.warnOQDepsCheck.setChecked(
                mySettings.value('irmt/oq_deps_warn', True, type=bool))
        self.oq_hazardlib_path_edit.setText(
                mySettings.value('irmt/oq_hazardlib_path', ''))
        self.oq_engine_path_edit.setText(
                mySettings.value('irmt/oq_engine_path', ''))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QSettings()
        # if the (stripped) hostname ends with '/', remove it
        platform_hostname = \
            self.platformHostnameEdit.text().strip().rstrip('/')
        engine_hostname = self.engineHostnameEdit.text().strip().rstrip('/')
        mySettings.setValue('irmt/oq_hazardlib_path',
                            self.oq_hazardlib_path_edit.text())
        mySettings.setValue('irmt/oq_engine_path',
                            self.oq_engine_path_edit.text())
        mySettings.setValue('irmt/oq_deps_warn',
                            self.warnOQDepsCheck.isChecked())
        mySettings.setValue('irmt/developer_mode',
                            self.developermodeCheck.isChecked())
        mySettings.setValue('irmt/platform_hostname', platform_hostname)
        mySettings.setValue('irmt/platform_username',
                            self.platformUsernameEdit.text())
        mySettings.setValue('irmt/platform_password',
                            self.platformPasswordEdit.text())
        mySettings.setValue('irmt/developer_mode',
                            self.developermodeCheck.isChecked())
        mySettings.setValue('irmt/engine_hostname', engine_hostname)
        mySettings.setValue('irmt/engine_username',
                            self.engineUsernameEdit.text())
        mySettings.setValue('irmt/engine_password',
                            self.enginePasswordEdit.text())
        mySettings.setValue('irmt/developer_mode',
                            self.developermodeCheck.isChecked())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        if self.irmt_main is not None:
            self.irmt_main.reset_engine_login()
        super(SettingsDialog, self).accept()

    @pyqtSlot()
    def on_oq_hazardlib_path_btn_clicked(self):
        path = QFileDialog.getExistingDirectory(
            self, self.tr('Choose OQ hazardlib directory'), QDir.homePath())
        if path:
            self.oq_hazardlib_path_edit.setText(path)

    @pyqtSlot()
    def on_oq_engine_path_btn_clicked(self):
        path = QFileDialog.getExistingDirectory(
                self, self.tr('Choose OQ engine directory'), QDir.homePath())
        if path:
            self.oq_engine_path_edit.setText(path)
