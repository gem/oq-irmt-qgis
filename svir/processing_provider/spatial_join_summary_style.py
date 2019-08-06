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

# NOTE: this is an extension of
# https://github.com/qgis/QGIS/blob/8a3c7b14c367771d096b4a6d006aa3c4b1017dd5/python/plugins/processing/algs/qgis/SpatialJoinSummary.py  # NOQA
# I tried to sublcass SpatialJoinSummary, but it did not work, therefore I was
# forced to copy and re-adapt the whole class, saving self.dest_id and
# implementing the postProcessing method

import math

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QCoreApplication
from qgis.PyQt.QtWidgets import QInputDialog
from qgis.utils import iface
from qgis.core import (NULL,
                       QgsField,
                       QgsFields,
                       QgsFeatureSink,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsStatisticalSummary,
                       QgsDateTimeStatisticalSummary,
                       QgsStringStatisticalSummary,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class SpatialJoinSummaryStyle(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    JOIN = "JOIN"
    PREDICATE = "PREDICATE"
    JOIN_FIELDS = "JOIN_FIELDS"
    SUMMARIES = "SUMMARIES"
    DISCARD_NONMATCHING = "DISCARD_NONMATCHING"
    OUTPUT = "OUTPUT"
    ADDED_FIELDS = "ADDED_FIELDS"

    def group(self):
        return self.tr('Zonal aggregation')

    def groupId(self):
        return 'aggregate'

    def name(self):
        return 'joinbylocationsummarystyle'

    def displayName(self):
        return self.tr(
            'Join attributes by location (summary) and style output')

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and
        the parameters and outputs associated with it..
        """
        return self.tr("Run joinbylocationsummary and style the output layer")

    def tags(self):
        return self.tr(
            "summary,aggregate,join,intersects,intersecting,touching,within,"
            "contains,overlaps,relation,spatial,"
            "stats,statistics,sum,maximum,minimum,mean,average,"
            "standard,deviation,style,"
            "count,distinct,unique,variance,median,quartile,range,"
            "majority,minority,histogram,distinct").split(',')

    def __init__(self):
        super().__init__()

    def icon(self):
        return QIcon(":/plugins/irmt/aggregate.svg")

    def svgIconPath(self):
        return QIcon(":/plugins/irmt/aggregate.svg")

    def createInstance(self):
        return SpatialJoinSummaryStyle()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self, config=None):
        self.predicates = (
            ('intersects', self.tr('intersects')),
            ('contains', self.tr('contains')),
            ('isEqual', self.tr('equals')),
            ('touches', self.tr('touches')),
            ('overlaps', self.tr('overlaps')),
            ('within', self.tr('within')),
            ('crosses', self.tr('crosses')))

        self.statistics = [
            ('count', self.tr('count')),
            ('unique', self.tr('unique')),
            ('min', self.tr('min')),
            ('max', self.tr('max')),
            ('range', self.tr('range')),
            ('sum', self.tr('sum')),
            ('mean', self.tr('mean')),
            ('median', self.tr('median')),
            ('stddev', self.tr('stddev')),
            ('minority', self.tr('minority')),
            ('majority', self.tr('majority')),
            ('q1', self.tr('q1')),
            ('q3', self.tr('q3')),
            ('iqr', self.tr('iqr')),
            ('empty', self.tr('empty')),
            ('filled', self.tr('filled')),
            ('min_length', self.tr('min_length')),
            ('max_length', self.tr('max_length')),
            ('mean_length', self.tr('mean_length'))]

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, self.tr('Input layer'),
            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.JOIN, self.tr('Join layer'),
            [QgsProcessing.TypeVectorPoint]))
        predicate = QgsProcessingParameterEnum(
            self.PREDICATE,
            self.tr('Geometric predicate'),
            options=[p[1] for p in self.predicates],
            allowMultiple=True, defaultValue=[0])
        predicate.setMetadata({
            'widget_wrapper': {
                'useCheckBoxes': True,
                'columns': 2}})
        self.addParameter(predicate)
        self.addParameter(QgsProcessingParameterField(
            self.JOIN_FIELDS,
            self.tr('Fields to summarise (leave empty to use all fields)'),
            parentLayerParameterName=self.JOIN,
            allowMultiple=True, optional=True))
        stat_idxs = [idx for idx, stat in enumerate(self.statistics)
                     if stat[0] in ('mean', 'sum')]
        self.addParameter(QgsProcessingParameterEnum(
            self.SUMMARIES,
            self.tr(
                'Summaries to calculate (leave empty to use all available)'),
            options=[p[1] for p in self.statistics],
            defaultValue=stat_idxs,
            allowMultiple=True, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.DISCARD_NONMATCHING,
            self.tr('Discard records which could not be joined'),
            defaultValue=False))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            self.tr('Joined layer')))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT))

        join_source = self.parameterAsSource(parameters, self.JOIN, context)
        if join_source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.JOIN))

        join_fields = self.parameterAsFields(
            parameters, self.JOIN_FIELDS, context)
        discard_nomatch = self.parameterAsBool(
            parameters, self.DISCARD_NONMATCHING, context)
        summaries = [self.statistics[i][0] for i in
                     sorted(self.parameterAsEnums(
                         parameters, self.SUMMARIES, context))]

        if not summaries:
            # none selected, so use all
            summaries = [s[0] for s in self.statistics]

        source_fields = source.fields()
        self.fields_to_join = QgsFields()
        join_field_indexes = []
        if not join_fields:
            # no fields selected, use all
            join_fields = [join_source.fields().at(i).name()
                           for i in range(len(join_source.fields()))]

        def addFieldKeepType(original, stat):
            """
            Adds a field to the output, keeping the same data type as the
            original
            """
            field = QgsField(original)
            field.setName(field.name() + '_' + stat)
            self.fields_to_join.append(field)

        def addField(original, stat, type):
            """
            Adds a field to the output, with a specified type
            """
            field = QgsField(original)
            field.setName(field.name() + '_' + stat)
            field.setType(type)
            if type == QVariant.Double:
                field.setLength(20)
                field.setPrecision(6)
            self.fields_to_join.append(field)

        numeric_fields = (
            ('count', QVariant.Int, 'count'),
            ('unique', QVariant.Int, 'variety'),
            ('min', QVariant.Double, 'min'),
            ('max', QVariant.Double, 'max'),
            ('range', QVariant.Double, 'range'),
            ('sum', QVariant.Double, 'sum'),
            ('mean', QVariant.Double, 'mean'),
            ('median', QVariant.Double, 'median'),
            ('stddev', QVariant.Double, 'stDev'),
            ('minority', QVariant.Double, 'minority'),
            ('majority', QVariant.Double, 'majority'),
            ('q1', QVariant.Double, 'firstQuartile'),
            ('q3', QVariant.Double, 'thirdQuartile'),
            ('iqr', QVariant.Double, 'interQuartileRange')
        )

        datetime_fields = (
            ('count', QVariant.Int, 'count'),
            ('unique', QVariant.Int, 'countDistinct'),
            ('empty', QVariant.Int, 'countMissing'),
            ('filled', QVariant.Int),
            ('min', None),
            ('max', None)
        )

        string_fields = (
            ('count', QVariant.Int, 'count'),
            ('unique', QVariant.Int, 'countDistinct'),
            ('empty', QVariant.Int, 'countMissing'),
            ('filled', QVariant.Int),
            ('min', None, 'min'),
            ('max', None, 'max'),
            ('min_length', QVariant.Int, 'minLength'),
            ('max_length', QVariant.Int, 'maxLength'),
            ('mean_length', QVariant.Double, 'meanLength')
        )

        field_types = []
        for f in join_fields:
            idx = join_source.fields().lookupField(f)
            if idx >= 0:
                join_field_indexes.append(idx)

                join_field = join_source.fields().at(idx)
                if join_field.isNumeric():
                    field_types.append('numeric')
                    field_list = numeric_fields
                elif join_field.type() in (
                        QVariant.Date, QVariant.Time, QVariant.DateTime):
                    field_types.append('datetime')
                    field_list = datetime_fields
                else:
                    field_types.append('string')
                    field_list = string_fields

                for f in field_list:
                    if f[0] in summaries:
                        if f[1] is not None:
                            addField(join_field, f[0], f[1])
                        else:
                            addFieldKeepType(join_field, f[0])

        out_fields = QgsProcessingUtils.combineFields(
            source_fields, self.fields_to_join)

        (sink, self.dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields, source.wkbType(),
            source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT))

        # do the join
        predicates = [self.predicates[i][0]
                      for i in self.parameterAsEnums(
                          parameters, self.PREDICATE, context)]

        features = source.getFeatures()
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, f in enumerate(features):
            if feedback.isCanceled():
                break

            if not f.hasGeometry():
                if not discard_nomatch:
                    # ensure consistent count of attributes - otherwise non
                    # matching features will have incorrect attribute length
                    # and provider may reject them
                    attrs = f.attributes()
                    if len(attrs) < len(out_fields):
                        attrs += [NULL] * (len(out_fields) - len(attrs))
                    f.setAttributes(attrs)
                    sink.addFeature(f, QgsFeatureSink.FastInsert)
                continue

            engine = None

            values = []

            request = QgsFeatureRequest().setFilterRect(
                f.geometry().boundingBox()).setSubsetOfAttributes(
                    join_field_indexes).setDestinationCrs(
                        source.sourceCrs(), context.transformContext())
            for test_feat in join_source.getFeatures(request):
                if feedback.isCanceled():
                    break

                join_attributes = []
                for a in join_field_indexes:
                    join_attributes.append(test_feat[a])

                if engine is None:
                    engine = QgsGeometry.createGeometryEngine(
                        f.geometry().constGet())
                    engine.prepareGeometry()

                for predicate in predicates:
                    if getattr(engine, predicate)(
                            test_feat.geometry().constGet()):
                        values.append(join_attributes)
                        break

            feedback.setProgress(int(current * total))

            if len(values) == 0:
                if discard_nomatch:
                    continue
                else:
                    # ensure consistent count of attributes - otherwise non
                    # matching features will have incorrect attribute length
                    # and provider may reject them
                    attrs = f.attributes()
                    if len(attrs) < len(out_fields):
                        attrs += [NULL] * (len(out_fields) - len(attrs))
                    f.setAttributes(attrs)
                    sink.addFeature(f, QgsFeatureSink.FastInsert)
            else:
                attrs = f.attributes()
                for i in range(len(join_field_indexes)):
                    attribute_values = [v[i] for v in values]
                    field_type = field_types[i]
                    if field_type == 'numeric':
                        stat = QgsStatisticalSummary()
                        for v in attribute_values:
                            stat.addVariant(v)
                        stat.finalize()
                        for s in numeric_fields:
                            if s[0] in summaries:
                                val = getattr(stat, s[2])()
                                attrs.append(
                                    val if not math.isnan(val) else NULL)
                    elif field_type == 'datetime':
                        stat = QgsDateTimeStatisticalSummary()
                        stat.calculate(attribute_values)
                        for s in datetime_fields:
                            if s[0] in summaries:
                                if s[0] == 'filled':
                                    attrs.append(
                                        stat.count() - stat.countMissing())
                                elif s[0] == 'min':
                                    attrs.append(stat.statistic(
                                        QgsDateTimeStatisticalSummary.Min))
                                elif s[0] == 'max':
                                    attrs.append(stat.statistic(
                                        QgsDateTimeStatisticalSummary.Max))
                                else:
                                    attrs.append(getattr(stat, s[2])())
                    else:
                        stat = QgsStringStatisticalSummary()
                        for v in attribute_values:
                            if v == NULL:
                                stat.addString('')
                            else:
                                stat.addString(str(v))
                        stat.finalize()
                        for s in string_fields:
                            if s[0] in summaries:
                                if s[0] == 'filled':
                                    attrs.append(
                                        stat.count() - stat.countMissing())
                                else:
                                    attrs.append(getattr(stat, s[2])())

                f.setAttributes(attrs)
                sink.addFeature(f, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: self.dest_id,
                self.ADDED_FIELDS: self.fields_to_join}

    def postProcessAlgorithm(self, context, feedback):
        processed_layer = QgsProcessingUtils.mapLayerFromString(
            self.dest_id, context)
        added_fieldnames = [field.name() for field in self.fields_to_join]
        if len(added_fieldnames) > 1:
            style_by = QInputDialog.getItem(
                iface.mainWindow(), "Style output by", "Field",
                added_fieldnames, editable=False)[0]
        else:
            style_by = added_fieldnames[0]
        LoadOutputAsLayerDialog.style_maps(
            processed_layer, style_by, iface)
        # NOTE: the user might use the following lines after calling the
        #       algorithm from python:
        # QgsProject.instance().addMapLayer(processed_layer)
        # iface.setActiveLayer(processed_layer)
        # iface.zoomToActiveLayer()
        return {self.OUTPUT: processed_layer}