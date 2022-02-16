# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-06-15
#        copyright            : (C) 2015 by GEM Foundation
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

import unittest
import os
import sys
import tempfile
from copy import deepcopy
from qgis.core import QgsVectorLayer
from qgis.utils import iface

from svir.calculations.calculate_utils import (calculate_node,
                                               get_node_attr_id_and_name,
                                               calculate_composite_variable,
                                               )
from svir.calculations.process_layer import ProcessLayer
from svir.utilities.utils import (set_operator,
                                  get_node,
                                  save_layer_as,
                                  )
from svir.utilities.shared import OPERATORS_DICT, DiscardedFeature
# from qgis.testing import start_app
# from qgis.testing.mocked import get_iface

# QGIS_APP = start_app()
# IFACE = get_iface()


PROJ_DEF_STD_OPERATORS = {
    "name": "IRI",
    "weight": 1.0,
    "level": "1.0",
    "operator": "Weighted sum",
    "type": "Integrated Risk Index",
    "children": [
        {"name": "RI",
         "type": "Risk Index",
         "children": [],
         "weight": 0.5,
         "level": "2.0"
         },
        {"name": "SVI",
         "type": "Social Vulnerability Index",
         "children": [
             {"name": "Education",
              "weight": 0.5,
              "level": "3.0",
              "operator": "Weighted sum",
              "type": "Social Vulnerability Theme",
              "children": [
                  {"name": ("Female population without secondary"
                            " education or higher"),
                   "isInverted": True,
                   "weight": 0.2,
                   "level": 4.0,
                   "field": "EDUEOCSAF",
                   "type": "Social Vulnerability Indicator",
                   "children": []
                   },
                  {"name": ("Male population without secondary"
                            " education or higher"),
                   "isInverted": True,
                   "weight": 0.3,
                   "level": 4.0,
                   "field": "EDUEOCSAM",
                   "type": "Social Vulnerability Indicator",
                   "children": []
                   },
                  {"name": "Scientific and technical journal articles",
                   "weight": 0.5,
                   "level": 4.0,
                   "field": "EDUEOCSTJ",
                   "type": "Social Vulnerability Indicator",
                   "children": []
                   }
              ]
              },
             {"name": "Environment",
              "weight": 0.5,
              "level": "3.0",
              "operator": "Weighted sum",
              "type": "Social Vulnerability Theme",
              "children": [
                  {"name": "Droughts, floods, extreme temperatures",
                   "weight": 0.5,
                   "level": 4.1,
                   "field": "ENVDIPDFT",
                   "type": "Social Vulnerability Indicator",
                   "children": []
                   },
                  {"name": "Natural disasters  - Number of deaths",
                   "weight": 0.5,
                   "level": 4.1,
                   "field": "ENVDIPIND",
                   "type": "Social Vulnerability Indicator",
                   "children": []
                   }
              ]
              }
         ],
         "weight": 0.5,
         "level": "2.0"
         }
    ],
    "description": ""
}


class CalculateCompositeVariableTestCase(unittest.TestCase):

    # NOTE: uncomment to enable displaying long diffs
    # maxDiff = None

    # NOTE: set to True to rebuild the reference outputs
    REBUILD_OUTPUTS = False

    def setUp(self):

        self.project_definition = PROJ_DEF_STD_OPERATORS

        # Load layer
        curr_dir_name = os.path.dirname(__file__)
        self.data_dir_name = os.path.join(
            curr_dir_name, os.pardir, 'data', 'calculate_indices')
        layer_path = os.path.join(
            self.data_dir_name, 'socioeconomic_data.gpkg')
        orig_layer = QgsVectorLayer(layer_path, 'Zonal Layer', 'ogr')
        # Avoid modifying the original files
        self.layer = ProcessLayer(orig_layer).duplicate_in_memory()

    def test_custom_operator(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['CUSTOM']
        # set economy's operator to custom and use a custom formula
        proj_def['children'][1]['children'][0]['operator'] = operator
        proj_def['children'][1]['children'][0]['fieldDescription'] = \
            'EDUEOCSAF plus one'
        proj_def['children'][1]['children'][0]['customFormula'] = \
            '"EDUEOCSAF" + 1'
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'custom_operator'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'custom_operator.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'custom_operator', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        try:
            self.assertEqual(res, True)
        except AssertionError:
            sys.stderr.write("The resulting layer is different than expected")
            sys.stderr.write("\n\n\nCalculated EDUCATION as EDUEOCSAF+1:\n")
            ProcessLayer(self.layer).pprint(usage='testing')
            sys.stderr.write("\n\n\nExpected layer (custom_operator.gpkg):\n")
            ProcessLayer(expected_layer).pprint(usage='testing')
            raise

    def test_simple_sum(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['SUM_S']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'simple_sum'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'simple_sum.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'simple_sum', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_weighted_sum(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['SUM_W']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'weighted_sum'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'weighted_sum.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'weighted_sum', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_simple_multiplication(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['MUL_S']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'simple_multiplication'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'simple_multiplication.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'simple_multiplication', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_weighted_multiplication(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['MUL_W']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'weighted_multiplication'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'weighted_multiplication.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'weighted_multiplication', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_average(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['AVG']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'average'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'average.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'average', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_geometric_mean_positive_argument(self):
        proj_def = deepcopy(self.project_definition)
        operator = OPERATORS_DICT['GEOM_MEAN']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'geometric_mean_positive_argument'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'geometric_mean_positive_argument.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'geometric_mean_positive_argument', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_geometric_mean_negative_argument(self):
        proj_def = deepcopy(self.project_definition)
        # do not invert EDUEOCSAM ==> it should cause the geometric mean to
        # attempt calculating the root of a negative number, so we should have
        # the corresponding field discarded with 'Invalid value' reason
        assert proj_def['children'][1]['children'][0]['children'][1]['field'] \
            == 'EDUEOCSAM'
        #                   SVI            Education      EDUEOCSAM
        proj_def['children'][1]['children'][0]['children'][1]['isInverted'] \
            = False
        operator = OPERATORS_DICT['GEOM_MEAN']
        node_attr_id, node_attr_name, discarded_feats = \
            calculate_education_node(proj_def, operator, self.layer)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'geometric_mean_negative_argument'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        expected_layer_path = os.path.join(
            self.data_dir_name, 'geometric_mean_negative_argument.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'geometric_mean_negative_argument', 'ogr')
        res = ProcessLayer(self.layer).has_same_content_as(expected_layer)
        self.assertEqual(res, True)

    def test_calculate_svi(self):
        proj_def = deepcopy(self.project_definition)
        svi_node = proj_def['children'][1]
        added_attrs_ids, discarded_feats, edited_node, any_change = \
            calculate_composite_variable(iface, self.layer, svi_node)
        proj_def['children'][1] = edited_node
        self.assertEqual(added_attrs_ids, set([10, 11, 12]))
        expected_discarded_feats = set([DiscardedFeature(1, 'Missing value'),
                                        DiscardedFeature(2, 'Missing value')])
        self.assertEqual(discarded_feats,
                         expected_discarded_feats)
        self.assertEqual(any_change, True)
        self.assertEqual(proj_def, proj_def_svi_calc_first_round)

        if self.REBUILD_OUTPUTS:
            res_layer_name = 'svi_calculation_first_round'
            write_output(self.layer, self.data_dir_name, res_layer_name)

        _, out_layer_path = tempfile.mkstemp(suffix='.gpkg')
        save_layer_as(self.layer, out_layer_path, 'GPKG')
        out_layer = QgsVectorLayer(
            out_layer_path, 'svi_calculation_first_round', 'ogr')

        expected_layer_path = os.path.join(
            self.data_dir_name, 'svi_calculation_first_round.gpkg')
        expected_layer = QgsVectorLayer(
            expected_layer_path, 'svi_calculation_first_round', 'ogr')
        res = ProcessLayer(out_layer).has_same_content_as(expected_layer)
        if not res:
            ProcessLayer(self.layer).pprint(usage='testing')
            ProcessLayer(expected_layer).pprint(usage='testing')
        self.assertEqual(res, True)

        # If the attributes have already been added to the layer, they should
        # be re-used instead of adding new ones
        # therefore the project definition should be the same as it was after
        # the first round
        svi_node = proj_def['children'][1]
        added_attrs_ids, discarded_feats, edited_node, any_change = \
            calculate_composite_variable(iface, self.layer, svi_node)
        proj_def['children'][1] = edited_node
        self.assertEqual(added_attrs_ids, set([]))
        expected_discarded_feats = set([DiscardedFeature(1, 'Missing value'),
                                        DiscardedFeature(2, 'Missing value')])
        self.assertEqual(discarded_feats,
                         expected_discarded_feats)
        self.assertEqual(any_change, True)
        self.assertEqual(proj_def, proj_def_svi_calc_first_round)

        _, out_layer_path = tempfile.mkstemp(suffix='.gpkg')
        save_layer_as(self.layer, out_layer_path, 'GPKG')
        out_layer = QgsVectorLayer(
            out_layer_path, 'svi_calculation_second_round', 'ogr')

        res = ProcessLayer(out_layer).has_same_content_as(expected_layer)
        if not res:
            ProcessLayer(self.layer).pprint(usage='testing')
            ProcessLayer(expected_layer).pprint(usage='testing')
        self.assertEqual(res, True)


def calculate_education_node(proj_def, operator, layer):
    """
    Use the calculate_node function to compute the 'Education' node using the
    given project definition and operator.
    The layer is updated as a side effect.
    """
    # set all operators of proj_def to the one selected
    proj_def = set_operator(proj_def, operator)
    # we are testing the calculation for a single node
    education_node = get_node(proj_def, 'Education')
    node_attr_id, node_attr_name, field_was_added = \
        get_node_attr_id_and_name(education_node, layer)
    discarded_feats = set()
    discarded_feats = calculate_node(
        education_node, node_attr_name, node_attr_id,
        layer, discarded_feats)
    return node_attr_id, node_attr_name, discarded_feats


def write_output(res_layer, data_dir_name, res_layer_name):
    res_layer_path = os.path.join(data_dir_name, res_layer_name + '.gpkg')
    save_layer_as(res_layer, res_layer_path, 'GPKG')


proj_def_svi_calc_first_round = {
    'children': [
        {'children': [],
         'level': '2.0',
         'name': 'RI',
         'type': 'Risk Index',
         'weight': 0.5},
        {'children': [
            {'children': [
                {'children': [],
                 'field': 'EDUEOCSAF',
                 'isInverted': True,
                 'level': 4.0,
                 'name': ('Female population without secondary'
                          ' education or higher'),
                 'type': 'Social Vulnerability Indicator',
                 'weight': 0.2},
                {'children': [],
                 'field': 'EDUEOCSAM',
                 'isInverted': True,
                 'level': 4.0,
                 'name': ('Male population without secondary'
                          ' education or higher'),
                 'type': 'Social Vulnerability Indicator',
                 'weight': 0.3},
                {'children': [],
                 'field': 'EDUEOCSTJ',
                 'level': 4.0,
                 'name': 'Scientific and technical journal articles',
                 'type': 'Social Vulnerability Indicator',
                 'weight': 0.5}],
             'field': u'Education',
             'level': '3.0',
             'name': 'Education',
             'operator': 'Weighted sum',
             'type': 'Social Vulnerability Theme',
             'weight': 0.5},
            {'children': [
                {'children': [],
                 'field': 'ENVDIPDFT',
                 'level': 4.1,
                 'name': 'Droughts, floods, extreme temperatures',
                 'type': 'Social Vulnerability Indicator',
                 'weight': 0.5},
                {'children': [],
                 'field': 'ENVDIPIND',
                 'level': 4.1,
                 'name': 'Natural disasters  - Number of deaths',
                 'type': 'Social Vulnerability Indicator',
                 'weight': 0.5}],
             'field': u'Environment',
             'level': '3.0',
             'name': 'Environment',
             'operator': 'Weighted sum',
             'type': 'Social Vulnerability Theme',
             'weight': 0.5}],
         'field': u'SVI',
         'level': '2.0',
         'name': 'SVI',
         'type': 'Social Vulnerability Index',
         'weight': 0.5}],
    'description': '',
    'level': '1.0',
    'name': 'IRI',
    'operator': 'Weighted sum',
    'type': 'Integrated Risk Index',
    'weight': 1.0
}
