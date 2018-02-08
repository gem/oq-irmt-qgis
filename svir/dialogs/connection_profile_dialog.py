# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2018 by GEM Foundation
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


import json
from qgis.PyQt.QtCore import pyqtSlot, QSettings
from qgis.PyQt.QtGui import QDialog, QDialogButtonBox
from svir.utilities.utils import get_ui_class
from svir.utilities.shared import (
                                   DEFAULT_PLATFORM_PROFILES,
                                   DEFAULT_ENGINE_PROFILES,
                                   )

FORM_CLASS = get_ui_class('ui_connection_profile.ui')


class ConnectionProfileDialog(QDialog, FORM_CLASS):
    """
    Dialog used to create/edit a connection profile to let the plugin interact
    with the OpenQuake Platform or the OpenQuake Engine
    """
    def __init__(self, platform_or_engine, profile_name='', parent=None):
        QDialog.__init__(self, parent)
        assert platform_or_engine in ('platform', 'engine'), platform_or_engine

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.platform_or_engine = platform_or_engine
        self.initial_profile_name = profile_name
        if self.initial_profile_name:
            profiles = json.loads(
                QSettings().value(
                    'irmt/%s_profiles' % self.platform_or_engine,
                    (DEFAULT_PLATFORM_PROFILES
                     if self.platform_or_engine == 'platform'
                     else DEFAULT_ENGINE_PROFILES)))
            profile = profiles[self.initial_profile_name]
            self.profile_name_edt.setText(self.initial_profile_name)
            self.username_edt.setText(profile['username'])
            self.password_edt.setText(profile['password'])
            self.hostname_edt.setText(profile['hostname'])
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(self.initial_profile_name != '')

    @pyqtSlot(str)
    def on_profile_name_edt_textEdited(self, profile_name):
        self.ok_button.setEnabled(profile_name != '')

    def accept(self):
        # if the (stripped) hostname ends with '/', remove it
        hostname = self.hostname_edt.text().strip().rstrip('/')
        # if the (stripped) engine hostname ends with '/engine/', remove it
        if self.platform_or_engine == 'engine':
            hostname = (
                hostname[:-7] if hostname.endswith('/engine') else hostname)
        edited_profile_name = self.profile_name_edt.text()
        mySettings = QSettings()
        mySettings.setValue(
            'irmt/current_%s_profile' % self.platform_or_engine,
            edited_profile_name)
        profiles = json.loads(
            mySettings.value(
                'irmt/%s_profiles' % self.platform_or_engine,
                (DEFAULT_PLATFORM_PROFILES
                 if self.platform_or_engine == 'platform'
                 else DEFAULT_ENGINE_PROFILES)))
        profiles[edited_profile_name] = {
            'username': self.username_edt.text(),
            'password': self.password_edt.text(),
            'hostname': hostname}
        if edited_profile_name != self.initial_profile_name:
            if self.initial_profile_name in profiles:
                del profiles[self.initial_profile_name]
        mySettings.setValue(
            'irmt/%s_profiles' % self.platform_or_engine,
            json.dumps(profiles))
        super(ConnectionProfileDialog, self).accept()
