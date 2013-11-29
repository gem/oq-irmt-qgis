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
from PyQt4.QtGui import QApplication
from qgis.core import (QgsMapLayerRegistry,
                       QgsVectorLayer,
                       QGis,
                       QgsMapLayer)
from layer_editing_manager import LayerEditingManager

DEBUG = False

class Utils(object):
    
    @staticmethod
    def tr(message):
        return QApplication.translate('Svir', message)

    @staticmethod
    def add_attributes_to_layer(layer, attribute_list):
        """
        Add attributes to a layer

        :param layer: QgsVectorLayer that needs to be modified
        :type layer: QgsVectorLayer

        :param attribute_list: list of QgsField to add to the layer
        :type attribute_list: list of QgsField
        """
        with LayerEditingManager(layer, 'Add attributes', DEBUG):
            # add attributes
            layer_pr = layer.dataProvider()
            layer_pr.addAttributes(attribute_list)

    @staticmethod
    def duplicate_in_memory(layer, new_name='', add_to_registry=False):
        """
        TODO: If this will be included in the processing QGIS core plugin, we
        will import and use that, and this method will be removed.

        Return a memory copy of a layer

        :param layer: QgsVectorLayer that shall be copied to memory.
        :type layer: QgsVectorLayer

        :param new_name: The name of the copied layer.
        :type new_name: str

        :param add_to_registry: if True, the new layer will be added to
        the QgsMapRegistry
        :type: bool

        :returns: An in-memory copy of a layer.
        :rtype: QgsMapLayer

        """
        if new_name is '':
            new_name = layer.name() + ' TMP'

        if layer.type() == QgsMapLayer.VectorLayer:
            v_type = layer.geometryType()
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

        crs = layer.crs().authid().lower()
        my_uuid = str(uuid.uuid4())
        uri = '%s?crs=%s&index=yes&uuid=%s' % (type_str, crs, my_uuid)
        mem_layer = QgsVectorLayer(uri, new_name, 'memory')
        mem_provider = mem_layer.dataProvider()

        provider = layer.dataProvider()
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

