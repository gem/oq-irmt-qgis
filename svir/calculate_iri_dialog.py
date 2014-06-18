# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
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


from PyQt4.QtGui import QDialog, QDialogButtonBox
from qgis.core import QgsMapLayerRegistry, QgsMapLayer

from ui.ui_calculate_iri import Ui_CalculateIRIDialog
from globals import NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES
from calculate_utils import calculate_iri, calculate_svi
from utils import reload_attrib_cbx, reload_layers_in_cbx


class CalculateIRIDialog(QDialog, Ui_CalculateIRIDialog):

    def __init__(self, iface, current_layer, project_definition, parent=None):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.current_layer = current_layer
        self.project_definition = project_definition
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.calculate_iri = self.calculate_iri_check.isChecked()

        reload_layers_in_cbx(self.aal_layer,
                             [QgsMapLayer.VectorLayer],
                             [self.current_layer.id()])
        reload_attrib_cbx(self.svi_id_field, self.current_layer,
                          NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES)
        self.ok_button.setEnabled(True)

    def calculate(self):
        """
        add an SVI attribute to the current layer
        """

        indicators_operator = self.indicators_combination_type.currentText()
        themes_operator = self.themes_combination_type.currentText()

        svi_attr_id, discarded_feats_ids = calculate_svi(
            self.iface, self.current_layer, self.project_definition,
            indicators_operator, themes_operator)

        if self.calculate_iri_check.isChecked():
            aal_layer = self.aal_layer.currentText()
            aal_field = self.aal_field.currentText()
            aal_id_field = self.aal_id_field.currentText()
            svi_id_field = self.svi_id_field.currentText()
            iri_operator = self.iri_combination_type.currentText()

            calculate_iri(self.iface, self.current_layer,
                          self.project_definition, iri_operator, svi_attr_id,
                          svi_id_field, aal_layer, aal_field, aal_id_field,
                          discarded_feats_ids)
        else:
            self.project_definition.pop('iri_field', None)

    def on_calculate_iri_check_toggled(self, on):
        self.calculate_iri = on
        if self.calculate_iri:
            self.check_iri_fields()
        else:
            self.ok_button.setEnabled(True)

    def on_aal_field_currentIndexChanged(self, index):
        self.check_iri_fields()

    def on_aal_layer_currentIndexChanged(self, index):
        selected_layer = QgsMapLayerRegistry.instance().mapLayers().values()[
            self.aal_layer.currentIndex()]
        reload_attrib_cbx(self.aal_field, selected_layer, NUMERIC_FIELD_TYPES)
        reload_attrib_cbx(self.aal_id_field, selected_layer,
                          NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES)
        self.check_iri_fields()

    def check_iri_fields(self):
        valid_state = False
        if (self.aal_field.currentText() and self.aal_layer.currentText()
                and self.aal_id_field and self.svi_id_field):
            valid_state = True
        self.ok_button.setEnabled(valid_state)
