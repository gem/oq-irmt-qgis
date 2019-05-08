# -*- coding: utf-8 -*-
# /***************************************************************************
# HyBridge
#                                 A QGIS plugin
# OpenQuake Hybridge
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2017 by GEM Foundation
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

import os.path

from qgis.PyQt.QtCore import (
    QCoreApplication, QObject, QSettings, QTranslator, qVersion,
    )

# DO NOT REMOVE THIS
# noinspection PyUnresolvedReferences
import svir.resources_rc  # pylint: disable=unused-import  # NOQA


class HyBridge(QObject):

    def __init__(self, iface):
        super(HyBridge, self).__init__()
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'hybridge_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        raise RuntimeError("HY-Bridge, HY-Bridge")

    def unload(self):
        pass
