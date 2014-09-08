# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2014-03-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
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
"""

from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox, QLabel, QLineEdit, QComboBox)
from PyQt4.QtGui import QSizePolicy

from ui.ui_create_weight_tree import Ui_CreateWeightTreeDialog
from globals import NUMERIC_FIELD_TYPES
from utils import reload_attrib_cbx


class CreateWeightTreeDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """

    def __init__(self, iface, layer, project_definition, merge_action):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_CreateWeightTreeDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.project_definition = project_definition
        self.layer = layer
        self.theme_boxes = None
        self.themes = None
        self.merge_action = merge_action

        self.generate_gui()
        self.populate_risk_field_cbx()
        try:
            risk_field = self.project_definition['risk_field']
            select_index = self.ui.risk_field_cbx.findText(risk_field)
            self.ui.risk_field_cbx.setCurrentIndex(select_index)
        except (TypeError, KeyError):
            pass
        self.ui.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(
            self.reset)

    def generate_gui(self):
        self.theme_boxes = []
        self.themes = set([''])
        dp = self.layer.dataProvider()
        fields = list(dp.fields())
        numeric_fields = [field for field in fields
                          if field.typeName() in NUMERIC_FIELD_TYPES]

        themes_list = []
        indicators_list = {}
        if self.project_definition:
            themes = self.project_definition['children'][1]['children']
            for theme in themes:
                themes_list.append(theme['name'])
                for indicator in theme['children']:
                    indicators_list[indicator['field']] = (theme['name'],
                                                           indicator['name'])

            # remove duplicates
            themes_list = list(set(themes_list))
            themes_list.sort()
        themes_list.insert(0, '')

        attribute_label = QLabel('Attribute')
        theme_label = QLabel('Theme')
        name_label = QLabel('Name')

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(5)
        theme_label.setSizePolicy(sizePolicy)
        name_label.setSizePolicy(sizePolicy)
        self.ui.grid_layout.addWidget(attribute_label, 0, 0)
        self.ui.grid_layout.addWidget(theme_label, 0, 1)
        self.ui.grid_layout.addWidget(name_label, 0, 2)

        for i, field in enumerate(numeric_fields, start=1):
            theme_name = ''
            indicator_name = ''
            if field.name() in indicators_list:
                theme_name = indicators_list[field.name()][0]
                indicator_name = indicators_list[field.name()][1]

            attribute_label = QLabel(field.name())
            attribute_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

            theme = QComboBox()
            theme.setEditable(True)
            theme.setDuplicatesEnabled(False)
            theme.setInsertPolicy(QComboBox.InsertAlphabetically)
            theme.addItems(themes_list)
            current_index = theme.findText(theme_name)
            current_index = current_index if current_index != -1 else 0
            theme.setCurrentIndex(current_index)
            theme.currentIndexChanged.connect(self.check_status)
            theme.lineEdit().editingFinished.connect(self.update_themes)
            self.theme_boxes.append(theme)

            name = QLineEdit(indicator_name)
            name.textChanged.connect(self.check_status)

            self.ui.grid_layout.addWidget(attribute_label, i, 0)
            self.ui.grid_layout.addWidget(theme, i, 1)
            self.ui.grid_layout.addWidget(name, i, 2)

        self.check_status()

    def update_themes(self):
        new_theme = self.sender().text()
        if new_theme not in self.themes:
            self.themes.update([new_theme])
            for theme_box in self.theme_boxes:
                # needed to avoid a strange behaviour when generating_gui
                if theme_box.findText(new_theme) == -1:
                    theme_box.addItem(new_theme)
            self.check_status()

    def indicators(self):
        indicators = []
        for i in range(1, self.ui.grid_layout.rowCount()):
            label = self.ui.grid_layout.itemAtPosition(i, 0).widget().text()
            theme = \
                self.ui.grid_layout.itemAtPosition(i, 1).widget().currentText()
            name = self.ui.grid_layout.itemAtPosition(i, 2).widget().text()
            if name:
                theme = theme if theme else ''
                indicators.append({'field': label,
                                   'theme': theme,
                                   'name': name})
        return indicators

    def check_status(self):
        valid_with_theme = True
        valid_without_theme = True
        enough_indicators = False

        for i in range(1, self.ui.grid_layout.rowCount()):
            theme = self.ui.grid_layout.itemAtPosition(
                i, 1).widget().currentText()
            name_field = self.ui.grid_layout.itemAtPosition(i, 2).widget()
            name = name_field.text()
            label = self.ui.grid_layout.itemAtPosition(i, 0).widget().text()

            if theme:
                valid_without_theme = False
                if name == '':
                    name_field.setText(label)
                    name = label

            if name:
                enough_indicators = True

            #either both or none are set
            if theme and name or (not theme and not name):
                continue
            else:
                valid_with_theme = False

        if valid_with_theme or valid_without_theme:
            if enough_indicators:
                self.ok_button.setEnabled(True)
            else:
                self.ok_button.setEnabled(False)
        else:
            self.ok_button.setDisabled(True)

    def reset(self):
        layout = self.ui.grid_layout
        # clear the layout as per
        # http://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt#answer-13103617
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        self.generate_gui()

    def populate_risk_field_cbx(self):
        reload_attrib_cbx(self.ui.risk_field_cbx,
                          self.iface.activeLayer(),
                          NUMERIC_FIELD_TYPES)
        self.ui.risk_field_cbx.insertItem(0, '')
        self.ui.risk_field_cbx.setCurrentIndex(0)

    @pyqtSlot()
    def on_merge_risk_btn_clicked(self):
        pre_fields_count = self.ui.risk_field_cbx.count()
        self.setDisabled(True)
        self.merge_action.trigger()
        self.populate_risk_field_cbx()
        self.setDisabled(False)
        post_fields_count = self.ui.risk_field_cbx.count()
        # a new field was added in the merge dialog
        if pre_fields_count < post_fields_count:
            self.ui.risk_field_cbx.setCurrentIndex(post_fields_count-1)