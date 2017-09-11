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


class TaxtwebDialog(StandaloneAppDialog):
    """
    Dialog that embeds the OpenQuake TaxtWEB standalone application

    :param taxonomy_dlg: a reference to the TaxonomyDialog instance is needed
        to let the embedded TaxtWEB application open the Taxonomy application,
        pointing to the chosen page in the glossary
    """

    def __init__(self, taxonomy_dlg):
        self.taxonomy_dlg = taxonomy_dlg
        # sanity check (we need a reference to the taxonomy dialog, to
        # point to taxonomies selected in the TaxtWEB app)
        assert(self.taxonomy_dlg is not None)
        app_name = 'taxtweb'
        app_descr = 'OpenQuake TaxtWEB'
        gem_header_name = "Gem--Qgis-Oq-Irmt--Taxtweb"
        gem_header_value = "0.1.0"
        super(TaxtwebDialog, self).__init__(
            app_name, app_descr, gem_header_name, gem_header_value)
        self.gem_api = TaxtwebApi(
            self.host, self.message_bar, self.taxonomy_dlg)
        self.build_gui()


class TaxtwebApi(GemApi):
    """
    API methods that are specific for the TaxtWEB application
    (other shared methods are defined in the CommonApi)
    """
    def __init__(self, host, message_bar, taxonomy_dlg):
        super(TaxtwebApi, self).__init__(host, message_bar)
        self.taxonomy_dlg = taxonomy_dlg

    @pyqtSlot(str)
    def point_to_taxonomy(self, url):
        qurl = QUrl("%s%s" % (self.host, url))
        self.taxonomy_dlg.web_view.load(qurl)
        self.taxonomy_dlg.show()
        self.taxonomy_dlg.raise_()
