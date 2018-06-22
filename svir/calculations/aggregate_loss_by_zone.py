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
from functools import partial

from qgis.core import (
    QgsApplication, QgsProcessingFeedback, QgsProcessingContext,
    QgsProcessingAlgRunnerTask, QgsProject, QgsMessageLog
    )


OUTPUT_LAYER = None

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
    The full description of the algorithm can be obtained as follows:
    processing.algorithmHelp('qgis:joinbylocationsummary') and it includes
    the lists of predicates and summaries.
    The code of the algorithm is here:
    https://github.com/qgis/QGIS/blob
    /483b4ff977e3d36b166fac792254c31e89e3aeae/python/plugins/processing/algs
    /qgis/SpatialJoinSummary.py  # NOQA

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
    global OUTPUT_LAYER

    # make sure to use the actual lists of predicates and summaries as defined
    # in the algorithm while running the initAlgorithm method
    alg = QgsApplication.processingRegistry().algorithmById(
        'qgis:joinbylocationsummary')

    # not required, done automatically by the task
    # alg.initAlgorithm()
    predicate_keys = [predicate[0] for predicate in alg.predicates]
    PREDICATES = dict(zip(predicate_keys, range(len(predicate_keys))))
    summary_keys = [statistic[0] for statistic in alg.statistics]
    SUMMARIES = dict(zip(summary_keys, range(len(summary_keys))))

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    params = {
        'DISCARD_NONMATCHING': discard_nonmatching,
        'INPUT': zonal_layer,
        'JOIN': points_layer,
        'PREDICATE': [PREDICATES[predicate] for predicate in predicates],
        'JOIN_FIELDS': join_fields,
        'SUMMARIES': [SUMMARIES[summary] for summary in summaries],
        'OUTPUT': 'memory:%s' % output_layer_name
        }

    task = QgsProcessingAlgRunnerTask(alg, params, context, feedback)
    task.executed.connect(partial(task_finished, context))
    QgsApplication.taskManager().addTask(task)
    QgsMessageLog.logMessage('Started task {}'.format(task.description()))

    task.waitForFinished()
    QgsApplication.processEvents()
    return OUTPUT_LAYER


def task_finished(context, successful, results):
    global OUTPUT_LAYER
    if not successful:
        return False

    OUTPUT_LAYER = context.takeResultLayer(results['OUTPUT'])
