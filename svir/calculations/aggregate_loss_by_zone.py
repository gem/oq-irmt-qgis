# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2015-02-23
#        copyright            : (C) 2016-2026 by GEM Foundation
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
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsApplication


def add_zone_id_to_points(points_layer, zonal_layer, zone_field_name):
    params = {'DISCARD_NONMATCHING': False,
              'INPUT': points_layer,
              'JOIN': zonal_layer,
              'JOIN_FIELDS': [zone_field_name],
              'METHOD': 1,  # one-to-one
              'OUTPUT': 'memory:points_layer_plus_zone_id',
              'PREDICATE': [0],  # intersects
              'PREFIX': ''}
    res = processing.run('qgis:joinattributesbylocation', params)
    output_layer = res['OUTPUT']
    point_attrs_dict = {field.name(): field.name()
                        for field in points_layer.fields()}

    return point_attrs_dict, output_layer, zone_field_name


def calculate_zonal_stats(callback, zonal_layer, points_layer, join_fields,
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
    The full description of the algorithm can be obtained as follows:
    processing.algorithmHelp('qgis:joinbylocationsummary') and it includes
    the lists of predicates and summaries.

    :param callback: function to be called once the aggregation is complete,
        passing the output zonal layer as a parameter
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
        (default: 'sum')

    :returns: when the task is complete or terminated, it
        calls the callback function, passing the output QgsVectorLayer as
        parameter, or None in case of failure
    """

    processing.Processing.initialize()
    alg_id = 'qgis:joinbylocationsummary'
    if not QgsApplication.processingRegistry().algorithmById(alg_id):
        raise ImportError('Unable to retrieve processing algorithm'
                          ' qgis:joinbylocationsummary')
    # NOTE: predicates are no more retrieavable in the c++ version of the
    # algorithm, so we can't make sure to use the actual lists of predicates
    # and summaries as defined in the algorithm when it is instantiated
    predicate_keys = ['intersects', 'contains', 'isEqual', 'touches',
                      'overlaps', 'within', 'crosses']
    PREDICATES = dict(zip(predicate_keys, range(len(predicate_keys))))
    summary_keys = [
        'count', 'unique', 'min', 'max', 'range', 'sum', 'mean', 'median',
        'stddev', 'minority', 'majority', 'q1', 'q3', 'iqr', 'empty', 'filled',
        'min_length', 'max_length', 'mean_length']
    SUMMARIES = dict(zip(summary_keys, range(len(summary_keys))))

    try:
        QgsApplication.setOverrideCursor(Qt.WaitCursor)
        # fix geometries first
        fixed_zonal_layer = processing.run(
            "qgis:fixgeometries",
            {"INPUT": zonal_layer, "OUTPUT": "TEMPORARY_OUTPUT"}
        )["OUTPUT"]
        params = {
            'DISCARD_NONMATCHING': discard_nonmatching,
            'INPUT': fixed_zonal_layer,
            'JOIN': points_layer,
            'PREDICATE': [PREDICATES[predicate] for predicate in predicates],
            'JOIN_FIELDS': join_fields,
            'SUMMARIES': [SUMMARIES[summary] for summary in summaries],
            'OUTPUT': 'memory:%s' % output_layer_name
        }
        result = processing.run(alg_id, params)
        output_layer = result.get('OUTPUT')
        if output_layer is None:
            raise RuntimeError(f"{alg_id} returned no output")
        output_layer.setName(output_layer_name)
        callback(output_layer)
    except Exception:
        import traceback
        traceback.print_exc()
        print("Processing parameters were:", params)
        callback(None)
    finally:
        QgsApplication.restoreOverrideCursor()
