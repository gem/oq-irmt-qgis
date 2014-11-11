# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
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
"""
import os.path
import tempfile
import uuid
import copy
import json
from math import ceil

from third_party.requests.exceptions import ConnectionError

from PyQt4.QtCore import (QSettings,
                          QTranslator,
                          QCoreApplication,
                          qVersion,
                          QVariant)

from PyQt4.QtGui import (QAction,
                         QIcon,
                         QProgressDialog,
                         QColor)

from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsField,
                       QgsGeometry,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       QgsVectorDataProvider,
                       QgsMessageLog,
                       QgsMapLayer,
                       QgsVectorFileWriter,
                       QgsGraduatedSymbolRendererV2,
                       QgsSymbolV2, QgsVectorGradientColorRampV2,
                       QgsRuleBasedRendererV2,
                       QgsFillSymbolV2)

from qgis.gui import QgsMessageBar

from qgis.analysis import QgsZonalStatistics
import processing as p
try:
    from processing.algs.saga.SagaUtils import SagaUtils
    saga_was_imported = True
except:
    print "Unable to import SagaUtils module from processing.algs.saga"
    saga_was_imported = False

from calculate_utils import calculate_svi, calculate_iri

from process_layer import ProcessLayer

import resources_rc  # pylint: disable=W0611  # NOQA

from select_input_layers_dialog import SelectInputLayersDialog
from select_layers_to_merge_dialog import SelectLayersToMergeDialog
from attribute_selection_dialog import AttributeSelectionDialog
from transformation_dialog import TransformationDialog
from select_attrs_for_stats_dialog import SelectAttrsForStatsDialog
from select_sv_variables_dialog import SelectSvVariablesDialog
from settings_dialog import SettingsDialog
from weight_data_dialog import WeightDataDialog
from create_weight_tree_dialog import CreateWeightTreeDialog

from import_sv_data import SvDownloader, SvDownloadError

from utils import (LayerEditingManager,
                   tr,
                   get_credentials,
                   TraceTimeManager,
                   WaitCursorManager,
                   assign_default_weights,
                   clear_progress_message_bar, create_progress_message_bar)
from globals import (INT_FIELD_TYPE_NAME,
                     DOUBLE_FIELD_TYPE_NAME,
                     NUMERIC_FIELD_TYPES,
                     TEXTUAL_FIELD_TYPES,
                     DEBUG,
                     PROJECT_TEMPLATE,
                     THEME_TEMPLATE,
                     INDICATOR_TEMPLATE, DEFAULT_OPERATOR)


class Svir:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'svir_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.loss_layer_is_vector = True
        # Input layer containing loss data
        self.loss_layer = None
        # Input layer specifying zones for aggregation and containing social
        # vulnerability data already aggregated by zone
        self.zonal_layer = None
        # From the zonal layer we might want to purge zones containing no loss
        # points, and build a purged zonal layer from that
        self.purged_layer = None
        # our own toolbar
        self.toolbar = None
        # keep a list of the menu items, in order to easily unload them later
        self.registered_actions = dict()
        # Name of the attribute containing loss values (in loss_layer)
        self.loss_attr_name = None
        # Name of the (optional) attribute containing zone id (in loss_layer)
        self.zone_id_in_losses_attr_name = None
        # Name of the attribute containing zone id (in zonal_layer)
        self.zone_id_in_zones_attr_name = None
        # We might have a user-provided layer with losses aggregated by zone
        self.loss_layer_to_merge = None
        # Attribute containing aggregated losses, that will be merged with SVI
        self.aggr_loss_attr_to_merge = None

        self.project_definitions = {}
        self.current_layer = None

        self.aggr_loss_attr_names = dict(count='PTS_CNT',
                                         sum='LOSS_SUM',
                                         avg='LOSS_AVG')

        self.iface.currentLayerChanged.connect(self.current_layer_changed)
        QgsMapLayerRegistry.instance().layersAdded.connect(self.layers_added)
        QgsMapLayerRegistry.instance().layersRemoved.connect(
            self.layers_removed)

    def initGui(self):

        # create our own toolbar
        self.toolbar = self.iface.addToolBar('SVIR')
        self.toolbar.setObjectName('SVIRToolBar')

        # Action to activate the modal dialog to import socioeconomic
        # data from the platform
        self.add_menu_item("import_sv_variables",
                           ":/plugins/svir/load.svg",
                           u"&Load socioeconomic indicators"
                           " from the OpenQuake Platform",
                           self.import_sv_variables,
                           enable=True,
                           add_to_layer_actions=False)
        # Action to activate the modal dialog to select a layer and one of its
        # attributes, in order to transform that attribute
        self.add_menu_item("transform_attribute",
                           ":/plugins/svir/transform.svg",
                           u"&Transform attribute",
                           self.transform_attribute,
                           enable=False,
                           add_to_layer_actions=True)
        # Action to activate the modal dialog to choose weighting of the
        # data from the platform
        self.add_menu_item("create_weight_tree",
                           ":/plugins/svir/define.svg",
                           u"&Define model structure",
                           self.create_weight_tree,
                           enable=False,
                           add_to_layer_actions=True)
        # Action to activate the modal dialog to choose weighting of the
        # data from the platform
        self.add_menu_item("weight_data",
                           ":/plugins/svir/weights.svg",
                           u"&Weight data and calculate indices",
                           self.weight_data,
                           enable=False,
                           add_to_layer_actions=True)
        # Action to activate the modal dialog to guide the user through loss
        # aggregation by zone
        self.add_menu_item("aggregate_losses",
                           ":/plugins/svir/aggregate.svg",
                           u"&Aggregate loss by zone",
                           self.aggregate_losses,
                           enable=True,
                           add_to_layer_actions=False)
        # Action for merging SVI with loss data (both aggregated by zone)
        self.add_menu_item("merge_svi_and_losses",
                           ":/plugins/svir/copy.svg",
                           u"Copy loss data into selected layer",
                           self.merge_svi_with_aggr_losses,
                           enable=False,
                           add_to_layer_actions=True)

        # FIXME Probably to be removed
        # Action for calculating RISKPLUS, RISKMULT and RISK1F indices
        self.add_menu_item("calculate_svir_indices",
                           ":/plugins/svir/calculate.svg",
                           u"Calculate common integrated risk indices",
                           self.calculate_svir_indices,
                           enable=False,
                           add_to_layer_actions=True)

        # Action to upload
        self.add_menu_item("upload",
                           ":/plugins/svir/upload.svg",
                           u"&Upload project to the OpenQuake Platform",
                           self.upload,
                           enable=False,
                           add_to_layer_actions=True)
        # Action to activate the modal dialog to set up settings for the
        # connection with the platform
        self.add_menu_item("settings",
                           ":/plugins/svir/settings.svg",
                           u"&OpenQuake Platform connection settings",
                           self.settings,
                           enable=True)
        self.update_actions_status()

    def layers_added(self):
        self.update_actions_status()

    def layers_removed(self, layer_ids):
        self.update_actions_status()
        for layer_id in layer_ids:
            self.project_definitions.pop(layer_id, None)

    def current_layer_changed(self, layer):
        self.current_layer = layer
        self.update_actions_status()

    def add_menu_item(self,
                      action_name,
                      icon_path,
                      label,
                      corresponding_method,
                      enable=False,
                      add_to_layer_actions=False,
                      layers_type=QgsMapLayer.VectorLayer
                      ):
        """
        Add an item to the SVIR plugin menu and a corresponding toolbar icon
        @param icon_path: Path of the icon associated to the action
        @param label: Name of the action, visible to the user
        @param corresponding_method: Method called when the action is triggered
        """
        if action_name in self.registered_actions:
            raise NameError("Action %s already registered" % action_name)
        action = QAction(QIcon(icon_path), label, self.iface.mainWindow())
        action.setEnabled(enable)
        action.triggered.connect(corresponding_method)
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(u"&SVIR", action)
        self.registered_actions[action_name] = action

        if add_to_layer_actions:
            self.iface.legendInterface().addLegendLayerAction(
                action,
                u"SVIR",
                action_name,
                layers_type,
                True)

    def update_actions_status(self):
        # Check if actions can be enabled
        reg = QgsMapLayerRegistry.instance()
        layer_count = len(list(reg.mapLayers()))
        # Enable/disable "transform" action
        self.registered_actions["transform_attribute"].setDisabled(
            layer_count == 0)
        # Enable/disable "merge SVI and aggregated losses" action
        self.registered_actions["merge_svi_and_losses"].setDisabled(
            layer_count < 2)

        #FIXME Probably to be removed
        # Enable/disable "calculate common SVIR indices" action
        self.registered_actions["calculate_svir_indices"].setDisabled(
            layer_count == 0)

        if DEBUG:
            print 'Selected: %s' % self.current_layer
        try:
            # Activate actions which require a vector layer to be selected
            if self.current_layer.type() != QgsMapLayer.VectorLayer:
                raise AttributeError
            proj_def = self.project_definitions[self.current_layer.id()]
            self.registered_actions["create_weight_tree"].setEnabled(True)
            self.registered_actions["weight_data"].setEnabled(True)
            self.registered_actions["transform_attribute"].setEnabled(True)

            # TODO maybe we want to have only an svi to allow upload, in that
            # case use 'svi_field' in proj_def
            # If IRI was calculated once at least enable upload
            self.registered_actions["upload"].setEnabled(
                'iri_field' in proj_def)

        except KeyError:
            # self.project_definitions[self.current_layer.id()] is not defined
            self.registered_actions["create_weight_tree"].setEnabled(True)
            self.registered_actions["weight_data"].setEnabled(False)
            self.registered_actions["transform_attribute"].setEnabled(True)
        except AttributeError:
            # self.current_layer.id() does not exist or self.current_layer
            # is not vector
            self.registered_actions["transform_attribute"].setEnabled(False)
            self.registered_actions["create_weight_tree"].setEnabled(False)
            self.registered_actions["weight_data"].setEnabled(False)
            self.registered_actions["merge_svi_and_losses"].setEnabled(False)

    def unload(self):
        # Remove the plugin menu items and toolbar icons
        for action_name in self.registered_actions:
            action = self.registered_actions[action_name]
            # Remove the actions in the layer legend
            self.iface.legendInterface().removeLegendLayerAction(action)
            self.iface.removePluginMenu(u"&SVIR", action)
            self.iface.removeToolBarIcon(action)
        clear_progress_message_bar(self.iface)

        #remove connects
        self.iface.currentLayerChanged.disconnect(self.current_layer_changed)
        QgsMapLayerRegistry.instance().layersAdded.disconnect(
            self.layers_added)
        QgsMapLayerRegistry.instance().layersRemoved.disconnect(
            self.layers_removed)

    def aggregate_losses(self):
        """
        Open a modal dialog to select a layer containing zonal data for social
        vulnerability and a layer containing loss data points. After data are
        loaded, self.calculate_stats()
        is automatically called, in order to aggregate loss points with
        respect to the same geometries defined for the socioeconomic
        data, and to compute zonal statistics (point count, loss sum,
        and average for each zone)
        """
        # Create the dialog (after translation) and keep reference
        dlg = SelectInputLayersDialog(self.iface)
        # Run the dialog event loop
        # See if OK was pressed
        if dlg.exec_():
            loss_layer_id = dlg.ui.loss_layer_cbx.itemData(
                dlg.ui.loss_layer_cbx.currentIndex())
            self.loss_layer = QgsMapLayerRegistry.instance().mapLayer(
                loss_layer_id)
            zonal_layer_id = dlg.ui.zonal_layer_cbx.itemData(
                dlg.ui.zonal_layer_cbx.currentIndex())
            self.zonal_layer = QgsMapLayerRegistry.instance().mapLayer(
                zonal_layer_id)

            # check if loss layer is raster or vector (aggregating by zone
            # is different in the two cases)
            self.loss_layer_is_vector = dlg.loss_layer_is_vector

            # Open dialog to ask the user to specify attributes
            # * loss from loss_layer
            # * zone_id from loss_layer
            # * svi from zonal_layer
            # * zone_id from zonal_layer
            if not self.attribute_selection():
                return

            # aggregate losses by zone (calculate count of points in the
            # zone and sum of loss values for the same zone)
            self.calculate_stats()

            if dlg.ui.purge_chk.isChecked():
                self.aggregate_loss_by_zone_and_purge_empty_zones()

            msg = 'Select "Merge SVI with loss data" from SVIR plugin menu ' \
                  'to add aggregated losses to the zonal layer'
            self.iface.messageBar().pushMessage(tr("Info"),
                                                tr(msg),
                                                level=QgsMessageBar.INFO,
                                                duration=8)
            self.update_actions_status()

    def import_sv_variables(self):
        """
        Open a modal dialog to select socioeconomic variables to
        download from the openquake platform
        """

        hostname, username, password = get_credentials(self.iface)
        # login to platform, to be able to retrieve sv indices
        sv_downloader = SvDownloader(hostname)

        try:
            msg = ("Connecting to the OpenQuake Platform...")
            with WaitCursorManager(msg, self.iface):
                sv_downloader.login(username, password)
        except (SvDownloadError, ConnectionError) as e:
            self.iface.messageBar().pushMessage(
                tr("Login Error"),
                tr(str(e)),
                level=QgsMessageBar.CRITICAL)
            self.settings()
            return

        try:
            dlg = SelectSvVariablesDialog(sv_downloader)
            if dlg.exec_():
                msg = ("Loading socioeconomic data from the OpenQuake "
                       "Platform...")
                # Retrieve the indices selected by the user
                indices_list = []
                project_definition = copy.deepcopy(PROJECT_TEMPLATE)
                svi_themes = project_definition[
                    'children'][1]['children']
                known_themes = []
                with WaitCursorManager(msg, self.iface):
                    while dlg.ui.selected_names_lst.count() > 0:
                        item = dlg.ui.selected_names_lst.takeItem(0)
                        item_text = item.text().replace('"', '')

                        sv = item_text.split(',', 2)
                        sv_theme = sv[0]
                        sv_field = sv[1]
                        sv_name = sv[2]
                        self._add_new_theme(svi_themes,
                                            known_themes,
                                            sv_theme,
                                            sv_name,
                                            sv_field)

                        indices_list.append(sv_field)

                    # create string for DB query
                    indices_string = ", ".join(indices_list)

                    assign_default_weights(svi_themes)

                    try:
                        fname, msg = sv_downloader.get_data_by_variables_ids(
                            indices_string)
                    except SvDownloadError as e:
                        self.iface.messageBar().pushMessage(
                            tr("Download Error"),
                            tr(str(e)),
                            level=QgsMessageBar.CRITICAL)
                        return

                display_msg = tr(
                    "Socioeconomic data loaded in a new layer")
                self.iface.messageBar().pushMessage(tr("Info"),
                                                    tr(display_msg),
                                                    level=QgsMessageBar.INFO,
                                                    duration=8)
                QgsMessageLog.logMessage(
                    msg, 'GEM Social Vulnerability Downloader')
                # don't remove the file, otherwise there will be concurrency
                # problems
                uri = ('file://%s?delimiter=,&crs=epsg:4326&'
                       'skipLines=25&trimFields=yes&wktField=geometry' % fname)
                # create vector layer from the csv file exported by the
                # platform (it is still not editable!)
                vlayer_csv = QgsVectorLayer(uri,
                                            'socioeconomic_data_export',
                                            'delimitedtext')
                # obtain a in-memory copy of the layer (editable) and add it to
                # the registry
                layer = ProcessLayer(vlayer_csv).duplicate_in_memory(
                    'socioeconomic_zonal_layer',
                    add_to_registry=True)
                self.iface.setActiveLayer(layer)
                self.project_definitions[layer.id()] = project_definition
                self.update_actions_status()

        except SvDownloadError as e:
            self.iface.messageBar().pushMessage(tr("Download Error"),
                                                tr(str(e)),
                                                level=QgsMessageBar.CRITICAL)

    @staticmethod
    def _add_new_theme(svi_themes,
                       known_themes,
                       indicator_theme,
                       indicator_name,
                       indicator_field):
        """add a new theme to the project_definition"""

        theme = copy.deepcopy(THEME_TEMPLATE)
        theme['name'] = indicator_theme
        if theme['name'] not in known_themes:
            known_themes.append(theme['name'])
            svi_themes.append(theme)
        theme_position = known_themes.index(theme['name'])
        level = float('4.%d' % theme_position)
        # add a new indicator to a theme
        new_indicator = copy.deepcopy(INDICATOR_TEMPLATE)
        new_indicator['name'] = indicator_name
        new_indicator['field'] = indicator_field
        new_indicator['level'] = level
        svi_themes[theme_position]['children'].append(new_indicator)

    def create_weight_tree(self):
        """
        Open a modal dialog to create a weight tree from an existing layer
        """
        current_layer_id = self.current_layer.id()
        try:
            project_definition = self.project_definitions[current_layer_id]
        except KeyError:
            project_definition = None
        dlg = CreateWeightTreeDialog(
            self.iface,
            self.current_layer,
            project_definition,
            self.registered_actions['merge_svi_and_losses'])

        if dlg.exec_():
            project_definition = copy.deepcopy(PROJECT_TEMPLATE)
            if dlg.ui.risk_field_cbx.currentText() != '':
                project_definition['risk_field'] = dlg.ui.risk_field_cbx.currentText()
            svi_themes = project_definition['children'][1]['children']
            known_themes = []
            for indicator in dlg.indicators():
                self._add_new_theme(svi_themes,
                                    known_themes,
                                    indicator['theme'],
                                    indicator['name'],
                                    indicator['field'])

            assign_default_weights(svi_themes)
            self.project_definitions[current_layer_id] = project_definition
            self.update_actions_status()

    def weight_data(self):
        """
        Open a modal dialog to select weights in a d3.js visualization
        """
        current_layer_id = self.current_layer.id()
        project_definition = self.project_definitions[current_layer_id]
        old_project_definition = copy.deepcopy(project_definition)

        first_svi = False
        if 'svi_field' not in project_definition:
            # auto generate svi field
            first_svi = True
            svi_attr_id, iri_attr_id = self.recalculate_indexes(
                project_definition)

        dlg = WeightDataDialog(self.iface, project_definition)
        dlg.json_cleaned.connect(self.weights_changed)

        if dlg.exec_():
            project_definition = dlg.project_definition
            self.update_actions_status()
        else:
            project_definition = old_project_definition
            if first_svi:
                # delete auto generated svi field
                ProcessLayer(self.current_layer).delete_attributes(
                    [svi_attr_id, iri_attr_id])
            else:
                # recalculate with the old weights
                self.recalculate_indexes(project_definition)

        dlg.json_cleaned.disconnect(self.weights_changed)

        # store the correct project definitions
        self.project_definitions[current_layer_id] = project_definition

        # if the user cancels the weighting before a definitive index was
        # created, we don't redraw
        if 'svi_field' in project_definition:
            self.redraw_ir_layer(project_definition)

    def weights_changed(self, data):
        self.recalculate_indexes(data)
        self.redraw_ir_layer(data)

    def recalculate_indexes(self, data):
        project_definition = data

        # when updating weights, we need to recalculate the indexes
        svi_attr_id, discarded_feats_ids = calculate_svi(self.iface,
                                                         self.current_layer,
                                                         project_definition)

        iri_attr_id = None
        # if an IRi has been already calculated, calculate a new one
        if 'risk_field' in data:
            risk_field = data['risk_field']
            try:
                iri_operator = data['operator']
            except KeyError:
                iri_operator = None

            iri_attr_id = calculate_iri(self.iface, self.current_layer,
                                        project_definition, svi_attr_id,
                                        risk_field, discarded_feats_ids,
                                        iri_operator)
        return svi_attr_id, iri_attr_id

    def redraw_ir_layer(self, data):
        # if an IRi has been already calculated, show it else show the SVI
        if 'iri_field' in data:
            target_field = data['iri_field']
            printing_str = 'IRI'
        else:
            target_field = data['svi_field']
            printing_str = 'SVI'

        if DEBUG:
            print 'REDRAWING %s using:\n%s' % (printing_str, data)

        rule_renderer = QgsRuleBasedRendererV2(
            QgsSymbolV2.defaultSymbol(self.current_layer.geometryType()))
        root_rule = rule_renderer.rootRule()

        not_null_rule = root_rule.children()[0].clone()
        not_null_rule.setSymbol(QgsFillSymbolV2.createSimple(
            {'style': 'no',
             'style_border': 'no'}))
        not_null_rule.setFilterExpression('%s IS NOT NULL' % target_field)
        not_null_rule.setLabel('%s:' % target_field)
        root_rule.appendChild(not_null_rule)

        null_rule = root_rule.children()[0].clone()
        null_rule.setSymbol(QgsFillSymbolV2.createSimple(
            {'style': 'no',
             'color_border': '255,255,0,255',
             'width_border': '0.5'}))
        null_rule.setFilterExpression('%s IS NULL' % target_field)
        null_rule.setLabel(tr('Invalid value'))
        root_rule.appendChild(null_rule)

        color1 = QColor("#FFEBEB")
        color2 = QColor("red")
        classes_count = 10
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            self.current_layer,
            target_field,
            classes_count,
            QgsGraduatedSymbolRendererV2.Quantile,
            QgsSymbolV2.defaultSymbol(self.current_layer.geometryType()),
            ramp)

        if graduated_renderer.ranges():
            range_index = len(graduated_renderer.ranges()) - 1
            # NOTE: Workaround to avoid rounding problem (QGIS renderer's bug)
            # which has the consequence to hide the zone containing the highest
            # value in some cases
            upper_value = graduated_renderer.ranges()[range_index].upperValue()
            increased_upper_value = ceil(upper_value * 10000.0) / 10000.0
            graduated_renderer.updateRangeUpperValue(
                range_index, increased_upper_value)
        elif DEBUG:
            print 'All features are NULL'

        # create value ranges
        rule_renderer.refineRuleRanges(not_null_rule, graduated_renderer)
        for rule in not_null_rule.children():
            label = rule.label().replace('"%s" >= ' % target_field, '')
            label = label.replace(' AND "%s" <= ' % target_field, ' - ')
            rule.setLabel(label)
        # remove default rule
        root_rule.removeChildAt(0)

        self.current_layer.setRendererV2(rule_renderer)
        self.iface.mapCanvas().refresh()
        self.iface.legendInterface().refreshLayerSymbology(self.current_layer)

    def settings(self):
        SettingsDialog(self.iface).exec_()

    def merge_svi_with_aggr_losses(self):
        """
        Merge aggregated loss data into the zonal layer (by zone id)
        """
        if self.select_layers_to_merge():
            # Add aggregated loss attribute to zonal_layer
            field = QgsField(self.aggr_loss_attr_to_merge, QVariant.Double)
            field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            ProcessLayer(self.current_layer).add_attributes([field])
            # Populate "loss" attribute with data from aggregation_layer
            self.copy_loss_values_to_current_layer()

            # FIXME Probably this is going to be removed
            msg = 'Select "Calculate common SVIR indices" from SVIR ' \
                  'plugin menu to calculate RISKPLUS, RISKMULT and RISK1F ' \
                  'indices'
            self.iface.messageBar().pushMessage(tr("Info"),
                                                tr(msg),
                                                level=QgsMessageBar.INFO,
                                                duration=8)

    def attribute_selection(self):
        """
        Open a modal dialog containing combo boxes, allowing the user
        to select what are the attribute names for
        * loss values (from loss layer)
        * zone id (from loss layer)
        * social vulnerability index (from zonal layer)
        * zone id (from zonal layer)
        """
        dlg = AttributeSelectionDialog()
        # if the loss layer does not contain an attribute specifying the ids of
        # zones, the user must not be forced to select such attribute, so we
        # add an "empty" option to the combobox
        dlg.ui.zone_id_attr_name_loss_cbox.addItem(
            tr("Use zonal geometries"))
        # populate combo boxes with field names taken by layers
        loss_dp = self.loss_layer.dataProvider()
        loss_fields = list(loss_dp.fields())
        # Load in the comboboxes only the names of the attributes compatible
        # with the following analyses: only numeric for losses and only
        # string for zone ids
        for field in loss_fields:
            # Accept only numeric fields to contain loss data
            if field.typeName() in NUMERIC_FIELD_TYPES:
                dlg.ui.loss_attr_name_cbox.addItem(field.name())
            # Accept only string fields to contain zone ids
            elif field.typeName() in TEXTUAL_FIELD_TYPES:
                dlg.ui.zone_id_attr_name_loss_cbox.addItem(field.name())
            else:
                raise TypeError("Unknown field: type is %d, typeName is %s" % (
                    field.type(), field.typeName()))
        zonal_dp = self.zonal_layer.dataProvider()
        zonal_fields = list(zonal_dp.fields())
        for field in zonal_fields:
            # Accept only string fields to contain zone ids
            if field.typeName() in TEXTUAL_FIELD_TYPES:
                dlg.ui.zone_id_attr_name_zone_cbox.addItem(field.name())
        # if the user presses OK
        if dlg.exec_():
            # retrieve attribute names from combobox selections
            self.loss_attr_name = dlg.ui.loss_attr_name_cbox.currentText()
            # index 0 is for "use zonal geometries" (no zone id available)
            if dlg.ui.zone_id_attr_name_loss_cbox.currentIndex() == 0:
                self.zone_id_in_losses_attr_name = None
            else:
                self.zone_id_in_losses_attr_name = \
                    dlg.ui.zone_id_attr_name_loss_cbox.currentText()
            self.zone_id_in_zones_attr_name = \
                dlg.ui.zone_id_attr_name_zone_cbox.currentText()
            self.update_actions_status()
            return True
        else:
            return False

    def transform_attribute(self):
        """
        A modal dialog is displayed to the user, for the selection of a layer,
        one of its attributes, a transformation algorithm and a variant of the
        algorithm
        """
        dlg = TransformationDialog(self.iface)
        reg = QgsMapLayerRegistry.instance()
        if not reg.count():
            msg = 'No layer available for transformation'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return
        if dlg.exec_():
            layer = reg.mapLayers().values()[
                dlg.ui.layer_cbx.currentIndex()]
            attribute_name = dlg.ui.attrib_cbx.currentText()
            algorithm_name = dlg.ui.algorithm_cbx.currentText()
            variant = dlg.ui.variant_cbx.currentText()
            inverse = dlg.ui.inverse_ckb.isChecked()
            new_attr_name = dlg.ui.new_field_name_txt.text()
            try:
                with WaitCursorManager("Applying transformation", self.iface):
                    res_attr_name, invalid_input_values = ProcessLayer(
                        layer).transform_attribute(attribute_name,
                                                   algorithm_name,
                                                   variant,
                                                   inverse,
                                                   new_attr_name)
                msg = ('The result of the transformation has been added to'
                       'layer %s as a new attribute named %s.') % (
                    layer.name(), res_attr_name)
                if invalid_input_values:
                    msg += (' The transformation could not '
                            'be performed for the following '
                            'input values: %s' % invalid_input_values)
                self.iface.messageBar().pushMessage(
                    tr("Info"),
                    tr(msg),
                    level=(QgsMessageBar.INFO if not invalid_input_values
                           else QgsMessageBar.WARNING),
                    duration=8)
            except (ValueError, NotImplementedError) as e:
                self.iface.messageBar().pushMessage(
                    tr("Error"),
                    tr(e.message),
                    level=QgsMessageBar.CRITICAL)

        elif dlg.use_advanced:
            layer = reg.mapLayers().values()[
                dlg.ui.layer_cbx.currentIndex()]
            if layer.isModified():
                layer.commitChanges()
                layer.triggerRepaint()
                msg = 'Calculation performed on layer %s' % layer.name()
                self.iface.messageBar().pushMessage(
                    tr("Info"),
                    tr(msg),
                    level=QgsMessageBar.INFO,
                    duration=8)
        self.update_actions_status()

    def select_layers_to_merge(self):
        """
        Open a modal dialog allowing the user to select a layer containing
        loss data and one containing SVI data, the aggregated loss attribute
        and the zone id that we want to use for merging.
        """
        dlg = SelectLayersToMergeDialog()
        reg = QgsMapLayerRegistry.instance()
        layer_list = [layer.name() for layer in reg.mapLayers().values()]
        if len(layer_list) < 2:
            msg = 'At least two layers must be available for merging!'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return False
        dlg.ui.loss_layer_cbox.addItems(layer_list)
        if dlg.exec_():
            self.loss_layer_to_merge = reg.mapLayers().values()[
                dlg.ui.loss_layer_cbox.currentIndex()]
            self.aggr_loss_attr_to_merge = \
                dlg.ui.aggr_loss_attr_cbox.currentText()
            self.zone_id_in_zones_attr_name = \
                dlg.ui.merge_attr_cbx.currentText()
            self.update_actions_status()
            return True
        else:
            return False

    def calculate_stats(self):
        """
        A loss_layer containing loss data points needs to be already loaded,
        and it can be a raster or vector layer.
        Another layer (zonal_layer) needs to be previously loaded as well,
        containing socioeconomic data aggregated by zone.
        This method calls other methods of the class in order to produce,
        for each feature (zone):
        * a "PTS_COUNT" attribute, specifying how many loss points are
          inside the zone
        * a "LOSS_SUM" attribute, summing the loss values for all the
          points that are inside the zone
        * a "LOSS_AVG" attribute, averaging losses for each zone
        """
        # add count, sum and avg fields for aggregating statistics
        count_field = QgsField(
            self.aggr_loss_attr_names['count'], QVariant.Int)
        count_field.setTypeName(INT_FIELD_TYPE_NAME)
        sum_field = QgsField(
            self.aggr_loss_attr_names['sum'], QVariant.Double)
        sum_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        avg_field = QgsField(
            self.aggr_loss_attr_names['avg'], QVariant.Double)
        avg_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
        assigned_field_names_d = ProcessLayer(self.zonal_layer).add_attributes(
            [count_field, sum_field, avg_field])
        self.aggr_loss_attr_names['count'] = \
            assigned_field_names_d[self.aggr_loss_attr_names['count']]
        self.aggr_loss_attr_names['sum'] = \
            assigned_field_names_d[self.aggr_loss_attr_names['sum']]
        self.aggr_loss_attr_names['avg'] = \
            assigned_field_names_d[self.aggr_loss_attr_names['avg']]
        if self.loss_layer_is_vector:
            # check if the user specified that the loss_layer contains an
            # attribute specifying what's the zone id for each loss point
            if self.zone_id_in_losses_attr_name:
                # then we can aggregate by zone id, instead of doing a
                # geo-spatial analysis to see in which zone each point is
                self.calculate_vector_stats_aggregating_by_zone_id(
                    self.loss_layer)
            else:
                # otherwise we need to acquire the zones' geometries from the
                # zonal layer and check if loss points are inside those zones
                alg_name = 'saga:clippointswithpolygons'
                # if SAGA is not installed, the check will return a error msg
                if saga_was_imported:
                    err_msg = SagaUtils.checkSagaIsInstalled()
                else:
                    err_msg = 'SagaUtils was not imported.'
                if err_msg is not None:
                    err_msg += tr(" In order to cope with complex geometries, "
                                  "a working installation of SAGA is "
                                  "recommended.")
                    QgsMessageLog.logMessage(err_msg)
                    self.calculate_vector_stats_using_geometries()
                else:
                    # using SAGA to find out in which zone each point is
                    res = p.runalg(alg_name,
                                   self.loss_layer,
                                   self.zonal_layer,
                                   self.zone_id_in_zones_attr_name,
                                   0,
                                   None)
                    if res is None:
                        msg = "An error occurred while attempting to " \
                              "compute zonal statistics with SAGA"
                        self.iface.messageBar().pushMessage(
                            tr("Error"),
                            tr(msg),
                            level=QgsMessageBar.CRITICAL)
                    else:
                        loss_layer_plus_zones = QgsVectorLayer(
                            res['CLIPS'],
                            'Points labeled by zone',
                            'ogr')
                        if DEBUG:
                            QgsMapLayerRegistry.instance().addMapLayer(
                                loss_layer_plus_zones)
                        self.calculate_vector_stats_aggregating_by_zone_id(
                            loss_layer_plus_zones)

        else:
            self.calculate_raster_stats()

    def calculate_vector_stats_aggregating_by_zone_id(self, loss_layer):
        """
        If we know the zone id of each point in the loss map, we
        don't need to use geometries while aggregating, and we can
        simply count by zone id
        """
        tot_points = len(list(loss_layer.getFeatures()))
        msg = tr("Step 2 of 3: aggregating losses by zone id...")
        msg_bar_item, progress = create_progress_message_bar(self.iface, msg)
        with TraceTimeManager(msg, DEBUG):
            zone_stats = {}
            for current_point, point_feat in enumerate(
                    loss_layer.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                # if the user picked an attribute from the loss layer, to be
                # used as zone id, use that; otherwise, use the attribute
                # copied from the zonal layer
                if self.zone_id_in_losses_attr_name:
                    zone_id_attr_name = self.zone_id_in_losses_attr_name
                else:
                    zone_id_attr_name = self.zone_id_in_zones_attr_name
                zone_id = point_feat[zone_id_attr_name]
                loss_value = point_feat[self.loss_attr_name]
                if zone_id in zone_stats:
                    # update zonal stats
                    zone_stats[zone_id]['count'] += 1
                    zone_stats[zone_id]['sum'] += loss_value
                else:
                    # initialize stats for the new zone found
                    zone_stats[zone_id] = {'count': 1,
                                           'sum': loss_value}
        clear_progress_message_bar(self.iface, msg_bar_item)

        msg = tr(
            "Step 3 of 3: writing point counts, loss sums and averages into "
            "the zonal layer...")
        with TraceTimeManager(msg, DEBUG):
            tot_zones = len(list(self.zonal_layer.getFeatures()))
            msg_bar_item, progress = create_progress_message_bar(
                self.iface, msg)
            with LayerEditingManager(self.zonal_layer,
                                     msg,
                                     DEBUG):
                count_index = self.zonal_layer.fieldNameIndex(
                    self.aggr_loss_attr_names['count'])
                sum_index = self.zonal_layer.fieldNameIndex(
                    self.aggr_loss_attr_names['sum'])
                avg_index = self.zonal_layer.fieldNameIndex(
                    self.aggr_loss_attr_names['avg'])
                for current_zone, zone_feat in enumerate(
                        self.zonal_layer.getFeatures()):
                    progress_perc = current_zone / float(tot_zones) * 100
                    progress.setValue(progress_perc)
                    # get the id of the current zone
                    zone_id = zone_feat[self.zone_id_in_zones_attr_name]
                    # initialize points_count, loss_sum and loss_avg
                    # to zero, and update them afterwards only if the zone
                    # contains at least one loss point
                    points_count = 0
                    loss_sum = 0.0
                    loss_avg = 0.0
                    # retrieve count and sum from the dictionary, using
                    # the zone id as key to get the values from the
                    # corresponding dict (otherwise, keep zero values)
                    if zone_id in zone_stats:
                        #points_count, loss_sum = zone_stats[zone_id]
                        points_count = zone_stats[zone_id]['count']
                        loss_sum = zone_stats[zone_id]['sum']
                        # division by zero should be impossible, because we are
                        # computing this only for zones containing at least one
                        # point (otherwise we keep all zeros)
                        loss_avg = loss_sum / points_count
                    # without casting to int and to float, it wouldn't work
                    fid = zone_feat.id()
                    self.zonal_layer.changeAttributeValue(
                        fid, count_index, int(points_count))
                    self.zonal_layer.changeAttributeValue(
                        fid, sum_index, float(loss_sum))
                    self.zonal_layer.changeAttributeValue(
                        fid, avg_index, float(loss_avg))
        clear_progress_message_bar(self.iface, msg_bar_item)

    def calculate_vector_stats_using_geometries(self):
        """
        On the hypothesis that we don't know what is the zone in which
        each point was collected,
        * we create a spatial index of the loss points
        * for each zone (in the layer containing zoneally-aggregated SVI
            * we identify points that are inside the zone's bounding box
            * we check if each of these points is actually inside the
              zone's geometry; if it is:
                * add 1 to the count of points in the zone
                * add the loss value to the total loss of the zone
        Notes:
        * self.loss_layer contains the not aggregated loss points
        * self.zonal_layer contains the zone geometries
        * self.aggregation_layer is the new layer with losses aggregated by
            zone
        """
        # to show the overall progress, cycling through points
        tot_points = len(list(self.loss_layer.getFeatures()))
        msg = tr(
            "Step 2 of 3: creating spatial index for loss points...")
        msg_bar_item, progress = create_progress_message_bar(self.iface, msg)

        # create spatial index
        with TraceTimeManager(tr("Creating spatial index for loss points..."),
                              DEBUG):
            spatial_index = QgsSpatialIndex()
            for current_point, loss_feature in enumerate(
                    self.loss_layer.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                spatial_index.insertFeature(loss_feature)

        clear_progress_message_bar(self.iface, msg_bar_item)

        with LayerEditingManager(self.zonal_layer,
                                 tr("Calculate point counts, sums and "
                                    "averages by zone"),
                                 DEBUG):
            # to show the overall progress, cycling through zones
            tot_zones = len(list(self.zonal_layer.getFeatures()))
            msg = tr("Step 3 of 3: aggregating points by zone...")
            msg_bar_item, progress = create_progress_message_bar(
                self.iface, msg)

            # check if there are no loss points contained in any of the zones
            # and later display a warning if that occurs
            no_loss_points_in_any_zone = True

            count_index = self.zonal_layer.fieldNameIndex(
                self.aggr_loss_attr_names['count'])
            sum_index = self.zonal_layer.fieldNameIndex(
                self.aggr_loss_attr_names['sum'])
            avg_index = self.zonal_layer.fieldNameIndex(
                self.aggr_loss_attr_names['avg'])

            for current_zone, zone_feature in enumerate(
                    self.zonal_layer.getFeatures()):
                progress_perc = current_zone / float(tot_zones) * 100
                progress.setValue(progress_perc)
                msg = "{0}% - Zone: {1} on {2}".format(progress_perc,
                                                       zone_feature.id(),
                                                       tot_zones)
                with TraceTimeManager(msg, DEBUG):
                    points_count = 0
                    loss_sum = 0
                    loss_avg = 0
                    zone_geometry = zone_feature.geometry()
                    # Find ids of points within the bounding box of the zone
                    point_ids = spatial_index.intersects(
                        zone_geometry.boundingBox())
                    # check if the points inside the bounding box of the zone
                    # are actually inside the zone's geometry
                    for point_id in point_ids:
                        msg = "Checking if point {0} is actually inside " \
                              "the zone".format(point_id)
                        with TraceTimeManager(msg, DEBUG):
                            # Get the point feature by the point's id
                            request = QgsFeatureRequest().setFilterFid(
                                point_id)
                            point_feature = self.loss_layer.getFeatures(
                                request).next()
                            point_geometry = QgsGeometry(
                                point_feature.geometry())
                            # check if the point is actually inside the zone
                            # and it is not only contained by its bounding box
                            if zone_geometry.contains(point_geometry):
                                points_count += 1
                                # we have found at least one loss point inside
                                # a zone
                                no_loss_points_in_any_zone = False
                                point_loss = point_feature[self.loss_attr_name]
                                loss_sum += point_loss
                    # if there's at least one point in the zone, update avg
                    if points_count > 0:
                        loss_avg = loss_sum / points_count
                    msg = ("Updating point counts, sums and averages "
                           "for the zone...")
                    with TraceTimeManager(tr(msg), DEBUG):
                        fid = zone_feature.id()
                        self.zonal_layer.changeAttributeValue(
                            fid, count_index, points_count)
                        self.zonal_layer.changeAttributeValue(
                            fid, sum_index, loss_sum)
                        self.zonal_layer.changeAttributeValue(
                            fid, avg_index, loss_avg)
        clear_progress_message_bar(self.iface, msg_bar_item)
        # display a warning in case none of the loss points are inside
        # any of the zones
        if no_loss_points_in_any_zone:
            msg = "No loss points are contained by any of the zones!"
            self.iface.messageBar().pushMessage(tr("Warning"),
                                                tr(msg),
                                                level=QgsMessageBar.INFO,
                                                duration=8)

    def calculate_raster_stats(self):
        """
        In case the layer containing loss data is raster, use
        QgsZonalStatistics to calculate PTS_COUNT, sum and average loss
        values for each zone
        """
        zonal_statistics = QgsZonalStatistics(
            self.zonal_layer,
            self.loss_layer.dataProvider().dataSourceUri())
        progress_dialog = QProgressDialog(
            tr('Calculating zonal statistics'),
            tr('Abort...'),
            0,
            0)
        zonal_statistics.calculateStatistics(progress_dialog)
        # TODO: This is not giving any warning in case no loss points are
        #       contained by any of the zones
        if progress_dialog.wasCanceled():
            self.iface.messageBar().pushMessage(
                tr("ZonalStats Error"),
                tr('You aborted aggregation, so there are '
                   'no data for analysis. Exiting...'),
                level=QgsMessageBar.CRITICAL)

    def aggregate_loss_by_zone_and_purge_empty_zones(self):
        """
        Create a new zonal layer containing all the zones of the
        aggregation layer that contain at least one loss point
        """
        self.purged_layer = ProcessLayer(self.zonal_layer).duplicate_in_memory(
            'Zonal data (purged empty zones)', add_to_registry=True)
        pr = self.purged_layer.dataProvider()
        caps = pr.capabilities()

        tot_zones = len(list(self.zonal_layer.getFeatures()))
        msg = tr("Purging zones containing no loss points...")
        msg_bar_item, progress = create_progress_message_bar(self.iface, msg)

        with LayerEditingManager(self.purged_layer,
                                 msg,
                                 DEBUG):
            for current_zone, zone_feature in enumerate(
                    self.purged_layer.getFeatures()):
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                # keep only zones which contain at least one loss point
                pts_count_attr_name = self.aggr_loss_attr_names['count']
                if zone_feature[pts_count_attr_name] == 0:
                    # delete the feature from the layer
                    if caps & QgsVectorDataProvider.deleteFeatures:
                        pr.deleteFeatures([zone_feature.id()])

        clear_progress_message_bar(self.iface, msg_bar_item)

        # Add purged layer to registry
        if self.purged_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.purged_layer)
            msg = "Zones containing at least one loss point have been " \
                  "copied into a new zonal layer."
            self.iface.messageBar().pushMessage(tr("Info"),
                                                tr(msg),
                                                level=QgsMessageBar.INFO,
                                                duration=8)
        else:
            raise RuntimeError('Purged layer invalid')

    def copy_loss_values_to_current_layer(self):
        """
        Copy loss values from the aggregation layer to the current layer
        which already contains socioeconomic related attributes
        """
        # to show the overall progress, cycling through zones
        tot_zones = len(list(self.loss_layer_to_merge.getFeatures()))
        msg = tr("Populating zonal layer with loss values...")
        msg_bar_item, progress = create_progress_message_bar(self.iface, msg)

        with LayerEditingManager(self.current_layer,
                                 tr("Add loss values to zonal layer"),
                                 DEBUG):

            aggr_loss_index = self.current_layer.fieldNameIndex(
                self.aggr_loss_attr_to_merge)

            # Begin populating "loss" attribute with data from the
            # aggregation_layer selected by the user (possibly purged from
            # zones containing no loss data)
            for current_zone, zonal_feat in enumerate(
                    self.current_layer.getFeatures()):
                zonal_feat_id = zonal_feat.id()
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                for aggr_feat in self.loss_layer_to_merge.getFeatures():
                    if (zonal_feat[self.zone_id_in_zones_attr_name] ==
                            aggr_feat[self.zone_id_in_zones_attr_name]):
                        self.current_layer.changeAttributeValue(
                            zonal_feat_id,
                            aggr_loss_index,
                            aggr_feat[self.aggr_loss_attr_to_merge])
        clear_progress_message_bar(self.iface, msg_bar_item)

    # FIXME Probably to be removed
    def calculate_svir_indices(self):
        """
        Calculate some common indices, combining total risk (in terms of
        losses) and social vulnerability index
        """
        dlg = SelectAttrsForStatsDialog(self.iface)
        reg = QgsMapLayerRegistry.instance()
        layer_count = reg.count()
        if layer_count < 1:
            msg = 'No layer available for statistical computations'
            self.iface.messageBar().pushMessage(tr("Error"),
                                                tr(msg),
                                                level=QgsMessageBar.CRITICAL)
            return
        if dlg.exec_():
            layer = reg.mapLayers().values()[
                dlg.ui.layer_cbx.currentIndex()]
            svi_attr_name = dlg.ui.svi_attr_cbx.currentText()
            aggr_loss_attr_name = dlg.ui.aggr_loss_attr_cbx.currentText()

            # add attributes:
            # RISKPLUS = TOTRISK + TOTSVI
            # RISKMULT = TOTRISK * TOTSVI
            # RISK1F   = TOTRISK * (1 + TOTSVI)
            riskplus_field = QgsField('RISKPLUS', QVariant.Double)
            riskplus_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            riskmult_field = QgsField('RISKMULT', QVariant.Double)
            riskmult_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            risk1f_field = QgsField('RISK1F', QVariant.Double)
            risk1f_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            ProcessLayer(layer).add_attributes(
                [riskplus_field, riskmult_field, risk1f_field])
            # for each zone, calculate the value of the output attributes
            # to show the overall progress, cycling through zones
            tot_zones = len(list(layer.getFeatures()))
            msg = tr("Calculating some common SVIR indices...")
            msg_bar_item, progress = create_progress_message_bar(
                self.iface, msg)
            with LayerEditingManager(layer,
                                     tr("Calculate some common SVIR indices"),
                                     DEBUG):
                riskplus_idx = layer.fieldNameIndex('RISKPLUS')
                riskmult_idx = layer.fieldNameIndex('RISKMULT')
                risk1f_idx = layer.fieldNameIndex('RISK1F')

                for current_zone, svir_feat in enumerate(
                        layer.getFeatures()):
                    svir_feat_id = svir_feat.id()
                    progress_percent = current_zone / float(tot_zones) * 100
                    progress.setValue(progress_percent)
                    layer.changeAttributeValue(
                        svir_feat_id,
                        riskplus_idx,
                        (svir_feat[aggr_loss_attr_name] +
                         svir_feat[svi_attr_name]))
                    layer.changeAttributeValue(
                        svir_feat_id,
                        riskmult_idx,
                        (svir_feat[aggr_loss_attr_name] *
                         svir_feat[svi_attr_name]))
                    layer.changeAttributeValue(
                        svir_feat_id,
                        risk1f_idx,
                        (svir_feat[aggr_loss_attr_name] *
                         (1 + svir_feat[svi_attr_name])))
            clear_progress_message_bar(self.iface, msg_bar_item)
        elif dlg.use_advanced:
            layer = reg.mapLayers().values()[
                dlg.ui.layer_cbx.currentIndex()]
            if layer.isModified():
                layer.commitChanges()
                layer.triggerRepaint()
                msg = 'Calculation performed on layer %s' % layer.name()
                self.iface.messageBar().pushMessage(
                    tr("Info"),
                    tr(msg),
                    level=QgsMessageBar.INFO,
                    duration=8)
        elif dlg.use_transform_dialog:
            self.transform_attribute()
        self.update_actions_status()

    def upload(self):
        temp_dir = tempfile.gettempdir()
        file_stem = '%s%ssvir_%s' % (temp_dir, os.path.sep, uuid.uuid4())

        data_json = '%s%s' % (file_stem, '_data.json')
        proj_json = '%s%s' % (file_stem, '_proj.json')

        project_definition = self.project_definitions[self.current_layer.id()]
        with open(proj_json, 'w') as outfile:
            json.dump(project_definition, outfile)

        QgsVectorFileWriter.writeAsVectorFormat(
            self.current_layer,
            data_json,
            'utf-8',
            self.current_layer.crs(),
            'GeoJson')
        msg = tr("Uploading to platform")
        msg_bar_item, progress = create_progress_message_bar(self.iface, msg)

        # TODO UPLOAD
        max_range = 1000000.0
        for i in range(int(max_range)):
            p_int = i / max_range * 100
            progress.setValue(p_int)
        clear_progress_message_bar(self.iface, msg_bar_item)
