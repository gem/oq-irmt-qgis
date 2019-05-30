# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsField,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink)
from processing.tools import vector


class NormalizeFieldAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm takes a vector layer and normalizes the values of one of
    its fields in the interval 0-1 (or 1-0 if 'inverted' is checked).
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    FIELD_TO_NORMALIZE = 'FIELD_TO_NORMALIZE'
    INVERTED = 'INVERTED'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return NormalizeFieldAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'normalizefield'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(
            "Min-max normalization (range 0-1) of a vector layer field")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Data Transformation')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'transform'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and
        the parameters and outputs associated with it..
        """
        return self.tr(
            "Min-max normalization (range 0-1) of a vector layer field")

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
                self.FIELD_TO_NORMALIZE,
                description=self.tr("Field to normalize"),
                defaultValue=None,
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,  # FIXME
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INVERTED,
                description=self.tr("Invert transformation"),
                defaultValue=False,
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

        fieldname_to_normalize = self.parameterAsString(
            parameters, self.FIELD_TO_NORMALIZE, context)
        field_to_normalize = [field for field in source.fields()
                              if field.name() == fieldname_to_normalize][0]
        normalized_field = QgsField(field_to_normalize)
        normalized_field_name = '%s_MIN_MAX' % fieldname_to_normalize
        normalized_field.setName(normalized_field_name)
        sink_fields = source.fields()
        sink_fields.append(normalized_field)

        (sink, self.dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            sink_fields,
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

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        original_values = vector.values(
            source, fieldname_to_normalize)[fieldname_to_normalize]

        min_value = min(original_values)
        max_value = max(original_values)
        min_max_range = float(max_value - min_value)
        if min_max_range == 0:
            raise ValueError(
                "The min_max transformation can not be performed"
                " if the range of valid values (max-min) is zero.")

        inverted = self.parameterAsBool(
            parameters, self.INVERTED, context)

        # Transform
        if inverted:
            normalized_values = [1.0 - ((x - min_value) / min_max_range)
                                 for x in original_values]
        else:
            normalized_values = [(x - min_value) / min_max_range
                                 for x in original_values]

        for current, source_feature in enumerate(source.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            sink_feature = QgsFeature(sink_fields)
            for field in source.fields():
                sink_feature[field.name()] = source_feature[field.name()]
            sink_feature[normalized_field_name] = normalized_values[current]
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

    def postProcessAlgorithm(self, context, feedback):

        processed_layer = QgsProcessingUtils.mapLayerFromString(
            self.dest_id, context)

        # Do smth with the layer, e.g. style it

        return {self.OUTPUT: processed_layer}
