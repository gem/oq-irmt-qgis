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
from PyQt4.QtCore import QVariant
from qgis import QPyNullVariant
from qgis.core import QgsField
from qgis.gui import QgsMessageBar
from shared import (DOUBLE_FIELD_TYPE_NAME, DEBUG, SUM_BASED_OPERATORS,
                    MUL_BASED_OPERATORS, DEFAULT_OPERATOR, OPERATORS_DICT,
                    IGNORING_WEIGHT_OPERATORS)
from process_layer import ProcessLayer
from utils import LayerEditingManager, tr


def add_numeric_attribute(proposed_attr_name, layer):
        field = QgsField(proposed_attr_name, QVariant.Double)
        field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
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

    :param iface: the iface, to be used to access the messageBar
    :param layer: the layer that contains the data to be used in the
                  calculation and that will be modified adding new fields if
                  needed
    :param node: the root node of the project definition's sub-tree to be
                 calculated

    :returns (added_attrs_ids, discarded_feats_ids, node):
        added_attrs_ids: the list of ids of the attributes added to the layer
                         during the calculation
        discarded_feats_ids: the ids of the features that can't contribute to
                             the calculation, because of missing data
        node: the transformed (or unmodified) sub-tree
        any_change: True if the calculation caused any change in the
                    subtree
    """
    original_subtree = node
    added_attrs_ids = []
    try:
        children = node['children']
    except KeyError:
        children = []
    if len(children) < 1:
        # we can't calculate the values for a node that has no children
        return [], [], original_subtree, False
    else:
        for child_idx, child in enumerate(children):
            child_added_attrs_ids, _, child, child_was_changed = \
                calculate_composite_variable(iface, layer, child)
            if child_added_attrs_ids:
                added_attrs_ids.extend(child_added_attrs_ids)
            if child_was_changed:
                # update the subtree with the modified child
                node['children'][child_idx] = child
    operator = node.get('operator', DEFAULT_OPERATOR)
    if 'field' in node:
        node_attr_name = node['field']
        # check that the field is still in the layer (the user might have
        # deleted it). If it is not there anymore, add a new field
        if layer.fieldNameIndex(node_attr_name) == -1:
            proposed_node_attr_name = node_attr_name
            node_attr_name = add_numeric_attribute(
                proposed_node_attr_name, layer)
        elif DEBUG:
            print 'Reusing %s for node' % node_attr_name
    elif 'name' in node:
        proposed_node_attr_name = node['name']
        node_attr_name = add_numeric_attribute(
            proposed_node_attr_name, layer)
    else:  # this corner case should never happen (hopefully)
        msg = 'This node has no name and it does not correspond to any field'
        iface.messageBar().pushMessage(tr('Error'), tr(msg),
                                       level=QgsMessageBar.CRITICAL)
        if added_attrs_ids:
            ProcessLayer(layer).delete_attributes(added_attrs_ids)
        return [], [], original_subtree, False
    # get the id of the new attribute
    node_attr_id = ProcessLayer(layer).find_attribute_id(
        node_attr_name)
    added_attrs_ids.append(node_attr_id)

    discarded_feats_ids = set()
    try:
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
                    msg = 'Invalid operator: %s' % operator
                    iface.messageBar().pushMessage(
                        tr('Error'), tr(msg), level=QgsMessageBar.CRITICAL)
                    if added_attrs_ids:
                        ProcessLayer(layer).delete_attributes(added_attrs_ids)
                    return [], [], original_subtree, False
                for child in children:
                    if 'field' not in child:
                        # for instance, if the RI can't be calculated, then
                        # also the IRI can't be calculated
                        # But it shouldn't happen, because all the children
                        # should be previously linked to corresponding fields
                        if added_attrs_ids:
                            ProcessLayer(layer).delete_attributes(
                                added_attrs_ids)
                        return [], [], original_subtree, False
                    if feat[child['field']] == QPyNullVariant(float):
                        discard_feat = True
                        discarded_feats_ids.add(feat_id)
                        break  # proceed to the next feature

                    # For "Average (equal weights)" it's equivalent to use
                    # equal weights, or to sum the indicators
                    # (all weights 1)
                    # and divide by the number of indicators (we use
                    # the latter solution)

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
                    node_value /= len(children)  # for sure, len(children)!=0
                layer.changeAttributeValue(
                    feat_id, node_attr_id, node_value)

        node['field'] = node_attr_name
        any_change = True
        return added_attrs_ids, discarded_feats_ids, node, any_change

    except TypeError as e:
        ProcessLayer(layer).delete_attributes([node_attr_id])
        msg = ('Could not calculate the composite variable due'
               ' to data problems: %s' % e)
        iface.messageBar().pushMessage(tr('Error'), tr(msg),
                                       level=QgsMessageBar.CRITICAL)
        if added_attrs_ids:
            ProcessLayer(layer).delete_attributes(
                added_attrs_ids)
        return [], [], original_subtree, False
