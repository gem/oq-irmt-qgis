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
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QColor
from configparser import ConfigParser
from qgis.core import Qgis

if Qgis.QGIS_VERSION_INT < 31000:
    from qgis.core import QgsGraduatedSymbolRenderer
    # the following is an enum
    DEFAULT_STYLE_MODE = QgsGraduatedSymbolRenderer.Quantile
else:
    # Quantile is the id of QgsClassificationQuantile
    DEFAULT_STYLE_MODE = 'Quantile'

DEBUG = QSettings().value('/irmt/developer_mode', False, type=bool)

cp = ConfigParser()
metadata_file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir,
    'metadata.txt')
with open(metadata_file_path, 'r', newline='') as f:
    cp.read_file(f)
IRMT_PLUGIN_VERSION = cp.get('general', 'version')
SUPPLEMENTAL_INFORMATION_VERSION = '1.0'


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

OQ_CSV_TO_LAYER_TYPES = set([
    'damages-stats',
    'agg_risk',
    'aggrisk',
    'aggrisk-stats',
    'risk_by_event',
    'events',
    'realizations',
    'mean_rates_by_src',
    'mean_disagg_by_src',
    'infra-avg_loss',
    'infra-node_el',
    'infra-taz_cl',
    'infra-dem_cl',
    'infra-event_ccl',
    'infra-event_pcl',
    'infra-event_wcl',
    'infra-event_efl',
])
OQ_EXTRACT_TO_LAYER_TYPES = set([
    'asset_risk',
    'damages-rlzs',
    'avg_losses-rlzs',
    'avg_losses-stats',
    'gmf_data',
    'hcurves',
    'hmaps',
    'ruptures',
    'uhs',
    'disagg-rlzs',
])
OQ_ZIPPED_TYPES = set([
    'input',
])
OQ_TO_LAYER_TYPES = (OQ_CSV_TO_LAYER_TYPES |
                     OQ_EXTRACT_TO_LAYER_TYPES |
                     OQ_ZIPPED_TYPES)
OQ_RST_TYPES = set([
    'fullreport',
])
OQ_EXTRACT_TO_VIEW_TYPES = set([
     'aggcurves',
     'aggcurves-stats',
     'damages-rlzs_aggr',
     'avg_losses-rlzs_aggr',
     'avg_losses-stats_aggr',
])
OQ_XMARKER_TYPES = set(['hcurves', 'uhs'])
OQ_ALL_TYPES = (OQ_TO_LAYER_TYPES | OQ_RST_TYPES | OQ_EXTRACT_TO_VIEW_TYPES)

LOG_LEVELS = {'I': 'Info (high verbosity)',
              'W': 'Warning (medium verbosity)',
              'C': 'Critical (low verbosity)'}

DEFAULT_SETTINGS = dict(
    color_from_rgba=QColor('#FFEBEB').rgba(),
    color_to_rgba=QColor('red').rgba(),
    style_mode=DEFAULT_STYLE_MODE,
    style_classes=10,
    force_restyling=True,
    experimental_enabled=False,
    developer_mode=False,
    log_level='C',
)

DEFAULT_ENGINE_PROFILES = (
    '{"Local OpenQuake Engine Server": {'
    '"username": "", "password": "",'
    '"hostname": "http://localhost:8800"}}')

# It is possible to set custom request attributes, with numeric codes above
# 1000. REQUEST_ATTRS dict gives a name to each custom attribute we defined.
REQUEST_ATTRS = {
                 # python callback function to be called as soon as the network
                 # access manager finishes satisfying a request to which this
                 # attribute is added
                 'instance_finished_cb': 1001,
                 # id of the javascript object that called the python gem_api.
                 # It is used when calling the js callback function, to make js
                 # know to which original object it refers
                 'js_cb_object_id': 1002,
                 # name of the javascript callback function
                 'js_cb_func': 1003,
                 }

RAMP_EXTREME_COLORS = {
    'Reds':
        {'top': '#67000d',
         'bottom': '#fff5f0'},
    'Blues':
        {'top': '#08306b',
         'bottom': '#f7fbff'},
    'Greens':
        {'top': '#00441b',
         'bottom': '#f7fcf5'},
    'Spectral':
        {'top': '#d7191c',
         'bottom': '#2b83ba'}
}

GEOM_FIELDNAMES = ('geom', 'the_geom', 'geometry', 'wkt')
