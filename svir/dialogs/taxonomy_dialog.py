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

from svir.dialogs.standalone_app_dialog import StandaloneAppDialog, GemApi


class TaxonomyDialog(StandaloneAppDialog):
    """
    Dialog that embeds the OpenQuake Taxonomy standalone application
    """

    def __init__(self):
        app_name = 'taxonomy'
        app_descr = 'OpenQuake Taxonomy'
        gem_header_name = "Gem--Qgis-Oq-Irmt--Taxonomy"
        gem_header_value = "0.1.0"
        super(TaxonomyDialog, self).__init__(
            app_name, app_descr, gem_header_name, gem_header_value)
        self.gem_api = TaxonomyApi(self.host, self.message_bar)
        self.build_gui()


class TaxonomyApi(GemApi):
    """
    API methods that are specific for the Taxonomy application
    (other shared methods are defined in the CommonApi)
    """
    pass
