# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014-2015 by GEM Foundation
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
import os
from collections import OrderedDict
from PyQt4.QtCore import QSettings
from ConfigParser import ConfigParser

DEBUG = QSettings().value('/svir/developer_mode', False, type=bool)

cp = ConfigParser()
cp.readfp(open(os.path.dirname(os.path.realpath(__file__)) + "/metadata.txt"))
SVIR_PLUGIN_VERSION = cp.get('general', 'version')
PLATFORM_REGISTRATION_URL = 'https://platform.openquake.org/account/signup/'

INT_FIELD_TYPE_NAME = "integer"
REAL_FIELD_TYPE_NAME = "Real"
DOUBLE_FIELD_TYPE_NAME = "double"

NUMERIC_FIELD_TYPES = (INT_FIELD_TYPE_NAME,
                       INT_FIELD_TYPE_NAME.capitalize(),
                       REAL_FIELD_TYPE_NAME,
                       REAL_FIELD_TYPE_NAME.lower(),
                       DOUBLE_FIELD_TYPE_NAME,
                       DOUBLE_FIELD_TYPE_NAME.capitalize())

STRING_FIELD_TYPE_NAME = "String"
TEXT_FIELD_TYPE_NAME = "text"

TEXTUAL_FIELD_TYPES = (STRING_FIELD_TYPE_NAME,
                       STRING_FIELD_TYPE_NAME.lower(),
                       TEXT_FIELD_TYPE_NAME,
                       TEXT_FIELD_TYPE_NAME.capitalize())

OPERATORS_DICT = OrderedDict()
OPERATORS_DICT['SUM_S'] = 'Simple sum (ignore weights)'
OPERATORS_DICT['SUM_W'] = 'Weighted sum'
OPERATORS_DICT['AVG'] = 'Average (ignore weights)'
OPERATORS_DICT['MUL_S'] = 'Simple multiplication (ignore weights)'
OPERATORS_DICT['MUL_W'] = 'Weighted multiplication'
OPERATORS_DICT['GEOM_MEAN'] = 'Geometric mean (ignore weights)'

DEFAULT_OPERATOR = OPERATORS_DICT['SUM_W']
IGNORING_WEIGHT_OPERATORS = (OPERATORS_DICT['SUM_S'],
                             OPERATORS_DICT['AVG'],
                             OPERATORS_DICT['MUL_S'],
                             OPERATORS_DICT['GEOM_MEAN'],
                             )
SUM_BASED_OPERATORS = (OPERATORS_DICT['SUM_S'],
                       OPERATORS_DICT['SUM_W'],
                       OPERATORS_DICT['AVG'],
                       )
MUL_BASED_OPERATORS = (OPERATORS_DICT['MUL_S'],
                       OPERATORS_DICT['MUL_W'],
                       OPERATORS_DICT['GEOM_MEAN'],
                       )

NODE_TYPES = {'IRI': 'Integrated Risk Index',
              'RI': 'Risk Index',
              'RISK_INDICATOR': 'Risk Indicator',
              'SVI': 'Social Vulnerability Index',
              'SV_THEME': 'Social Vulnerability Theme',
              'SV_INDICATOR': 'Social Vulnerability Indicator',
              }


PROJECT_TEMPLATE = {
    'name': 'IRI',
    'type': NODE_TYPES['IRI'],
    'weight': 1.0,
    'level': '1.0',
    'operator': DEFAULT_OPERATOR,
    'children': [
        {'name': 'RI',
         'type': NODE_TYPES['RI'],
         'weight': 0.5,
         'level': '2.0',
         'children': []},
        {'name': 'SVI',
         'type': NODE_TYPES['SVI'],
         'weight': 0.5,
         'level': '2.0',
         'children': []}
    ]
}

THEME_TEMPLATE = {
    'name': '',
    'weight': 1.0,
    'level': '3.0',
    'type': NODE_TYPES['SV_THEME'],
    'operator': DEFAULT_OPERATOR,
    'children': []
}

# Actually not used, because it's built in the d3 javascript
INDICATOR_TEMPLATE = {
    'name': '',
    'weight': 1.0,
    'level': '4.0',
    'type': NODE_TYPES['SV_INDICATOR'],
    'field': '',
    'children': []
}

# FIXME
DEMO_JSON = {
    "name": "IR",
    "weight": "",
    "level": 1.0,
    "children": [
        {"name": "RI",
         "weight": 0.5},
        {"name": "SVI",
         "weight": 0.5,
         "level": 2.0},
        {"name": "svi",
         "weight": 0.5,
         "level": 2.0,
         "children": [
             {"name": "population",
              "weight": 0.16,
              "level": 3.1,
              "type": "categoryIndicator",
              "children": [
                  {"name": "QFEMALE", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QURBAN", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "MIGFOREIGN", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "MIGMUNICIP", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QFOREIGN", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QAGEDEP", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "POPDENT", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "PPUNIT", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QFHH", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QRENTAL", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QDISABLED", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"},
                  {"name": "QSSINT", "weight": 0.083, "level": 4.0,
                   "type": "primaryIndicator"}]
              },
             {"name": "economy",
              "weight": 0.16,
              "level": 3.1,
              "type": "categoryIndicator",
              "children": [
                  {"name": "QUNEMPL", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"},
                  {"name": "QFEMLBR", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"},
                  {"name": "QSECOEMPL", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"},
                  {"name": "QSERVEMPL", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"},
                  {"name": "QNOSKILLEMPL", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"},
                  {"name": "PCPP", "weight": 0.167, "level": 4.1,
                   "type": "primaryIndicator"}]
              },
             {"name": "education",
              "weight": 0.16,
              "level": 3.1,
              "type": "categoryIndicator",
              "children": [
                  {"name": "QEDLESS", "weight": 0.5, "level": 4.2,
                   "type": "primaryIndicator"},
                  {"name": "EDUTERTIARY", "weight": 0.5, "level": 4.2,
                   "type": "primaryIndicator"}
                  ]
              },
             {"name": "infrastructure",
              "weight": 0.16,
              "level": 3.1,
              "type": "categoryIndicator",
              "children": [
                  {"name": "QBLDREPAIR", "weight": 0.25, "level": 4.4,
                   "type": "primaryIndicator"},
                  {"name": "NEWBUILD", "weight": 0.25, "level": 4.4,
                   "type": "primaryIndicator"},
                  {"name": "QPOPNOWATER", "weight": 0.25, "level": 4.4,
                   "type": "primaryIndicator"},
                  {"name": "QPOPNOWASTE", "weight": 0.25, "level": 4.4,
                   "type": "primaryIndicator"}]
              },
             {"name": "governance",
              "weight": 0.16,
              "level": 3.1,
              "type": "categoryIndicator",
              "children": [
                  {"name": "CRIMERATE", "weight": 0.33, "level": 4.5,
                   "type": "primaryIndicator"},
                  {"name": "QNOVOTEMU", "weight": 0.33, "level": 4.5,
                   "type": "primaryIndicator"},
                  {"name": "QNOVOTEPR", "weight": 0.33, "level": 4.5,
                   "type": "primaryIndicator"}]
              }]
         }]
}
