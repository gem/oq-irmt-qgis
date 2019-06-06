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
from svir.processing_provider.transform_field import TransformFieldAlgorithm
from svir.calculations.transformation_algs import rank


class RankAlgorithm(TransformFieldAlgorithm):
    """
    This algorithm takes a vector layer and ranks the values of one of
    its fields
    """

    INVERSE = 'INVERSE'
    VARIANT = 'VARIANT'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'rank'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(
            "Rank values of a vector layer field")

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and
        the parameters and outputs associated with it..
        """
        return self.tr(
            r"""Assign ranks to data, dealing with ties using the chosen
            strategy.
            """)

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INVERSE,
                description=self.tr("Assign higher ranks to smaller values"),
                defaultValue=False,
            )
        )
        self.variants = (
            ('AVERAGE', self.tr('Average')),
            ('MIN', self.tr('Minimum')),
            ('MAX', self.tr('Maximum')),
            ('DENSE', self.tr('Dense')),
            ('ORDINAL', self.tr('Ordinal')))

        variant = QgsProcessingParameterEnum(
            self.VARIANT,
            self.tr('Tie strategy'),
            options=[p[1] for p in self.variants],
            allowMultiple=False, defaultValue=[1], optional=False)
        self.addParameter(variant)

    def transform_values(self, original_values, parameters, context):
        inverse = self.parameterAsBool(parameters, self.INVERSE, context)
        variant = [self.variants[i][0]
                   for i in self.parameterAsEnums(
                       parameters, self.VARIANT, context)][0]
        original_non_missing = [value for value in original_values
                                if value is not None]
        transformed_non_missing, _ = rank(
            original_non_missing, inverse=inverse, variant_name=variant)
        transformed_values = [None] * len(original_values)
        j = 0
        for i in range(len(original_values)):
            if original_values[i] is None:
                continue
            transformed_values[i] = transformed_non_missing[j]
            j += 1
        return transformed_values
