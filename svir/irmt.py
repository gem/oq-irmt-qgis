# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2017 by GEM Foundation
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

import qgis  # NOQA: it loads the environment

import os.path
import tempfile
import uuid
import fileinput
import re
import processing

from copy import deepcopy
from math import floor, ceil
from qgis.core import (
                       QgsVectorLayer,
                       QgsMapLayer,
                       QgsGraduatedSymbolRenderer,
                       QgsSymbol, QgsGradientColorRamp,
                       QgsRuleBasedRenderer,
                       QgsFillSymbol,
                       QgsProject,
                       QgsExpression,
                       Qgis,
                       QgsApplication,
                       QgsWkbTypes,
                       )

from qgis.PyQt.QtCore import (
                              QSettings,
                              QTranslator,
                              QCoreApplication,
                              qVersion,
                              QUrl,
                              Qt,
                              QUrlQuery,
                              )
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QApplication, QMenu
from qgis.PyQt.QtGui import QIcon, QDesktopServices

from svir.dialogs.viewer_dock import ViewerDock
from svir.utilities.import_sv_data import get_loggedin_downloader
from svir.dialogs.download_layer_dialog import DownloadLayerDialog
from svir.dialogs.projects_manager_dialog import ProjectsManagerDialog
from svir.dialogs.select_sv_variables_dialog import SelectSvVariablesDialog
from svir.dialogs.settings_dialog import SettingsDialog
from svir.dialogs.transformation_dialog import TransformationDialog
from svir.dialogs.upload_settings_dialog import UploadSettingsDialog
from svir.dialogs.weight_data_dialog import WeightDataDialog
from svir.dialogs.recovery_modeling_dialog import RecoveryModelingDialog
from svir.dialogs.recovery_settings_dialog import RecoverySettingsDialog
from svir.dialogs.ipt_dialog import IptDialog
from svir.dialogs.taxtweb_dialog import TaxtwebDialog
from svir.dialogs.taxonomy_dialog import TaxonomyDialog
from svir.dialogs.drive_oq_engine_server_dialog import (
    DriveOqEngineServerDialog)

from svir.thread_worker.abstract_worker import start_worker
from svir.thread_worker.download_platform_data_worker import (
    DownloadPlatformDataWorker)
from svir.calculations.calculate_utils import calculate_composite_variable
from svir.calculations.process_layer import ProcessLayer
from svir.utilities.utils import (tr,
                                  WaitCursorManager,
                                  assign_default_weights,
                                  clear_progress_message_bar,
                                  SvNetworkError,
                                  count_heading_commented_lines,
                                  replace_fields,
                                  toggle_select_features_widget,
                                  read_layer_suppl_info_from_qgs,
                                  write_layer_suppl_info_to_qgs,
                                  log_msg,
                                  save_layer_as_shapefile,
                                  get_style,
                                  get_checksum,
                                  warn_scipy_missing,
                                  )
from svir.utilities.shared import (DEBUG,
                                   PROJECT_TEMPLATE,
                                   THEME_TEMPLATE,
                                   INDICATOR_TEMPLATE,
                                   OPERATORS_DICT)
from svir.ui.tool_button_with_help_link import QToolButtonWithHelpLink

# DO NOT REMOVE THIS
# noinspection PyUnresolvedReferences
import svir.resources_rc  # pylint: disable=unused-import  # NOQA

from svir import IS_SCIPY_INSTALLED


class Irmt(object):
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n',
                                   'irmt_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # our own toolbar
        self.toolbar = None

        # our own menu
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setTitle("OpenQuake IRMT")

        # keep a list of the menu items, in order to easily unload them later
        self.registered_actions = dict()

        # avoid dialog to be deleted right after showing it
        self.drive_oq_engine_server_dlg = None
        self.ipt_dlg = None
        self.taxtweb_dlg = None
        self.taxonomy_dlg = None

        # keep track of the supplemental information for each layer
        # layer_id -> {}
        # where each dict contains 'platform_layer_id',
        # 'selected_project_definition_idx', 'project_definitions'
        self.supplemental_information = {}

        self.iface.currentLayerChanged.connect(self.current_layer_changed)
        self.iface.newProjectCreated.connect(self.current_layer_changed)
        self.iface.projectRead.connect(self.current_layer_changed)
        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().layersRemoved.connect(
            self.layers_removed)

        # get or create directory to store input files for the OQ-Engine
        self.ipt_dir = self.get_ipt_dir()

    def initGui(self):
        # create our own toolbar
        self.toolbar = self.iface.addToolBar('OpenQuake IRMT')
        self.toolbar.setObjectName('IRMTToolBar')

        menu_bar = self.iface.mainWindow().menuBar()
        get_menu = self.get_menu(menu_bar, 'OpenQuake IRMT')

        if get_menu is not None:
            self.menu = get_menu

        self.menu_action = menu_bar.insertMenu(
            self.iface.firstRightStandardMenu().menuAction(), self.menu)

        # Action to activate the modal dialog to import socioeconomic
        # data from the platform
        self.add_menu_item("import_sv_variables",
                           ":/plugins/irmt/load.svg",
                           u"&Load socioeconomic indicators"
                           " from the OpenQuake Platform",
                           self.import_sv_variables,
                           enable=True,
                           add_to_layer_actions=False,
                           submenu='OQ Platform')
        # Action to activate the modal dialog to import socioeconomic
        # data from the platform
        self.add_menu_item("import_layer",
                           ":/plugins/irmt/load_layer.svg",
                           u"&Import project from the OpenQuake Platform",
                           self.download_layer,
                           enable=True,
                           add_to_layer_actions=False,
                           submenu='OQ Platform')
        # Action to upload
        self.add_menu_item("upload",
                           ":/plugins/irmt/upload.svg",
                           u"&Upload project to the OpenQuake Platform",
                           self.upload,
                           enable=self.experimental_enabled(),
                           add_to_layer_actions=True,
                           submenu='OQ Platform')
        # # Action to drive ipt
        # self.add_menu_item("ipt",
        #                    ":/plugins/irmt/ipt.svg",
        #                    u"OpenQuake Input Preparation Toolkit",
        #                    self.ipt,
        #                    enable=self.experimental_enabled(),
        #                    submenu='OQ Engine',
        #                    add_to_toolbar=True)
        # # Action to drive taxtweb
        # self.add_menu_item("taxtweb",
        #                    ":/plugins/irmt/taxtweb.svg",
        #                    u"OpenQuake TaxtWEB",
        #                    self.taxtweb,
        #                    enable=self.experimental_enabled(),
        #                    submenu='OQ Engine',
        #                    add_to_toolbar=True)
        # Action to drive the oq-engine server
        self.add_menu_item("drive_engine_server",
                           ":/plugins/irmt/drive_oqengine.svg",
                           u"Drive the OpenQuake Engine",
                           self.on_drive_oq_engine_server_btn_clicked,
                           enable=True,
                           submenu='OQ Engine',
                           add_to_toolbar=True)
        # Action to manage the projects
        self.add_menu_item("project_definitions_manager",
                           ":/plugins/irmt/copy.svg",
                           u"&Manage project definitions",
                           self.project_definitions_manager,
                           enable=False,
                           add_to_layer_actions=True,
                           submenu='Integrated risk')
        # Action to activate the modal dialog to choose weighting of the
        # data from the platform
        self.add_menu_item("weight_data",
                           ":/plugins/irmt/weights.svg",
                           u"&Weight data and calculate indices",
                           self.weight_data,
                           enable=False,
                           add_to_layer_actions=True,
                           add_to_toolbar=True,
                           submenu='Integrated risk')

        # Action to run the recovery analysis
        self.add_menu_item("recovery_modeling",
                           ":/plugins/irmt/recovery.svg",
                           u"Run recovery modeling",
                           self.recovery_modeling,
                           enable=self.experimental_enabled(),
                           submenu='Recovery modeling')
        # Action to set the recovery modeling parameters
        self.add_menu_item("recovery_settings",
                           ":/plugins/irmt/recovery_settings.svg",
                           u"Recovery modeling settings",
                           self.recovery_settings,
                           enable=self.experimental_enabled(),
                           submenu='Recovery modeling')

        # Action to activate the modal dialog to select a layer and one of
        # its attributes, in order to transform that attribute
        self.add_menu_item("transform_attributes",
                           ":/plugins/irmt/transform.svg",
                           u"&Transform attributes",
                           self.transform_attributes,
                           enable=False,
                           add_to_toolbar=True,
                           add_to_layer_actions=True,
                           submenu='Utilities')
        # Action to open the Processing algorithm
        # "Join attributes by location (summary)"
        self.add_menu_item("aggregate",
                           ":/plugins/irmt/aggregate.svg",
                           u"&Aggregate points by zone",
                           self.aggregate,
                           enable=True,
                           add_to_toolbar=False,
                           add_to_layer_actions=False,
                           submenu='Utilities')

        self.menu.addSeparator()

        # Action to activate the modal dialog to set up show_settings for the
        # connection with the platform
        self.add_menu_item("show_settings",
                           ":/plugins/irmt/settings.svg",
                           u"&OpenQuake IRMT settings",
                           self.show_settings,
                           enable=True,
                           add_to_toolbar=True)

        self._create_viewer_dock()

        # Action to open the plugin's manual
        self.add_menu_item("help",
                           ":/plugins/irmt/manual.svg",
                           u"OpenQuake IRMT &manual",
                           self.show_manual,
                           enable=True,
                           add_to_toolbar=True)

        self.update_actions_status()

    @staticmethod
    def get_menu(parent, title):
        actions = parent.actions()
        # check if the given menu already exists
        for action in actions:
            if action.text() == title:
                return action.menu()
        return None

    def experimental_enabled(self):
        experimental_enabled = QSettings().value(
            '/irmt/experimental_enabled', False, type=bool)
        return experimental_enabled

    def recovery_modeling(self):
        if IS_SCIPY_INSTALLED:
            dlg = RecoveryModelingDialog(self.iface)
            dlg.exec_()
        else:
            warn_scipy_missing(self.iface.messageBar())

    def recovery_settings(self):
        dlg = RecoverySettingsDialog(self.iface)
        dlg.exec_()

    def aggregate(self):
        processing.Processing.initialize()
        alg_id = 'qgis:joinbylocationsummary'
        alg = QgsApplication.processingRegistry().algorithmById(alg_id)
        # make sure to use the actual lists of predicates and summaries as
        # defined in the algorithm when it is instantiated
        predicate_keys = [predicate[0] for predicate in alg.predicates]
        PREDICATES = dict(zip(predicate_keys, range(len(predicate_keys))))
        default_predicates = ['intersects']
        summary_keys = [statistic[0] for statistic in alg.statistics]
        SUMMARIES = dict(zip(summary_keys, range(len(summary_keys))))
        default_summaries = ['sum', 'mean']
        zonal_layer = None
        points_layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                zonal_layer = layer
                continue
            elif layer.geometryType() == QgsWkbTypes.PointGeometry:
                points_layer = layer
                continue
        initial_params = {
            'INPUT': zonal_layer,
            'JOIN': points_layer,
            'PREDICATE': [PREDICATES[predicate]
                          for predicate in default_predicates],
            'SUMMARIES': [SUMMARIES[summary]
                          for summary in default_summaries],
            }
        processing.execAlgorithmDialog(alg_id, initial_params)

    def ipt(self):
        if self.ipt_dlg is None:
            # we need self because ipt must be able to drive the oq-engine
            self.ipt_dlg = IptDialog(self.ipt_dir, self)
        self.ipt_dlg.show()
        self.ipt_dlg.raise_()

    def taxtweb(self):
        if self.taxtweb_dlg is None:
            self.instantiate_taxonomy_dlg()
            self.taxtweb_dlg = TaxtwebDialog(self.taxonomy_dlg)
        self.taxtweb_dlg.show()
        self.taxtweb_dlg.raise_()

    def instantiate_taxonomy_dlg(self):
        if self.taxonomy_dlg is None:
            self.taxonomy_dlg = TaxonomyDialog()

    def taxonomy(self):
        self.instantiate_taxonomy_dlg()
        self.taxonomy_dlg.show()
        self.taxonomy_dlg.raise_()

    def on_drive_oq_engine_server_btn_clicked(self):
        # we can't call drive_oq_engine_server directly, otherwise the signal
        # triggered by the button would set show=False (it silently passes an
        # additional parameter)
        self.drive_oq_engine_server(show=True)

    def drive_oq_engine_server(self, show=True):
        if self.drive_oq_engine_server_dlg is None:
            self.drive_oq_engine_server_dlg = DriveOqEngineServerDialog(
                self.iface, self.viewer_dock)
        else:
            self.drive_oq_engine_server_dlg.attempt_login()
        if show:
            self.drive_oq_engine_server_dlg.show()
            self.drive_oq_engine_server_dlg.raise_()
        if self.drive_oq_engine_server_dlg.is_logged_in:
            self.drive_oq_engine_server_dlg.start_polling()
        else:
            self.drive_oq_engine_server_dlg.reject()
            self.drive_oq_engine_server_dlg = None

    def on_same_fs(self, checksum_file_path, local_checksum):
        # initialize drive_oq_engine_server_dlg dialog without displaying it
        self.drive_oq_engine_server(show=False)
        return self.drive_oq_engine_server_dlg.on_same_fs(
            checksum_file_path, local_checksum)

    def reset_drive_oq_engine_server_dlg(self):
        if self.drive_oq_engine_server_dlg is not None:
            was_dlg_visible = self.drive_oq_engine_server_dlg.isVisible()
            self.drive_oq_engine_server_dlg.reject()
            self.drive_oq_engine_server_dlg = DriveOqEngineServerDialog(
                self.iface, self.viewer_dock)
            if was_dlg_visible:
                self.drive_oq_engine_server_dlg.show()

    def show_manual(self):
        base_url = os.path.abspath(os.path.join(
            __file__, os.pardir, 'help', 'build', 'html', 'index.html'))
        if not os.path.exists(base_url):
            msg = 'Help file not found: %s' % base_url
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
        url = QUrl.fromLocalFile(base_url)
        QDesktopServices.openUrl(url)

    def layers_added(self):
        self.update_actions_status()

    def layers_removed(self, layer_ids):
        for layer_id in layer_ids:
            self.clear_layer_suppl_info(layer_id)
        self.update_actions_status()

    def clear_layer_suppl_info(self, layer_id):
        self.supplemental_information.pop(layer_id, None)
        QgsProject.instance().removeEntry('irmt', layer_id)

    def current_layer_changed(self, layer=None):
        self.update_actions_status()
        output_type = ''
        if layer:
            output_type = layer.customProperty('output_type') or ''
        self.viewer_dock.change_output_type(output_type)
        self.viewer_dock.layer_changed()

    def add_menu_item(self,
                      action_name,
                      icon_path,
                      label,
                      corresponding_method,
                      enable=False,
                      add_to_layer_actions=False,
                      layers_type=QgsMapLayer.VectorLayer,
                      set_checkable=False,
                      set_checked=False,
                      submenu=None,
                      add_to_toolbar=False,
                      ):
        """
        Add an item to the OpenQuake IRMT menu and a corresponding toolbar icon

        :param icon_path: path of the icon associated to the action
        :param label: name of the action, visible to the user
        :param corresponding_method: method called when the action is triggered
        """
        if action_name in self.registered_actions:
            raise NameError("Action %s already registered" % action_name)
        action = QAction(QIcon(icon_path), label, self.iface.mainWindow())
        action.setEnabled(enable)
        action.setCheckable(set_checkable)
        action.setChecked(set_checked)
        action.triggered.connect(corresponding_method)

        self.registered_actions[action_name] = action

        if add_to_layer_actions:
            self.iface.addCustomActionForLayerType(
                action,
                u"OpenQuake IRMT",
                layers_type,
                True)

        if submenu is None:
            menu = self.menu
        else:
            get_menu = self.get_menu(self.menu, submenu)
            if get_menu is not None:
                menu = get_menu
            else:
                menu = self.menu.addMenu(submenu)

        if add_to_toolbar:
            help_url = 'http://docs.openquake.org/oq-irmt-qgis/'
            # NOTE: the "what's this" functionality has been removed from QGIS
            #       so the help_url will never be used. Anyway, buttons defined
            #       this way keep working to run the corresponding actions.
            button = QToolButtonWithHelpLink(action, help_url)
            self.toolbar.addWidget(button)

        menu.addAction(action)

        return action

    def update_actions_status(self):
        """
        Enable plugin's actions depending on the current status of the workflow
        """
        reg = QgsProject.instance()
        layer_count = len(list(reg.mapLayers()))
        # Enable/disable "transform" action
        self.registered_actions["transform_attributes"].setDisabled(
            layer_count == 0)

        if DEBUG:
            log_msg('Selected: %s' % self.iface.activeLayer())
        try:
            # Activate actions which require a vector layer to be selected
            if self.iface.activeLayer().type() != QgsMapLayer.VectorLayer:
                raise AttributeError
            self.supplemental_information[self.iface.activeLayer().id()]
            self.registered_actions[
                "project_definitions_manager"].setEnabled(True)
            self.registered_actions["weight_data"].setEnabled(True)
            self.registered_actions["transform_attributes"].setEnabled(True)
            read_layer_suppl_info_from_qgs(
                self.iface.activeLayer().id(), self.supplemental_information)
            self.registered_actions["upload"].setEnabled(
                self.experimental_enabled())
        except KeyError:
            # self.supplemental_information[self.iface.activeLayer().id()]
            # is not defined
            self.registered_actions["upload"].setEnabled(False)
            self.registered_actions[
                "project_definitions_manager"].setEnabled(True)
            self.registered_actions["weight_data"].setEnabled(True)
        except AttributeError:
            # self.iface.activeLayer().id() does not exist
            # or self.iface.activeLayer() is not vector
            self.registered_actions["transform_attributes"].setEnabled(False)
            self.registered_actions["weight_data"].setEnabled(False)
            self.registered_actions["upload"].setEnabled(False)
            self.registered_actions[
                "project_definitions_manager"].setEnabled(False)

    def unload(self):
        """
        Remove all plugin's actions and corresponding buttons and connects
        """
        # Remove the plugin menu items and toolbar icons
        for action_name in self.registered_actions:
            action = self.registered_actions[action_name]
            # Remove the actions in the layer legend
            self.iface.removeCustomActionForLayerType(action)
            self.iface.removeToolBarIcon(action)
        clear_progress_message_bar(self.iface.messageBar())

        self.menu.clear()
        self.iface.mainWindow().menuBar().removeAction(self.menu_action)

        # remove the dock
        self.viewer_dock.remove_connects()
        self.viewer_dock.deleteLater()

        # remove connects
        self.iface.currentLayerChanged.disconnect(self.current_layer_changed)
        self.iface.newProjectCreated.disconnect(self.current_layer_changed)
        self.iface.projectRead.disconnect(self.current_layer_changed)
        QgsProject.instance().layersAdded.disconnect(
            self.layers_added)
        QgsProject.instance().layersRemoved.disconnect(
            self.layers_removed)

    def import_sv_variables(self):
        """
        Open a modal dialog to select socioeconomic variables to
        download from the openquake platform
        """
        # login to platform, to be able to retrieve sv indices
        sv_downloader = get_loggedin_downloader(self.iface.messageBar())
        if sv_downloader is None:
            self.show_settings()
            return
        try:
            dlg = SelectSvVariablesDialog(sv_downloader)
            if dlg.exec_():
                dest_filename, _ = QFileDialog.getSaveFileName(
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
                # load_geometries = dlg.load_geometries_chk.isChecked()
                load_geometries = True
                msg = ("Loading socioeconomic data from the OpenQuake "
                       "Platform...")
                # Retrieve the indices selected by the user
                indices_list = []
                iso_codes_list = []
                project_definition = deepcopy(PROJECT_TEMPLATE)
                svi_themes = project_definition[
                    'children'][1]['children']
                known_themes = []
                with WaitCursorManager(msg, self.iface.messageBar()):
                    while dlg.indicator_multiselect.selected_widget.count(
                            ) > 0:
                        item = \
                            dlg.indicator_multiselect.selected_widget.takeItem(
                                0)
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
                    while dlg.country_multiselect.selected_widget.count() > 0:
                        item = \
                            dlg.country_multiselect.selected_widget.takeItem(0)
                        # get the iso from something like:
                        # country_name (iso_code)
                        iso_code = item.text().split('(')[1].split(')')[0]
                        iso_codes_list.append(iso_code)

                    # create string for DB query
                    indices_string = ",".join(indices_list)
                    iso_codes_string = ",".join(iso_codes_list)

                    assign_default_weights(svi_themes)

                    worker = DownloadPlatformDataWorker(
                        sv_downloader,
                        indices_string,
                        load_geometries,
                        iso_codes_string)
                    worker.successfully_finished.connect(
                        lambda result: self._data_download_successful(
                            result,
                            load_geometries,
                            dest_filename,
                            project_definition,
                            dlg.indicators_info_dict))
                    start_worker(worker, self.iface.messageBar(),
                                 'Downloading data from platform')
        except SvNetworkError as e:
            log_msg('An error occurred. See the traceback for details.',
                    level='C', message_bar=self.iface.messageBar(),
                    exception=e)

    def _data_download_successful(
            self, result, load_geometries, dest_filename, project_definition,
            indicators_info_dict):
        """
        Called once the DonloadPlatformDataWorker has successfully downloaded
        socioeconomic data as a csv file.

        :param result: a tuple (fname, msg) where fname is the name of the csv
            file exported by the OQ-Platform and msg is the message
            returned
        :param load_geometries: if True, also geometries were downloaded
        :type load_geometries: bool
        :param dest_filename: name of the file that will store the vector layer
            containing the downloaded data
        :param project_definition: the project definition that was
            automatically built based on the DB structure
        :param indicators_info_dict:
            dict ind_code -> dict with additional info about it
        """
        fname, msg = result
        display_msg = tr("Socioeconomic data loaded in a new layer")
        log_msg(display_msg, level='S', message_bar=self.iface.messageBar())
        # don't remove the file, otherwise there will be concurrency
        # problems

        # fix an issue of QGIS 10, that is unable to read
        # multipolygons if they contain spaces between two polygons.
        # We remove those spaces from the csv file before importing it.
        # TODO: Remove this as soon as QGIS solves that issue
        for line in fileinput.input(fname, inplace=True):
            line = re.sub('\)\),\s\(\(', ')),((', line.rstrip())
            line = re.sub('\),\s\(', '),(', line.rstrip())
            # thanks to inplace=True, 'print line' writes the line into the
            # input file, overwriting the original line
            print(line)

        # count top lines in the csv starting with '#'
        lines_to_skip_count = count_heading_commented_lines(fname)

        url = QUrl.fromLocalFile(fname)
        url_query = QUrlQuery()
        url_query.addQueryItem('delimiter', ',')
        url_query.addQueryItem('skipLines', str(lines_to_skip_count))
        url_query.addQueryItem('trimFields', 'yes')
        if load_geometries:
            url_query.addQueryItem('crs', 'epsg:4326')
            url_query.addQueryItem('wktField', 'geometry')
        url.setQuery(url_query)
        layer_uri = url.toString()
        # create vector layer from the csv file exported by the
        # platform (it is still not editable!)
        vlayer_csv = QgsVectorLayer(layer_uri,
                                    'socioeconomic_data_export',
                                    'delimitedtext')
        if not load_geometries:
            if vlayer_csv.isValid():
                QgsProject.instance().addMapLayer(vlayer_csv)
            else:
                raise RuntimeError('Layer invalid')
            layer = vlayer_csv
        else:
            writer_error, error_msg = save_layer_as_shapefile(
                vlayer_csv, dest_filename)
            if writer_error:
                raise RuntimeError(
                    'Could not save shapefile. %s: %s' % (writer_error,
                                                          error_msg))
            layer = QgsVectorLayer(
                dest_filename, 'Socioeconomic data', 'ogr')
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                raise RuntimeError('Layer invalid')
        self.iface.setActiveLayer(layer)
        suppl_info = {
            'selected_project_definition_idx': 0,
            'project_definitions': [project_definition]}
        write_layer_suppl_info_to_qgs(layer.id(), suppl_info)
        self.update_actions_status()

        # assign ind_name as alias for each ind_code
        for field_idx, field in enumerate(layer.fields()):
            if field.name() in indicators_info_dict:
                layer.setFieldAlias(
                    field_idx, indicators_info_dict[field.name()]['name'])
            elif field.name() == 'ISO':
                layer.setFieldAlias(
                    field_idx, 'Country ISO code')
            elif field.name() == 'COUNTRY_NA':
                layer.setFieldAlias(
                    field_idx, 'Country name')

    def download_layer(self):
        """
        Open dialog to select one of the integrated risk projects available on
        the OQ-Platform and download it as a qgis project
        """
        sv_downloader = get_loggedin_downloader(self.iface.messageBar())
        if sv_downloader is None:
            self.show_settings()
            return

        dlg = DownloadLayerDialog(self.iface, sv_downloader)
        if dlg.exec_():
            read_layer_suppl_info_from_qgs(
                dlg.downloaded_layer_id, self.supplemental_information)
            suppl_info = self.supplemental_information[dlg.downloaded_layer_id]
            # in case of multiple project definitions, let the user select one
            if len(suppl_info['project_definitions']) > 1:
                self.project_definitions_manager()
            self.update_actions_status()

    @staticmethod
    def _add_new_theme(svi_themes,
                       known_themes,
                       indicator_theme,
                       indicator_name,
                       indicator_field):
        """add a new theme to the project_definition"""

        theme = deepcopy(THEME_TEMPLATE)
        theme['name'] = indicator_theme
        if theme['name'] not in known_themes:
            known_themes.append(theme['name'])
            svi_themes.append(theme)
        theme_position = known_themes.index(theme['name'])
        level = float('4.%d' % theme_position)
        # add a new indicator to a theme
        new_indicator = deepcopy(INDICATOR_TEMPLATE)
        new_indicator['name'] = indicator_name
        new_indicator['field'] = indicator_field
        new_indicator['level'] = level
        svi_themes[theme_position]['children'].append(new_indicator)

    def project_definitions_manager(self):
        """
        Open a dialog to manage one or multiple project definitions for the
        selected layer.
        """
        read_layer_suppl_info_from_qgs(
            self.iface.activeLayer().id(), self.supplemental_information)
        select_proj_def_dlg = ProjectsManagerDialog(self.iface)
        if select_proj_def_dlg.exec_():
            selected_project_definition = select_proj_def_dlg.selected_proj_def
            added_attrs_ids, discarded_feats, project_definition = \
                self._recalculate_indexes(selected_project_definition)
            self.notify_added_attrs_and_discarded_feats(added_attrs_ids,
                                                        discarded_feats)
            select_proj_def_dlg.suppl_info['project_definitions'][
                select_proj_def_dlg.suppl_info[
                    'selected_project_definition_idx']] = project_definition
            write_layer_suppl_info_to_qgs(
                self.iface.activeLayer().id(), select_proj_def_dlg.suppl_info)
            self.redraw_ir_layer(project_definition)

    def notify_added_attrs_and_discarded_feats(self,
                                               added_attrs_ids,
                                               discarded_feats):
        """
        Notify through the message bar that new attributes have been added
        to the layer and specify if missing or invalid values were found.
        """
        if added_attrs_ids:
            all_field_names = [
                field.name() for field in self.iface.activeLayer().fields()]
            added_attrs_names = [all_field_names[attr_id]
                                 for attr_id in added_attrs_ids]
            msg = ('New attributes have been added to the layer: %s'
                   % ', '.join(added_attrs_names))
            log_msg(msg, level='S', message_bar=self.iface.messageBar())
        if discarded_feats:
            discarded_feats_ids_missing = [
                feat.feature_id for feat in discarded_feats
                if feat.reason == 'Missing value']
            if discarded_feats_ids_missing:
                widget = toggle_select_features_widget(
                    tr('Warning'),
                    tr('Missing values were found in some features while '
                       'calculating composite variables'),
                    tr('Select features with incomplete data'),
                    self.iface.activeLayer(),
                    discarded_feats_ids_missing,
                    self.iface.activeLayer().selectedFeatureIds())
                self.iface.messageBar().pushWidget(widget, Qgis.Warning)
            discarded_feats_ids_invalid = [
                feat.feature_id for feat in discarded_feats
                if feat.reason == 'Invalid value']
            if discarded_feats_ids_invalid:
                widget = toggle_select_features_widget(
                    tr('Warning'),
                    tr('Invalid values were found in some features while '
                       'calculating composite variables using the chosen '
                       'operators (e.g. the geometric mean fails when '
                       'attempting to perform the root of a '
                       'negative value)'),
                    tr('Select features with invalid data'),
                    self.iface.activeLayer(),
                    discarded_feats_ids_invalid,
                    self.iface.activeLayer().selectedFeatureIds())
                self.iface.messageBar().pushWidget(widget, Qgis.Warning)

    def weight_data(self):
        """
        Open a modal dialog to select weights in a d3.js visualization and to
        run integrated risk calculations.
        """
        active_layer_id = self.iface.activeLayer().id()
        # get the project definition to work with, or create a default one
        read_layer_suppl_info_from_qgs(
            active_layer_id, self.supplemental_information)
        try:
            suppl_info = self.supplemental_information[active_layer_id]
            orig_project_definition = suppl_info['project_definitions'][
                suppl_info['selected_project_definition_idx']]
        except KeyError:
            orig_project_definition = deepcopy(PROJECT_TEMPLATE)
            suppl_info = {'selected_project_definition_idx': 0,
                          'project_definitions': [orig_project_definition]
                          }
            write_layer_suppl_info_to_qgs(active_layer_id, suppl_info)
        edited_project_definition = deepcopy(orig_project_definition)

        # Save the style so the following styling can be undone
        fd, sld_file_name = tempfile.mkstemp(suffix=".sld")
        os.close(fd)
        (resp_text, sld_was_saved) = \
            self.iface.activeLayer().saveSldStyle(sld_file_name)
        if sld_was_saved:
            if DEBUG:
                log_msg('original sld saved in %s' % sld_file_name)
        else:
            err_msg = 'Unable to save the sld: %s' % resp_text
            log_msg(err_msg, level='C', message_bar=self.iface.messageBar())

        dlg = WeightDataDialog(self.iface, edited_project_definition)
        dlg.show()
        self.redraw_ir_layer(edited_project_definition)

        dlg.json_cleaned.connect(lambda data: self._weights_changed(data, dlg))
        if dlg.exec_():
            # If the user just opens the dialog and presses OK, it probably
            # means they want to just run the index calculation, so we
            # recalculate the indexes. In case they have already made any
            # change and consequent calculations, we don't need to redo the
            # same calculation after OK is pressed.
            if not dlg.any_changes_made:
                (added_attrs_ids,
                 discarded_feats,
                 edited_project_definition) = self._recalculate_indexes(
                    dlg.project_definition)
                dlg.added_attrs_ids.update(added_attrs_ids)
                dlg.discarded_feats = discarded_feats
            # But if changes were made to the tree while the on-the-fly
            # calculation was disabled, then we need to recalculate indices
            # using the modified project definition
            elif dlg.modified_project_definition:
                (added_attrs_ids,
                 discarded_feats,
                 edited_project_definition) = self._recalculate_indexes(
                    dlg.modified_project_definition)
                dlg.added_attrs_ids.update(added_attrs_ids)
                dlg.discarded_feats = discarded_feats
            else:
                edited_project_definition = deepcopy(dlg.project_definition)
            self.notify_added_attrs_and_discarded_feats(
                dlg.added_attrs_ids, dlg.discarded_feats)
            self.update_actions_status()
        else:  # 'cancel' was pressed or the dialog was closed
            if sld_was_saved:  # was able to save the original style
                self.iface.activeLayer().loadSldStyle(sld_file_name)
            # if any of the indices were saved before starting to edit the
            # tree, the corresponding fields might have been modified.
            # Therefore we recalculate the indices using the old project
            # definition
            if dlg.any_changes_made:
                edited_project_definition = deepcopy(orig_project_definition)
                iri_node = edited_project_definition
                ri_node = edited_project_definition['children'][0]
                svi_node = edited_project_definition['children'][1]
                if ('field' in iri_node
                        or 'field' in ri_node or 'field' in svi_node):
                    added_attrs_ids, _, edited_project_definition = \
                        self._recalculate_indexes(iri_node)
                    dlg.added_attrs_ids.update(added_attrs_ids)
                # delete attributes added while the dialog was open
                ProcessLayer(self.iface.activeLayer()).delete_attributes(
                    dlg.added_attrs_ids)
        dlg.json_cleaned.disconnect()
        # store the correct project definitions
        selected_idx = suppl_info['selected_project_definition_idx']
        suppl_info['project_definitions'][selected_idx] = deepcopy(
            edited_project_definition)
        write_layer_suppl_info_to_qgs(active_layer_id, suppl_info)
        self.redraw_ir_layer(edited_project_definition)

    def _weights_changed(self, data, dlg):
        added_attrs_ids, discarded_feats, project_definition = \
            self._recalculate_indexes(data)
        dlg.added_attrs_ids.update(added_attrs_ids)
        dlg.discarded_feats = discarded_feats
        dlg.update_project_definition(project_definition)
        self.redraw_ir_layer(project_definition)

    def _recalculate_indexes(self, data):
        project_definition = deepcopy(data)

        if self.is_iri_computable(project_definition):
            iri_node = deepcopy(project_definition)
            msg = 'Calculating %s' % iri_node['name']
            with WaitCursorManager(msg, self.iface.messageBar()):
                (added_attrs_ids, discarded_feats,
                 iri_node, was_iri_computed) = calculate_composite_variable(
                    self.iface, self.iface.activeLayer(), iri_node)
            project_definition = deepcopy(iri_node)
            return added_attrs_ids, discarded_feats, project_definition

        svi_added_attrs_ids = set()
        svi_discarded_feats = set()
        ri_added_attrs_ids = set()
        ri_discarded_feats = set()

        was_svi_computed = False
        if self.is_svi_computable(project_definition):
            svi_node = deepcopy(project_definition['children'][1])
            msg = 'Calculating %s' % svi_node['name']
            with WaitCursorManager(msg, self.iface.messageBar()):
                (svi_added_attrs_ids, svi_discarded_feats,
                 svi_node, was_svi_computed) = calculate_composite_variable(
                    self.iface, self.iface.activeLayer(), svi_node)
            project_definition['children'][1] = deepcopy(svi_node)

        was_ri_computed = False
        if self.is_ri_computable(project_definition):
            ri_node = deepcopy(project_definition['children'][0])
            msg = 'Calculating %s' % ri_node['name']
            with WaitCursorManager(msg, self.iface.messageBar()):
                (ri_added_attrs_ids, ri_discarded_feats,
                 ri_node, was_ri_computed) = calculate_composite_variable(
                    self.iface, self.iface.activeLayer(), ri_node)
            project_definition['children'][0] = deepcopy(ri_node)

        if not was_svi_computed and not was_ri_computed:
            return set(), set(), data
        added_attrs_ids = set()
        discarded_feats = set()
        if svi_added_attrs_ids:
            added_attrs_ids.update(svi_added_attrs_ids)
        if svi_discarded_feats:
            discarded_feats.update(svi_discarded_feats)
        if ri_added_attrs_ids:
            added_attrs_ids.update(ri_added_attrs_ids)
        if ri_discarded_feats:
            discarded_feats.update(ri_discarded_feats)
        return added_attrs_ids, discarded_feats, project_definition

    def is_svi_computable(self, proj_def):
        """
        Check if is it possible to compute the social vulnerability index,
        depending on the current project definition structure.
        """
        try:
            svi_node = proj_def['children'][1]
        except KeyError:
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

    def is_svi_renderable(self, proj_def):
        """
        Check if is it possible to render the social vulnerability index,
        depending on the current project definition structure.
        """
        if not self.is_svi_computable(proj_def):
            return False
        # check that that the svi_node has a corresponding field
        try:
            svi_node = proj_def['children'][1]
        except KeyError:
            return False
        if 'field' not in svi_node:
            return False
        return True

    def is_ri_computable(self, proj_def):
        """
        Check if is it possible to compute the risk index,
        depending on the current project definition structure.
        """
        try:
            ri_node = proj_def['children'][0]
        except KeyError:
            return False
        # check that there is at least one risk indicator
        if 'children' not in ri_node:
            return False
        if len(ri_node['children']) == 0:
            return False
        return True

    def is_ri_renderable(self, proj_def):
        """
        Check if is it possible to render the risk index,
        depending on the current project definition structure.
        """
        if not self.is_ri_computable(proj_def):
            return False
        try:
            ri_node = proj_def['children'][0]
        except KeyError:
            return False
        # check that that the ri_node has a corresponding field
        if 'field' not in ri_node:
            return False
        return True

    def is_iri_computable(self, proj_def):
        """
        Check if is it possible to compute the integrated risk index,
        depending on the current project definition structure.
        """
        iri_node = proj_def
        # if the IRI node is a custom field, then we don't want to recompute it
        # unless the description contains a valid formula
        if iri_node['operator'] == OPERATORS_DICT['CUSTOM']:
            customFormula = proj_def.get('customFormula', '')
            expression = QgsExpression(customFormula)
            if customFormula == '' or not expression.isValid():
                return False
        # check that all the sub-indices are well-defined
        if not self.is_ri_computable(iri_node):
            return False
        if not self.is_svi_computable(iri_node):
            return False
        return True

    def is_iri_renderable(self, proj_def):
        """
        Check if is it possible to render the integrated risk index,
        depending on the current project definition structure.
        """
        iri_node = proj_def
        # check that that the iri_node has a corresponding field
        if 'field' not in iri_node:
            return False
        # if the IRI node is a custom field, then we assume it is renderable
        if iri_node['operator'] == OPERATORS_DICT['CUSTOM']:
            return True
        if not self.is_iri_computable(proj_def):
            return False
        return True

    def redraw_ir_layer(self, data):
        """
        If the user has explicitly selected a field to use for styling, use
        it, otherwise attempt to show the IRI, or the SVI, or the RI
        """
        if 'style_by_field' in data:
            target_field = data['style_by_field']
            printing_str = target_field
        # if an IRI has been already calculated, show it
        elif self.is_iri_renderable(data):
            iri_node = data
            target_field = iri_node['field']
            printing_str = 'IRI'
        # else show the SVI if possible
        elif self.is_svi_renderable(data):
            svi_node = data['children'][1]
            target_field = svi_node['field']
            printing_str = 'SVI'
        # otherwise attempt to show the RI
        elif self.is_ri_renderable(data):
            ri_node = data['children'][0]
            target_field = ri_node['field']
            printing_str = 'RI'
        else:  # if none of them can be rendered, then do nothing
            return
        # proceed only if the target field is actually a field of the layer
        if self.iface.activeLayer().fields().indexOf(target_field) == -1:
            return
        if DEBUG:
            import pprint
            ppdata = pprint.pformat(data, indent=4)
            log_msg('REDRAWING %s using: \n%s' % (printing_str, ppdata))

        style = get_style(self.iface.activeLayer(), self.iface.messageBar())
        if style['force_restyling']:
            self._apply_style(style, target_field)

        # NOTE QGIS3 probably not needed
        # self.iface.layerTreeView().refreshLayerSymbology(
        #     self.iface.activeLayer().id())

        self.iface.mapCanvas().refresh()

    def _apply_style(self, style, target_field):
        rule_renderer = QgsRuleBasedRenderer(
            QgsSymbol.defaultSymbol(self.iface.activeLayer().geometryType()))
        root_rule = rule_renderer.rootRule()

        not_null_rule = root_rule.children()[0].clone()
        # strip parentheses from stringified color HSL
        col_str = str(style['color_from'].getHsl())[1:-1]
        not_null_rule.setSymbol(QgsFillSymbol.createSimple(
            {'color': col_str,
             'color_border': '0,0,0,255'}))
        not_null_rule.setFilterExpression('%s IS NOT NULL' % target_field)
        not_null_rule.setLabel('%s:' % target_field)
        root_rule.appendChild(not_null_rule)

        null_rule = root_rule.children()[0].clone()
        null_rule.setSymbol(QgsFillSymbol.createSimple(
            {'style': 'no',
             'color_border': '255,255,0,255',
             'width_border': '0.5'}))
        null_rule.setFilterExpression('%s IS NULL' % target_field)
        null_rule.setLabel(tr('Invalid value'))
        root_rule.appendChild(null_rule)

        ramp = QgsGradientColorRamp(
            style['color_from'], style['color_to'])
        graduated_renderer = QgsGraduatedSymbolRenderer.createRenderer(
            self.iface.activeLayer(),
            target_field,
            style['classes'],
            style['mode'],
            QgsSymbol.defaultSymbol(self.iface.activeLayer().geometryType()),
            ramp)

        if graduated_renderer.ranges():
            first_range_index = 0
            last_range_index = len(graduated_renderer.ranges()) - 1
            # NOTE: Workaround to avoid rounding problem (QGIS renderer's bug)
            # which creates problems styling the zone containing the lowest
            # and highest values in some cases
            lower_value = \
                graduated_renderer.ranges()[first_range_index].lowerValue()
            decreased_lower_value = floor(lower_value * 10000.0) / 10000.0
            graduated_renderer.updateRangeLowerValue(
                first_range_index, decreased_lower_value)
            upper_value = \
                graduated_renderer.ranges()[last_range_index].upperValue()
            increased_upper_value = ceil(upper_value * 10000.0) / 10000.0
            graduated_renderer.updateRangeUpperValue(
                last_range_index, increased_upper_value)
        elif DEBUG:
            log_msg('All features are NULL')
        # create value ranges
        rule_renderer.refineRuleRanges(not_null_rule, graduated_renderer)
        # remove default rule
        root_rule.removeChildAt(0)

        self.iface.activeLayer().setRenderer(rule_renderer)

    def show_settings(self):
        """
        Open a dialog to specify the connection settings used to interact
        with the OpenQuake Platform
        """
        SettingsDialog(self.iface, self).exec_()

    def transform_attributes(self):
        """
        A modal dialog is displayed to the user, enabling to transform one or
        more attributes of the active layer, using one of the available
        algorithms and variants
        """
        reg = QgsProject.instance()
        if not reg.count():
            msg = 'No layer available for transformation'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return

        dlg = TransformationDialog(self.iface)
        if dlg.exec_():
            layer = self.iface.activeLayer()
            input_attr_names = [
                field_name_plus_alias.split('(')[0].strip()
                for field_name_plus_alias in
                dlg.fields_multiselect.get_selected_items()]
            input_attr_aliases = [
                field_name_plus_alias.split('(')[1].split(')')[0].strip()
                for field_name_plus_alias in
                dlg.fields_multiselect.get_selected_items()]
            algorithm_name = dlg.algorithm_cbx.currentText()
            variant = dlg.variant_cbx.currentText()
            inverse = dlg.inverse_ckb.isChecked()
            for input_attr_idx, input_attr_name in enumerate(input_attr_names):
                target_attr_alias = input_attr_aliases[input_attr_idx]
                if dlg.overwrite_ckb.isChecked():
                    target_attr_name = input_attr_name
                elif dlg.fields_multiselect.selected_widget.count() == 1:
                    target_attr_name = dlg.new_field_name_txt.text()
                else:
                    # the limit of 10 chars for shapefiles is handled by
                    # ProcessLayer.add_attributes
                    target_attr_name = '_' + input_attr_name
                try:
                    msg = "Applying '%s' transformation to field '%s'" % (
                        algorithm_name, input_attr_name)
                    with WaitCursorManager(msg, self.iface.messageBar()):
                        res_attr_name, invalid_input_values = ProcessLayer(
                            layer).transform_attribute(input_attr_name,
                                                       algorithm_name,
                                                       variant,
                                                       inverse,
                                                       target_attr_name,
                                                       target_attr_alias)
                    msg = ('Transformation %s has been applied to attribute %s'
                           ' of layer %s.') % (algorithm_name,
                                               input_attr_name,
                                               layer.name())
                    if target_attr_name == input_attr_name:
                        msg += (' The original values of the attribute have'
                                ' been overwritten by the transformed values.')
                    else:
                        msg += (' The results of the transformation'
                                ' have been saved into the new'
                                ' attribute %s (%s).') % (res_attr_name,
                                                          target_attr_alias)
                    if invalid_input_values:
                        msg += (' The transformation could not'
                                ' be performed for the following'
                                ' input values: %s' % invalid_input_values)
                    level = 'S' if not invalid_input_values else 'W'
                    log_msg(msg, level=level,
                            message_bar=self.iface.messageBar())
                except (ValueError, NotImplementedError, TypeError) as e:
                    log_msg(e.message, level='C',
                            message_bar=self.iface.messageBar(),
                            exception=e)
                else:  # only if the transformation was performed successfully
                    active_layer_id = self.iface.activeLayer().id()
                    read_layer_suppl_info_from_qgs(
                        active_layer_id, self.supplemental_information)
                    if (dlg.track_new_field_ckb.isChecked()
                            and target_attr_name != input_attr_name
                            and (active_layer_id
                                 in self.supplemental_information)):
                        suppl_info = self.supplemental_information[
                            active_layer_id]
                        try:
                            proj_defs = suppl_info['project_definitions']
                        except KeyError:
                            # do nothing if the project still has no project
                            # definitions to update
                            pass
                        else:
                            for proj_def in proj_defs:
                                replace_fields(proj_def,
                                               input_attr_name,
                                               target_attr_name)
                            suppl_info['project_definitions'] = proj_defs
                            write_layer_suppl_info_to_qgs(active_layer_id,
                                                          suppl_info)
        elif dlg.use_advanced:
            layer = self.iface.activeLayer()
            if layer.isModified():
                layer.commitChanges()
                layer.triggerRepaint()
                msg = 'Calculation performed on layer %s' % layer.name()
                log_msg(msg, level='S', message_bar=self.iface.messageBar())
        self.update_actions_status()

    def upload(self):
        """
        Open a dialog to upload the current project to the OpenQuake Platform
        """
        temp_dir = tempfile.gettempdir()
        file_stem = '%s%sqgis_irmt_%s' % (temp_dir, os.path.sep, uuid.uuid4())

        active_layer_id = self.iface.activeLayer().id()
        read_layer_suppl_info_from_qgs(
            active_layer_id, self.supplemental_information)
        suppl_info = self.supplemental_information[active_layer_id]
        # add layer's bounding box
        extent = self.iface.activeLayer().extent()
        bbox = {'minx': extent.xMinimum(),
                'miny': extent.yMinimum(),
                'maxx': extent.xMaximum(),
                'maxy': extent.yMaximum()}
        suppl_info['bounding_box'] = bbox

        dlg = UploadSettingsDialog(self.iface, suppl_info, file_stem)
        dlg.exec_()

    def toggle_dock_visibility(self):
        """Show or hide the dock widget."""
        if self.viewer_dock.isVisible():
            self.viewer_dock.setVisible(False)
        else:
            self.viewer_dock.setVisible(True)
            self.viewer_dock.raise_()

    def _create_viewer_dock(self):
        """Create dockwidget and tabify it with the legend."""

        # Action to drive the oq-engine server
        action = self.add_menu_item("toggle_viewer_dock",
                                    ":/plugins/irmt/plot.svg",
                                    u"Toggle viewer dock",
                                    self.toggle_dock_visibility,
                                    enable=True,
                                    add_to_toolbar=True,
                                    set_checkable=True,
                                    set_checked=True)

        self.viewer_dock = ViewerDock(self.iface, action)
        self.viewer_dock.setObjectName('IRMT-Dock')
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.viewer_dock)
        legend_tab = self.iface.mainWindow().findChild(QApplication, 'Legend')
        if legend_tab:
            self.iface.mainWindow().tabifyDockWidget(
                legend_tab, self.viewer_dock)
            self.viewer_dock.raise_()
        self.registered_actions['toggle_viewer_dock'].setChecked(
            self.viewer_dock.isVisible())
        self.viewer_dock.visibilityChanged[bool].connect(
            self.on_viewer_dock_visibility_changed)

    def on_viewer_dock_visibility_changed(self, visible):
        self.registered_actions['toggle_viewer_dock'].setChecked(visible)

    def get_ipt_dir(self):
        home_dir = os.path.expanduser("~")
        ipt_dir = os.path.join(home_dir, ".gem", "irmt", "ipt")
        if not os.path.exists(ipt_dir):
            os.makedirs(ipt_dir)
        return ipt_dir

    def get_ipt_checksum(self):
        unique_filename = ".%s" % uuid.uuid4().hex
        checksum_file_path = os.path.join(self.ipt_dir, unique_filename)
        with open(checksum_file_path, "w") as f:
            f.write(os.urandom(32))
        return checksum_file_path, get_checksum(checksum_file_path)
