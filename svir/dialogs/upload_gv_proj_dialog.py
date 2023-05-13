# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2020-01-23
#        copyright            : (C) 2020 by GEM Foundation
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

import os
import re
import json
import tempfile
from requests import Session
from qgis.server import QgsServerProjectUtils
from qgis.core import (
    QgsApplication, QgsProcessingContext, QgsProcessingFeedback, QgsProject,
    QgsProcessingUtils, QgsField, QgsFields, QgsFeature, QgsGeometry,
    QgsWkbTypes, QgsMemoryProviderUtils, QgsCoordinateReferenceSystem,
    QgsTask, QgsMapLayerType, QgsVectorLayer)
from qgis.PyQt.QtCore import QVariant, QDir, QFile
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QMessageBox)
from processing.gui.AlgorithmExecutor import execute
from svir.tasks.consolidate_task import ConsolidateTask
from svir.utilities.utils import (
    get_ui_class, log_msg, get_credentials, tr, geoviewer_login)
from svir.utilities.shared import (
    LICENSES, DEFAULT_LICENSE, PROJECT_KINDS,
    DEFAULT_PROJECT_KIND)


FORM_CLASS = get_ui_class('ui_upload_gv_proj.ui')


class UploadGvProjDialog(QDialog, FORM_CLASS):
    """
    Workflow:
    1. check that all geometries are valid for all layers
    (NOTE: some layers might contain no geometries, but they could be used as
    data sources, joined to layers containing geometries)
    2. check that a valid CRS has been set for the project
    3. let the user pick a type for the project
    4. let the user pick a license
    5. consolidate layers into .gpkg files and project into a .qgs
    6. use "api/project/upload" to upload the consolidated project
    """
    def __init__(self, message_bar, parent=None):
        self.message_bar = message_bar
        super().__init__(parent)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.proj_name_le.textEdited.connect(self.set_ok_btn_status)
        # self.add_layer_with_invalid_geometries()  # useful to test validity
        self.populate_license_cbx()
        self.populate_kind_cbx()
        self.check_project_properties()
        self.check_geometries()
        self.check_crs()
        self.session = Session()
        self.authenticate()
        self.get_geoviewer_project_list()

    def authenticate(self):
        self.hostname, username, password = get_credentials('geoviewer')
        geoviewer_login(self.hostname, username, password, self.session)

    def set_ok_btn_status(self, proj_name):
        self.ok_button.setEnabled(bool(proj_name))

    def populate_license_cbx(self):
        # FIXME: licenses should be retrieved from those available in the
        # GeoViewer
        for license_name, license_link in LICENSES:
            self.license_cbx.addItem(license_name, license_link)
        self.license_cbx.setCurrentIndex(
            self.license_cbx.findText(DEFAULT_LICENSE[0]))

    def populate_kind_cbx(self):
        # FIXME: kinds should be retrieved from those available in the
        # GeoViewer
        for kind_name, kind_text in PROJECT_KINDS:
            self.project_kind_cbx.addItem(kind_text, kind_name)
        self.project_kind_cbx.setCurrentIndex(
            self.project_kind_cbx.findData(DEFAULT_PROJECT_KIND))

    def add_layer_with_invalid_geometries(self):
        # NOTE: userful to test the validation
        fields = QgsFields()
        layer_wkb_name = 'Polygon'
        wkb_type = getattr(QgsWkbTypes, layer_wkb_name)
        fields.append(QgsField('int_f', QVariant.Int))
        polygon_layer = QgsMemoryProviderUtils.createMemoryLayer(
            '%s_layer' % layer_wkb_name, fields, wkb_type,
            QgsCoordinateReferenceSystem(4326))
        polygon_layer.startEditing()
        f = QgsFeature(polygon_layer.fields())
        f.setAttributes([1])
        # Flake!
        f.setGeometry(QgsGeometry.fromWkt(
            'POLYGON ((0 0, 2 2, 0 2, 2 0, 0 0))'))
        f2 = QgsFeature(polygon_layer.fields())
        f2.setAttributes([1])
        f2.setGeometry(QgsGeometry.fromWkt(
            'POLYGON((1.1 1.1, 1.1 2.1, 2.1 2.1, 2.1 1.1, 1.1 1.1))'))
        polygon_layer.addFeatures([f, f2])
        polygon_layer.commitChanges()
        polygon_layer.rollBack()
        QgsProject.instance().addMapLayers([polygon_layer])

    def check_project_properties(self):
        p = QgsProject.instance()
        add_geoms_to_feat_resp = p.readBoolEntry("WMSAddWktGeometry", "/")[0]
        if not add_geoms_to_feat_resp:
            msg = 'Would you like to add geometry to GetFeatureInfo response?'
            ret = QMessageBox.question(
                self, '', msg, QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                p.writeEntryBool("WMSAddWktGeometry", "/", True)

        # FIXME: this returns False even if the precision is set to 1
        geom_precision = p.readEntry("WMSPrecision", "/")[0]
        if geom_precision != 1:
            msg = ('Would you like to set GetFeatureInfo geometry precision '
                   'to 1 decimal place?')
            ret = QMessageBox.question(
                self, '', msg, QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                p.writeEntry("WMSPrecision", "/", 1)
        # if not QgsServerProjectUtils.wmsFeatureInfoSegmentizeWktGeometry(p):
        #     msg = ('Project QGIS Server property "Segmentize feature info'
        #            ' geometry" is disabled')
        #     log_msg(msg, level='W',
        #             message_bar=self.message_bar)
        if not QgsServerProjectUtils.owsServiceCapabilities(p):
            msg = ('Would you like to enable service capabilities?')
            ret = QMessageBox.question(
                self, '', msg, QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                p.writeEntryBool("WMSServiceCapabilities", "/", True)
            # log_msg("Project capabilities are disabled", level='C',
            #         message_bar=self.message_bar)
            # self.reject()
            # return

        # FIXME: we should set the extent to the current one
        if QgsServerProjectUtils.wmsExtent(p).isEmpty():
            msg = ('Would you like to advertise project extent?')
            ret = QMessageBox.question(
                self, '', msg, QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                p.writeEntry("WMSExtent", "/", True)
            # log_msg("Project extent is not advertised", level='C',
            #         message_bar=self.message_bar)
            # self.reject()
            # return

    def check_geometries(self):
        layers = list(QgsProject.instance().mapLayers().values())
        if len(layers) == 0:
            log_msg("The project has no layers",
                    level='C', message_bar=self.message_bar)
            return
        registry = QgsApplication.instance().processingRegistry()
        feedback = MessageBarFeedback(self.message_bar)
        # feedback = ConsoleFeedBack()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        parameters = {}
        parameters['VALID_OUTPUT'] = 'memory:'
        parameters['INVALID_OUTPUT'] = 'memory:'
        parameters['ERROR_OUTPUT'] = 'memory:'
        # QGIS method
        # parameters['METHOD'] = 1
        # GEOS method
        parameters['METHOD'] = 2
        alg = registry.createAlgorithmById('qgis:checkvalidity')
        for layer in layers:
            if layer.type() != QgsMapLayerType.VectorLayer:
                # If it is not in a group for basemaps, give a warning
                root = QgsProject.instance().layerTreeRoot()
                tree_layer = root.findLayer(layer.id())
                assert tree_layer
                layer_parent = tree_layer.parent()
                if (not layer_parent or
                        layer_parent.name().lower().strip().replace(
                            ' ', '') not in ('basemap', 'basemaps')):
                    msg = ("Layer %s looks like a basemap, and it should"
                           " probably be added to a group called"
                           " 'Basemaps'" % layer.name())
                    log_msg(msg, level='W', message_bar=self.message_bar)
                continue
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                continue
            parameters['INPUT_LAYER'] = layer.id()
            ok, results = execute(
                alg, parameters, context=context, feedback=feedback)
            invalid_geoms_layer = QgsProcessingUtils.mapLayerFromString(
                results['INVALID_OUTPUT'], context)
            if invalid_geoms_layer.featureCount():
                feedback.reportError(
                    "Layer '%s' contains features with invalid geometries."
                    " A layer containing these invalid geometries was added"
                    " to the project." % layer.name())
                QgsProject.instance().addMapLayer(invalid_geoms_layer)

    def check_crs(self):
        layers = list(QgsProject.instance().mapLayers().values())
        for layer in layers:
            if (isinstance(layer, QgsVectorLayer)
                    and layer.geometryType() == QgsWkbTypes.NullGeometry):
                continue
            if not layer.crs().isValid():
                msg = ("Layer '%s' does not have a valid coordinate"
                       " reference system" % layer.name())
                log_msg(msg, level='W', message_bar=self.message_bar)
        if not QgsProject.instance().crs().isValid():
            msg = ("The current project does not have a valid coordinate"
                   " reference system")
            log_msg(msg, level='C', message_bar=self.message_bar)

    def accept(self):
        project_name = self.proj_name_le.text()
        if project_name.endswith('.qgs'):
            project_name = project_name[:-4]
        if not project_name:
            msg = tr("Please specify the project name")
            log_msg(msg, level='C', message_bar=self.message_bar)
            return
        if project_name in self.proj_names:
            msg = ("A project named %s already exists" % project_name)
            log_msg(msg, level='C', message_bar=self.message_bar)
            return
        QgsProject.instance().write()
        super().accept()
        self.consolidate(project_name)

    def consolidate(self, project_name):
        outputDir = tempfile.mkdtemp()
        outputDir = os.path.join(outputDir,
                                 get_valid_filename(project_name))

        # create main directory if not exists
        d = QDir(outputDir)
        if not d.exists():
            if not d.mkpath("."):
                msg = tr("Can't create directory to store the project.")
                log_msg(msg, level='C', message_bar=self.message_bar)
                return

        # create directory for layers if not exists
        if not d.mkdir("layers"):
            msg = tr("Can't create directory for layers.")
            log_msg(msg, level='C', message_bar=self.message_bar)
            return

        # copy project file
        projectFile = QgsProject.instance().fileName()
        try:
            if projectFile:
                f = QFile(projectFile)
                newProjectFile = os.path.join(outputDir,
                                              '%s.qgs' % project_name)
                f.copy(newProjectFile)
            else:
                newProjectFile = os.path.join(
                    outputDir, '%s.qgs' % project_name)
                p = QgsProject.instance()
                p.write(newProjectFile)
        except Exception as exc:
            log_msg(str(exc), level='C',
                    message_bar=self.message_bar,
                    exception=exc)
            return

        # start consolidate task that does all real work
        self.consolidateTask = ConsolidateTask(
            'Consolidation', QgsTask.CanCancel, outputDir, newProjectFile,
            True)
        self.consolidateTask.begun.connect(self.on_consolidation_begun)
        self.consolidateTask.taskCompleted.connect(
            lambda: self.on_consolidation_completed(
                newProjectFile))

        QgsApplication.taskManager().addTask(self.consolidateTask)
        # super().accept()

    def on_consolidation_begun(self):
        log_msg("Consolidation started.", level='I', duration=4)

    def on_consolidation_completed(self, project_file):
        zipped_project = "%s.zip" % os.path.splitext(project_file)[0]
        log_msg("The project was consolidated and saved to '%s'"
                % zipped_project, level='S')
        self.upload_to_geoviewer(zipped_project)

    def get_geoviewer_project_list(self):
        r = self.session.get(self.hostname + '/api/project_list/', timeout=10)
        if r.ok:
            content = json.loads(r.text)
            self.proj_names = [proj['fields']['name'] for proj in content]
            msg = ("Projects available on the OpenQuake GeoViewer: %s"
                   % self.proj_names)
            log_msg(msg, level='S', message_bar=self.message_bar)
        else:
            log_msg(r.reason, level='C', message_bar=self.message_bar)

    def upload_to_geoviewer(self, zipped_project):
        project_license = self.license_cbx.currentText()
        # FIXME: probably the license should be added to the project properties
        # and it should be read GeoViewer-side through an api
        project_kind = self.project_kind_cbx.currentData()
        auto_create_map = self.auto_create_map_ckb.isChecked()
        files = {'file': open(zipped_project, 'rb')}
        data = {'license': project_license, 'kind': project_kind,
                'auto_create_map': auto_create_map}
        r = self.session.post(
            self.hostname + '/api/project/upload', files=files, data=data,
            timeout=20)
        if r.ok:
            msg = ("The project was successfully uploaded to the"
                   " OpenQuake GeoViewer")
            log_msg(msg, level='S', message_bar=self.message_bar)
        else:
            log_msg(r.reason, level='C', message_bar=self.message_bar)


class ConsoleFeedBack(QgsProcessingFeedback):

    def reportError(self, error, fatalError=False):
        print(error)


class MessageBarFeedback(QgsProcessingFeedback):

    def __init__(self, message_bar):
        self.message_bar = message_bar
        super().__init__()

    def pushCommandInfo(self, info):
        self.message_bar.pushInfo('Info', info)

    def pushConsoleInfo(self, info):
        self.message_bar.pushCritical('Info', info)

    def pushDebugInfo(self, info):
        self.message_bar.pushCritical('Info', info)

    def pushInfo(self, info):
        self.message_bar.pushInfo('Info', info)

    def reportError(self, error, fatalError=False):
        self.message_bar.pushCritical('Error', error)

    def setProgressText(self, text):
        self.message_bar.pushInfo('Info', text)


# from https://github.com/django/django/blob/master/django/utils/text.py#L223
def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')  # FIXME: str
    return re.sub(r'(?u)[^-\w.]', '', s)
