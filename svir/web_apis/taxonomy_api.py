# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2016 by GEM Foundation
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

from qgis.PyQt.QtGui import QIcon
from hybridge.websocket.web_api import WebApi


class TaxonomyApi(WebApi):
    def __init__(self, plugin, plugin_name,
                 action, message_bar, parent=None):
        super().__init__(plugin, plugin_name, 'taxonomy', action,
                         message_bar)
        self.icon_standard = QIcon(":/plugins/irmt/taxonomy.svg")
        self.icon_connected = QIcon(":/plugins/irmt/taxonomy_connected.svg")
