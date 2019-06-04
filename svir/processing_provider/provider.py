from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from svir.processing_provider.min_max_alg import MinMaxAlgorithm
from svir.processing_provider.z_score_alg import ZScoreAlgorithm
from svir.processing_provider.spatial_join_summary_style import (
    SpatialJoinSummaryStyle)


class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(MinMaxAlgorithm())
        self.addAlgorithm(ZScoreAlgorithm())
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
