# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Integrated Risk Modelling Toolkit
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
from copy import deepcopy
from qgis.core import QgsProject

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox,
                         QInputDialog)

from svir.ui.ui_projects_manager_dialog import Ui_ProjectsManagerDialog
from svir.utilities.utils import tr
from svir.utilities.shared import PROJECT_TEMPLATE


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
        self.suppl_info = {}
        self.selected_proj_def = None
        self.get_suppl_info()
        self.populate_proj_def_cbx()

    def get_suppl_info(self):
        active_layer_id = self.iface.activeLayer().id()
        suppl_info_str, is_available = \
            QgsProject.instance().readEntry('irmt', active_layer_id)
        if is_available and suppl_info_str:
            self.suppl_info = json.loads(suppl_info_str)

    # NOTE: Still unused
    def get_selected_proj_def(self):
        try:
            selected_idx = self.suppl_info['selected_project_definition_idx']
            self.selected_proj_def = self.suppl_info['project_definitions'][
                selected_idx]
        except KeyError:
            return None

    def populate_proj_def_cbx(self):
        self.ui.proj_def_cbx.blockSignals(True)
        self.ui.proj_def_cbx.clear()
        for proj_def in self.suppl_info['project_definitions']:
            if 'title' in proj_def:
                self.ui.proj_def_cbx.addItem(proj_def['title'])
            else:
                self.ui.proj_def_cbx.addItem('Untitled project definition')
        if ('selected_project_definition_idx' in self.suppl_info
                and self.suppl_info['selected_project_definition_idx']
                is not None):
            self.ui.proj_def_cbx.setCurrentIndex(
                self.suppl_info['selected_project_definition_idx'])
        self.ui.proj_def_cbx.blockSignals(False)
        self.update_form()

    def update_proj_def_title(self):
        if self.selected_proj_def is not None:
            try:
                self.ui.proj_def_title.setText(self.selected_proj_def['title'])
            except KeyError:
                self.ui.proj_def_title.setText('')

    def update_proj_def_descr(self):
        if self.selected_proj_def is not None:
            try:
                self.ui.proj_def_descr.setPlainText(
                    self.selected_proj_def['description'])
            except KeyError:
                self.ui.proj_def_descr.setPlainText('')

    def display_proj_def_raw(self):
        proj_def_str = json.dumps(self.selected_proj_def,
                                  sort_keys=False,
                                  indent=2,
                                  separators=(',', ': '))
        self.ui.proj_def_raw.setPlainText(proj_def_str)

    def add_proj_def(self, title, proj_def=None):
        if proj_def is None:
            proj_def = deepcopy(PROJECT_TEMPLATE)
        proj_def['title'] = title
        self.suppl_info['project_definitions'].append(proj_def)
        self.suppl_info['selected_project_definition_idx'] = \
            len(self.suppl_info['project_definitions']) - 1
        self.populate_proj_def_cbx()

    def update_title_in_combo(self):
        current_index = self.ui.proj_def_cbx.currentIndex()
        self.ui.proj_def_cbx.setItemText(
            current_index, self.ui.proj_def_title.text())

    @pyqtSlot(str)
    def on_proj_def_title_textEdited(self):
        self.selected_proj_def['title'] = self.ui.proj_def_title.text()
        self.update_title_in_combo()
        self.display_proj_def_raw()

    @pyqtSlot()
    def on_proj_def_descr_textChanged(self):
        self.selected_proj_def['description'] = \
            self.ui.proj_def_descr.toPlainText()
        self.display_proj_def_raw()

    def update_form(self):
        self.suppl_info['selected_project_definition_idx'] = \
            self.ui.proj_def_cbx.currentIndex()
        self.selected_proj_def = self.suppl_info['project_definitions'][
            self.suppl_info['selected_project_definition_idx']]
        self.update_proj_def_title()
        self.update_proj_def_descr()
        self.display_proj_def_raw()

    @pyqtSlot(str)
    def on_proj_def_cbx_currentIndexChanged(self):
        self.update_form()

    @pyqtSlot()
    def on_clone_btn_clicked(self):
        title = (self.selected_proj_def['title'] + ' (copy)'
                 if 'title' in self.selected_proj_def
                 else '(copy)')
        title, ok = QInputDialog().getText(self,
                                           tr('Assign a title'),
                                           tr('Project definition title'),
                                           text=title)
        if ok:
            self.add_proj_def(title, self.selected_proj_def)

    @pyqtSlot()
    def on_add_proj_def_btn_clicked(self):
        title, ok = QInputDialog().getText(
            self, tr('Assign a title'), tr('Project definition title'))
        if ok:
            self.add_proj_def(title)

    @pyqtSlot()
    def on_proj_def_raw_textChanged(self):
        try:
            project_definition_str = self.ui.proj_def_raw.toPlainText()
            project_definition = json.loads(project_definition_str)
            self.suppl_info['project_definitions'][self.suppl_info[
                'selected_project_definition_idx']] = project_definition
            self.ok_button.setEnabled(True)
        except ValueError as e:
            print e
            self.ok_button.setEnabled(False)
