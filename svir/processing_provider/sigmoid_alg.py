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
from svir.calculations.transformation_algs import sigmoid


class SigmoidAlgorithm(TransformFieldsAlgorithm):
    """
    This algorithm takes a vector layer and calculates the logistic
    sigmoid of the values of one of its fields
    """

    INVERSE = 'INVERSE'

    def name(self):
        return 'logistic_sigmoid'

    def displayName(self):
        return self.tr(
            "Logistic sigmoid (S-shaped) function")

    def shortHelpString(self):
        return self.tr(
            "The Sigmoid function is a transformation having an 'S' shape"
            " (sigmoid curve). It is used to transform values on (-∞, ∞)"
            " into numbers on (0, 1). The Sigmoid function is often utilized"
            " because the transformation is relative to a convergence upon an"
            " upper limit as defined by the S-curve.\n"
            "This algorithm utilizes"
            " a 'simple sigmoid function' as well as its inverse. The inverse"
            " of the Sigmoid function is a logit function which transfers"
            " variables on (0, 1) into a new variable on (-∞, ∞).\n\n"
            "Logistic sigmoid function:\n"
            "f(x) = 1 / 1 + e^(-x)\n\n"
            "Inverse function:\n"
            "f(x) = ln(x / (1-x))")

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INVERSE,
                description=self.tr("Inverted function"),
                defaultValue=False,
            )
        )

    def transform_values(self, original_values, parameters, context):
        inverse = self.parameterAsBool(parameters, self.INVERSE, context)
        transformed_values, _ = sigmoid(original_values, inverse=inverse)
        return transformed_values
