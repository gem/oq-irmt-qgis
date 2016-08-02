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

from PyQt4 import QtGui, QtCore

from svir.utilities.utils import get_ui_class
from svir.utilities.shared import PLATFORM_REGISTRATION_URL

FORM_CLASS = get_ui_class('ui_settings.ui')


class SettingsDialog(QtGui.QDialog, FORM_CLASS):
    """
    Dialog used to specify the connection settings used to interact with the
    OpenQuake Platform or the OpenQuake Engine, and to toggle the
    developer mode option.
    """
    def __init__(self, iface, parent=None, server='platform'):
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.server = server
        # Set up the user interface from Designer.
        self.setupUi(self)
        if self.server == 'platform':
            self.topGroupBox.setTitle(
                'OpenQuake Platform connection settings')
            link_text = ('<a href="%s">Register to the OpenQuake Platform</a>'
                         % PLATFORM_REGISTRATION_URL)
            self.registration_link_lbl.setText(link_text)
        elif self.server == 'engine':
            self.topGroupBox.setTitle(
                'OpenQuake Engine connection settings')
            self.registration_link_lbl.hide()
        else:
            raise ValueError(self.server)
        self.restoreState()

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QtCore.QSettings()

        if self.server == 'platform':
            username = mySettings.value('irmt/platform_username', '')
            password = mySettings.value('irmt/platform_password', '')
            hostname = mySettings.value(
                'irmt/platform_hostname', 'https://platform.openquake.org')

        elif self.server == 'engine':
            username = mySettings.value('irmt/engine_username', '')
            password = mySettings.value('irmt/engine_password', '')
            hostname = mySettings.value('irmt/engine_hostname',
                                        'localhost:8000')
        else:
            raise ValueError(self.server)

        # hack for strange mac behaviour
        if not username:
            username = ''
        if not password:
            password = ''
        if not hostname:
            hostname = ''

        self.usernameEdit.setText(username)
        self.passwordEdit.setText(password)
        self.hostnameEdit.setText(hostname)

        self.developermodeCheck.setChecked(
            mySettings.value('irmt/developer_mode', False, type=bool))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        # if the (stripped) hostname ends with '/', remove it
        hostname = self.hostnameEdit.text().strip().rstrip('/')
        if self.server == 'platform':
            mySettings.setValue('irmt/platform_hostname', hostname)
            mySettings.setValue('irmt/platform_username',
                                self.usernameEdit.text())
            mySettings.setValue('irmt/platform_password',
                                self.passwordEdit.text())
            mySettings.setValue('irmt/developer_mode',
                                self.developermodeCheck.isChecked())
        elif self.server == 'engine':
            mySettings.setValue('irmt/engine_hostname', hostname)
            mySettings.setValue('irmt/engine_username',
                                self.usernameEdit.text())
            mySettings.setValue('irmt/engine_password',
                                self.passwordEdit.text())
            mySettings.setValue('irmt/developer_mode',
                                self.developermodeCheck.isChecked())
        else:
            raise ValueError(self.server)

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        super(SettingsDialog, self).accept()
