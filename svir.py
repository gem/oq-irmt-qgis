# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013-2015 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
import json
import os.path
import tempfile
import uuid
import copy
import zipfile
import StringIO

from math import ceil
from download_layer_dialog import DownloadLayerDialog
from metadata_utilities import write_iso_metadata_file, get_supplemental_info

from PyQt4.QtCore import (QSettings,
                          QTranslator,
                          QCoreApplication,
                          qVersion,
                          QVariant,
                          QUrl)

from PyQt4.QtGui import (QAction,
                         QIcon,
                         QProgressDialog,
                         QColor,
                         QFileDialog,
                         QDesktopServices,
                         QMessageBox)

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
                       QgsFillSymbolV2,
                       QgsProject,)

from qgis.gui import QgsMessageBar

from qgis.analysis import QgsZonalStatistics
import processing as p
from set_project_definition_dialog import SetProjectDefinitionDialog
from upload_metadata_dialog import UploadMetadataDialog

try:
    from processing.algs.saga.SagaUtils import SagaUtils
    saga_was_imported = True
except:
    print "Unable to import SagaUtils module from processing.algs.saga"
    saga_was_imported = False

from calculate_utils import calculate_svi, calculate_ri, calculate_iri

from process_layer import ProcessLayer

import resources_rc  # pylint: disable=W0611  # NOQA

from select_input_layers_dialog import SelectInputLayersDialog
from attribute_selection_dialog import AttributeSelectionDialog
from transformation_dialog import TransformationDialog
from select_sv_variables_dialog import SelectSvVariablesDialog
from settings_dialog import SettingsDialog
from weight_data_dialog import WeightDataDialog
from upload_settings_dialog import UploadSettingsDialog

from import_sv_data import get_loggedin_downloader

from utils import (LayerEditingManager,
                   tr,
                   TraceTimeManager,
                   WaitCursorManager,
                   assign_default_weights,
                   clear_progress_message_bar, create_progress_message_bar,
                   SvNetworkError, ask_for_download_destination,
                   files_exist_in_destination, confirm_overwrite,
                   count_heading_commented_lines)
from shared import (SVIR_PLUGIN_VERSION,
                    INT_FIELD_TYPE_NAME,
                    DOUBLE_FIELD_TYPE_NAME,
                    NUMERIC_FIELD_TYPES,
                    TEXTUAL_FIELD_TYPES,
                    DEBUG,
                    PROJECT_TEMPLATE,
                    THEME_TEMPLATE,
                    INDICATOR_TEMPLATE)


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
        # our own toolbar
        self.toolbar = None
        # keep a list of the menu items, in order to easily unload them later
        self.registered_actions = dict()
        # Name of the attribute containing loss values (in loss_layer)
        self.loss_attr_names = None
        # Name of the (optional) attribute containing zone id (in loss_layer)
        self.zone_id_in_losses_attr_name = None
        # Name of the attribute containing zone id (in zonal_layer)
        self.zone_id_in_zones_attr_name = None
        # We might have a user-provided layer with losses aggregated by zone
        self.loss_layer_to_merge = None
        # Attribute containing aggregated losses, that will be merged with SVI
        self.aggr_loss_attr_to_merge = None
        # Dict associating loss attribute names and the corresponding attribute
        # names created in the zonal layer
        self.loss_attrs_dict = {}

        self.current_layer = None

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
        # Action to activate the modal dialog to import socioeconomic
        # data from the platform
        self.add_menu_item("import_layer",
                           ":/plugins/svir/load_layer.svg",
                           u"&Import project from the OpenQuake Platform",
                           self.import_layer,
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
        # Action to set a preexisting project definition to a layer
        self.add_menu_item("set_project_definition",
                           ":/plugins/svir/copy.svg",
                           u"&Set project definition",
                           self.set_project_definition,
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

        # Action to upload
        self.add_menu_item("upload",
                           ":/plugins/svir/upload.svg",
                           u"&Upload project to the OpenQuake Platform",
                           self.upload,
                           enable=False,
                           add_to_layer_actions=True)
        # Action to activate the modal dialog to set up show_settings for the
        # connection with the platform
        self.add_menu_item("show_settings",
                           ":/plugins/svir/settings.svg",
                           u"&OpenQuake Platform connection settings",
                           self.show_settings,
                           enable=True)

        self.update_actions_status()

    def layers_added(self):
        self.update_actions_status()

    def layers_removed(self, layer_ids):
        self.update_actions_status()
        for layer_id in layer_ids:
            self.update_proj_def(layer_id)

    def sync_proj_def(self):
        # get project_definitions from the project's properties
        # it returns a tuple, with the returned value and a boolean indicating
        # if such property is available
        resp = QgsProject.instance().readEntry('svir', 'project_definitions')
        if resp[1] is True:
            self.project_definitions = json.loads(resp[0])
        else:
            self.project_definitions = {}
        if DEBUG:
            print "self.project_definitions synchronized with project, as:"
            print self.project_definitions

    def update_proj_def(self, layer_id, proj_def=None):
        self.sync_proj_def()
        # add the project definition to the list
        # or pop the layer's project definition if no proj_def is provided
        if proj_def is not None:
            self.project_definitions[layer_id] = proj_def
        else:
            self.project_definitions.pop(layer_id, None)
        # set the QgsProject's property
        QgsProject.instance().writeEntry(
            'svir', 'project_definitions',
            json.dumps(self.project_definitions,
                       sort_keys=False,
                       indent=2,
                       separators=(',', ': ')))
        if DEBUG:
            print "Project's property 'project_definitions' updated:"
            print QgsProject.instance().readEntry(
                'svir', 'project_definitions')[0]

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

        if DEBUG:
            print 'Selected: %s' % self.current_layer
        try:
            # Activate actions which require a vector layer to be selected
            if self.current_layer.type() != QgsMapLayer.VectorLayer:
                raise AttributeError
            self.registered_actions["set_project_definition"].setEnabled(True)
            self.registered_actions["weight_data"].setEnabled(True)
            self.registered_actions["transform_attribute"].setEnabled(True)
            self.sync_proj_def()
            proj_def = self.project_definitions[self.current_layer.id()]
            self.registered_actions["upload"].setEnabled(proj_def is not None)
        except KeyError:
            # self.project_definitions[self.current_layer.id()] is not defined
            pass  # We can still use the weight_data dialog
        except AttributeError:
            # self.current_layer.id() does not exist or self.current_layer
            # is not vector
            self.registered_actions["transform_attribute"].setEnabled(False)
            self.registered_actions["weight_data"].setEnabled(False)
            self.registered_actions["upload"].setEnabled(False)
            self.registered_actions["set_project_definition"].setEnabled(False)

    def unload(self):
        # Remove the plugin menu items and toolbar icons
        for action_name in self.registered_actions:
            action = self.registered_actions[action_name]
            # Remove the actions in the layer legend
            self.iface.legendInterface().removeLegendLayerAction(action)
            self.iface.removePluginMenu(u"&SVIR", action)
            self.iface.removeToolBarIcon(action)
        clear_progress_message_bar(self.iface.messageBar())

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
        # for safety, clean variables that might be there from a previous
        # attempt
        self.loss_attr_names = None
        self.zone_id_in_losses_attr_name = None
        self.zone_id_in_zones_attr_name = None
        self.loss_attrs_dict = {}
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
            # zone, sum and average loss values for the same zone)
            self.calculate_stats()

            if dlg.ui.purge_chk.isChecked():
                self.purge_zones_without_loss_points()

            self.update_actions_status()

    def import_sv_variables(self):
        """
        Open a modal dialog to select socioeconomic variables to
        download from the openquake platform
        """

        # login to platform, to be able to retrieve sv indices
        sv_downloader = get_loggedin_downloader(self.iface)
        if sv_downloader is None:
            self.show_settings()
            return

        try:
            dlg = SelectSvVariablesDialog(sv_downloader)
            if dlg.exec_():
                dest_filename = QFileDialog.getSaveFileName(
                    dlg,
                    'Download destination',
                    os.path.expanduser("~"),
                    'Shapefiles (*.shp)')
                if dest_filename:
                    if dest_filename[-4:] != ".shp":
                        dest_filename += ".shp"
                else:
                    return
                # TODO: We should fix the workflow in case no geometries are
                # downloaded. Currently we must download them, so the checkbox
                # to let the user choose has been temporarily removed.
                # load_geometries = dlg.ui.load_geometries_chk.isChecked()
                load_geometries = True
                msg = ("Loading socioeconomic data from the OpenQuake "
                       "Platform...")
                # Retrieve the indices selected by the user
                indices_list = []
                iso_codes_list = []
                project_definition = copy.deepcopy(PROJECT_TEMPLATE)
                svi_themes = project_definition[
                    'children'][1]['children']
                known_themes = []
                with WaitCursorManager(msg, self.iface):
                    while dlg.ui.list_multiselect.selected_widget.count() > 0:
                        item = \
                            dlg.ui.list_multiselect.selected_widget.takeItem(0)
                        ind_code = item.text().split(':')[0]
                        ind_info = dlg.indicators_info_dict[ind_code]
                        sv_theme = ind_info['theme']
                        sv_field = ind_code
                        sv_name = ind_info['name']

                        self._add_new_theme(svi_themes,
                                            known_themes,
                                            sv_theme,
                                            sv_name,
                                            sv_field)

                        indices_list.append(sv_field)
                    while dlg.ui.country_select.selected_widget.count() > 0:
                        item = \
                            dlg.ui.country_select.selected_widget.takeItem(0)
                        # get the iso from something like:
                        # country_name (iso_code)
                        iso_code = item.text().split('(')[1].split(')')[0]
                        iso_codes_list.append(iso_code)

                    # create string for DB query
                    indices_string = ",".join(indices_list)
                    iso_codes_string = ",".join(iso_codes_list)

                    assign_default_weights(svi_themes)

                    try:
                        fname, msg = sv_downloader.get_sv_data(
                            indices_string, load_geometries, iso_codes_string)
                    except SvNetworkError as e:
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

                # count top lines in the csv starting with '#'
                lines_to_skip_count = count_heading_commented_lines(fname)
                if load_geometries:
                    uri = ('file://%s?delimiter=,&crs=epsg:4326&skipLines=%s'
                           '&trimFields=yes&wktField=geometry' % (
                               fname, lines_to_skip_count))
                else:
                    uri = ('file://%s?delimiter=,&skipLines=%s'
                           '&trimFields=yes' % (fname,
                                                lines_to_skip_count))
                # create vector layer from the csv file exported by the
                # platform (it is still not editable!)
                vlayer_csv = QgsVectorLayer(uri,
                                            'socioeconomic_data_export',
                                            'delimitedtext')
                if not load_geometries:
                    if vlayer_csv.isValid():
                        QgsMapLayerRegistry.instance().addMapLayer(vlayer_csv)
                    else:
                        raise RuntimeError('Layer invalid')
                    layer = vlayer_csv
                else:
                    result = QgsVectorFileWriter.writeAsVectorFormat(
                        vlayer_csv, dest_filename, 'CP1250',
                        None, 'ESRI Shapefile')
                    if result != QgsVectorFileWriter.NoError:
                        raise RuntimeError('Could not save shapefile')
                    layer = QgsVectorLayer(
                        dest_filename, 'Socioeconomic data', 'ogr')
                    if layer.isValid():
                        QgsMapLayerRegistry.instance().addMapLayer(layer)
                    else:
                        raise RuntimeError('Layer invalid')
                self.iface.setActiveLayer(layer)
                self.update_proj_def(layer.id(), project_definition)
                self.update_actions_status()

        except SvNetworkError as e:
            self.iface.messageBar().pushMessage(tr("Download Error"),
                                                tr(str(e)),
                                                level=QgsMessageBar.CRITICAL)

    def import_layer(self):
        sv_downloader = get_loggedin_downloader(self.iface)
        if sv_downloader is None:
            self.show_settings()
            return

        dlg = DownloadLayerDialog(sv_downloader)
        if dlg.exec_():
            dest_dir = ask_for_download_destination(dlg)
            if not dest_dir:
                return
            try:
                #download and unzip layer
                shape_url_fmt = (
                    '%s/geoserver/wfs?'
                    'format_options=charset:UTF-8'
                    '&typename=%s'
                    '&outputFormat=SHAPE-ZIP'
                    '&version=1.0.0'
                    '&service=WFS'
                    '&request=GetFeature')
                shape_url = shape_url_fmt % (sv_downloader.host, dlg.layer_id)
                with WaitCursorManager("Downloading project", self.iface):
                    request = sv_downloader.sess.get(shape_url)

                downloaded_zip = zipfile.ZipFile(
                    StringIO.StringIO(request.content))
            except SvNetworkError as e:
                self.iface.messageBar().pushMessage(
                    tr("Download Error"),
                    tr(str(e)),
                    level=QgsMessageBar.CRITICAL)
                return
            files_in_zip = downloaded_zip.namelist()
            shp_file = next(
                filename for filename in files_in_zip if '.shp' in filename)
            file_in_destination = files_exist_in_destination(
                dest_dir, files_in_zip)

            if file_in_destination:
                while confirm_overwrite(dlg, file_in_destination) == \
                        QMessageBox.No:
                    dest_dir = ask_for_download_destination(dlg)
                    file_in_destination = files_exist_in_destination(
                        dest_dir, downloaded_zip.namelist())
                    if not file_in_destination:
                        break

            downloaded_zip.extractall(dest_dir)
            request_url = '%s/svir/get_layer_metadata_url?layer_name=%s' % (
                sv_downloader.host, dlg.layer_id)
            get_metadata_url_resp = sv_downloader.sess.get(request_url)
            if not get_metadata_url_resp.ok:
                self.iface.messageBar().pushMessage(
                    tr("Download Error"),
                    tr('Unable to locate the metadata'),
                    level=QgsMessageBar.CRITICAL)
                return
            metadata_url = get_metadata_url_resp.content
            request = sv_downloader.sess.get(metadata_url)
            metadata_xml = request.content

            project_definition = get_supplemental_info(
                metadata_xml, '{http://www.isotc211.org/2005/gmd}MD_Metadata/')
            dest_file = os.path.join(dest_dir, shp_file)
            layer = QgsVectorLayer(
                dest_file,
                dlg.extra_infos[dlg.layer_id]['Title'], 'ogr')
            if layer.isValid():
                QgsMapLayerRegistry.instance().addMapLayer(layer)
                self.iface.messageBar().pushMessage(
                    tr('Download successful'),
                    tr('Shapefile downloaded to %s' % dest_file),
                    duration=8)
            else:
                self.iface.messageBar().pushMessage(
                    tr("Download Error"),
                    tr('Layer invalid'),
                    level=QgsMessageBar.CRITICAL)
                return
            self.iface.setActiveLayer(layer)
            self.update_proj_def(layer.id(), project_definition)
            self.update_actions_status()

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

    def set_project_definition(self):
        """
        Open a modal dialog to select weights in a d3.js visualization
        """
        self.sync_proj_def()
        current_layer_id = self.iface.activeLayer().id()
        try:
            project_definition = self.project_definitions[current_layer_id]
        except KeyError:
            project_definition = PROJECT_TEMPLATE
            self.update_proj_def(current_layer_id, project_definition)
        old_project_definition = copy.deepcopy(project_definition)

        dlg = SetProjectDefinitionDialog(self.iface, project_definition, )
        if dlg.exec_():
            project_definition = dlg.project_definition
            self.update_actions_status()
        else:
            project_definition = old_project_definition

        print project_definition

        self.update_proj_def(current_layer_id, project_definition)
        self.redraw_ir_layer(project_definition)

    def weight_data(self):
        """
        Open a modal dialog to select weights in a d3.js visualization
        """
        current_layer_id = self.current_layer.id()
        try:
            project_definition = self.project_definitions[current_layer_id]
        except KeyError:
            project_definition = PROJECT_TEMPLATE
            self.update_proj_def(current_layer_id, project_definition)
        old_project_definition = copy.deepcopy(project_definition)

        first_svi = False
        # if the svi_node does not contain the field name
        if 'field' not in project_definition['children'][1]:  # svi_node
            # auto generate svi field
            first_svi = True
            svi_attr_id, ri_attr_id, iri_attr_id = self.recalculate_indexes(
                project_definition)

        dlg = WeightDataDialog(self.iface, project_definition)
        dlg.show()

        dlg.json_cleaned.connect(self.weights_changed)
        if dlg.exec_():
            project_definition = dlg.project_definition
            self.update_actions_status()
        else:
            project_definition = old_project_definition
            if first_svi:
                # delete auto generated svi field
                ProcessLayer(self.current_layer).delete_attributes(
                    [svi_attr_id, ri_attr_id, iri_attr_id])
            else:
                # recalculate with the old weights
                self.recalculate_indexes(project_definition)
        dlg.json_cleaned.disconnect(self.weights_changed)
        # store the correct project definitions
        self.update_proj_def(current_layer_id, project_definition)
        self.redraw_ir_layer(project_definition)

    def weights_changed(self, data):
        self.recalculate_indexes(data)
        self.redraw_ir_layer(data)

    def recalculate_indexes(self, data):
        project_definition = data

        # when updating weights, we need to recalculate the indexes
        svi_attr_id, discarded_feats_ids_svi = calculate_svi(
            self.iface, self.current_layer, project_definition)
        ri_attr_id, discarded_feats_ids_ri = calculate_ri(
            self.iface, self.current_layer, project_definition)
        if svi_attr_id is None or ri_attr_id is None:
            return None, None, None
        discarded_feats_ids = discarded_feats_ids_svi | discarded_feats_ids_ri
        iri_attr_id, discarded_feats_ids = calculate_iri(
            self.iface, self.current_layer,
            project_definition,
            svi_attr_id,
            ri_attr_id, discarded_feats_ids)
        return svi_attr_id, ri_attr_id, iri_attr_id

    def is_svi_renderable(self, proj_def):
        svi_node = proj_def['children'][1]
        # check that that the svi_node has a corresponding field
        if 'field' not in svi_node:
            return False
        # check that there is at least one theme
        if 'children' not in svi_node:
            return False
        if len(svi_node['children']) == 0:
            return False
        # check that each theme contains at least one indicator
        for theme_node in svi_node['children']:
            if 'children' not in theme_node:
                return False
            if len(theme_node['children']) == 0:
                return False
        return True

    def is_ri_renderable(self, proj_def):
        ri_node = proj_def['children'][0]
        # check that that the ri_node has a corresponding field
        if 'field' not in ri_node:
            return False
        # check that there is at least one risk indicator
        if 'children' not in ri_node:
            return False
        if len(ri_node['children']) == 0:
            return False
        return True

    def is_iri_renderable(self, proj_def):
        iri_node = proj_def
        # check that that the iri_node has a corresponding field
        if 'field' not in iri_node:
            return False
        # check that all the sub-indices are well-defined
        if not self.is_ri_renderable(proj_def):
            return False
        if not self.is_svi_renderable(proj_def):
            return False
        return True

    def redraw_ir_layer(self, data):
        # if an IRI has been already calculated, show it
        # else show the SVI, else RI
        if self.is_iri_renderable(data):
            target_field = data['field']
            printing_str = 'IRI'
        elif self.is_svi_renderable(data):
            svi_node = data['children'][1]
            target_field = svi_node['field']
            printing_str = 'SVI'
        elif self.is_ri_renderable(data):
            ri_node = data['children'][0]
            target_field = ri_node['field']
            printing_str = 'RI'
        else:
            return
        if self.current_layer.fieldNameIndex(target_field) == -1:
            return
        if DEBUG:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            print 'REDRAWING %s using:' % printing_str
            pp.pprint(data)

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

    def show_settings(self):
        SettingsDialog(self.iface).exec_()

    def attribute_selection(self):
        """
        Open a modal dialog containing combo boxes, allowing the user
        to select what are the attribute names for
        * loss values (from loss layer)
        * zone id (from loss layer)
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
        default_zone_id_loss = None
        for field in loss_fields:
            # The zone id is usually textual, but it might also be numeric
            dlg.ui.zone_id_attr_name_loss_cbox.addItem(field.name())
            # Accept only numeric fields to contain loss data
            if field.typeName() in NUMERIC_FIELD_TYPES:
                dlg.ui.loss_attrs_multisel.add_unselected_items([field.name()])
            elif field.typeName() in TEXTUAL_FIELD_TYPES:
                default_zone_id_loss = field.name()
            else:
                raise TypeError("Unknown field: type is %d, typeName is %s" % (
                    field.type(), field.typeName()))
        if default_zone_id_loss:
            default_idx = dlg.ui.zone_id_attr_name_loss_cbox.findText(
                default_zone_id_loss)
            if default_idx != -1:  # -1 for not found
                dlg.ui.zone_id_attr_name_loss_cbox.setCurrentIndex(default_idx)
        zonal_dp = self.zonal_layer.dataProvider()
        zonal_fields = list(zonal_dp.fields())
        default_zone_id_zonal = None
        for field in zonal_fields:
            # Although the ID is usually a string, it might possibly be numeric
            dlg.ui.zone_id_attr_name_zone_cbox.addItem(field.name())
            # by default, set the selection to the first textual field
            if field.typeName() in TEXTUAL_FIELD_TYPES:
                default_zone_id_zonal = field.name()
        if default_zone_id_zonal:
            default_idx = dlg.ui.zone_id_attr_name_zone_cbox.findText(
                default_zone_id_zonal)
            if default_idx != -1:  # -1 for not found
                dlg.ui.zone_id_attr_name_zone_cbox.setCurrentIndex(default_idx)
        # if the user presses OK
        if dlg.exec_():
            # retrieve attribute names from selections
            self.loss_attr_names = \
                list(dlg.ui.loss_attrs_multisel.get_selected_items())
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
                msg = ('Transformation %s has been applied to attribute %s of'
                       ' layer %s and the resulting attribute %s has been'
                       ' saved into the same layer.') % (algorithm_name,
                                                         attribute_name,
                                                         layer.name(),
                                                         res_attr_name)
                if invalid_input_values:
                    msg += (' The transformation could not '
                            'be performed for the following '
                            'input values: %s' % invalid_input_values)
                self.iface.messageBar().pushMessage(
                    tr("Info"),
                    tr(msg),
                    level=(QgsMessageBar.INFO if not invalid_input_values
                           else QgsMessageBar.WARNING))
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

    def calculate_stats(self):
        """
        A loss_layer containing loss data points needs to be already loaded,
        and it can be a raster or vector layer.
        Another layer (zonal_layer) needs to be previously loaded as well,
        containing socioeconomic data aggregated by zone.
        This method calls other methods of the class in order to produce,
        for each feature (zone):
        * a "LOSS_PTS" attribute, specifying how many loss points are
          inside the zone
        * for each loss variable:
            * a "SUM" attribute, summing the loss values for all the
            points that are inside the zone
            * a "AVG" attribute, averaging losses for each zone
        """
        # add count, sum and avg fields for aggregating statistics
        # (one new attribute for the count of points, then a sum and an average
        # for all the other loss attributes)
        self.loss_attrs_dict = {}
        count_field = QgsField(
            'LOSS_PTS', QVariant.Int)
        count_field.setTypeName(INT_FIELD_TYPE_NAME)
        count_added = \
            ProcessLayer(self.zonal_layer).add_attributes([count_field])
        # add_attributes returns a dict
        #     proposed_attr_name -> assigned_attr_name
        # so the actual count attribute name is the first value of the dict
        self.loss_attrs_dict['count'] = count_added.values()[0]
        for loss_attr_name in self.loss_attr_names:
            self.loss_attrs_dict[loss_attr_name] = {}
            sum_field = QgsField('SUM_%s' % loss_attr_name, QVariant.Double)
            sum_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            sum_added = \
                ProcessLayer(self.zonal_layer).add_attributes([sum_field])
            # see comment above
            self.loss_attrs_dict[loss_attr_name]['sum'] = sum_added.values()[0]
            avg_field = QgsField('AVG_%s' % loss_attr_name, QVariant.Double)
            avg_field.setTypeName(DOUBLE_FIELD_TYPE_NAME)
            avg_added = \
                ProcessLayer(self.zonal_layer).add_attributes([avg_field])
            # see comment above
            self.loss_attrs_dict[loss_attr_name]['avg'] = avg_added.values()[0]
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
                    self.iface.messageBar().pushMessage(
                        tr("Warning"),
                        tr(err_msg),
                        level=QgsMessageBar.WARNING)
                    self.calculate_vector_stats_using_geometries()
                else:
                    # using SAGA to find out in which zone each point is
                    # (it does not compute any other statistics)
                    # NOTE: The algorithm builds a new loss layer, in which
                    #       each point will have an additional attribute,
                    #       indicating the zone to which the point belongs. Be
                    #       aware that such attribute is not actually the id of
                    #       the zone, but the value of the attribute
                    #       self.zone_id_in_zones_attr_name, which might
                    #       possibly be not unique, causing later the grouping
                    #       of points with the same value, even if
                    #       geographically belonging to different polygons. For
                    #       this reason, the user MUST select carefully the
                    #       attribute in the zonal layer!
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
                        # If the zone id attribute name was already taken in
                        # the loss layer, when SAGA added the new attribute, it
                        # was given a different name by default. We need to get
                        # the new attribute name (as the difference between the
                        # loss_layer and the loss_layer_plus_zones)
                        new_fields = set(
                            field.name() for field in
                            loss_layer_plus_zones.dataProvider().fields())
                        orig_fields = set(
                            field.name() for field in
                            self.loss_layer.dataProvider().fields())
                        zone_field_name = (new_fields - orig_fields).pop()
                        if zone_field_name:
                            self.zone_id_in_losses_attr_name = zone_field_name
                        else:
                            self.zone_id_in_losses_attr_name = \
                                self.zone_id_in_zones_attr_name
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
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)
        # if the user picked an attribute from the loss layer, to be
        # used as zone id, use that; otherwise, use the attribute
        # copied from the zonal layer
        if not self.zone_id_in_losses_attr_name:
            self.zone_id_in_losses_attr_name = self.zone_id_in_zones_attr_name
        with TraceTimeManager(msg, DEBUG):
            zone_stats = {}
            for current_point, point_feat in enumerate(
                    loss_layer.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                zone_id = point_feat[self.zone_id_in_losses_attr_name]
                if zone_id not in zone_stats:
                    zone_stats[zone_id] = {}
                for loss_attr_name in self.loss_attr_names:
                    if loss_attr_name not in zone_stats[zone_id]:
                        zone_stats[zone_id][loss_attr_name] = {
                            'count': 0, 'sum': 0.0}
                    loss_value = point_feat[loss_attr_name]
                    zone_stats[zone_id][loss_attr_name]['count'] += 1
                    zone_stats[zone_id][loss_attr_name]['sum'] \
                        += loss_value
        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        msg = tr(
            "Step 3 of 3: writing point counts, loss sums and averages into "
            "the zonal layer...")
        with TraceTimeManager(msg, DEBUG):
            tot_zones = len(list(self.zonal_layer.getFeatures()))
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            with LayerEditingManager(self.zonal_layer,
                                     msg,
                                     DEBUG):
                count_idx = self.zonal_layer.fieldNameIndex(
                    self.loss_attrs_dict['count'])
                sum_idx = {}
                avg_idx = {}
                for loss_attr_name in self.loss_attr_names:
                    sum_idx[loss_attr_name] = self.zonal_layer.fieldNameIndex(
                        self.loss_attrs_dict[loss_attr_name]['sum'])
                    avg_idx[loss_attr_name] = self.zonal_layer.fieldNameIndex(
                        self.loss_attrs_dict[loss_attr_name]['avg'])
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
                    loss_sum = {}
                    loss_avg = {}
                    for loss_attr_name in self.loss_attr_names:
                        loss_sum[loss_attr_name] = 0.0
                        loss_avg[loss_attr_name] = 0.0
                    # retrieve count and sum from the dictionary, using
                    # the zone id as key to get the values from the
                    # corresponding dict (otherwise, keep zero values)
                    if zone_id in zone_stats:
                        for loss_attr_name in self.loss_attr_names:
                            points_count = \
                                zone_stats[zone_id][loss_attr_name]['count']
                            loss_sum[loss_attr_name] = \
                                zone_stats[zone_id][loss_attr_name]['sum']
                            # division by zero should be impossible, because
                            # we are computing this only for zones containing
                            # at least one point (otherwise we keep all zeros)
                            loss_avg[loss_attr_name] = (
                                loss_sum[loss_attr_name] / points_count)
                            zone_stats[zone_id][loss_attr_name]['avg'] = \
                                loss_avg
                    # without casting to int and to float, it wouldn't work
                    fid = zone_feat.id()
                    self.zonal_layer.changeAttributeValue(
                        fid, count_idx, int(points_count))
                    for loss_attr_name in self.loss_attr_names:
                        self.zonal_layer.changeAttributeValue(
                            fid, sum_idx[loss_attr_name],
                            float(loss_sum[loss_attr_name]))
                        self.zonal_layer.changeAttributeValue(
                            fid, avg_idx[loss_attr_name],
                            float(loss_avg[loss_attr_name]))
        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        self.notify_loss_aggregation_by_zone_complete()

    def notify_loss_aggregation_by_zone_complete(self):
        added_attrs = []
        added_attrs.append(self.loss_attrs_dict['count'])
        for loss_attr_name in self.loss_attr_names:
            added_attrs.extend(self.loss_attrs_dict[loss_attr_name].values())
        msg = "New attributes [%s] have been added to the zonal layer" % (
            ', '.join(added_attrs))
        self.iface.messageBar().pushMessage(
            tr("Info"),
            tr(msg),
            level=QgsMessageBar.INFO,
            duration=8)

    def calculate_vector_stats_using_geometries(self):
        """
        On the hypothesis that we don't know what is the zone in which
        each point was collected (and if we can't use SAGA),
        we use an alternative implementation of what SAGA does, i.e.,
        we add a field to the loss layer, containing the id of the zone
        to which it belongs. In order to achieve that:
        * we create a spatial index of the loss points
        * for each zone (in the layer containing zonally-aggregated SVI
            * we identify points that are inside the zone's bounding box
            * we check if each of these points is actually inside the
              zone's geometry; if it is:
                * copy the zone id into the new field of the loss point
        * then we calculate_vector_stats_aggregating_by_zone_id
        Notes:
        * self.loss_layer contains the not aggregated loss points
        * self.zonal_layer contains the zone geometries
        * self.aggregation_layer is the new layer with losses aggregated by
            zone
        """
        # make a copy of the loss layer and use that from now on
        add_to_registry = True if DEBUG else False
        loss_layer_plus_zones = \
            ProcessLayer(self.loss_layer).duplicate_in_memory(
                add_to_registry=add_to_registry)
        # add to it the new attribute that will contain the zone id
        # and to do that we need to know the type of the zone id field
        zonal_layer_fields = self.zonal_layer.dataProvider().fields()
        zone_id_field_variant = [
            field.type() for field in zonal_layer_fields
            if field.name() == self.zone_id_in_zones_attr_name][0]
        zone_id_field = QgsField(
            self.zone_id_in_zones_attr_name, zone_id_field_variant)
        assigned_attr_names_dict = \
            ProcessLayer(loss_layer_plus_zones).add_attributes(
                [zone_id_field])
        self.zone_id_in_losses_attr_name = assigned_attr_names_dict.values()[0]
        # get the index of the new attribute, to be used to update its values
        zone_id_attr_idx = loss_layer_plus_zones.fieldNameIndex(
            self.zone_id_in_losses_attr_name)
        # to show the overall progress, cycling through points
        tot_points = len(list(loss_layer_plus_zones.getFeatures()))
        msg = tr(
            "Step 2 of 3: creating spatial index for loss points...")
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)

        # create spatial index
        with TraceTimeManager(tr("Creating spatial index for loss points..."),
                              DEBUG):
            spatial_index = QgsSpatialIndex()
            for current_point, loss_feature in enumerate(
                    loss_layer_plus_zones.getFeatures()):
                progress_perc = current_point / float(tot_points) * 100
                progress.setValue(progress_perc)
                spatial_index.insertFeature(loss_feature)

        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        with LayerEditingManager(loss_layer_plus_zones,
                                 tr("Label each point with the zone id"),
                                 DEBUG):
            # to show the overall progress, cycling through zones
            tot_zones = len(list(self.zonal_layer.getFeatures()))
            msg = tr("Step 3 of 3: labeling points by zone id...")
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            for current_zone, zone_feature in enumerate(
                    self.zonal_layer.getFeatures()):
                progress_perc = current_zone / float(tot_zones) * 100
                progress.setValue(progress_perc)
                msg = "{0}% - Zone: {1} on {2}".format(progress_perc,
                                                       zone_feature.id(),
                                                       tot_zones)
                with TraceTimeManager(msg, DEBUG):
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
                            point_feature = loss_layer_plus_zones.getFeatures(
                                request).next()
                            point_geometry = QgsGeometry(
                                point_feature.geometry())
                            # check if the point is actually inside the zone
                            # and it is not only contained by its bounding box
                            if zone_geometry.contains(point_geometry):
                                zone_id = zone_feature[
                                    self.zone_id_in_zones_attr_name]
                                loss_layer_plus_zones.changeAttributeValue(
                                    point_id, zone_id_attr_idx, zone_id)
        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        self.calculate_vector_stats_aggregating_by_zone_id(
            loss_layer_plus_zones)

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

    def purge_zones_without_loss_points(self):
        """
        Delete from the zonal layer the zones that contain no loss points
        """
        pr = self.zonal_layer.dataProvider()
        caps = pr.capabilities()

        tot_zones = len(list(self.zonal_layer.getFeatures()))
        msg = tr("Purging zones containing no loss points...")
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)

        empty_zones_ids = []

        with LayerEditingManager(self.zonal_layer,
                                 msg,
                                 DEBUG):
            for current_zone, zone_feature in enumerate(
                    self.zonal_layer.getFeatures()):
                progress_percent = current_zone / float(tot_zones) * 100
                progress.setValue(progress_percent)
                # save the ids of the zones to purge (which contain no loss
                # points)
                if zone_feature[self.loss_attrs_dict['count']] == 0:
                    empty_zones_ids.append(zone_feature.id())
            if caps & QgsVectorDataProvider.DeleteFeatures:
                pr.deleteFeatures(empty_zones_ids)

        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)

        msg = "Zones containing no loss points were deleted"
        self.iface.messageBar().pushMessage(tr("Warning"),
                                            tr(msg),
                                            level=QgsMessageBar.WARNING)

    def upload(self):
        temp_dir = tempfile.gettempdir()
        file_stem = '%s%sqgis_svir_%s' % (temp_dir, os.path.sep, uuid.uuid4())
        data_file = '%s%s' % (file_stem, '.shp')
        xml_file = file_stem + '.xml'

        project_definition = self.project_definitions[self.current_layer.id()]

        QgsVectorFileWriter.writeAsVectorFormat(
            self.current_layer,
            data_file,
            'utf-8',
            self.current_layer.crs(),
            'ESRI Shapefile')

        file_size_mb = os.path.getsize(data_file)
        file_size_mb += os.path.getsize(file_stem + '.shx')
        file_size_mb += os.path.getsize(file_stem + '.dbf')
        # convert bytes to MB
        file_size_mb = file_size_mb / 1024 / 1024

        dlg = UploadSettingsDialog(file_size_mb, self.iface)
        if dlg.exec_():
            project_definition['title'] = dlg.ui.title_le.text()
            zone_label_field = dlg.ui.zone_label_field_cbx.currentText()
            project_definition['zone_label_field'] = zone_label_field

            license_name = dlg.ui.license_cbx.currentText()
            license_idx = dlg.ui.license_cbx.currentIndex()
            license_url = dlg.ui.license_cbx.itemData(license_idx)
            license_txt = '%s (%s)' % (license_name, license_url)
            project_definition['license'] = license_txt
            project_definition['svir_plugin_version'] = SVIR_PLUGIN_VERSION
            if DEBUG:
                print 'xml_file:', xml_file
            write_iso_metadata_file(xml_file,
                                    project_definition)
            metadata_dialog = UploadMetadataDialog(
                self.iface, file_stem, project_definition)
            if metadata_dialog.exec_():
                QDesktopServices.openUrl(QUrl(metadata_dialog.layer_url))
        else:
            print "metadata_dialog cancelled"
