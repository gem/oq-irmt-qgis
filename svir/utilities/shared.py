# -*- coding: utf-8 -*-
# /***************************************************************************
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
from PyQt4.QtGui import QColor
from ConfigParser import ConfigParser
from qgis.core import QgsGraduatedSymbolRendererV2

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

    def __ne__(self, other):
        # python requrires to explicitly define not equal so we implement the
        # negation of __eq__
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
                       DOUBLE_FIELD_TYPE_NAME.capitalize(),
                       'qint8', 'qint16', 'qint32', 'qint64',
                       'qlonglong', 'qreal')

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
OPERATORS_DICT['CUSTOM'] = 'Use a custom field'

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

RECOVERY_DEFAULTS = {
    'transfer_probabilities': [
        [1, 0, 0, 0, 0, 0],
        [0.6, 0.4, 0, 0, 0, 0],
        [0.2, 0.4, 0.3, 0.1, 0, 0],
        [0, 0, 0.2, 0.4, 0.3, 0.1],
        [0, 0, 0, 0, 0.2, 0.8]],
    'inspection_times': [0, 30, 30, 30, 30, 0],
    'assessment_times': [0, 0, 0, 60, 60, 0],
    'mobilization_times': [0, 0, 0, 120, 365, 365],
    'recovery_times': [0, 50, 108, 156, 252, 612],
    'repair_times': [0, 13, 27, 39, 63, 153],
    'lead_time_dispersion': 0.75,
    'repair_time_dispersion': 0.4,
}
RECOVERY_DEFAULTS['n_loss_based_dmg_states'] = len(
    RECOVERY_DEFAULTS['transfer_probabilities'])
RECOVERY_DEFAULTS['n_recovery_based_dmg_states'] = len(
    RECOVERY_DEFAULTS['transfer_probabilities'][0])

# Notes on recovery modeling:
#
# assessment_times:
#    The entry in row n is the assessment time for the (n - 1)th damage state
# inspection_times:
#    The entry in row n is the inspection time for the (n - 1)th damage state
# mobilization_times:
#    The entry in row n is the mobilization time for the (n - 1)th damage state
# recovery_times:
#    The entry in row n is the recovery time for the (n - 1)th damage state
# repair_times:
#    The entry in row n is the repair time for the (n - 1)th damage state
# NB: The following is referred to the Napa case specifically!
# Note on transfer probabilities: There is a 5*6 matrix where rows
# describe loss-based damage states (No
# damage/Slight/Moderate/Extensive/Complete) and columns present
# recovery-based damage states(No damage/Trigger inspection/Loss
# Function /Not Occupiable/Irreparable/Collapse). The element(i,j)
# in the matrix is the probability of recovery-based damage state j
# occurs given loss-based damage state i


OQ_CSV_LOADABLE_TYPES = set(['ruptures'])
OQ_NPZ_LOADABLE_TYPES = set([
    'hmaps', 'hcurves', 'uhs', 'gmf_data', 'dmg_by_asset', 'losses_by_asset'])
OQ_ALL_LOADABLE_TYPES = OQ_CSV_LOADABLE_TYPES | OQ_NPZ_LOADABLE_TYPES
OQ_RST_TYPES = set(['fullreport'])
OQ_NO_MAP_TYPES = set(
    ['agg_curves-rlzs', 'agg_curves-stats', 'dmg_by_asset_aggr'])


DEFAULT_SETTINGS = dict(
    platform_username='',
    platform_password='',
    platform_hostname='https://platform.openquake.org',
    engine_username='',
    engine_password='',
    engine_hostname='http://localhost:8800',
    color_from_rgba=QColor('#FFEBEB').rgba(),
    color_to_rgba=QColor('red').rgba(),
    style_mode=QgsGraduatedSymbolRendererV2.Quantile,
    style_classes=10,
    force_restyling=True,
)
