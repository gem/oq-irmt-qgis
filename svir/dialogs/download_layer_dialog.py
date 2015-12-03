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
                                  ask_for_download_destination,
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
        dest_dir = ask_for_download_destination(self)
        if not dest_dir:
            return

        worker = DownloadPlatformProjectWorker(self.sv_downloader,
                                               self.layer_id)
        worker.successfully_finished.connect(
            lambda zip_file: self._import_layer(
                zip_file, self.sv_downloader, dest_dir, self))
        start_worker(worker, self.iface.messageBar(),
                     'Downloading data from platform')

    def _import_layer(self, zip_file, sv_downloader, dest_dir, parent_dlg):
        files_in_zip = zip_file.namelist()
        shp_file = next(
            filename for filename in files_in_zip if '.shp' in filename)
        file_in_destination = files_exist_in_destination(
            dest_dir, files_in_zip)

        if file_in_destination:
            while confirm_overwrite(parent_dlg, file_in_destination) == \
                    QMessageBox.No:
                dest_dir = ask_for_download_destination(parent_dlg)
                if not dest_dir:
                    return
                file_in_destination = files_exist_in_destination(
                    dest_dir, zip_file.namelist())
                if not file_in_destination:
                    break

        zip_file.extractall(dest_dir)

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

        dest_file = os.path.join(dest_dir, shp_file)
        layer = QgsVectorLayer(
            dest_file,
            parent_dlg.extra_infos[parent_dlg.layer_id]['Title'], 'ogr')
        if layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            self.iface.messageBar().pushMessage(
                tr('Import successful'),
                tr('Shapefile imported to %s' % dest_file),
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
