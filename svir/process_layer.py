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
import uuid
from types import NoneType
from PyQt4.QtCore import QVariant
from qgis import QPyNullVariant
from qgis.core import (QgsMapLayer,
                       QGis,
                       QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsField)
from utils import LayerEditingManager

from transformation_algs import (TRANSFORMATION_ALGS, transform)

from globals import DEBUG, DOUBLE_FIELD_TYPE_NAME


class ProcessLayer():

    def __init__(self, layer):
        self.layer = layer

    def add_attributes(self, attribute_list, simulate=False):
        """
        Add attributes to the layer

        :param attribute_list: list of QgsField to add to the layer
        :type attribute_list: list of QgsField

        :return: dict having as keys the elements of the list of attributes
        passed as input argument, and as values the actual names of the
        assigned attributes
        """
        with LayerEditingManager(self.layer, 'Add attributes', DEBUG):
            # add attributes
            layer_pr = self.layer.dataProvider()
            proposed_attribute_dict = {}
            proposed_attribute_list = []
            for input_attribute in attribute_list:
                input_attribute_name = input_attribute.name()[:10]
                proposed_attribute_name = input_attribute_name
                i = 1
                while True:
                    current_attribute_names = \
                        [attribute.name() for attribute in layer_pr.fields()]
                    if proposed_attribute_name in current_attribute_names:
                        # If the attribute is already assigned, change the
                        # proposed_attribute_name
                        i_num_digits = len(str(i))
                        # 10 = shapefile limit
                        # 1 = underscore
                        max_name_len = 10 - i_num_digits - 1
                        proposed_attribute_name = '%s_%d' % (
                            input_attribute_name[:max_name_len], i)
                        i += 1
                    else:
                        # If the attribute name is not already assigned,
                        # add it to the proposed_attribute_dict
                        proposed_attribute_dict[input_attribute_name] = \
                            proposed_attribute_name
                        input_attribute.setName(proposed_attribute_name)
                        proposed_attribute_list.append(input_attribute)
                        break
            if not simulate:
                added_ok = layer_pr.addAttributes(proposed_attribute_list)
                if not added_ok:
                    raise AttributeError(
                        'Unable to add attributes %s' %
                        proposed_attribute_list)
        return proposed_attribute_dict

    def delete_attributes(self, attribute_list):
        """
        Delete attributes from the layer

        :param attribute_list: list of id to remove from the layer
        :type attribute_list: list of int

        :return: true in case of success and false in case of failure
        """
        with LayerEditingManager(self.layer, 'Remove attributes', DEBUG):
            # remove attributes
            layer_pr = self.layer.dataProvider()
            if DEBUG:
                print "REMOVING %s" % attribute_list
            return layer_pr.deleteAttributes(attribute_list)

    def transform_attribute(
            self, input_attr_name, algorithm_name, variant="",
            inverse=False, new_attr_name=None, simulate=False):
        """
        Use one of the available transformation algorithms to transform an
        attribute of the layer, and add a new attribute with the
        transformed data
        """
        # get the id of the attribute named input_attr_name
        input_attr_id = self.find_attribute_id(input_attr_name)

        # build the name of the output transformed attribute
        # WARNING! Shape files support max 10 chars for attribute names
        if not new_attr_name:
            if variant:
                new_attr_name = algorithm_name[:5] + '_' + variant[:4]
            else:
                new_attr_name = algorithm_name[:10]
        else:
            new_attr_name = new_attr_name[:10]
        new_attr_name = new_attr_name.replace(' ', '_')
        field = QgsField(new_attr_name, QVariant.Double)
        field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        if simulate:
            attr_names_dict = self.add_attributes([field], simulate=simulate)
            # get the name actually assigned to the new attribute
            actual_new_attr_name = attr_names_dict[new_attr_name]
            return actual_new_attr_name

        # a dict will contain all the values for the chosen input attribute,
        # keeping as key, for each value, the id of the corresponding feature
        initial_dict = dict()
        for feat in self.layer.getFeatures():
            initial_dict[feat.id()] = feat[input_attr_id]

        # get the transformation algorithm from the register
        algorithm = TRANSFORMATION_ALGS[algorithm_name]

        # transform the values in the dictionary with the chosen algorithm
        try:
            transformed_dict = transform(
                initial_dict, algorithm, variant, inverse)
        except ValueError:
            raise
        except NotImplementedError:
            raise

        attr_names_dict = self.add_attributes([field], simulate=simulate)
        # get the name actually assigned to the new attribute
        actual_new_attr_name = attr_names_dict[new_attr_name]
        # get the id of the new attribute
        new_attr_id = self.find_attribute_id(actual_new_attr_name)

        with LayerEditingManager(
                self.layer, 'Write transformed values', DEBUG):
            for feat in self.layer.getFeatures():
                feat_id = feat.id()
                value = transformed_dict[feat_id]
                if type(value) not in (QPyNullVariant, NoneType):
                    value = float(value)
                self.layer.changeAttributeValue(feat_id, new_attr_id, value)
        return actual_new_attr_name

    def find_attribute_id(self, attribute_name):
        """
        Get the id of the attribute called attribute_name
        @param attribute_name: name of the attribute
        @return: id of the attribute, or raise AttributeError
        exception if not found
        """
        attribute_id = None
        pr = self.layer.dataProvider()
        for field_id, field in enumerate(pr.fields()):
            if field.name() == attribute_name:
                attribute_id = field_id
                return attribute_id
        # In case the attribute has not been found, raise exception
        raise AttributeError('Attribute name %s not found' % attribute_name)

    def duplicate_in_memory(self, new_name='', add_to_registry=False):
        """
        Return a memory copy of the layer

        :param new_name: The name of the copied layer.
        :type new_name: str

        :param add_to_registry: if True, the new layer will be added to
        the QgsMapRegistry
        :type: bool

        :returns: An in-memory copy of a layer.
        :rtype: QgsMapLayer

        """
        if new_name is '':
            new_name = self.layer.name() + ' TMP'

        if self.layer.type() == QgsMapLayer.VectorLayer:
            v_type = self.layer.wkbType()
            if v_type == QGis.WKBPoint:
                type_str = "point"
            elif v_type == QGis.WKBLineString:
                type_str = "linestring"
            elif v_type == QGis.WKBPolygon:
                type_str = "polygon"
            elif v_type == QGis.WKBMultiPoint:
                type_str = "multipoint"
            elif v_type == QGis.WKBMultiLineString:
                type_str = "multilinestring"
            elif v_type == QGis.WKBMultiPolygon:
                type_str = "multipolygon"
            else:
                raise TypeError('Layer type %s can not be accepted' % v_type)
        else:
            raise RuntimeError('Layer is not a VectorLayer')

        crs = self.layer.crs().authid().lower()
        my_uuid = str(uuid.uuid4())
        uri = '%s?crs=%s&index=yes&uuid=%s' % (type_str, crs, my_uuid)
        mem_layer = QgsVectorLayer(uri, new_name, 'memory')
        with LayerEditingManager(mem_layer, 'Duplicating layer', DEBUG):
            mem_provider = mem_layer.dataProvider()

            provider = self.layer.dataProvider()
            v_fields = provider.fields()

            fields = []
            for i in v_fields:
                fields.append(i)

            mem_provider.addAttributes(fields)

            for ft in provider.getFeatures():
                mem_provider.addFeatures([ft])

        if add_to_registry:
            if mem_layer.isValid():
                QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
            else:
                raise RuntimeError('Layer invalid')

        return mem_layer

    def is_type_in(self, type_list):
        """
        @param type_list: we want to check if the type of the layer is
        included in this list
        @return: True if the layer is a VectorLayer and its type is in the list
        """
        if self.layer.type() == QgsMapLayer.VectorLayer:
            v_type = self.layer.wkbType()
            if v_type == QGis.WKBPoint:
                type_str = "point"
            elif v_type == QGis.WKBLineString:
                type_str = "linestring"
            elif v_type == QGis.WKBPolygon:
                type_str = "polygon"
            elif v_type == QGis.WKBMultiPoint:
                type_str = "multipoint"
            elif v_type == QGis.WKBMultiLineString:
                type_str = "multilinestring"
            elif v_type == QGis.WKBMultiPolygon:
                type_str = "multipolygon"
            else:
                raise TypeError('Layer type %s can not be accepted' % v_type)
            return type_str in type_list
        else:
            return False
