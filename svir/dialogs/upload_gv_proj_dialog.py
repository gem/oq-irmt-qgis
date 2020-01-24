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
import traceback
import tempfile
from requests import Session
from qgis.core import (
    QgsApplication, QgsProcessingContext, QgsProcessingFeedback, QgsProject,
    QgsProcessingUtils, QgsField, QgsFields, QgsFeature, QgsGeometry,
    QgsWkbTypes, QgsMemoryProviderUtils, QgsCoordinateReferenceSystem,
    QgsTask)
from qgis.PyQt.QtCore import QSettings, QVariant, QDir, QFile
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox)
from processing.gui.AlgorithmExecutor import execute
from svir.tasks.consolidate_task import ConsolidateTask
from svir.utilities.utils import get_ui_class, log_msg, geoviewer_login, tr
from svir.utilities.shared import (
    DEFAULT_GEOVIEWER_PROFILES, LICENSES, DEFAULT_LICENSE)


FORM_CLASS = get_ui_class('ui_upload_gv_proj.ui')


class UploadGvProjDialog(QDialog, FORM_CLASS):
    """
    Workflow:
    1. check that all geometries are valid for all layers
    2. check that a valid CRS has been set for the project
    3. let the user pick a license
    4. consolidate layers into .gpkg files and project into a .qgs
    5. use "api/project/upload" to upload the consolidated project
    """
    def __init__(self, message_bar):
        self.message_bar = message_bar
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.proj_name_le.textEdited.connect(self.set_ok_btn_status)
        # self.add_layer_with_invalid_geometries()  # useful to test validity
        self.check_geometries()
        self.check_crs()
        self.populate_license_cbx()

    def set_ok_btn_status(self, proj_name):
        self.ok_button.setEnabled(bool(proj_name))

    def populate_license_cbx(self):
        for license_name, license_link in LICENSES:
            self.license_cbx.addItem(license_name, license_link)
        self.license_cbx.setCurrentIndex(
            self.license_cbx.findText(DEFAULT_LICENSE[0]))

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

    def check_geometries(self):
        layers = list(QgsProject.instance().mapLayers().values())
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
            parameters['INPUT_LAYER'] = layer.id()
            ok, results = execute(
                alg, parameters, context=context, feedback=feedback)
            invalid_layer = QgsProcessingUtils.mapLayerFromString(
                results['INVALID_OUTPUT'], context)
            if invalid_layer.featureCount():
                feedback.reportError(
                    "Layer '%s' contains features with invalid geometries."
                    " Please run Vector -> Geometry Tools -> Check Validity"
                    " for further information" % layer.name())
        feedback.pushInfo(
            'All features in all layers in the project are valid')

    def check_crs(self):
        layers = list(QgsProject.instance().mapLayers().values())
        for layer in layers:
            if not layer.crs().isValid():
                msg = ("Layer '%s' does not have a valid coordinate"
                       " reference system" % layer.name())
                log_msg(msg, level='C', message_bar=self.message_bar)

    def accept(self):
        self.consolidate()
        self.upload_to_geoviewer()
        super().accept()

    def consolidate(self):
        project_name = self.proj_name_le.text()
        if project_name.endswith('.qgs'):
            project_name = project_name[:-4]
        if not project_name:
            msg = tr("Please specify the project name")
            log_msg(msg, level='C', message_bar=self.message_bar)
            return

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
        super().accept()

    def on_consolidation_begun(self):
        log_msg("Consolidation started.", level='I', duration=4,
                message_bar=self.message_bar)

    def on_consolidation_completed(self, project_file):
        zipped_project = "%s.zip" % os.path.splitext(project_file)[0]
        log_msg("Uploading '%s' to geoviewer" % zipped_project, level='I',
                message_bar=self.message_bar)
        self.upload_to_geoviewer()

    def upload_to_geoviewer(self):
        pass


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
