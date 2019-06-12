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

from qgis.core import QgsProcessingParameterBoolean
from svir.processing_provider.transform_fields import TransformFieldsAlgorithm
from svir.calculations.transformation_algs import z_score


class ZScoreAlgorithm(TransformFieldsAlgorithm):

    INVERSE = 'INVERSE'

    def name(self):
        return 'zscore'

    def displayName(self):
        return self.tr("Z-score normalization of vector layer fields")

    def shortHelpString(self):
        return self.tr(
            "This is a widely used normalization/standardization technique,"
            " that converts variables to a common scale with a mean of zero"
            " and standard deviation of one.\n"
            "Variables with outliers that are extreme values may have a"
            " greater effect while combining them with other variables into"
            " composite indicators. The latter may not be desirable if the"
            " intention is to support compensability where a deficit in one"
            " variable can be offset (or compensated) by a surplus in"
            " another.\n"
            "Z-score handles outliers, but does not produce normalized data"
            " with the exact same scale.\n\n"
            "Direct transformation:\n"
            "f(x_i) = x_i - μ_x / σ_x\n\n"
            "Inverse transformation:\n"
            "Multiply each input by -1, before doing the same")

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INVERSE,
                description=self.tr("Invert min and max (range 1-0)"),
                defaultValue=False,
            )
        )

    def transform_values(self, original_values, parameters, context):
        inverse = self.parameterAsBool(parameters, self.INVERSE, context)
        transformed_values, _ = z_score(original_values, inverse=inverse)
        return transformed_values
