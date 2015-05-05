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
                         QInputDialog)
from qgis.core import QgsProject
from ui.ui_projects_manager_dialog import Ui_ProjectsManagerDialog
from utils import tr
from shared import PROJECT_TEMPLATE


class ProjectsManagerDialog(QDialog):
    """
    Modal dialog allowing to select (and possibly edit) one of the project
    definitions available for the active layer, or for creating a new project
    definition
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_ProjectsManagerDialog()
        self.ui.setupUi(self)
        self.cancel_button = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.project_definitions = None  # it will store the project
                                         # definitions for the active layer
        self.selected_idx = None  # index of the selected project definition
        self.platform_layer_id = None  # id of the geonode layer on platform
        self.zone_label_field = None  # field containing zone identifiers
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
        else:
            self.project_definitions = {'selected_idx': None, 'proj_defs': []}
        for proj_def in self.project_definitions['proj_defs']:
            if 'platform_layer_id' in proj_def:
                self.platform_layer_id = proj_def['platform_layer_id']
            if 'zone_label_field' in proj_def:
                self.zone_label_field = proj_def['zone_label_field']

    def populate_proj_def_cbx(self):
        self.ui.proj_def_cbx.clear()
        for proj_def in self.project_definitions['proj_defs']:
            if 'title' in proj_def:
                self.ui.proj_def_cbx.addItem(proj_def['title'])
            else:
                self.ui.proj_def_cbx.addItem('Untitled project definition')
        if self.project_definitions['selected_idx'] is not None:
            self.ui.proj_def_cbx.setCurrentIndex(
                self.project_definitions['selected_idx'])

    def display_proj_def_details(self):
        # display the corresponding project definition in the textedit
        proj_def = self.project_definitions['proj_defs'][self.selected_idx]
        proj_def_str = json.dumps(proj_def,
                                  sort_keys=False,
                                  indent=2,
                                  separators=(',', ': '))
        self.ui.proj_def_detail.setText(proj_def_str)

    def add_proj_def(self, title):
        proj_def_template = PROJECT_TEMPLATE
        proj_def_template['title'] = title
        if self.platform_layer_id:
            proj_def_template['platform_layer_id'] = self.platform_layer_id
        if self.zone_label_field:
            proj_def_template['zone_label_field'] = self.zone_label_field
        self.project_definitions['proj_defs'].append(proj_def_template)
        self.project_definitions['selected_idx'] = len(
            self.project_definitions['proj_defs']) - 1
        self.populate_proj_def_cbx()

    @pyqtSlot(str)
    def on_proj_def_cbx_currentIndexChanged(self):
        self.selected_idx = self.ui.proj_def_cbx.currentIndex()
        self.display_proj_def_details()

    @pyqtSlot()
    def on_add_proj_def_btn_clicked(self):
        title, ok = QInputDialog().getText(
            self, tr('Assign a title'), tr('Project definition title'))
        if ok:
            self.add_proj_def(title)

    @pyqtSlot()
    def on_proj_def_detail_textChanged(self):
        try:
            project_definition = self.ui.proj_def_detail.toPlainText()
            self.project_definitions['proj_defs'][
                self.selected_idx] = json.loads(project_definition)
            self.ok_button.setEnabled(True)
        except ValueError as e:
            print e
            self.ok_button.setEnabled(False)
