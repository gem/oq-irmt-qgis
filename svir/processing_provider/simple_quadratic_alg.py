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

from qgis.core import (
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       )
from svir.processing_provider.transform_fields import TransformFieldsAlgorithm
from svir.calculations.transformation_algs import simple_quadratic


class SimpleQuadraticAlgorithm(TransformFieldsAlgorithm):

    INVERSE = 'INVERSE'
    VARIANT = 'VARIANT'

    def name(self):
        return 'simple_quadratic'

    def displayName(self):
        return self.tr(
            "Simple quadratic (U-shaped) transformation"
            " of vector layer fields")

    def shortHelpString(self):
        return self.tr(
            "Quadratic or U-shaped functions are the product of a polynomial"
            " equation of degree 2. In a quadratic function, the variable is"
            " always squared resulting in a parabola or U-shaped curve. This"
            " algorithm offers an increasing or decreasing variant of the"
            " quadratic equation for horizontal translations and the"
            " respective inverses of the two for vertical translations.\n"
            "This algorithm performs the simple quadratic transformation"
            " (increasing or decreasing, with bottom = 0) of the values of"
            " vector layer fields.")

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INVERSE,
                description=self.tr("Inverse"),
                defaultValue=False,
            )
        )
        self.variants = (
            ('INCREASING', self.tr('Increasing')),
            ('DECREASING', self.tr('Decreasing')))
        variant = QgsProcessingParameterEnum(
            self.VARIANT,
            self.tr('Variant'),
            options=[p[1] for p in self.variants],
            allowMultiple=False, defaultValue=0, optional=False)
        self.addParameter(variant)

    def transform_values(self, original_values, parameters, context):
        inverse = self.parameterAsBool(parameters, self.INVERSE, context)
        variant = [self.variants[i][0]
                   for i in self.parameterAsEnums(
                       parameters, self.VARIANT, context)][0]
        # TODO: to avoid this, slightly change the simple_quadratic function
        original_non_missing = [value for value in original_values
                                if value is not None]
        transformed_non_missing, _ = simple_quadratic(
            original_non_missing, inverse=inverse, variant_name=variant)
        transformed_values = [None] * len(original_values)
        j = 0
        for i in range(len(original_values)):
            if original_values[i] is None:
                continue
            transformed_values[i] = transformed_non_missing[j]
            j += 1
        return transformed_values
