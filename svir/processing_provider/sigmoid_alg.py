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
from svir.processing_provider.transform_field import TransformFieldAlgorithm
from svir.calculations.transformation_algs import sigmoid


class SigmoidAlgorithm(TransformFieldAlgorithm):
    """
    This algorithm takes a vector layer and calculates the logistic
    sigmoid of the values of one of its fields
    """

    INVERSE = 'INVERSE'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'sigmoid'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(
            "Logistic sigmoid of values of a vector layer field")

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and
        the parameters and outputs associated with it..
        """
        return self.tr(
            r"""
            Logistic sigmoid function:
                :math:`f(x) = \frac{1}{1 + e^{-x}}`

            Inverse function:
                :math:`f(x) = \ln(\frac{x}{1-x})`
            """)

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
