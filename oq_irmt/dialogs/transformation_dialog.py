# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Integrated Risk Modelling Toolkit
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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)

from oq_irmt.ui.ui_transformation import Ui_TransformationDialog
from oq_irmt.calculations.transformation_algs import (RANK_VARIANTS,
                                 QUADRATIC_VARIANTS,
                                 LOG10_VARIANTS,
                                 TRANSFORMATION_ALGS)
from oq_irmt.utilities.shared import NUMERIC_FIELD_TYPES
from oq_irmt.calculations.process_layer import ProcessLayer


class TransformationDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to transform
    one or multiple attributes in the active layer, using one of the available
    algorithms and variants.
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.attr_name_user_def = False
        self.use_advanced = False
        # Set up the user interface from Designer.
        self.ui = Ui_TransformationDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.fill_fields_multiselect()

        alg_list = TRANSFORMATION_ALGS.keys()
        self.ui.algorithm_cbx.addItems(alg_list)
        if self.ui.algorithm_cbx.currentText() in ['RANK', 'QUADRATIC']:
            self.reload_variant_cbx()
        self.ui.inverse_ckb.setDisabled(
            self.ui.algorithm_cbx.currentText() in ['LOG10'])
        self.ui.warning_lbl.hide()
        self.ui.warning_lbl.setText(
            "<font color='red'>"
            "WARNING: the original attribute will be overwritten by the"
            " results of the transformation (it can not be undone)"
            "</font>")
        self.ui.fields_multiselect.selection_changed.connect(
            self.set_ok_button)
        self.ui.fields_multiselect.selection_changed.connect(
            self.set_new_field_editable)
        self.ui.fields_multiselect.selection_changed.connect(
            self.update_default_fieldname)
        self.set_ok_button()
        self.set_new_field_editable()

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.ui.fields_multiselect.selected_widget.count() > 0)

    def set_new_field_editable(self):
        n_fields_selected = self.ui.fields_multiselect.selected_widget.count()
        self.ui.new_field_name_lbl.setEnabled(n_fields_selected == 1)
        self.ui.new_field_name_txt.setEnabled(n_fields_selected == 1)

    @pyqtSlot(int)
    def on_overwrite_ckb_stateChanged(self):
        overwrite_checked = self.ui.overwrite_ckb.isChecked()
        self.ui.new_field_name_lbl.setDisabled(overwrite_checked)
        self.ui.new_field_name_txt.setDisabled(overwrite_checked)
        self.ui.track_new_field_ckb.setDisabled(overwrite_checked)
        if overwrite_checked:
            self.attr_name_user_def = False
            self.ui.warning_lbl.show()
        else:
            self.ui.warning_lbl.hide()
        self.update_default_fieldname()

    @pyqtSlot()
    def on_calc_btn_clicked(self):
        self.close()
        # layer is put in editing mode. If the user clicks on ok, the field
        # calculator will update the layers attributes.
        # if the user clicks cancel, the field calculator does nothing.
        # the layer stays in editing mode with the use_advanced flag set.
        # the calling code should take care of doing layer.commitChanges()
        # if the flag is set to true.
        self.use_advanced = True
        self.iface.activeLayer().startEditing()
        self.iface.actionOpenFieldCalculator().trigger()

    @pyqtSlot(str)
    def on_algorithm_cbx_currentIndexChanged(self):
        self.reload_variant_cbx()
        self.update_default_fieldname()

    @pyqtSlot(str)
    def on_variant_cbx_currentIndexChanged(self):
        self.update_default_fieldname()

    @pyqtSlot()
    def on_new_field_name_txt_editingFinished(self):
        self.attr_name_user_def = True
        new_field_name = self.ui.new_field_name_txt.text()
        # if the name of the new field is empty, automatically assign a name
        if not new_field_name:
            self.update_default_fieldname()

    @pyqtSlot(str)
    def on_new_field_name_txt_textEdited(self):
        # we assume exactly one item is in the selected list
        input_field_name = \
            self.ui.fields_multiselect.selected_widget.item(0).text()
        new_field_name = self.ui.new_field_name_txt.text()
        # if the name of the new field is equal to the name of the input field,
        # automatically check the 'overwrite' checkbox (and consequently
        # display the warning)
        if new_field_name == input_field_name:
            self.ui.overwrite_ckb.setChecked(True)

    def reload_variant_cbx(self):
        self.ui.variant_cbx.clear()
        self.ui.variant_cbx.setEnabled(True)
        if self.ui.algorithm_cbx.currentText() == 'RANK':
            self.ui.variant_cbx.addItems(RANK_VARIANTS)
        elif self.ui.algorithm_cbx.currentText() == 'QUADRATIC':
            self.ui.variant_cbx.addItems(QUADRATIC_VARIANTS)
        elif self.ui.algorithm_cbx.currentText() == 'LOG10':
            self.ui.variant_cbx.addItems(LOG10_VARIANTS)
        else:
            self.ui.variant_cbx.setDisabled(True)
        self.ui.inverse_ckb.setDisabled(
            self.ui.algorithm_cbx.currentText() in ['LOG10'])

    def update_default_fieldname(self):
        if self.ui.fields_multiselect.selected_widget.count() != 1:
            self.ui.new_field_name_txt.setText('')
            self.attr_name_user_def = False
            return
        if (not self.attr_name_user_def
                or not self.ui.new_field_name_txt.text()):
            attribute_name = \
                self.ui.fields_multiselect.selected_widget.item(0).text()
            algorithm_name = self.ui.algorithm_cbx.currentText()
            variant = self.ui.variant_cbx.currentText()
            inverse = self.ui.inverse_ckb.isChecked()
            if self.ui.overwrite_ckb.isChecked():
                new_attr_name = attribute_name
            else:
                new_attr_name = \
                    ProcessLayer(self.iface.activeLayer()).transform_attribute(
                        attribute_name, algorithm_name, variant,
                        inverse, simulate=True)
            self.ui.new_field_name_txt.setText(new_attr_name)
            self.attr_name_user_def = False

    def fill_fields_multiselect(self):
        field_names = [
            field.name()
            for field in self.iface.activeLayer().dataProvider().fields()
            if field.typeName() in NUMERIC_FIELD_TYPES]
        self.ui.fields_multiselect.set_unselected_items(field_names)
