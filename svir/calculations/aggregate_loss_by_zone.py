# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-02-23
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

import processing

# NOTE: summaries and predicates might be changed externally, so we need
# some integration tests between the plugin and the QGIS processing
# library, to identify those possible changes
# (the full description of the algorithm can be obtained as follows:
#  processing.algorithmHelp('qgis:joinbylocationsummary') and it includes
#  the lists of predicates and summaries)
summary_keys = (
    'count unique min max range sum mean median stddev minority majority '
    'q1 q3 iqr empty filled min_length max_length mean_length').split()
SUMMARIES = dict(zip(summary_keys, range(len(summary_keys))))
predicate_keys = (
    'intersects contains equals touches overlaps within crosses').split()
PREDICATES = dict(zip(predicate_keys, range(len(predicate_keys))))

def calculate_zonal_stats(zonal_layer, points_layer, join_fields,
                          output_layer_name, discard_nonmatching=False,
                          predicates=('intersects',), summaries=('sum',)):
    """
    Leveraging the QGIS processing algorithm 'Join attributes by location
    (summary)', that is described in QGIS as follows:
    This algorithm takes an input vector layer and creates a new vector layer
    that is an extended version of the input one, with additional attributes in
    its attribute table. The additional attributes and their values are taken
    from a second vector layer. A spatial criteria is applied to select the
    values from the second layer that are added to each feature from the first
    layer in the resulting one. The algorithm calculates a statistical summary
    for the values from matching features in the second layer (e.g. maximum
    value, mean value, etc).

    :param zonal_layer: vector layer containing polygons (or its path)
    :param points_layer: vector layer containing points (or its path)
    :param join_fields: fields for which we want to calculate statistics
        (e.g. structural)
    :param output_layer_name: a memory layer will be produced, named
        'memory:output_layer_name'
    :param discard_nonmatching: discard records which could not be joined
        (in our case, purge zones that contain no loss/damage points)
    :param predicates: geometric predicates (default: 'intersects')
    :param summaries: statistics to be calculated for each join field

    :returns: the output QgsVectorLayer
    """
    res = processing.run(
        "qgis:joinbylocationsummary",
        {'DISCARD_NONMATCHING': discard_nonmatching,
         'INPUT': zonal_layer,
         'JOIN': points_layer,
         'PREDICATE': [PREDICATES[predicate] for predicate in predicates],
         'JOIN_FIELDS': join_fields,
         'SUMMARIES': [SUMMARIES[summary] for summary in summaries],
         'OUTPUT':'memory:%s' % output_layer_name})
    output_layer = res['OUTPUT']
    return output_layer
