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
from PyQt4.QtCore import QVariant
from qgis.core import (QgsMapLayer,
                       QGis,
                       QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsField)
from layer_editing_manager import LayerEditingManager

from normalization_algs import (NORMALIZATION_ALGS,
                                normalize)

from utils import DEBUG


class ProcessLayer():

    def __init__(self, layer):
        self.layer = layer

    def add_attributes(self, attribute_list):
        """
        Add attributes to the layer

        :param attribute_list: list of QgsField to add to the layer
        :type attribute_list: list of QgsField
        """
        with LayerEditingManager(self.layer, 'Add attributes', DEBUG):
            # add attributes
            layer_pr = self.layer.dataProvider()
            layer_pr.addAttributes(attribute_list)

    def normalize_attribute(self,
                            input_attr_name,
                            algorithm_name,
                            variant="",
                            inverse=False):
        """
        Use one of the available normalization algorithms to normalize an
        attribute of the layer, and add a new attribute with the
        normalized data, named as something like 'attr_name__algorithm', e.g.,
        'TOTLOSS__MIN_MAX'
        """
        pr = self.layer.dataProvider()

        # get the id of the attribute named input_attr_name
        input_attr_id = None
        for field_id, field in enumerate(pr.fields()):
            if field.name() == input_attr_name:
                input_attr_id = field_id
        if not input_attr_id:
            raise AttributeError

        # build the name of the output normalized attribute
        new_attr_name = input_attr_name + '__' + algorithm_name
        self.add_attributes([QgsField(new_attr_name, QVariant.Double)])

        # get the id of the new attribute
        new_attr_id = None
        for field_id, field in enumerate(pr.fields()):
            if field.name() == new_attr_name:
                new_attr_id = field_id
        if not input_attr_id:
            raise AttributeError

        # a dict will contain all the values for the chosen input attribute,
        # keeping as key, for each value, the id of the corresponding feature
        initial_dict = dict()
        for feat in self.layer.getFeatures():
            initial_dict[feat.id()] = feat[input_attr_id]

        # get the normalization algorithm from the register
        algorithm = NORMALIZATION_ALGS[algorithm_name]

        # normalize the values in the dictionary with the chosen algorithm
        normalized_dict = normalize(initial_dict, algorithm, variant, inverse)

        with LayerEditingManager(self.layer, 'Write normalized values', DEBUG):
            for feat in self.layer.getFeatures():
                feat_id = feat.id()
                self.layer.changeAttributeValue(
                    feat_id, new_attr_id, float(normalized_dict[feat_id]))

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
            v_type = self.layer.geometryType()
            if v_type == QGis.Point:
                type_str = 'Point'
            elif v_type == QGis.Line:
                type_str = 'Line'
            elif v_type == QGis.Polygon:
                type_str = 'Polygon'
            else:
                raise RuntimeError('Layer is whether Point nor '
                                   'Line nor Polygon')
        else:
            raise RuntimeError('Layer is not a VectorLayer')

        crs = self.layer.crs().authid().lower()
        my_uuid = str(uuid.uuid4())
        uri = '%s?crs=%s&index=yes&uuid=%s' % (type_str, crs, my_uuid)
        mem_layer = QgsVectorLayer(uri, new_name, 'memory')
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
