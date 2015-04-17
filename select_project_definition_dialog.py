# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2015-04-16
        copyright            : (C) 2015 by GEM Foundation
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

import json
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox,
                         )
from qgis.core import QgsProject
from ui.ui_select_project_definition import Ui_SelectProjectDefinitionDialog


class SelectProjectDefinitionDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SelectProjectDefinitionDialog()
        self.ui.setupUi(self)
        self.cancel_button = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.project_definitions = None  # it will store the project
                                         # definitions for the active layer
        self.selected_idx = None  # index of the selected project definition
        self.get_project_definitions()
        self.populate_proj_def_cbx()

    def get_project_definitions(self):
        all_project_definitions_str, is_available = \
            QgsProject.instance().readEntry('svir', 'project_definitions')
        if is_available and all_project_definitions_str:
            all_project_definitions = json.loads(all_project_definitions_str)
            try:
                self.project_definitions = all_project_definitions[
                    self.iface.activeLayer().id()]
            except KeyError:
                self.project_definitions = {'selected_idx': None,
                                            'proj_defs': []}
                self.cancel_button.animateClick()
                return
        else:
            self.project_definitions = {'selected_idx': None, 'proj_defs': []}
        # TODO: Avoid opening the dialog if it's useless
        if len(self.project_definitions['proj_defs']) == 0:
            self.cancel_button.animateClick()
            return
        if len(self.project_definitions['proj_defs']) == 1:
            self.selected_idx = 0
            self.display_proj_def_details()
            self.ok_button.animateClick()
            return

    def populate_proj_def_cbx(self):
        for proj_def in self.project_definitions['proj_defs']:
            if 'title' in proj_def:
                self.ui.proj_def_cbx.addItem(proj_def['title'])
            else:
                self.ui.proj_def_cbx.addItem('Untitled project definition')

    def display_proj_def_details(self):
        # display the corresponding project definition in the textedit
        proj_def = self.project_definitions['proj_defs'][self.selected_idx]
        proj_def_str = json.dumps(proj_def,
                                  sort_keys=False,
                                  indent=2,
                                  separators=(',', ': '))
        self.ui.proj_def_detail.setText(proj_def_str)

    @pyqtSlot(str)
    def on_proj_def_cbx_currentIndexChanged(self):
        self.selected_idx = self.ui.proj_def_cbx.currentIndex()
        self.display_proj_def_details()
