# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2019 by GEM Foundation
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
from qgis.core import (QgsProcessingUtils,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingAlgorithm)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.utils import iface
from processing.algs.qgis import SpatialJoinSummary
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
import processing

# pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]
#pluginPath = '/home/paolo/projects/oq-irmt-qgis/svir'


# class SpatialJoinSummaryStyle(SpatialJoinSummary):
class SpatialJoinSummaryStyle(QgsProcessingAlgorithm):

    # def group(self):
    #     return self.tr('OpenQuake IRMT')

    # def groupId(self):
    #     return 'irmt'

    #def __init__(self):
    #    super().__init__()
    
    # def createInstance(self):
    #    return SpatialJoinSummaryStyle()

    def initAlgorithm(self, config=None):
        pass
    #     self.addParameter(QgsProcessingParameterFeatureSink(
    #         self.OUTPUT, self.tr('Joined layer')))
    #     super().initAlgorithm(config)
    #     # TODO: add parameter style_by

    def name(self):
        return 'joinbylocationsummarystyle'

    def displayName(self):
        return self.tr(
            'Join attributes by location (summary) and style output')

    # def processAlgorithm(self, parameters, context, feedback):
    #     return {'OUTPUT': 1}
    #     output = super().processAlgorithm(parameters, context, feedback)
    #     self.dest_id = output[self.OUTPUT]

    # def postProcessAlgorithm(self, context, feedback):
    #     processed_layer = QgsProcessingUtils.mapLayerFromString(
    #         self.dest_id, context)
    #     style_by = processed_layer.fields()[-1].name()
    #     LoadOutputAsLayerDialog.style_maps(
    #         self.dest_id, style_by, iface, 'input')
    #     return {self.OUTPUT: processed_layer}
