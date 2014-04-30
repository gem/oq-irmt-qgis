# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QVariant
from qgis.core import QgsField
from globals import DOUBLE_FIELD_TYPE_NAME, DEBUG
from process_layer import ProcessLayer
from ui.ui_calculate_iri import Ui_CalculateIRIDialog
from utils import LayerEditingManager


class CalculateIRIDialog(QtGui.QDialog, Ui_CalculateIRIDialog):
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
        attr_names = ProcessLayer(self.current_layer).add_attributes(
            [svi_field])
        print attr_names

        # get the id of the new attribute
        svi_attr_id = ProcessLayer(self.current_layer).find_attribute_id(
            attr_names[svi_attr_name])

        with LayerEditingManager(self.current_layer, 'Add SVI', DEBUG):
            for feat in self.current_layer.getFeatures():
                feat_id = feat.id()

                sum_based_combinations = set(['Average', 'Sum'])
                mul_based_combinations = set(['Multiplication'])

                # init svi_value to the correct value depending on
                # themes_combination
                if themes_combination in sum_based_combinations:
                    svi_value = 0
                elif themes_combination in mul_based_combinations:
                    svi_value = 1

                # iterate all themes of SVI
                for theme in themes:
                    indicators = theme['children']

                    # init theme_result to the correct value depending on
                    # indicators_combination
                    if indicators_combination in sum_based_combinations:
                        theme_result = 0
                    elif indicators_combination in mul_based_combinations:
                        theme_result = 1

                    # iterate all indicators of a theme
                    for indicator in indicators:
                        indicator_weighted = (feat[indicator['field']] *
                                              indicator['weight'])
                        if indicators_combination in sum_based_combinations:
                            theme_result += indicator_weighted
                        elif indicators_combination in mul_based_combinations:
                            theme_result *= indicator_weighted
                    if indicators_combination == 'Average':
                        theme_result /= len(indicators)

                    # combine the indicators of each theme
                    theme_weighted = theme_result * theme['weight']
                    if themes_combination in sum_based_combinations:
                            svi_value += theme_weighted
                    elif themes_combination in mul_based_combinations:
                        svi_value *= theme_weighted
                if themes_combination == 'Average':
                    svi_value /= len(themes)

                self.current_layer.changeAttributeValue(
                    feat_id, svi_attr_id, svi_value)