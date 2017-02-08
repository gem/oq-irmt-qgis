# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2014 by GEM Foundation
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

import sys

import uuid
from numpy.testing import assert_almost_equal
from pprint import pformat
from types import NoneType
from PyQt4.QtCore import QPyNullVariant
from qgis.core import (QgsMapLayer,
                       QGis,
                       QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsField)

from PyQt4.QtCore import QVariant
from svir.calculations.transformation_algs import TRANSFORMATION_ALGS, \
    transform
from svir.utilities.shared import DEBUG, DOUBLE_FIELD_TYPE_NAME

from svir.utilities.utils import LayerEditingManager, tr, log_msg


class ProcessLayer():
    """
    Set of utilities to manage a layer or compare layers.

    :param layer: layer to be processed
    :type layer: QgsVectorLayer

    An example of usage:

    .. code-block:: python

       has_same_content = \\
           ProcessLayer(a_layer).has_same_content_as(another_layer)

    """
    def __init__(self, layer):
        self.layer = layer

    def pprint(self, usage='gui'):
        """
        Pretty print the contents of the layer

        :param usage:
            it can be either 'gui' or 'testing', indicating if the output has
            to be written to the QGIS logging system (default) or to stderr as
            it is useful for testing
        """
        if usage == 'gui':
            logger_func = log_msg
            spacer = ''
        elif usage == 'testing':
            logger_func = sys.stderr.write
            spacer = '\n'
        else:
            raise ValueError('Usage "%s" is not implemented')
        logger_func(spacer + 'Layer: %s' % self.layer.name())
        logger_func(spacer + str(
            [field.name() for field in self.layer.fields()]))
        ppdata = pformat(
            [feature.attributes()
             for feature in self.layer.getFeatures()])
        logger_func(spacer + ppdata)

    def has_same_projection_as(self, other_layer):
        """
        Check if the layer uses the same projection as another layer

        :param other_layer: layer to compare with
        :type other_layer: QgsVectorLayer
        :returns: (bool, str):

            (True, msg)
                if the layers use the same coordinates,
                specifying the projection in the message

            (False, msg)
                if they use different projections,
                specifying the projections in the message
        """
        this_layer_projection = self.layer.crs().geographicCRSAuthId()
        other_layer_projection = other_layer.crs().geographicCRSAuthId()
        if (this_layer_projection != other_layer_projection):
            msg = tr("The two layers use different coordinate"
                     " reference systems (%s vs %s)"
                     % (this_layer_projection, other_layer_projection))
            return False, msg
        else:
            msg = tr("Both layers use the following coordinate"
                     " reference system: %s" % this_layer_projection)
            return True, msg

    def has_same_content_as(self, other_layer):
        """
        Check if the layer has the same content as another layer

        :param other_layer: layer to compare with
        :type other_layer: QgsVectorLayer
        """
        len_this = self.layer.featureCount()
        len_other = other_layer.featureCount()
        # Check if the layers have the same number of rows (features)
        if len_this != len_other:
            return False
        # Check if the layers have the same field names (columns)
        this_fields = [field.name() for field in self.layer.fields()]
        other_fields = [field.name() for field in other_layer.fields()]
        if this_fields != other_fields:
            return False
        this_features = self.layer.getFeatures()
        other_features = other_layer.getFeatures()
        # we already checked that the layers have the same number of features
        # and now we want to make sure that for each feature the contents are
        # the same
        for i in xrange(len_this):
            this_feature = this_features.next()
            other_feature = other_features.next()
            this_feat_data = this_feature.attributes()
            other_feat_data = other_feature.attributes()
            if len(this_feat_data) != len(other_feat_data):
                return False
            for j in xrange(len(this_feat_data)):
                if isinstance(this_feat_data[j], (int, long, float, complex)):
                    try:
                        assert_almost_equal(this_feat_data[j],
                                            other_feat_data[j])
                    except AssertionError:
                        return False
                else:
                    if this_feat_data[j] != other_feat_data[j]:
                        return False
        return True

    def add_attributes(self, attribute_list, simulate=False):
        """
        Add attributes to the layer

        :param attribute_list: list of QgsField to add to the layer
        :type attribute_list: list of QgsField

        :return: dict having as keys the elements of the list of attributes
                 passed as input argument, and as values the actual names of
                 the assigned attributes
        """
        if simulate:
            description = 'Simulate add attributes'
        else:
            description = 'Add attributes'
        with LayerEditingManager(self.layer, description, DEBUG):
            # add attributes
            layer_pr = self.layer.dataProvider()
            proposed_attribute_dict = {}
            proposed_attribute_list = []
            for input_attribute in attribute_list:
                input_attribute_name = input_attribute.name()
                proposed_attribute_name = \
                    input_attribute_name[:10].upper().replace(' ', '_')
                i = 1
                while True:
                    current_attribute_names = \
                        [attribute.name() for attribute in self.layer.fields()]
                    if proposed_attribute_name in current_attribute_names:
                        # If the attribute is already assigned, change the
                        # proposed_attribute_name
                        i_num_digits = len(str(i))
                        # 10 = shapefile limit
                        # 1 = underscore
                        max_name_len = 10 - i_num_digits - 1
                        proposed_attribute_name = '%s_%d' % (
                            input_attribute_name[
                                :max_name_len].upper().replace(' ', '_'), i)
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

        :param attribute_list: list of ids of attributes to be removed
                               from the layer (if a list of field names
                               is given instead of a list of ids, then
                               the corresponding indices are found
                               and used)
        :type attribute_list: list of int (or list of str)

        :return: true in case of success and false in case of failure
        """
        attr_idx_list = []
        with LayerEditingManager(self.layer, 'Remove attributes', DEBUG):
            layer_pr = self.layer.dataProvider()
            for attribute in attribute_list:
                if isinstance(attribute, basestring):
                    attr_idx = layer_pr.fieldNameIndex(attribute)
                else:
                    attr_idx = attribute
                attr_idx_list.append(attr_idx)
            # remove attributes
            if DEBUG:
                log_msg("REMOVING %s, (indices %s)" % (
                    attribute_list, attr_idx_list))
            return layer_pr.deleteAttributes(attr_idx_list)

    def transform_attribute(
            self, input_attr_name, algorithm_name, variant="",
            inverse=False, new_attr_name=None, simulate=False):
        """
        Use one of the available transformation algorithms to transform an
        attribute of the layer, and add a new attribute with the
        transformed data, or overwrite the input attribute with the results

        :param input_attr_name: name of the attribute to be transformed
        :param algorithm_name: name of the transformation algorithm
        :param variant: name of the algorithm variant
        :param inverse: boolean indicating if the inverse transformation
                        has to be performed
        :param new_attr_name: name of the target attribute that will store the
                              results of the transformation (if it is equal to
                              the input_attr_name, the attribute will be
                              overwritten)
        :param simulate: if True, the method will just simulate the creation
                         of the target attribute and return the name that would
                         be assigned to it
        :returns: (actual_new_attr_name, invalid_input_values)
        """
        # get the id of the attribute named input_attr_name
        input_attr_id = self.find_attribute_id(input_attr_name)
        overwrite = (new_attr_name is not None
                     and new_attr_name == input_attr_name)
        if simulate or not overwrite:
            # add a new attribute to store the results of the transformation
            # or simulate adding a new attribute and return the name of the
            # name that would be assigned to the new attribute if it would be
            # added.
            # NOTE: building the name of the output transformed attribute,
            #       we take into account the chosen algorithm and variant and
            #       we truncate the new name to 10 characters (max allowed for
            #       shapefiles)
            if not new_attr_name:
                if variant:
                    new_attr_name = algorithm_name[:5] + '_' + variant[:4]
                else:
                    new_attr_name = algorithm_name
            field = QgsField(new_attr_name, QVariant.Double)
            field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            if simulate:
                attr_names_dict = self.add_attributes([field],
                                                      simulate=simulate)
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
        invalid_input_values = None
        try:
            transformed_dict, invalid_input_values = transform(
                initial_dict, algorithm, variant, inverse)
        except ValueError:
            raise
        except NotImplementedError:
            raise

        if overwrite:
            actual_new_attr_name = input_attr_name
            new_attr_id = input_attr_id
        else:
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
        return actual_new_attr_name, invalid_input_values

    def find_attribute_id(self, attribute_name):
        """
        Get the id of the attribute called attribute_name
        :param attribute_name: name of the attribute
        :return: id of the attribute, or raise AttributeError
        exception if not found
        """
        attribute_id = None
        for field_id, field in enumerate(self.layer.fields()):
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
            new_name = self.layer.name() + ' (copy)'

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
            elif v_type == QGis.WKBNoGeometry:
                type_str = ""
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
        :param type_list: we want to check if the type of the layer is
                          included in this list
        :return: True if the layer is a VectorLayer and its type is in the list
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

    def count_vertices(self):
        """
        Inspired by "https://github.com/GeospatialEnablingTechnologies/
                             GET-Qgis-plugins/blob/master/Vertices_Counter/
                             Vertices_Counter.py"

        Count the total number of vertices in the layer.
        In DEBUG mode, also print vertices count for each single feature

        :return: The total number of vertices in the layer
        """
        layer_vertices = 0
        for feat in self.layer.getFeatures():
            feature_vertices = 0
            geom = feat.geometry()
            geom_type = geom.type()
            if geom_type == QGis.Polygon:
                if geom.isMultipart():
                    polygons = geom.asMultiPolygon()
                else:
                    polygons = [geom.asPolygon()]
                for polygon in polygons:
                    for ring in polygon:
                        feature_vertices += len(ring)
            elif geom_type == QGis.Line:
                if geom.isMultipart():
                    lines = geom.asMultiPolyline()
                else:
                    lines = [geom.asPolyline()]
                for line in lines:
                    feature_vertices += len(line)
            elif geom_type == QGis.Point:
                if geom.isMultipart():
                    points = geom.asMultiPoint()
                else:
                    points = [geom.asPoint()]
                for point in points:
                    feature_vertices += 1
            else:
                raise TypeError(
                    'Geometry type %s can not be accepted' % geom_type)
            layer_vertices += feature_vertices
            if DEBUG:
                log_msg("Feature %d, %d vertices"
                        % (feat.id(), feature_vertices))
        return layer_vertices
