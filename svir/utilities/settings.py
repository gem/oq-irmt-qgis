
# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2015 by GEM Foundation
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

from PyQt4.QtCore import QSettings
from svir.dialogs.settings_dialog import SettingsDialog


def get_platform_credentials(iface):
    """
    Get from the QSettings the credentials to access the OpenQuake Platform

    :returns: tuple (hostname, username, password)

    """
    qs = QSettings()
    hostname = qs.value('irmt/platform_hostname', '')
    username = qs.value('irmt/platform_username', '')
    password = qs.value('irmt/platform_password', '')
    if not (hostname and username and password):
        SettingsDialog(iface).exec_()
        hostname = qs.value('irmt/platform_hostname', '')
        username = qs.value('irmt/platform_username', '')
        password = qs.value('irmt/platform_password', '')
    return hostname, username, password


def get_engine_credentials(iface):
    """
    Get from the QSettings the credentials to access the OpenQuake Engine

    :returns: tuple (hostname, username, password)

    """
    qs = QSettings()
    hostname = qs.value('irmt/engine_hostname', '')
    username = qs.value('irmt/engine_username', '')
    password = qs.value('irmt/engine_password', '')
    if not hostname:
        SettingsDialog(iface).exec_()
        hostname = qs.value('irmt/engine_hostname', '')
        username = qs.value('irmt/engine_username', '')
        password = qs.value('irmt/engine_password', '')
    return hostname, username, password
