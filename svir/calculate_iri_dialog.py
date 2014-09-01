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

from ui.ui_calculate_iri import Ui_CalculateIRIDialog
from globals import NUMERIC_FIELD_TYPES, COMBINATION_TYPES, DEFAULT_COMBINATION
from calculate_utils import calculate_iri, calculate_svi
from utils import reload_attrib_cbx
from process_layer import ProcessLayer


class CalculateIRIDialog(QDialog, Ui_CalculateIRIDialog):

    def __init__(self, iface, current_layer, project_definition, parent=None):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.current_layer = current_layer
        self.project_definition = project_definition
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        reload_attrib_cbx(
            self.svi_field_cbx, current_layer, NUMERIC_FIELD_TYPES)
        reload_attrib_cbx(self.aal_field, current_layer, NUMERIC_FIELD_TYPES)
        self.ok_button.setEnabled(True)
        self.iri_combination_type.addItems(COMBINATION_TYPES)
        idx = self.iri_combination_type.findText(DEFAULT_COMBINATION)
        self.iri_combination_type.setCurrentIndex(idx)

    def calculate(self):
        """
        add an SVI attribute to the current layer
        """

        if self.recalculate_svi_check.isChecked():
            svi_attr_id, discarded_feats_ids = calculate_svi(
                self.iface, self.current_layer, self.project_definition)

        else:
            svi_attr_name = self.svi_field_cbx.currentText()
            svi_attr_id = ProcessLayer(
                self.current_layer).find_attribute_id(svi_attr_name)
            # FIXME: get the NULL values for the SVI attribute
            discarded_feats_ids = []

        aal_field_name = self.aal_field.currentText()
        iri_operator = self.iri_combination_type.currentText()
        calculate_iri(self.iface, self.current_layer,
                      self.project_definition, svi_attr_id,
                      aal_field_name, discarded_feats_ids, iri_operator)

    def on_recalculate_svi_check_toggled(self, on):
        self.svi_field_cbx.setEnabled(not on)

    def on_aal_field_currentIndexChanged(self, index):
        self.check_iri_fields()

    def check_iri_fields(self):
        valid_state = False
        if self.aal_field.currentText():
            valid_state = True
        self.ok_button.setEnabled(valid_state)
