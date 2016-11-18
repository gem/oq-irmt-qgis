# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
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

from copy import deepcopy
from qgis.core import QgsField, QgsExpression
from qgis.gui import QgsMessageBar

from PyQt4.QtCore import QVariant, QPyNullVariant

from svir.utilities.shared import (DOUBLE_FIELD_TYPE_NAME,
                                   STRING_FIELD_TYPE_NAME,
                                   DEBUG,
                                   SUM_BASED_OPERATORS,
                                   MUL_BASED_OPERATORS, DEFAULT_OPERATOR,
                                   OPERATORS_DICT,
                                   IGNORING_WEIGHT_OPERATORS,
                                   DiscardedFeature)
from svir.calculations.process_layer import ProcessLayer
from svir.utilities.utils import LayerEditingManager, tr, log_msg


class InvalidNode(Exception):
    pass


class InvalidOperator(Exception):
    pass


class InvalidChild(Exception):
    pass


def add_numeric_attribute(proposed_attr_name, layer):
    field = QgsField(proposed_attr_name, QVariant.Double)
    field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
    assigned_attr_names = ProcessLayer(layer).add_attributes(
        [field])
    assigned_attr_name = assigned_attr_names[proposed_attr_name]
    return assigned_attr_name


def add_textual_attribute(proposed_attr_name, layer):
    field = QgsField(proposed_attr_name, QVariant.String)
    field.setTypeName(STRING_FIELD_TYPE_NAME)
    assigned_attr_names = ProcessLayer(layer).add_attributes(
        [field])
    assigned_attr_name = assigned_attr_names[proposed_attr_name]
    return assigned_attr_name


def calculate_composite_variable(iface, layer, node):
    """
    Calculate a composite variable (a tree node that has children) starting
    from the children's values and inverters and using the operator defined
    for the node.
    While calculating a composite index, the tree can be modified. For
    instance, a theme that was not associated to any field in the layer, could
    be linked to a new field that is created before performing the calculation.
    For this reason, the function must return the modified tree, and the
    original tree needs to be modified accordingly.
    If the children of the node are not final leaves of the tree, the function
    will be called recursively to compute those children, before proceeding
    with the calculation of the node.

    :param iface: the iface, to be used to access the messageBar
    :param layer: the layer that contains the data to be used in the
                  calculation and that will be modified adding new fields if
                  needed
    :param node: the root node of the project definition's sub-tree to be
                 calculated

    :returns (added_attrs_ids, discarded_feats, node, any_change):
        added_attrs_ids: the set of ids of the attributes added to the layer
                         during the calculation
        discarded_feats: the set of DiscardedFeature that can't contribute to
                         the calculation, because of missing data or invalid
                         data (e.g. when it's impossible to calculate the
                         geometric mean because it causes the calculation of
                         the fractionary power of a negative value)
        node: the transformed (or unmodified) sub-tree
        any_change: True if the calculation caused any change in the
                    subtree
    """
    # Avoid touching the original node, and manipulate a copy instead.
    # If anything fails, the original node will be returned
    edited_node = deepcopy(node)
    # keep a list of attributes added to the layer, so they can be deleted if
    # the calculation can not be completed, and they can be notified to the
    # user if the calculation is done without errors
    added_attrs_ids = set()
    discarded_feats = set()
    any_change = False

    children = edited_node.get('children', [])
    if not children:
        # we don't calculate the values for a node that has no children
        return set(), set(), node, False
    for child_idx, child in enumerate(children):
        child_results = calculate_composite_variable(iface, layer, child)
        (child_added_attrs_ids, child_discarded_feats,
         child, child_was_changed) = child_results
        if child_added_attrs_ids:
            added_attrs_ids.update(child_added_attrs_ids)
        if child_discarded_feats:
            discarded_feats.update(child_discarded_feats)
        if child_was_changed:
            # update the subtree with the modified child
            # e.g., a theme might have been linked to a new layer's field
            edited_node['children'][child_idx] = deepcopy(child)
    try:
        node_attr_id, node_attr_name, field_was_added = \
            get_node_attr_id_and_name(edited_node, layer)
    except InvalidNode as e:
        iface.messageBar().pushMessage(tr('Error'), str(e),
                                       level=QgsMessageBar.CRITICAL)
        if added_attrs_ids:
            ProcessLayer(layer).delete_attributes(added_attrs_ids)
        return set(), set(), node, False
    if field_was_added:
        added_attrs_ids.add(node_attr_id)
    try:
        node_discarded_feats = calculate_node(edited_node,
                                              node_attr_name,
                                              node_attr_id,
                                              layer,
                                              discarded_feats)
    except (InvalidOperator, InvalidChild) as e:
        iface.messageBar().pushMessage(
            tr('Error'), str(e), level=QgsMessageBar.CRITICAL)
        if added_attrs_ids:
            ProcessLayer(layer).delete_attributes(added_attrs_ids)
        return set(), set(), node, False
    except TypeError as e:
        msg = ('Could not calculate the composite variable due'
               ' to data problems: %s' % e)
        iface.messageBar().pushMessage(tr('Error'), tr(msg),
                                       level=QgsMessageBar.CRITICAL)
        if added_attrs_ids:
            ProcessLayer(layer).delete_attributes(
                added_attrs_ids)
        return set(), set(), node, False

    discarded_feats.update(node_discarded_feats)
    edited_node['field'] = node_attr_name
    any_change = True
    return added_attrs_ids, discarded_feats, edited_node, any_change


def get_node_attr_id_and_name(node, layer):
    """
    Get the field (id and name) to be re-used to store the results of the
    calculation, if possible. Otherwise, add a new field to the layer and
    return its id and name.
    Also return True if a new field was added, or False if an old field
    was re-used.
    """
    field_was_added = False
    if 'field' in node:
        node_attr_name = node['field']
        # check that the field is still in the layer (the user might have
        # deleted it). If it is not there anymore, add a new field
        if layer.fieldNameIndex(node_attr_name) == -1:  # not found
            proposed_node_attr_name = node_attr_name
            node_attr_name = add_numeric_attribute(
                proposed_node_attr_name, layer)
            field_was_added = True
        elif DEBUG:
            log_msg('Reusing field %s' % node_attr_name)
    elif 'name' in node:
        proposed_node_attr_name = node['name']
        node_attr_name = add_numeric_attribute(
            proposed_node_attr_name, layer)
        field_was_added = True
    else:  # this corner case should never happen (hopefully)
        raise InvalidNode('This node has no name and it does'
                          ' not correspond to any field')
    # get the id of the new attribute
    node_attr_id = ProcessLayer(layer).find_attribute_id(
        node_attr_name)
    return node_attr_id, node_attr_name, field_was_added


def calculate_node(
        node, node_attr_name, node_attr_id, layer, discarded_feats):
    operator = node.get('operator', DEFAULT_OPERATOR)
    if operator == OPERATORS_DICT['CUSTOM']:
        description = node.get('fieldDescription', '')
        expression = QgsExpression(description)
        if description == '' or not expression.isValid():
            # use the custom field values instead of recalculating them
            for feat in layer.getFeatures():
                if feat[node['field']] == QPyNullVariant(float):
                    discard_feat = True
                    discarded_feat = DiscardedFeature(
                        feat.id(), 'Missing value')
                    discarded_feats.add(discarded_feat)
            return discarded_feats
        else:
            # attempt to retrieve a formula from the description and to
            # calculate the field values based on that formula
            expression.prepare(layer.fields())
            with LayerEditingManager(layer,
                                    'Calculating %s' % node_attr_name,
                                    DEBUG):
                for feat in layer.getFeatures():
                    value = expression.evaluate(feat)
                    if value == QPyNullVariant(float):
                        discard_feat = True
                        discarded_feat = DiscardedFeature(
                            feat.id(), 'Missing value')
                        discarded_feats.add(discarded_feat)
                    layer.changeAttributeValue(feat.id(), node_attr_id, value)
            return discarded_feats
    # the existance of children should already be checked
    children = node['children']
    with LayerEditingManager(layer,
                             'Calculating %s' % node_attr_name,
                             DEBUG):
        for feat in layer.getFeatures():
            # If a feature contains any NULL value, discard_feat will
            # be set to True and the corresponding node value will be
            # set to NULL
            discard_feat = False
            feat_id = feat.id()

            # init node_value to the correct value depending on the
            # node's operator
            if operator in SUM_BASED_OPERATORS:
                node_value = 0
            elif operator in MUL_BASED_OPERATORS:
                node_value = 1
            else:
                raise InvalidOperator('Invalid operator: %s' % operator)
            for child in children:
                if 'field' not in child:
                    raise InvalidChild()
                    # for instance, if the RI can't be calculated, then
                    # also the IRI can't be calculated
                    # But it shouldn't happen, because all the children
                    # should be previously linked to corresponding fields
                if feat[child['field']] == QPyNullVariant(float):
                    discard_feat = True
                    discarded_feat = DiscardedFeature(feat_id, 'Missing value')
                    discarded_feats.add(discarded_feat)
                    break  # proceed to the next feature
                # multiply a variable by -1 if it isInverted
                try:
                    inversion_factor = -1 if child['isInverted'] else 1
                except KeyError:  # child is not inverted
                    inversion_factor = 1
                if operator in IGNORING_WEIGHT_OPERATORS:
                    # although these operators ignore weights, they
                    # take into account the inversion
                    child_weighted = \
                        feat[child['field']] * inversion_factor
                else:  # also multiply by the weight
                    child_weighted = (
                        child['weight'] *
                        feat[child['field']] * inversion_factor)

                if operator in SUM_BASED_OPERATORS:
                    node_value += child_weighted
                elif operator in MUL_BASED_OPERATORS:
                    node_value *= child_weighted
                else:
                    error_message = 'Invalid operator: %s' % operator
                    raise RuntimeError(error_message)
            if discard_feat:
                node_value = QPyNullVariant(float)
            elif operator == OPERATORS_DICT['AVG']:
                # it is equivalent to do a weighted sum with equal weights, or
                # to do the simple sum (ignoring weights) and dividing by the
                # number of children (we use the latter solution)
                node_value /= len(children)  # for sure, len(children)!=0
            elif operator == OPERATORS_DICT['GEOM_MEAN']:
                # the geometric mean
                # (see http://en.wikipedia.org/wiki/Geometric_mean)
                # is the product of the N combined items, elevated by 1/N
                try:
                    node_value **= 1. / len(children)
                # it can raise ValueError: negative number cannot be raised
                #                          to a fractional power
                except ValueError:
                    node_value = QPyNullVariant(float)
                    discarded_feat = DiscardedFeature(feat_id, 'Invalid value')
                    discarded_feats.add(discarded_feat)
            layer.changeAttributeValue(
                feat_id, node_attr_id, node_value)
    return discarded_feats
