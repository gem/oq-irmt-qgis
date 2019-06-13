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

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from svir.processing_provider.rank_alg import RankAlgorithm
from svir.processing_provider.sigmoid_alg import SigmoidAlgorithm
from svir.processing_provider.min_max_alg import MinMaxAlgorithm
from svir.processing_provider.z_score_alg import ZScoreAlgorithm
from svir.processing_provider.log10_alg import Log10Algorithm
from svir.processing_provider.simple_quadratic_alg import (
    SimpleQuadraticAlgorithm)
from svir.processing_provider.spatial_join_summary_style import (
    SpatialJoinSummaryStyle)


class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        # Field Transformation
        self.addAlgorithm(RankAlgorithm())
        self.addAlgorithm(MinMaxAlgorithm())
        self.addAlgorithm(SigmoidAlgorithm())
        self.addAlgorithm(SimpleQuadraticAlgorithm())
        self.addAlgorithm(ZScoreAlgorithm())
        self.addAlgorithm(Log10Algorithm())
        # Zonal aggregation
        self.addAlgorithm(SpatialJoinSummaryStyle())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'irmt'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('OpenQuake IRMT')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        # return QgsProcessingProvider.icon(self)
        return QIcon(":/plugins/irmt/icon.svg.png")
