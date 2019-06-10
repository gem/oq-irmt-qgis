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

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingException,
                       QgsProcessingParameterFeatureSink)
from processing.tools import vector


class TransformFieldAlgorithm(QgsProcessingAlgorithm):
    """
    Parent class for algorithms that perform field transformations
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    FIELDS_TO_TRANSFORM = 'FIELDS_TO_TRANSFORM'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return type(self)()

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Field transformation')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'transform'

    def icon(self):
        return QIcon(":/plugins/irmt/transform.svg")

    def svgIconPath(self):
        return QIcon(":/plugins/irmt/transform.svg")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDS_TO_TRANSFORM,
                description=self.tr(
                    "Fields to transform"
                    " (leave empty to transform all numeric fields)"),
                # defaultValue=None,
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=True,
                optional=True,
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the
        # algorithm encountered a fatal error. The exception text can be any
        # string, but in this case we use the pre-built invalidSourceError
        # method to return a standard helper text for when a source cannot be
        # evaluated
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT))

        fields_to_transform = self.parameterAsFields(
            parameters, self.FIELDS_TO_TRANSFORM, context)
        source_fields = source.fields()
        if not fields_to_transform:
            # no fields selected, use all numeric ones
            fields_to_transform = [source_fields.at(i).name()
                                   for i in range(len(source_fields))
                                   if source_fields.at(i).isNumeric()]
        self.transformed_fields = QgsFields()

        transformation_name = self.name()

        fields_to_transform_idxs = []
        for f in fields_to_transform:
            idx = source.fields().lookupField(f)
            if idx >= 0:
                fields_to_transform_idxs.append(idx)
                field_to_transform = source.fields().at(idx)
                if field_to_transform.isNumeric():
                    transformed_field = QgsField(field_to_transform)
                    transformed_field.setName(
                        "%s_%s" % (field_to_transform.name(),
                                   transformation_name))
                    transformed_field.setType(QVariant.Double)
                    transformed_field.setLength(20)
                    transformed_field.setPrecision(6)
                    self.transformed_fields.append(transformed_field)

        out_fields = QgsProcessingUtils.combineFields(
            source_fields, self.transformed_fields)

        (sink, self.dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            source.wkbType(),
            source.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the
        # algorithm encountered a fatal error. The exception text can be any
        # string, but in this case we use the pre-built invalidSinkError method
        # to return a standard helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / len(fields_to_transform)
        transformed_values = {}

        for current, fieldname_to_transform in enumerate(fields_to_transform):
            original_values = vector.values(
                source, fieldname_to_transform)[fieldname_to_transform]
            transformed_values[fieldname_to_transform] = self.transform_values(
                original_values, parameters, context)
            feedback.setProgress(int(current * total))

        feedback.setProgress(0)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, source_feature in enumerate(source.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            sink_feature = QgsFeature(out_fields)

            # copy original fields
            for field in source.fields():
                sink_feature[field.name()] = source_feature[field.name()]

            for original_fieldname, transformed_field in zip(
                    fields_to_transform, self.transformed_fields):
                sink_feature[transformed_field.name()] = \
                    transformed_values[original_fieldname][current]
            sink_feature.setGeometry(source_feature.geometry())

            # Add a feature in the sink
            sink.addFeature(sink_feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: self.dest_id}
