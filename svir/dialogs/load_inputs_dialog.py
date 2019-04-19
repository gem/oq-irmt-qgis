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

# import os
# import tempfile
import zipfile
import json
import os
import configparser
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import (
    QDialog, QLabel, QComboBox, QVBoxLayout, QDialogButtonBox)
from svir.utilities.utils import import_layer_from_csv, log_msg


class LoadInputsDialog(QDialog):
    """
    Dialog to browse zipped input files
    """
    def __init__(self, zip_filepath, iface, parent=None):
        super().__init__(parent)
        self.zip_filepath = zip_filepath
        self.iface = iface
        ini_str = self.get_ini_str(self.zip_filepath)
        self.multi_peril_csv_dict = self.get_multi_peril_csv_dict(ini_str)
        self.setWindowTitle('Load peril data from csv')
        peril_lbl = QLabel('Peril')
        self.peril_cbx = QComboBox()
        self.peril_cbx.addItems(self.multi_peril_csv_dict.keys())
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        vlayout = QVBoxLayout()
        vlayout.addWidget(peril_lbl)
        vlayout.addWidget(self.peril_cbx)
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
        multi_peril_csv_str = config['volcano_hazard']['multi_peril_csv']
        multi_peril_csv_dict = json.loads(
            multi_peril_csv_str.replace('\'', '"'))
        return multi_peril_csv_dict

    def load_from_csv(self, csv_path):
        # extract the name of the csv file and remove the extension
        layer_name = os.path.splitext(os.path.basename(csv_path))[0]
        try:
            self.layer = import_layer_from_csv(
                self, csv_path, layer_name, self.iface)
        except RuntimeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            return
        # self.style_maps(layer=self.layer, style_by='intensity')
        QgsProject.instance().addMapLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()
        # log_msg('Layer %s was loaded successfully' % layer_name,
        #         level='S', message_bar=self.iface.messageBar())

    def accept(self):
        log_msg('Ok clicked', message_bar=self.iface.messageBar())
        chosen_peril = self.peril_cbx.currentText()
        zfile = zipfile.ZipFile(self.zip_filepath)
        extracted_csv_path = zfile.extract(
            self.multi_peril_csv_dict[chosen_peril],
            path=os.path.dirname(self.zip_filepath))
        self.load_from_csv(extracted_csv_path)
        super().accept()

    def reject(self):
        log_msg('Cancel clicked', message_bar=self.iface.messageBar())
        super().reject()
