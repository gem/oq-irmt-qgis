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


from qgis.PyQt.QtCore import QUrl, pyqtSlot
from svir.dialogs.standalone_app_dialog import StandaloneAppDialog, GemApi
from svir.websocket.web_app import WebApp


class TaxtwebApp(WebApp):
    def __init__(self, wss, message_bar):
        super(TaxtwebApp, self).__init__('taxtweb', wss, message_bar)


class TaxtwebApi(GemApi):
    """
    API methods that are specific for the TaxtWEB application
    (other shared methods are defined in the CommonApi)
    """
    def __init__(self, message_bar, taxonomy_dlg, parent=None):
        super(TaxtwebApi, self).__init__(message_bar, parent)
        self.taxonomy_dlg = taxonomy_dlg

    @pyqtSlot(str)
    def point_to_taxonomy(self, url):
        qurl = QUrl("%s%s" % (self.parent().host, url))
        self.taxonomy_dlg.web_view.load(qurl)
        self.taxonomy_dlg.show()
        self.taxonomy_dlg.raise_()
