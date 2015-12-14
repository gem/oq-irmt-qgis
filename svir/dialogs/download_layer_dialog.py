# -*- coding: utf-8 -*-
#/***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

import json
import os
import tempfile
import shutil
from xml.etree import ElementTree
from PyQt4 import Qt

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QListWidgetItem,
                         QMessageBox)
from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer,  QgsMapLayerRegistry
from svir.thread_worker.abstract_worker import start_worker
from svir.thread_worker.download_platform_project_worker import (
    DownloadPlatformProjectWorker)

from svir.ui.ui_download_layer import Ui_DownloadLayerDialog
from svir.utilities.utils import (WaitCursorManager,
                                  SvNetworkError,
                                  ask_for_destination_full_path_name,
                                  files_exist_in_destination,
                                  confirm_overwrite,
                                  tr,
                                  write_layer_suppl_info_to_qgs,
                                  )

NS_NET_OPENGIS_WFS = '{http://www.opengis.net/wfs}'


class DownloadLayerDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select and download one
    of the projects available on the OQ-Platform
    """
    def __init__(self, iface, downloader):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_DownloadLayerDialog()
        self.ui.setupUi(self)

        self.iface = iface
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = downloader

        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.ui.layer_lbl.setText('Project definition')

        self.layer_id = None  # needed after ok is pressed
        self.downloaded_layer_id = None  # the id of the layer created
        self.extra_infos = {}

        self.set_ok_button()
        with WaitCursorManager():
            self.get_capabilities()

    @pyqtSlot()
    def on_layers_lst_itemSelectionChanged(self):
        layer_id = self.ui.layers_lst.currentItem().data(Qt.Qt.ToolTipRole)
        if layer_id is not None:
            self.layer_id = layer_id
            self.ui.layer_lbl.setText('Project details for "%s"' % layer_id)
            layer_infos = self.extra_infos[layer_id]
            bb = layer_infos['Bounding Box']
            layer_infos_str = "Title:\n\t" + layer_infos['Title']
            layer_infos_str += "\nAbstract:\n\t" + layer_infos['Abstract']
            layer_infos_str += "\nBounding box:"
            layer_infos_str += "\n\tminx = " + bb['minx']
            layer_infos_str += "\n\tminy = " + bb['miny']
            layer_infos_str += "\n\tmaxx = " + bb['maxx']
            layer_infos_str += "\n\tmaxy = " + bb['maxy']
            layer_infos_str += "\nKeywords:\n\t" + layer_infos['Keywords']
            self.ui.layer_detail.setText(layer_infos_str)
        self.set_ok_button()

    @pyqtSlot(QListWidgetItem)
    def on_layers_lst_itemDoubleClicked(self, item):
        self.accept()

    def set_ok_button(self):
        self.ok_button.setDisabled(
            len(self.ui.layers_lst.selectedItems()) == 0)

    def get_capabilities(self):
        wfs = '/geoserver/wfs?'
        params = ('SERVICE=WFS'
                  '&VERSION=1.0.0'
                  '&REQUEST=GetCapabilities'
                  '&SRSNAME=EPSG:4326')
        url = '%s%s%s' % (self.sv_downloader.host, wfs, params)
        result = self.sv_downloader.sess.get(url)
        if result.status_code == 200:
            self.parse_get_capabilities(result.content)
        else:
            raise SvNetworkError(
                "Unable to download layers: %s" % result.error)

    def parse_get_capabilities(self, xml):
        # this raises a IOError if the file doesn't exist
        root = ElementTree.fromstring(xml)
        layers = root.find('%sFeatureTypeList' % NS_NET_OPENGIS_WFS)

        for layer in layers:
            try:
                keywords = layer.find('%sKeywords' % NS_NET_OPENGIS_WFS).text
                if keywords is not None and (
                        'IRMT_QGIS_Plugin' in keywords or
                        # this is for backward compatibility
                        'SVIR_QGIS_Plugin' in keywords):
                    title = layer.find('%sTitle' % NS_NET_OPENGIS_WFS).text
                    layer_id = layer.find('%sName' % NS_NET_OPENGIS_WFS).text
                    abstract = layer.find(
                        '%sAbstract' % NS_NET_OPENGIS_WFS).text
                    bbox = layer.find(
                        '%sLatLongBoundingBox' % NS_NET_OPENGIS_WFS).attrib

                    self.extra_infos[layer_id] = {
                        'Title': title,
                        'Abstract': abstract,
                        'Keywords': keywords,
                        'Bounding Box': bbox}

                    # update combo box
                    item = QListWidgetItem()
                    item.setData(Qt.Qt.DisplayRole, title)
                    item.setData(Qt.Qt.ToolTipRole, layer_id)
                    self.ui.layers_lst.addItem(item)
            except AttributeError:
                continue

    def accept(self):
        dest_full_path_name = ask_for_destination_full_path_name(self)
        if not dest_full_path_name:
            return
        # ignoring file extension
        dest_file_stem_path, _dest_file_ext = os.path.splitext(
            dest_full_path_name)

        worker = DownloadPlatformProjectWorker(self.sv_downloader,
                                               self.layer_id)
        worker.successfully_finished.connect(
            lambda zip_file: self._import_layer(
                zip_file, self.sv_downloader, dest_file_stem_path, self))
        start_worker(worker, self.iface.messageBar(),
                     'Downloading data from platform')

    def _replace_file_names(self, source_files, dest_file_stem):
        # the name from the zip_file will be replaced with dest_file_stem
        dest_file_names = []
        for source_file in source_files:
            _name, ext = os.path.splitext(source_file)
            dest_file_name = dest_file_stem + ext
            dest_file_names.append(dest_file_name)
        return dest_file_names

    def _import_layer(
            self, zip_file, sv_downloader, dest_file_stem_path, parent_dlg):
        files_in_zip = zip_file.namelist()
        shp_file_in_zip = next(
            filename for filename in files_in_zip if '.shp' in filename)
        dest_dir = os.path.dirname(dest_file_stem_path)
        files_to_create = self._replace_file_names(files_in_zip,
                                                   dest_file_stem_path)
        existing_files_in_destination = files_exist_in_destination(
            dest_dir, files_to_create)

        if existing_files_in_destination:
            while confirm_overwrite(
                    parent_dlg,
                    existing_files_in_destination) == QMessageBox.No:
                dest_full_path_name = ask_for_destination_full_path_name(
                    parent_dlg)
                if not dest_full_path_name:
                    continue
                # ignoring file extension
                dest_file_stem_path, _dest_file_ext = os.path.splitext(
                    dest_full_path_name)
                dest_dir = os.path.dirname(dest_file_stem_path)
                files_to_create = self._replace_file_names(files_in_zip,
                                                           dest_file_stem_path)
                existing_files_in_destination = files_exist_in_destination(
                    dest_dir, files_to_create)
                if not existing_files_in_destination:
                    break

        temp_path = os.path.join(tempfile.gettempdir(), shp_file_in_zip[:-4])
        if os.path.exists(temp_path):
            temp_dir = temp_path
            # clearing the temp_dir should be safe
            for the_file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, the_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        else:
            temp_dir = os.makedirs(temp_path)
        zip_file.extractall(temp_dir)
        # copy extracted files to the destination directory chosen by the user,
        # substituting the file names with the name chosen by the user
        for the_file in os.listdir(temp_dir):
            _name, ext = os.path.splitext(the_file)
            new_file_path = dest_file_stem_path + ext
            # the full file name of the shapefile will be used to create the
            # vector layer
            if ext == '.shp':
                new_shp_file_path = new_file_path
            shutil.move(os.path.join(temp_dir, the_file), new_file_path)

        request_url = '%s/svir/get_supplemental_information?layer_name=%s' % (
            sv_downloader.host, parent_dlg.layer_id)
        get_supplemental_information_resp = sv_downloader.sess.get(request_url)
        if not get_supplemental_information_resp.ok:
            self.iface.messageBar().pushMessage(
                tr("Download Error"),
                tr('Unable to retrieve the project definitions for the layer'),
                level=QgsMessageBar.CRITICAL)
            return
        supplemental_information = json.loads(
            get_supplemental_information_resp.content)
        # attempt to convert supplemental information in old list format
        # or those that did not nest project definitions into a
        # project_definitions attribute
        if (isinstance(supplemental_information, list)
                or 'project_definitions' not in supplemental_information):
            supplemental_information = {
                'project_definitions': supplemental_information}

        layer = QgsVectorLayer(
            new_shp_file_path,
            parent_dlg.extra_infos[parent_dlg.layer_id]['Title'], 'ogr')
        if layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            self.iface.messageBar().pushMessage(
                tr('Import successful'),
                tr('Shapefile imported to %s' % new_shp_file_path),
                duration=8)
        else:
            self.iface.messageBar().pushMessage(
                tr("Import Error"),
                tr('Layer invalid'),
                level=QgsMessageBar.CRITICAL)
            return
        try:
            # dlg.layer_id has the format "oqplatform:layername"
            style_name = parent_dlg.layer_id.split(':')[1] + '.sld'
            request_url = '%s/gs/rest/styles/%s' % (
                sv_downloader.host, style_name)
            get_style_resp = sv_downloader.sess.get(request_url)
            if not get_style_resp.ok:
                raise SvNetworkError(get_style_resp.reason)
            fd, sld_file = tempfile.mkstemp(suffix=".sld")
            os.close(fd)
            with open(sld_file, 'w') as f:
                f.write(get_style_resp.text)
            layer.loadSldStyle(sld_file)
        except Exception as e:
            error_msg = ('Unable to download and apply the'
                         ' style layer descriptor: %s' % e)
            self.iface.messageBar().pushMessage(
                'Error downloading style',
                error_msg, level=QgsMessageBar.WARNING,
                duration=8)
        self.iface.setActiveLayer(layer)
        project_definitions = supplemental_information['project_definitions']
        # ensure backwards compatibility with projects with a single
        # project definition
        if not isinstance(project_definitions, list):
            project_definitions = [project_definitions]
        supplemental_information['project_definitions'] = project_definitions
        supplemental_information['platform_layer_id'] = parent_dlg.layer_id
        if 'selected_project_definition_idx' not in supplemental_information:
            supplemental_information['selected_project_definition_idx'] = 0
        self.downloaded_layer_id = layer.id()
        write_layer_suppl_info_to_qgs(
            self.downloaded_layer_id, supplemental_information)
        super(DownloadLayerDialog, self).accept()
