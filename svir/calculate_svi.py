# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QVariant
from qgis.core import QgsField
from globals import DOUBLE_FIELD_TYPE_NAME, DEBUG
from process_layer import ProcessLayer
from ui.ui_calculate_svi import Ui_CalculateSVIDialog
from utils import LayerEditingManager


class CalculateSVIDialog(QtGui.QDialog, Ui_CalculateSVIDialog):
    def __init__(self, iface, current_layer, project_definition, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.current_layer = current_layer
        self.project_definition = project_definition
        self.setupUi(self)

    def calculate(self):
        """
        add an SVI attribute to the current layer
        """

        indicators_combination = self.indicators_combination_type.currentText()
        themes_combination = self.themes_combination_type.currentText()
        iri_combination = self.iri_combination_type.currentText()

        themes = self.project_definition['children'][1]['children']
        svi_attr_name = 'SVI'
        svi_field = QgsField(svi_attr_name, QVariant.Double)
        svi_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        ProcessLayer(self.current_layer).add_attributes([svi_field])

        # get the id of the new attribute
        svi_attr_id = ProcessLayer(self.current_layer).find_attribute_id(
            svi_attr_name)

        with LayerEditingManager(self.current_layer, 'Add SVI', DEBUG):
            for feat in self.current_layer.getFeatures():
                feat_id = feat.id()

                svi_value = 0
                for theme in themes:
                    indicators = theme['children']
                    theme_result = 0
                    for indicator in indicators:
                        indicator_weighted = (feat[indicator['field']] *
                                              indicator['weight'])
                        if indicators_combination in ['Average', 'Sum']:
                            theme_result += indicator_weighted
                        else:
                            theme_result *= indicator_weighted
                    if indicators_combination == 'Average':
                        theme_result /= len(indicators)

                    # combine the indicators of each theme
                    theme_weighted = theme_result * theme['weight']
                    if themes_combination in ['Average', 'Sum']:
                            svi_value += theme_weighted
                    else:
                        svi_value *= theme_weighted
                if themes_combination == 'Average':
                    svi_value /= len(themes)

                self.current_layer.changeAttributeValue(
                    feat_id, svi_attr_id, svi_value)