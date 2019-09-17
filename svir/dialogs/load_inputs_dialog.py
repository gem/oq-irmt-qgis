# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2019 by GEM Foundation
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

import zipfile
import json
import os
import configparser
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QDialogButtonBox, QGroupBox, QCheckBox)
from svir.utilities.utils import (
    import_layer_from_csv, log_msg, get_headers, write_metadata_to_layer)
from svir.utilities.shared import GEOM_FIELDNAMES
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadInputsDialog(QDialog):
    """
    Dialog to browse zipped input files
    """

    loading_canceled = pyqtSignal()
    loading_completed = pyqtSignal()

    def __init__(self, drive_engine_dlg, zip_filepath, iface, parent=None):
        super().__init__(parent)
        self.drive_engine_dlg = drive_engine_dlg
        self.zip_filepath = zip_filepath
        self.iface = iface
        ini_str = self.get_ini_str(self.zip_filepath)
        self.multi_peril_csv_dict = self.get_multi_peril_csv_dict(ini_str)
        self.setWindowTitle('Load peril data from csv')
        self.peril_gbx = QGroupBox('Peril')
        self.peril_vlayout = QVBoxLayout()
        self.perils = self.multi_peril_csv_dict.keys()
        self.peril_gbx.setLayout(self.peril_vlayout)
        for peril in self.perils:
            chk = QCheckBox(peril)
            chk.setChecked(True)
            self.peril_vlayout.addWidget(chk)
        self.higher_on_top_chk = QCheckBox('Render higher values on top')
        self.higher_on_top_chk.setChecked(False)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.peril_gbx)
        vlayout.addWidget(self.higher_on_top_chk)
        vlayout.addWidget(self.button_box)
        self.setLayout(vlayout)

    @staticmethod
    def get_ini_str(filepath):
        zfile = zipfile.ZipFile(filepath)
        for fname in zfile.namelist():
            if os.path.splitext(fname)[1] == '.ini':
                ini_str = zfile.open(
                    zfile.NameToInfo[fname]).read().decode('utf8')
                break
        return ini_str

    @staticmethod
    def get_multi_peril_csv_dict(ini_str):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read_string(ini_str)
        multi_peril_csv_str = None
        for key in config:
            if 'multi_peril_csv' in config[key]:
                multi_peril_csv_str = config[key]['multi_peril_csv']
                break
        if multi_peril_csv_str is None:
            raise KeyError('multi_peril_csv not found in .ini file')
        multi_peril_csv_dict = json.loads(
            multi_peril_csv_str.replace('\'', '"'))
        return multi_peril_csv_dict

    def load_from_csv(self, csv_path, peril):
        # extract the name of the csv file and remove the extension
        layer_name, ext = os.path.splitext(os.path.basename(csv_path))
        wkt_field = None
        headers = get_headers(csv_path)
        for header in headers:
            if header.lower() in GEOM_FIELDNAMES:
                wkt_field = header
                break
        try:
            self.layer = import_layer_from_csv(
                self, csv_path, layer_name, self.iface, wkt_field=wkt_field,
                add_to_legend=True, add_on_top=True, zoom_to_layer=True)
        except RuntimeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            raise exc
        if 'intensity' in [field.name() for field in self.layer.fields()]:
            LoadOutputAsLayerDialog.style_maps(
                self.layer, 'intensity', self.iface, 'input',
                render_higher_on_top=self.higher_on_top_chk.isChecked())
        user_params = {'peril': peril}
        write_metadata_to_layer(
            self.drive_engine_dlg, 'input', self.layer, user_params)
        log_msg('Layer %s was loaded successfully' % layer_name,
                level='S', message_bar=self.iface.messageBar())

    def accept(self):
        super().accept()
        for chk in self.peril_gbx.findChildren(QCheckBox):
            if chk.isChecked():
                peril = chk.text()
                zfile = zipfile.ZipFile(self.zip_filepath)
                extracted_csv_path = zfile.extract(
                    self.multi_peril_csv_dict[peril],
                    path=os.path.dirname(self.zip_filepath))
                self.load_from_csv(extracted_csv_path, peril)
        self.loading_completed.emit()

    def reject(self):
        super().reject()
        self.loading_canceled.emit()
