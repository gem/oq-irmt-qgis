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
from svir.calculations.transformation_algs import min_max


class MinMaxAlgorithm(TransformFieldsAlgorithm):

    INVERSE = 'INVERSE'

    def name(self):
        return 'min_max'

    def displayName(self):
        return self.tr(
            "Min-max normalization (to range 0-1) of vector layer fields")

    def shortHelpString(self):
        return self.tr(
            "For each field, the minimum value of that field gets transformed"
            " into a 0, the maximum value gets transformed into a 1, and"
            " every other value gets transformed into a decimal between"
            " 0 and 1. It guarantees that all transformed fields will have the"
            " exact same scale, but does not handle outliers well.\n\n"
            "Direct transformation:\n"
            "f(x_i) = (x_i - min(x)) / (max(x) - min(x))\n\n"
            "Inverse transformation:\n"
            "f(x_i) = 1 - (x_i - min(x)) / (max(x) - min(x))")

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
        transformed_values, _ = min_max(original_values, inverse=inverse)
        return transformed_values
