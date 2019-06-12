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

from numpy import nan
from qgis.core import (
                       NULL,
                       QgsProcessingParameterEnum,
                       )
from svir.processing_provider.transform_fields import TransformFieldsAlgorithm
from svir.calculations.transformation_algs import log10_


class Log10Algorithm(TransformFieldsAlgorithm):

    VARIANT = 'VARIANT'

    def name(self):
        return 'log10_'

    def displayName(self):
        return self.tr(
            "Modified log10 transformation (coping with zeros) of"
            " vector layer fields")

    def shortHelpString(self):
        return self.tr(
            "The log10 function is valid only for real positive values.\n"
            "This algorithm copes with the case in which any zeros are"
            "present in the input data, offering two strategies:\n\n"
            "Ignore zeros:\n"
            "each zero in input is transformed into nan\n\n"
            "Increment all values by one:\n"
            "each input value is incremented by 1 before running the"
            " transformation.\n\n"
            "The algorithm uses the numpy.log10 function to transform the"
            " (possibly modified) list of values")

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.variants = (
            ('INCREMENT BY ONE IF ZEROS ARE FOUND',
             self.tr('Increment all input values by one')),
            ('IGNORE ZEROS', self.tr('Ignore zeros')))
        variant = QgsProcessingParameterEnum(
            self.VARIANT,
            self.tr('In case any zero is found in the input values'),
            options=[p[1] for p in self.variants],
            allowMultiple=False, defaultValue=1, optional=False)
        self.addParameter(variant)

    def transform_values(self, original_values, parameters, context):
        variant = [self.variants[i][0]
                   for i in self.parameterAsEnums(
                       parameters, self.VARIANT, context)][0]
        # TODO: to avoid this, slightly change the called function
        original_non_missing = [value for value in original_values
                                if value is not None]
        transformed_non_missing, _ = log10_(
            original_non_missing, variant_name=variant)
        transformed_values = [None] * len(original_values)
        j = 0
        for i in range(len(original_values)):
            if original_values[i] is None:
                continue
            transformed_values[i] = transformed_non_missing[j]
            if transformed_values[i] == NULL:
                transformed_values[i] = nan
            j += 1
        return transformed_values
