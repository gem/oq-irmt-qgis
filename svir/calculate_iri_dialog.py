# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant, QPyNullVariant
from PyQt4.QtGui import QDialog, QDialogButtonBox, QPushButton, QToolButton
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
                   tr, toggle_select_features)


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

        reload_layers_in_cbx(self.aal_layer, QgsMapLayer.VectorLayer)
        reload_attrib_cbx(self.svi_id_field, self.current_layer,
                          NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES)
        self.ok_button.setEnabled(True)

    def calculate(self):
        """
        add an SVI attribute to the current layer
        """

        indicators_combination = self.indicators_combination_type.currentText()
        themes_combination = self.themes_combination_type.currentText()

        themes = self.project_definition['children'][1]['children']
        svi_attr_name = 'SVI'
        svi_field = QgsField(svi_attr_name, QVariant.Double)
        svi_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        attr_names = ProcessLayer(self.current_layer).add_attributes(
            [svi_field])

        # get the id of the new attribute
        svi_attr_id = ProcessLayer(self.current_layer).find_attribute_id(
            attr_names[svi_attr_name])

        discarded_feats_ids = []
        try:
            with LayerEditingManager(self.current_layer, 'Add SVI', DEBUG):
                for feat in self.current_layer.getFeatures():
                    # If a feature contains any NULL value, discard_feat will
                    # be set to True and the corresponding SVI will be set to
                    # NULL
                    discard_feat = False
                    feat_id = feat.id()

                    # init svi_value to the correct value depending on
                    # themes_combination
                    if themes_combination in SUM_BASED_COMBINATIONS:
                        svi_value = 0
                    elif themes_combination in MUL_BASED_COMBINATIONS:
                        svi_value = 1

                    # iterate all themes of SVI
                    for theme in themes:
                        indicators = theme['children']

                        # init theme_result to the correct value depending on
                        # indicators_combination
                        if indicators_combination in SUM_BASED_COMBINATIONS:
                            theme_result = 0
                        elif indicators_combination in MUL_BASED_COMBINATIONS:
                            theme_result = 1

                        # iterate all indicators of a theme
                        for indicator in indicators:
                            if (feat[indicator['field']] ==
                                    QPyNullVariant(float)):
                                discard_feat = True
                                discarded_feats_ids.append(feat_id)
                                break
                            indicator_weighted = (feat[indicator['field']] *
                                                  indicator['weight'])
                            if indicators_combination in \
                                    SUM_BASED_COMBINATIONS:
                                theme_result += indicator_weighted
                            elif indicators_combination in \
                                    MUL_BASED_COMBINATIONS:
                                theme_result *= indicator_weighted
                        if discard_feat:
                            break
                        if indicators_combination == 'Average':
                            theme_result /= len(indicators)

                        # combine the indicators of each theme
                        theme_weighted = theme_result * theme['weight']
                        if themes_combination in SUM_BASED_COMBINATIONS:
                                svi_value += theme_weighted
                        elif themes_combination in MUL_BASED_COMBINATIONS:
                            svi_value *= theme_weighted
                    if discard_feat:
                        svi_value = QPyNullVariant(float)
                    else:
                        if themes_combination == 'Average':
                            svi_value /= len(themes)

                    self.current_layer.changeAttributeValue(
                        feat_id, svi_attr_id, svi_value)
            msg = ('The SVI has been calculated for fields containing'
                   'non-NULL values and it was added to the layer as '
                   'a new attribute called %s') % attr_names[svi_attr_name]
            self.iface.messageBar().pushMessage(
                tr("Info"), tr(msg), level=QgsMessageBar.INFO)
            if discarded_feats_ids:

                msg = 'Invalid indicators were found in some features'

                widget = self.iface.messageBar().createMessage(
                    tr("Warning"), msg)
                button = QToolButton(widget)
                button.setCheckable(True)
                button.setText("Select invalid features")
                current_feats_ids = self.current_layer.selectedFeaturesIds()
                button.toggled.connect(
                    lambda on, layer=self.current_layer,
                           new_feature_ids=discarded_feats_ids,
                           old_feature_ids=current_feats_ids:
                           toggle_select_features(layer,
                                                  on,
                                                  new_feature_ids,
                                                  old_feature_ids))
                widget.layout().addWidget(button)
                self.iface.messageBar().pushWidget(widget,
                                                   QgsMessageBar.WARNING)
        except TypeError as e:
            self.current_layer.dataProvider().deleteAttributes(
                [svi_attr_id])
            msg = 'Could not calculate SVI due to data problems: %s' % e
            self.iface.messageBar().pushMessage(tr("Error"),
                                                tr(msg),
                                                level=QgsMessageBar.CRITICAL)

        if self.calculate_iri_check.isChecked():
            self._calculateIRI(svi_attr_id, discarded_feats_ids)

    def _calculateIRI(self, svi_attr_id, discarded_feats_ids):
        """
        Copy the AAL and calculate an IRI attribute to the current layer
        """

        aal_weight = self.project_definition['children'][0]['weight']
        svi_weight = self.project_definition['children'][1]['weight']

        iri_combination = self.iri_combination_type.currentText()

        iri_attr_name = 'IRI'
        iri_field = QgsField(iri_attr_name, QVariant.Double)
        iri_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        copy_aal_attr_name = 'AAL'
        aal_field = QgsField(copy_aal_attr_name, QVariant.Double)
        aal_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)

        attr_names = ProcessLayer(self.current_layer).add_attributes(
            [aal_field, iri_field])

        # get the id of the new attributes
        iri_attr_id = ProcessLayer(self.current_layer).find_attribute_id(
            attr_names[iri_attr_name])
        copy_aal_attr_id = ProcessLayer(self.current_layer).find_attribute_id(
            attr_names[copy_aal_attr_name])

        join_layer = QgsMapLayerRegistry.instance().mapLayersByName(
            self.aal_layer.currentText())[0]
        join_info = QgsVectorJoinInfo()
        join_info.joinLayerId = join_layer.id()
        join_info.joinFieldName = self.aal_id_field.currentText()
        join_info.targetFieldName = self.svi_id_field.currentText()
        self.current_layer.addJoin(join_info)

        aal_attr_name = '%s_%s' % (self.aal_layer.currentText(),
                                   self.aal_field.currentText())

        try:
            with LayerEditingManager(self.current_layer, 'Add IRI', DEBUG):
                for feat in self.current_layer.getFeatures():
                    feat_id = feat.id()
                    svi_value = feat.attributes()[svi_attr_id]
                    aal_value = feat[aal_attr_name]
                    if feat_id in discarded_feats_ids:
                        iri_value = QPyNullVariant(float)
                    elif iri_combination == 'Sum':
                        iri_value = (
                            svi_value * svi_weight + aal_value * aal_weight)
                    elif iri_combination == 'Multiplication':
                        iri_value = (
                            svi_value * svi_weight * aal_value * aal_weight)
                    elif iri_combination == 'Average':
                        iri_value = (svi_value * svi_weight +
                                     aal_value * aal_weight) / 2.0

                    # copy AAL
                    self.current_layer.changeAttributeValue(
                        feat_id, copy_aal_attr_id, aal_value)
                    # store IRI
                    self.current_layer.changeAttributeValue(
                        feat_id, iri_attr_id, iri_value)
        except TypeError:
            self.current_layer.dataProvider().deleteAttributes(
                [iri_attr_id, copy_aal_attr_id])
            msg = 'Could not calculate IRI due to data problems'
            self.iface.messageBar().pushMessage(tr("Error"),
                                                tr(msg),
                                                level=QgsMessageBar.CRITICAL)
        finally:
            self.current_layer.removeJoin(join_info.joinLayerId)

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
