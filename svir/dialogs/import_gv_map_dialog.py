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

import json
import traceback
import tempfile
import requests
import zipfile
import os
from requests import Session
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import (
    QDialog, QTableWidgetItem, QPushButton)
from svir.utilities.utils import (
    get_ui_class, log_msg, geoviewer_login, get_credentials)

BUTTON_WIDTH = 75

FORM_CLASS = get_ui_class('ui_import_gv_map.ui')


class ImportGvMapDialog(QDialog, FORM_CLASS):
    """
    Dialog listing maps available on a connected OqGeoviewer, showing map
    properties and a button to download the map as a QGIS project
    """
    def __init__(self, message_bar):
        self.message_bar = message_bar
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.session = Session()
        self.authenticate()
        map_list = self.get_published_map_list()
        if map_list:
            self.show_map_list(map_list)
        else:
            log_msg('There are no published maps available',
                    level='W', message_bar=self.message_bar)
            self.reject()

    def authenticate(self):
        self.hostname, username, password = get_credentials('geoviewer')
        geoviewer_login(self.hostname, username, password, self.session)

    def show_map_list(self, map_list):
        fields_to_display = list(map_list[0]['fields'])
        name_idx = fields_to_display.index('name')
        fields_to_display.pop(name_idx)
        fields_to_display.insert(0, 'name')

        self.list_of_maps_tbl.setRowCount(len(map_list))
        self.list_of_maps_tbl.setColumnCount(len(fields_to_display) + 1)
        for row, map in enumerate(map_list):
            # FIXME
            # if map['fields']['downloadable']:
            button = QPushButton('Download')
            self.list_of_maps_tbl.setCellWidget(
                row, 0, button)
            # self.list_of_maps_tbl.setColumnWidth(0, BUTTON_WIDTH)
            self.list_of_maps_tbl.setHorizontalHeaderItem(
                0, QTableWidgetItem(''))
            button.clicked.connect(
                lambda checked=False,
                map_name=map['fields']['name'],
                map_slug=map['fields']['slug']:
                    self.on_download_btn_clicked(map_name, map_slug))
            for col, field in enumerate(fields_to_display, start=1):
                item = QTableWidgetItem(str(map['fields'][field]))
                self.list_of_maps_tbl.setItem(row, col, item)
                self.list_of_maps_tbl.setHorizontalHeaderItem(
                    col, QTableWidgetItem(field))

    def download_url(self, url, save_path, chunk_size=128):
        r = requests.get(url, stream=True)
        if not r.ok:
            msg = 'Unable to download the selected map.'
            if r.reason == 'Forbidden':
                msg += (' Most likely, the map is set as published but the'
                        ' corresponding project is not set as downloadable.')
            else:
                msg += ' ' + r.reason
            log_msg(msg, level='C', message_bar=self.message_bar)
            self.reject()
            return False
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
            return True

    def on_download_btn_clicked(self, map_name, map_slug):
        msg = 'Downloading map %s (%s)' % (map_name, map_slug)
        log_msg(msg, level='S', message_bar=self.message_bar)
        map_download_url = '%s/map/%s/download' % (self.hostname, map_slug)
        zip_file = tempfile.NamedTemporaryFile(suffix='.zip')
        zip_file.close()
        if not self.download_url(map_download_url, zip_file.name):
            return
        dirpath = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_file.name, 'r') as zip_ref:
            zip_ref.extractall(dirpath)
        log_msg('The project was downloaded into the folder: %s' % dirpath,
                level='S')
        for filename in os.listdir(dirpath):
            if filename.endswith('.qgs'):
                qgsfilepath = os.path.join(dirpath, filename)
                project = QgsProject.instance()
                project.read(qgsfilepath)
                break

    def get_published_map_list(self):
        map_list_url = self.hostname + '/api/map_list/'
        try:
            resp = self.session.get(map_list_url, timeout=10)
        except Exception:
            msg = "Unable to retrieve the list of maps.\n%s" % (
                traceback.format_exc())
            log_msg(msg, level='C', message_bar=self.messageBar())
            self.reject()
            return
        if resp.status_code != 200:  # 200 means successful:OK
            msg = ('Unable to retrieve the list of maps: %s' % resp.text)
            log_msg(msg, level='C', message_bar=self.messageBar())
            self.reject()
            return
        map_list = json.loads(resp.text)
        published_map_list = [map for map in map_list
                        if map['fields']['published']]
        return published_map_list
