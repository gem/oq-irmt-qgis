
# -*- coding: utf-8 -*-
# /***************************************************************************
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

import os
import zipfile
import tempfile
from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsSymbolV2,
                       QgsVectorGradientColorRampV2,
                       QgsGraduatedSymbolRendererV2,
                       QgsRendererRangeV2,
                       )
from PyQt4.QtCore import pyqtSlot, QDir, QSettings, QFileInfo

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         )
from svir.utilities.utils import get_ui_class, log_msg

FORM_CLASS = get_ui_class('ui_load_geojson_as_layer.ui')


class LoadGeoJsonAsLayerDialog(QDialog, FORM_CLASS):
    """
    FIXME This is not working for zipfiles yet
    """
    def __init__(self, iface, geojson_path=None):
        self.iface = iface
        self.geojson_path = geojson_path
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        if self.geojson_path:
            self.geojson_path_le.setText(self.geojson_path)
            self.rlz_cbx.setEnabled(True)
            self.imt_cbx.setEnabled(True)
            self.poe_cbx.setEnabled(True)
            self.populate_rlz_cbx()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.geojson_path = self.open_file_dialog()

    @pyqtSlot(str)
    def on_rlz_cbx_currentIndexChanged(self):
        rlz = self.rlz_cbx.currentText()
        self.imts = {}
        for pars in self.names_params.values():
            if pars['rlz'] != rlz:
                continue
            imt = pars['imt']
            poe = pars['poe']
            if imt not in self.imts:
                self.imts[imt] = [poe]
            else:
                self.imts[imt].append(poe)
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(self.imts.keys())

    @pyqtSlot(str)
    def on_imt_cbx_currentIndexChanged(self):
        imt = self.imt_cbx.currentText()
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.imts[imt])

    @pyqtSlot(str)
    def on_poe_cbx_currentIndexChanged(self):
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select GeoJson file or archive to import')
        # FIXME: still not working for zip archives
        # filters = self.tr('GeoJson maps (*.geojson);;'
        #                   'Zip archives (*.zip)')
        filters = self.tr('GeoJson maps (*.geojson)')
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        geojson_path, self.file_type = QFileDialog.getOpenFileNameAndFilter(
            self, text, default_dir, filters)
        if not geojson_path:
            return
        selected_dir = QFileInfo(geojson_path).dir().path()
        QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
        self.geojson_path = geojson_path
        self.geojson_path_le.setText(self.geojson_path)
        if self.file_type == self.tr('Zip archives (*.zip)'):
            zz = zipfile.ZipFile(self.geojson_path, 'r')
            namelist = zz.namelist()
            self.names_params = {}
            for name in namelist:
                # Example: hazard_map-0.1-SA(0.2)-rlz-000_24.geojson
                _, poe, imt, _, end = name.split('-')
                rlz = end.split('_')[0]
                self.names_params[name] = dict(rlz=rlz, imt=imt, poe=poe)
            # rlzs = set(value['rlz'] for value in names_params.values())
            zz.close()
            self.populate_rlz_cbx()
        self.load_layer(geojson_path)

    def load_layer(self, geojson_path):
        base_name = os.path.basename(geojson_path)
        layer_name, ext = os.path.splitext(base_name)
        self.layer = QgsVectorLayer(geojson_path, layer_name, 'ogr')
        if self.layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(self.layer)
            self.field_name = self.layer.dataProvider().fields()[0].name()
            self.style_layer()
            msg = 'Layer [%s] successfully loaded' % layer_name
            log_msg(msg, level='I', message_bar=self.iface.messageBar())
            self.accept()
        else:
            msg = 'Invalid geojson'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def populate_rlz_cbx(self):
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        rlzs = list(set(value['rlz'] for value in self.names_params.values()))
        self.rlz_cbx.addItems(rlzs)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.poe_cbx.currentIndex != -1)

    def style_layer(self):
        color1 = QColor("#FFEBEB")
        color2 = QColor("red")
        classes_count = 10
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol = symbol.createSimple({'outline_width': '0.000001'})
        symbol.setAlpha(1)  # opacity
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            self.layer,
            self.field_name,
            classes_count,
            # QgsGraduatedSymbolRendererV2.Quantile,
            QgsGraduatedSymbolRendererV2.EqualInterval,
            symbol,
            ramp)
        graduated_renderer.updateRangeLowerValue(0, 0.0)
        symbol_zeros = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol_zeros = symbol.createSimple({'outline_width': '0.000001'})
        symbol_zeros.setColor(QColor(222, 255, 222))
        zeros_min = 0.0
        zeros_max = 0.0
        range_zeros = QgsRendererRangeV2(
            zeros_min, zeros_max, symbol_zeros,
            " %.4f - %.4f" % (zeros_min, zeros_max), True)
        graduated_renderer.addClassRange(range_zeros)
        graduated_renderer.moveClass(classes_count, 0)
        self.layer.setRendererV2(graduated_renderer)
        self.layer.setLayerTransparency(30)  # percent
        self.layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(
            self.layer)
        self.iface.mapCanvas().refresh()

    def accept(self):
        if self.file_type == self.tr('Zip archives (*.zip)'):
            rlz = self.rlz_cbx.currentText()
            imt = self.imt_cbx.currentText()
            poe = self.poe_cbx.currentText()
            [filename] = [
                name for name, params in self.names_params.iteritems()
                if params['rlz'] == rlz
                and params['imt'] == imt
                and params['poe'] == poe]
            self.geojson_path = self.geojson_path_le.text()
            zz = zipfile.ZipFile(self.geojson_path, 'r')
            dest_folder = tempfile.gettempdir()
            dest_file = zz.extract(filename, dest_folder)
            zz.close()
            self.load_layer(dest_file)
        super(LoadGeoJsonAsLayerDialog, self).accept()
