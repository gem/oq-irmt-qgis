# -*- coding: utf-8 -*-
#/***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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

import os
from collections import OrderedDict
from PyQt4.QtCore import QSettings
from ConfigParser import ConfigParser

DEBUG = QSettings().value('/irmt/developer_mode', False, type=bool)

cp = ConfigParser()
cp.readfp(open(os.path.dirname(os.path.realpath(__file__)) +
               '/../metadata.txt'))
IRMT_PLUGIN_VERSION = cp.get('general', 'version')
PLATFORM_REGISTRATION_URL = 'https://platform.openquake.org/account/signup/'
SUPPLEMENTAL_INFORMATION_VERSION = '1.0'
PROJECT_DEFINITION_VERSION = '1.0'


class DiscardedFeature(object):
    """
    Class storing information about a discarded feature

    :param feature_id: unique feature identifier
    :param reason: indicating if the feature is being discarded because of a
                   missing value or an invalid value
    """

    valid_reasons = ('Missing value', 'Invalid value')

    def __init__(self, feature_id, reason):
        self.feature_id = feature_id
        self.reason = reason
        if self.reason not in self.valid_reasons:
            raise ValueError(
                'Invalid reason. It must be one of %s'
                % [valid_reason for valid_reason in self.valid_reasons])

    def __eq__(self, other):  # two instances are equal if
        return (self.feature_id == other.feature_id
                and self.reason == other.reason)

    def __ne__(self, other):  # python requrires to explicitly define not equal
                              # so we implement the negation of __eq__
        return not self.__eq__(other)

    def __lt__(self, other):  # for sorting
        return (self.feature_id < other.feature_id
                and self.reason < other.reason)

    def __hash__(self):  # what is unique
        return hash((self.feature_id, self.reason))

    def __repr__(self):
        return 'Feature id: %s, reason: %s' % (self.feature_id, self.reason)


INT_FIELD_TYPE_NAME = 'integer'
REAL_FIELD_TYPE_NAME = 'Real'
DOUBLE_FIELD_TYPE_NAME = 'double'

NUMERIC_FIELD_TYPES = (INT_FIELD_TYPE_NAME,
                       INT_FIELD_TYPE_NAME.capitalize(),
                       REAL_FIELD_TYPE_NAME,
                       REAL_FIELD_TYPE_NAME.lower(),
                       DOUBLE_FIELD_TYPE_NAME,
                       DOUBLE_FIELD_TYPE_NAME.capitalize())

STRING_FIELD_TYPE_NAME = 'String'
TEXT_FIELD_TYPE_NAME = 'text'

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
    'project_definition_version': PROJECT_DEFINITION_VERSION,
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


HELP_PAGES_LOOKUP = {
    'import_sv_variables': '05_load_indicators_from_platform.html',
    'import_layer': '06_download_project_from_platform.html',
    'transform_attributes': '07_transform_attribute.html',
    'project_definitions_manager': '08_project_definitions_manager.html',
    'weight_data': '09_weighting_and_calculating.html',
    'aggregate_losses': '10_aggregate_loss_by_zone.html',
    'upload': '11_upload_project_to_platform.html',
    'show_platform_settings': '04_connection_settings.html',
    'show_engine_settings': 'FIXME',
    'load_hcurves_from_hdf5_as_layer': 'FIXME',
    'load_loss_curves_from_hdf5_as_layer': 'FIXME',
    'load_hmaps_from_hdf5_as_layer': 'FIXME',
    'load_loss_maps_from_hdf5_as_layer': 'FIXME',
    'load_scenario_damage_gmfs_from_hdf5_as_layer': 'FIXME',
    'load_scenario_damage_by_asset_from_hdf5_as_layer': 'FIXME',
    'load_geojson_as_layer': 'FIXME',
    'drive_engine_server': 'FIXME',
    'toggle_viewer_dock': 'FIXME',
    'help': 'index.html',
}
