# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant, QPyNullVariant
from PyQt4.QtGui import QDialog, QDialogButtonBox, QToolButton
from qgis.core import QgsField, QgsMapLayerRegistry, QgsMapLayer, \
    QgsVectorJoinInfo
from qgis.gui import QgsMessageBar
from globals import DOUBLE_FIELD_TYPE_NAME, DEBUG, NUMERIC_FIELD_TYPES, \
    SUM_BASED_COMBINATIONS, MUL_BASED_COMBINATIONS, TEXTUAL_FIELD_TYPES
from process_layer import ProcessLayer
from ui.ui_calculate_iri import Ui_CalculateIRIDialog
from utils import (LayerEditingManager,
                   reload_attrib_cbx,
                   reload_layers_in_cbx,
                   tr)
from calculate_utils import calculate_iri, calculate_svi


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
