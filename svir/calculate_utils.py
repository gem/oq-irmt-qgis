# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant, QPyNullVariant
from PyQt4.QtGui import QToolButton
from qgis.core import QgsField, QgsMapLayerRegistry, QgsVectorJoinInfo
from qgis.gui import QgsMessageBar
from globals import DOUBLE_FIELD_TYPE_NAME, DEBUG, SUM_BASED_COMBINATIONS,\
    MUL_BASED_COMBINATIONS
from process_layer import ProcessLayer
from utils import (LayerEditingManager,
                   tr, toggle_select_features, toggle_select_features_widget)


def calculate_svi(iface, current_layer, project_definition,
                  indicators_operator, themes_operator):
    """
    add an SVI attribute to the current layer
    """
    themes = project_definition['children'][1]['children']
    svi_attr_name = 'SVI'
    svi_field = QgsField(svi_attr_name, QVariant.Double)
    svi_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
    attr_names = ProcessLayer(current_layer).add_attributes(
        [svi_field])

    # get the id of the new attribute
    svi_attr_id = ProcessLayer(current_layer).find_attribute_id(
        attr_names[svi_attr_name])

    discarded_feats_ids = []
    try:
        with LayerEditingManager(current_layer, 'Add SVI', DEBUG):
            for feat in current_layer.getFeatures():
                # If a feature contains any NULL value, discard_feat will
                # be set to True and the corresponding SVI will be set to
                # NULL
                discard_feat = False
                feat_id = feat.id()

                # init svi_value to the correct value depending on
                # themes_operator
                if themes_operator in SUM_BASED_COMBINATIONS:
                    svi_value = 0
                elif themes_operator in MUL_BASED_COMBINATIONS:
                    svi_value = 1

                # iterate all themes of SVI
                for theme in themes:
                    indicators = theme['children']

                    # init theme_result to the correct value depending on
                    # indicators_operator
                    if indicators_operator in SUM_BASED_COMBINATIONS:
                        theme_result = 0
                    elif indicators_operator in MUL_BASED_COMBINATIONS:
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
                        if indicators_operator in \
                                SUM_BASED_COMBINATIONS:
                            theme_result += indicator_weighted
                        elif indicators_operator in \
                                MUL_BASED_COMBINATIONS:
                            theme_result *= indicator_weighted
                    if discard_feat:
                        break
                    if indicators_operator == 'Average':
                        theme_result /= len(indicators)

                    # combine the indicators of each theme
                    theme_weighted = theme_result * theme['weight']
                    if themes_operator in SUM_BASED_COMBINATIONS:
                        svi_value += theme_weighted
                    elif themes_operator in MUL_BASED_COMBINATIONS:
                        svi_value *= theme_weighted
                if discard_feat:
                    svi_value = QPyNullVariant(float)
                else:
                    if themes_operator == 'Average':
                        svi_value /= len(themes)

                current_layer.changeAttributeValue(
                    feat_id, svi_attr_id, svi_value)
        msg = ('The SVI has been calculated for fields containing '
               'non-NULL values and it was added to the layer as '
               'a new attribute called %s') % attr_names[svi_attr_name]
        iface.messageBar().pushMessage(
            tr('Info'), tr(msg), level=QgsMessageBar.INFO)
        if discarded_feats_ids:
            widget = toggle_select_features_widget(
                tr('Warning'),
                tr('Invalid indicators were found in some features while '
                   'calculating SVI'),
                tr('Select invalid features'),
                current_layer,
                discarded_feats_ids,
                current_layer.selectedFeaturesIds())
            iface.messageBar().pushWidget(widget, QgsMessageBar.WARNING)

        project_definition['indicators_operator'] = indicators_operator
        project_definition['themes_operator'] = themes_operator
        project_definition['svi_field'] = attr_names[svi_attr_name]
        return svi_attr_id, discarded_feats_ids

    except TypeError as e:
        current_layer.dataProvider().deleteAttributes([svi_attr_id])
        msg = 'Could not calculate SVI due to data problems: %s' % e
        iface.messageBar().pushMessage(tr('Error'), tr(msg),
                                       level=QgsMessageBar.CRITICAL)


def calculate_iri(iface, current_layer, project_definition, iri_operator,
                  svi_attr_id, svi_id_field, aal_layer, aal_field, aal_id_field,
                  discarded_feats_ids):
    """
    Copy the AAL and calculate an IRI attribute to the current layer
    """

    aal_weight = project_definition['children'][0]['weight']
    svi_weight = project_definition['children'][1]['weight']

    iri_attr_name = 'IRI'
    iri_field = QgsField(iri_attr_name, QVariant.Double)
    iri_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
    copy_aal_attr_name = 'AAL'
    aal_attribute = QgsField(copy_aal_attr_name, QVariant.Double)
    aal_attribute.setTypeName(DOUBLE_FIELD_TYPE_NAME)

    attr_names = ProcessLayer(current_layer).add_attributes(
        [aal_attribute, iri_field])

    # get the id of the new attributes
    iri_attr_id = ProcessLayer(current_layer).find_attribute_id(
        attr_names[iri_attr_name])
    copy_aal_attr_id = ProcessLayer(current_layer).find_attribute_id(
        attr_names[copy_aal_attr_name])

    join_layer = QgsMapLayerRegistry.instance().mapLayersByName(aal_layer)[0]
    join_info = QgsVectorJoinInfo()
    join_info.joinLayerId = join_layer.id()
    join_info.joinFieldName = aal_id_field
    join_info.targetFieldName = svi_id_field
    current_layer.addJoin(join_info)

    aal_attr_name = '%s_%s' % (aal_layer, aal_field)
    discarded_aal_feats_ids = []

    try:
        with LayerEditingManager(current_layer, 'Add IRI', DEBUG):
            for feat in current_layer.getFeatures():
                feat_id = feat.id()
                svi_value = feat.attributes()[svi_attr_id]
                aal_value = feat[aal_attr_name]
                if (aal_value == QPyNullVariant(float)
                        or feat_id in discarded_feats_ids):
                    iri_value = QPyNullVariant(float)
                    discarded_aal_feats_ids.append(feat_id)
                elif iri_operator == 'Sum':
                    iri_value = (
                        svi_value * svi_weight + aal_value * aal_weight)
                elif iri_operator == 'Multiplication':
                    iri_value = (
                        svi_value * svi_weight * aal_value * aal_weight)
                elif iri_operator == 'Average':
                    iri_value = (svi_value * svi_weight +
                                 aal_value * aal_weight) / 2.0

                # copy AAL
                current_layer.changeAttributeValue(
                    feat_id, copy_aal_attr_id, aal_value)
                # store IRI
                current_layer.changeAttributeValue(
                    feat_id, iri_attr_id, iri_value)
        project_definition['iri_operator'] = iri_operator
        # set the field name for the copied AAL layer
        project_definition['aal_field'] = attr_names[copy_aal_attr_name]
        project_definition['joined_aal_field'] = aal_field
        project_definition['iri_field'] = attr_names[iri_attr_name]
        project_definition['aal_id_field'] = aal_id_field
        project_definition['svi_id_field'] = svi_id_field
        project_definition['aal_layer'] = aal_layer
        msg = ('The IRI has been calculated for fields containing '
               'non-NULL values and it was added to the layer as '
               'a new attribute called %s') % attr_names[iri_attr_name]
        iface.messageBar().pushMessage(tr('Info'), tr(msg),
                                       level=QgsMessageBar.INFO)
        widget = toggle_select_features_widget(
            tr('Warning'),
            tr('Invalid values were found in some features while calculating '
               'IRI'),
            tr('Select invalid features'),
            current_layer,
            discarded_aal_feats_ids,
            current_layer.selectedFeaturesIds())
        iface.messageBar().pushWidget(widget, QgsMessageBar.WARNING)

    except TypeError as e:
        current_layer.dataProvider().deleteAttributes(
            [iri_attr_id, copy_aal_attr_id])
        msg = 'Could not calculate IRI due to data problems: %s' % e
        iface.messageBar().pushMessage(tr('Error'), tr(msg),
                                       level=QgsMessageBar.CRITICAL)
    finally:
        current_layer.removeJoin(join_info.joinLayerId)
