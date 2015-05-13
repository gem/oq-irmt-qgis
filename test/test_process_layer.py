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

# import qgis libs so that we set the correct sip api version
import qgis   # pylint: disable=W0611  # NOQA
import os.path

import unittest

from PyQt4.QtCore import QVariant

from qgis.core import QgsVectorLayer, QgsField

from process_layer import ProcessLayer
from shared import INT_FIELD_TYPE_NAME, STRING_FIELD_TYPE_NAME

from utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class CheckProjectionsTestCase(unittest.TestCase):
    def setUp(self):
        curr_dir_name = os.path.dirname(__file__)
        data_dir_name = os.path.join(
            curr_dir_name, 'data/process_layer/check_projections')

        loss_layer_epsg4326_file_path = os.path.join(
            data_dir_name, 'loss_layer_epsg4326.shp')
        zonal_layer_epsg4326_file_path = os.path.join(
            data_dir_name, 'zonal_layer_epsg4326.shp')
        zonal_layer_epsg4269_file_path = os.path.join(
            data_dir_name, 'zonal_layer_epsg4269.shp')

        self.loss_layer_epsg4326 = QgsVectorLayer(
            loss_layer_epsg4326_file_path, 'loss_layer_epsg4326', 'ogr')
        self.zonal_layer_epsg4326 = QgsVectorLayer(
            zonal_layer_epsg4326_file_path, 'zonal_layer_epsg4326', 'ogr')
        self.zonal_layer_epsg4269 = QgsVectorLayer(
            zonal_layer_epsg4269_file_path, 'zonal_layer_epsg4269', 'ogr')

    def test_same_projections(self):
        res, msg = \
            ProcessLayer(self.loss_layer_epsg4326).has_same_projection_as(
                self.zonal_layer_epsg4326)
        self.assertEqual(res, True)

    def test_different_projections(self):
        res, msg = \
            ProcessLayer(self.loss_layer_epsg4326).has_same_projection_as(
                self.zonal_layer_epsg4269)
        self.assertEqual(res, False)


class CompareLayerContentTestCase(unittest.TestCase):

    def setUp(self):
        # a and b are equal
        # c is longer than a and b but they have the same partial content
        # d is different with respect to all the others
        curr_dir_name = os.path.dirname(__file__)
        data_dir_name = os.path.join(curr_dir_name,
                                     'data/process_layer/compare')
        layer_a_file_path = os.path.join(data_dir_name, 'layer_a.shp')
        layer_b_file_path = os.path.join(data_dir_name, 'layer_b.shp')
        layer_c_file_path = os.path.join(data_dir_name, 'layer_c.shp')
        layer_d_file_path = os.path.join(data_dir_name, 'layer_d.shp')
        self.layer_a = QgsVectorLayer(layer_a_file_path, 'layer_a', 'ogr')
        self.layer_b = QgsVectorLayer(layer_b_file_path, 'layer_b', 'ogr')
        self.layer_c = QgsVectorLayer(layer_c_file_path, 'layer_c', 'ogr')
        self.layer_d = QgsVectorLayer(layer_d_file_path, 'layer_d', 'ogr')

    def test_same_content_case_layers_are_equal(self):
        res = ProcessLayer(self.layer_a).has_same_content_as(self.layer_b)
        self.assertEqual(res, True)

    def test_same_content_case_first_layer_has_more_features(self):
        res = ProcessLayer(self.layer_c).has_same_content_as(self.layer_a)
        self.assertEqual(res, False)

    def test_same_content_case_second_layer_has_more_features(self):
        res = ProcessLayer(self.layer_a).has_same_content_as(self.layer_c)
        self.assertEqual(res, False)

    def test_same_content_case_layers_are_completely_different(self):
        res = ProcessLayer(self.layer_a).has_same_content_as(self.layer_d)
        self.assertEqual(res, False)


class AddAttributesTestCase(unittest.TestCase):

    def setUp(self):
        uri = 'Point?crs=epsg:4326'
        self.layer = QgsVectorLayer(uri, 'TestLayer', 'memory')
        self.dp = self.layer.dataProvider()

    def test_find_attribute_id(self):
        field_names = ['first', 'second']
        field_one = QgsField(field_names[0], QVariant.String)
        field_one.setTypeName(STRING_FIELD_TYPE_NAME)
        field_two = QgsField(field_names[1], QVariant.Int)
        field_two.setTypeName(INT_FIELD_TYPE_NAME)
        attributes = [field_one, field_two]
        ProcessLayer(self.layer).add_attributes(attributes)
        added_field_names = [field.name() for field in self.dp.fields()]
        # Double-check that add_attributes is working properly
        self.assertEqual(added_field_names, field_names)
        # Check that both attributes are correctly found
        for attr_name in field_names:
            try:
                ProcessLayer(self.layer).find_attribute_id(attr_name)
            except AttributeError:
                print "We would expect both attributes to be found!"
                raise
        # Check that an inexistent field doesn't get found and that the
        # AttributeError exception is correctly raised
        with self.assertRaises(AttributeError):
            ProcessLayer(self.layer).add_attributes('dummy')

    def test_add_attributes(self):
        field_one = QgsField('first', QVariant.String)
        field_one.setTypeName(STRING_FIELD_TYPE_NAME)
        field_two = QgsField('second', QVariant.Int)
        field_two.setTypeName(INT_FIELD_TYPE_NAME)
        attributes = [field_one, field_two]
        added_attributes = ProcessLayer(self.layer).add_attributes(attributes)
        expected_dict = {'first': 'first',
                         'second': 'second'}
        self.assertDictEqual(added_attributes, expected_dict)
        # Let's add 2 other fields with the same names of the previous ones
        # ==> Since the names are already taken, we expect to add fields with
        # the same names plus '_1'
        field_three = QgsField('first', QVariant.String)
        field_three.setTypeName(STRING_FIELD_TYPE_NAME)
        field_four = QgsField('second', QVariant.Int)
        field_four.setTypeName(INT_FIELD_TYPE_NAME)
        attributes = [field_three, field_four]
        added_attributes = ProcessLayer(self.layer).add_attributes(attributes)
        expected_dict = {'first': 'first_1',
                         'second': 'second_1'}
        self.assertEqual(added_attributes, expected_dict)
        # Let's add 2 other fields with the same names of the previous ones
        # ==> Since the names are already taken, as well as the corresponding
        # '_1' versions, we expect to add fields with the same names plus '_2'
        field_five = QgsField('first', QVariant.String)
        field_five.setTypeName(STRING_FIELD_TYPE_NAME)
        field_six = QgsField('second', QVariant.Int)
        field_six.setTypeName(INT_FIELD_TYPE_NAME)
        attributes = [field_five, field_six]
        added_attributes = ProcessLayer(self.layer).add_attributes(attributes)
        expected_dict = {'first': 'first_2',
                         'second': 'second_2'}
        self.assertEqual(added_attributes, expected_dict)
