# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
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
from PyQt4.QtGui import (QDialog, QDialogButtonBox)
from ui.ui_set_project_definition import Ui_SetProjectDefinitionDialog


class SetProjectDefinitionDialog(QDialog, Ui_SetProjectDefinitionDialog):
    """
    Modal dialog giving to the user the possibility to select
    a layer and an attribute of the same layer, and then a transformation
    algorithm and one of its variants (if the algorithm has any).
    """
    def __init__(self, iface, project_definition):
        QDialog.__init__(self)
        self.iface = iface
        self.project_definition = project_definition
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.layer_name.setText("Project definition for layer: %s" %
                                iface.activeLayer().name())
        self.project_definition_te.setText(json.dumps(
            self.project_definition,
            sort_keys=False,
            indent=2,
            separators=(',', ': ')))

    def on_project_definition_te_textChanged(self):
        try:
            project_definition = self.project_definition_te.toPlainText()
            self.project_definition = json.loads(project_definition)
            self.ok_button.setEnabled(True)
        except ValueError:
            self.ok_button.setEnabled(False)

