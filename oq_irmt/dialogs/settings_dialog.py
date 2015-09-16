# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
from PyQt4 import QtGui, QtCore

from oq_irmt.ui.ui_settings import Ui_SettingsDialog
from oq_irmt.utilities.shared import PLATFORM_REGISTRATION_URL


class SettingsDialog(QtGui.QDialog, Ui_SettingsDialog):
    """
    Dialog used to specify the connection settings used to interact with the
    OpenQuake Platform
    """
    def __init__(self, iface, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        # Set up the user interface from Designer.
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        link_text = ('<a href="%s">Register to the OpenQuake Platform</a>'
                     % PLATFORM_REGISTRATION_URL)
        self.ui.registration_link_lbl.setText(link_text)

        self.restoreState()

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        platform_username = mySettings.value('svir/platform_username', '')
        platform_password = mySettings.value('svir/platform_password', '')
        platform_hostname = mySettings.value(
            'svir/platform_hostname', 'https://platform.openquake.org')

        # hack for strange mac behaviour
        if not platform_username:
            platform_username = ''
        if not platform_password:
            platform_password = ''
        if not platform_hostname:
            platform_hostname = ''

        self.ui.usernameEdit.setText(platform_username)
        self.ui.passwordEdit.setText(platform_password)
        self.ui.hostnameEdit.setText(platform_hostname)

        self.ui.developermodeCheck.setChecked(
            mySettings.value('svir/developer_mode', False, type=bool))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        # if the (stripped) hostname ends with '/', remove it
        hostname = self.ui.hostnameEdit.text().strip().rstrip('/')
        mySettings.setValue('svir/platform_hostname', hostname)
        mySettings.setValue('svir/platform_username',
                            self.ui.usernameEdit.text())
        mySettings.setValue('svir/platform_password',
                            self.ui.passwordEdit.text())
        mySettings.setValue('svir/developer_mode',
                            self.ui.developermodeCheck.isChecked())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        self.close()
