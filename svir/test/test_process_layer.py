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

# Copyright (c) 2013-2014, GEM Foundation.
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

import unittest

import qgis  # pylint: disable=W0611  # NOQA

from PyQt4.QtCore import QVariant

from qgis.core import QgsVectorLayer, QgsField

from process_layer import ProcessLayer
from globals import INT_FIELD_TYPE_NAME, STRING_FIELD_TYPE_NAME


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
        assert added_field_names == field_names
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
        assert added_attributes == expected_dict
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
        assert added_attributes == expected_dict
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
        assert added_attributes == expected_dict
