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

import json

from PyQt4.QtCore import (Qt,
                          QUrl,
                          QSettings,
                          pyqtProperty,
                          pyqtSignal)

from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox, QLabel, QLineEdit, QComboBox,
                         QToolButton)
from PyQt4.QtWebKit import QWebSettings

from ui.ui_create_weight_tree import Ui_CreateWeightTreeDialog


class CreateWeightTreeDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """

    def __init__(self, iface, layer, project_definition):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_CreateWeightTreeDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.project_definition = project_definition
        self.layer = layer
        self.theme_boxes = []
        self.themes = ['']

        self.generate_gui()

    def generate_gui(self):
        dp = self.layer.dataProvider()
        fields = list(dp.fields())

        indicators_list = {}
        if self.project_definition:
            themes = self.project_definition['children'][1]['children']
            for theme in themes:
                for indicator in theme['children']:
                    indicators_list[indicator['field']] = (theme['name'],
                                                           indicator['name'])

        for i, field in enumerate(fields, start=1):
            theme_name = ''
            indicator_name = ''
            if field.name() in indicators_list:
                theme_name = indicators_list[field.name()][0]
                indicator_name = indicators_list[field.name()][1]

            label = QLabel(field.name())

            theme = QComboBox()
            theme.setEditable(True)
            theme.setDuplicatesEnabled(False)
            theme.setInsertPolicy(QComboBox.InsertAlphabetically)
            theme.addItem(theme_name)
            theme.addItem('')
            theme.currentIndexChanged.connect(self.check_status)
            theme.lineEdit().editingFinished.connect(
                lambda: self.update_themes(self.sender().parent()))
            self.theme_boxes.append(theme)

            name = QLineEdit(indicator_name)
            name.editingFinished.connect(self.check_status)

            self.ui.grid_layout.addWidget(label, i, 0)
            self.ui.grid_layout.addWidget(theme, i, 1)
            self.ui.grid_layout.addWidget(name, i, 2)

        self.check_status()

    def update_themes(self, new_theme_box):
        new_theme = new_theme_box.currentText()
        if new_theme not in self.themes:
            self.themes.append(new_theme)
            for theme_box in self.theme_boxes:
                theme_box.addItem(new_theme)
            self.check_status()

    def indicators(self):
        indicators = []
        for i in range(1, self.ui.grid_layout.rowCount()):
            label = self.ui.grid_layout.itemAtPosition(i, 0).widget().text()
            theme = self.ui.grid_layout.itemAtPosition(i, 1).widget().currentText()
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
        for i in range(1, self.ui.grid_layout.rowCount()):
            theme = self.ui.grid_layout.itemAtPosition(
                i, 1).widget().currentText()
            name = self.ui.grid_layout.itemAtPosition(i, 2).widget().text()

            if theme:
                valid_without_theme = False

            #either both or none are set
            if theme and name or (not theme and not name):
                continue
            else:
                valid_with_theme = False

        if valid_with_theme or valid_without_theme:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setDisabled(True)

