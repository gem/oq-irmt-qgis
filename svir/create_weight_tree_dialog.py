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
                         QDialogButtonBox, QLabel, QLineEdit)
from PyQt4.QtWebKit import QWebSettings

from ui.ui_create_weight_tree import Ui_CreateWeightTreeDialog


class CreateWeightTreeDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """

    def __init__(self, iface, layer):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_CreateWeightTreeDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.project_definition = None
        self.layer = layer

        self.generate_gui()

    def generate_gui(self):
        dp = self.layer.dataProvider()
        fields = list(dp.fields())
        for i, field in enumerate(fields, start=1):
            label = QLabel(field.name())
            theme = QLineEdit()
            name = QLineEdit()
            self.ui.grid_layout.addWidget(label, i, 0)
            self.ui.grid_layout.addWidget(theme, i, 1)
            self.ui.grid_layout.addWidget(name, i, 2)

    def indicators(self):
        indicators = []
        for i in range(self.ui.grid_layout.rowCount()):
            label = self.ui.grid_layout.itemAtPosition(i, 0).widget().text()
            theme = self.ui.grid_layout.itemAtPosition(i, 1).widget().text()
            name = self.ui.grid_layout.itemAtPosition(i, 2).widget().text()
            if name and theme:
                indicators.append({'field': label,
                                   'theme': theme,
                                   'name': name})
        return indicators

