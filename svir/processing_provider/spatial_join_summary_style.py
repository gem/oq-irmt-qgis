# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2019 by GEM Foundation
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

from qgis.core import QgsProcessing, QgsProcessingUtils
from qgis.utils import iface
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QInputDialog
from processing.algs.qgis.SpatialJoinSummary import SpatialJoinSummary

from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class SpatialJoinSummaryStyle(SpatialJoinSummary):

    def __init__(self):
        super(SpatialJoinSummary, self).__init__()

    def group(self):
        return self.tr('Zonal aggregation')

    def groupId(self):
        return 'aggregate'

    def name(self):
        return 'joinbylocationsummarystyle'

    def displayName(self):
        return self.tr(
            'Join attributes by location (summary) and style output')

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and
        the parameters and outputs associated with it..
        """
        return self.tr("Run joinbylocationsummary and style the output layer")

    def tags(self):
        return self.tr(
            "summary,aggregate,join,intersects,intersecting,touching,within,"
            "contains,overlaps,relation,spatial,"
            "stats,statistics,sum,maximum,minimum,mean,average,"
            "standard,deviation,style,"
            "count,distinct,unique,variance,median,quartile,range,"
            "majority,minority,histogram,distinct").split(',')

    def icon(self):
        return QIcon(":/plugins/irmt/aggregate.svg")

    def svgIconPath(self):
        return QIcon(":/plugins/irmt/aggregate.svg")

    def createInstance(self):
        return SpatialJoinSummaryStyle()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)

        super().parameterDefinition(self.INPUT).setDataTypes(
            [QgsProcessing.TypeVectorPolygon])
        super().parameterDefinition(self.JOIN).setDataTypes(
            [QgsProcessing.TypeVectorPoint])

        stat_idxs = [idx for idx, stat in enumerate(self.statistics)
                     if stat[0] in ('mean', 'sum')]
        super().parameterDefinition(self.SUMMARIES).setDefaultValue(stat_idxs)

    def processAlgorithm(self, parameters, context, feedback):
        output = super().processAlgorithm(parameters, context, feedback)
        self.parameters = parameters
        self.dest_id = output[self.OUTPUT]
        return {self.OUTPUT: self.dest_id}

    def postProcessAlgorithm(self, context, feedback):

        input_layer = QgsProcessingUtils.mapLayerFromString(
            self.parameters[self.INPUT], context)

        processed_layer = QgsProcessingUtils.mapLayerFromString(
            self.dest_id, context)

        added_fieldnames = set(processed_layer.fields().names()) - set(
            input_layer.fields().names())
        if len(added_fieldnames) > 1:
            style_by = QInputDialog.getItem(
                iface.mainWindow(), "Style output by", "Field",
                added_fieldnames, editable=False)[0]
        else:
            style_by = added_fieldnames[0]
        LoadOutputAsLayerDialog.style_maps(
            processed_layer, style_by, iface)
        # NOTE: the user might use the following lines after calling the
        #       algorithm from python:
        # QgsProject.instance().addMapLayer(processed_layer)
        # iface.setActiveLayer(processed_layer)
        # iface.zoomToActiveLayer()
        return {self.OUTPUT: processed_layer}
