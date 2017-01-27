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
import csv
from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsSymbolV2,
                       QgsVectorGradientColorRampV2,
                       QgsGraduatedSymbolRendererV2,
                       QgsRendererRangeV2,
                       QgsVectorFileWriter,
                       )
from PyQt4.QtCore import pyqtSlot, QDir, QUrl, QSettings, QFileInfo

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         )
from svir.utilities.utils import get_ui_class, log_msg

FORM_CLASS = get_ui_class('ui_load_csv_as_layer.ui')


class LoadCsvAsLayerDialog(QDialog, FORM_CLASS):
    """
    """
    def __init__(self, iface, csv_path=None):
        self.iface = iface
        self.csv_path = csv_path
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        if self.csv_path:
            self.csv_path_le.setText(self.csv_path)
            self.dmg_state_cbx.setEnabled(True)
            self.loss_type_cbx.setEnabled(True)
            loss_types, damage_states = \
                self.read_loss_types_and_damage_states_from_csv_header(
                    self.csv_path)
            self.populate_loss_type_cbx(loss_types)
            self.populate_dmg_state_cbx(damage_states)

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.csv_path = self.open_file_dialog()

    @pyqtSlot(str)
    def on_dmg_state_cbx_currentIndexChanged(self):
        self.set_ok_button()

    @pyqtSlot(str)
    def on_loss_type_cbx_currentIndexChanged(self):
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select CSV file or archive to import')
        filters = self.tr('CSV (*.csv)')
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        csv_path, self.file_type = QFileDialog.getOpenFileNameAndFilter(
            self, text, default_dir, filters)
        if not csv_path:
            return
        selected_dir = QFileInfo(csv_path).dir().path()
        QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
        self.csv_path = csv_path
        self.csv_path_le.setText(self.csv_path)
        # read the header of the csv, so we can select from its fields
        loss_types, damage_states = \
            self.read_loss_types_and_damage_states_from_csv_header(
                self.csv_path)
        self.populate_loss_type_cbx(loss_types)
        self.populate_dmg_state_cbx(damage_states)

    def read_loss_types_and_damage_states_from_csv_header(self, csv_path):
        with open(csv_path, "rb") as source:
            reader = csv.reader(source)
            self.csv_header = reader.next()
            # ignore asset_ref, taxonomy, lon, lat
            names = self.csv_header[4:]
            # extract from column names such as: structural~no_damage_mean
            loss_types = set([name.split('~')[0] for name in names])
            damage_states = set(['_'.join(name.split('~')[1].split('_')[:-1])
                                 for name in names])
            return list(loss_types), list(damage_states)

    def import_layer_from_csv(self,
                              csv_path,
                              dest_shp=None):
        longitude_field = 'lon'
        latitude_field = 'lat'
        # lines_to_skip_count = 0
        url = QUrl.fromLocalFile(csv_path)
        url.addQueryItem('type', 'csv')
        url.addQueryItem('xField', longitude_field)
        url.addQueryItem('yField', latitude_field)
        url.addQueryItem('spatialIndex', 'no')
        url.addQueryItem('subsetIndex', 'no')
        url.addQueryItem('watchFile', 'no')
        url.addQueryItem('delimiter', ',')
        url.addQueryItem('crs', 'epsg:4326')
        # url.addQueryItem('skipLines', str(lines_to_skip_count))
        url.addQueryItem('trimFields', 'yes')
        layer_uri = str(url.toEncoded())
        csv_layer = QgsVectorLayer(layer_uri, 'dmg_by_asset', "delimitedtext")
        dest_filename = dest_shp or QFileDialog.getSaveFileName(
            self,
            'Save loss shapefile as...',
            os.path.expanduser("~"),
            'Shapefiles (*.shp)')
        if dest_filename:
            if dest_filename[-4:] != ".shp":
                dest_filename += ".shp"
        else:
            return
        result = QgsVectorFileWriter.writeAsVectorFormat(
            csv_layer, dest_filename, 'CP1250',
            None, 'ESRI Shapefile')
        if result != QgsVectorFileWriter.NoError:
            raise RuntimeError('Could not save shapefile')
        shp_layer = QgsVectorLayer(
            dest_filename, 'Damage by asset', 'ogr')
        if shp_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(shp_layer)
        else:
            msg = 'Invalid loss map'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        return shp_layer

    def populate_dmg_state_cbx(self, damage_states):
        self.dmg_state_cbx.clear()
        self.dmg_state_cbx.setEnabled(True)
        self.dmg_state_cbx.addItems(damage_states)

    def populate_loss_type_cbx(self, loss_types):
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(loss_types)

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.dmg_state_cbx.currentIndex != -1
            and self.loss_type_cbx.currentIndex != -1)

    def style_layer(self, layer, field_name):
        color1 = QColor("#FFEBEB")
        color2 = QColor("red")
        classes_count = 10
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol = symbol.createSimple({'outline_width': '0.000001'})
        symbol.setAlpha(1)  # opacity
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            layer,
            field_name,
            classes_count,
            # QgsGraduatedSymbolRendererV2.Quantile,
            QgsGraduatedSymbolRendererV2.EqualInterval,
            symbol,
            ramp)
        graduated_renderer.updateRangeLowerValue(0, 0.0)
        symbol_zeros = QgsSymbolV2.defaultSymbol(layer.geometryType())
        symbol_zeros = symbol.createSimple({'outline_width': '0.000001'})
        symbol_zeros.setColor(QColor(222, 255, 222))
        zeros_min = 0.0
        zeros_max = 0.0
        range_zeros = QgsRendererRangeV2(
            zeros_min, zeros_max, symbol_zeros,
            " %.4f - %.4f" % (zeros_min, zeros_max), True)
        graduated_renderer.addClassRange(range_zeros)
        graduated_renderer.moveClass(classes_count, 0)
        layer.setRendererV2(graduated_renderer)
        layer.setLayerTransparency(30)  # percent
        layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(layer)
        self.iface.mapCanvas().refresh()

    def accept(self):
        layer = self.import_layer_from_csv(self.csv_path_le.text())
        damage_state = self.dmg_state_cbx.currentText()
        loss_type = self.loss_type_cbx.currentText()
        field_idx = -1  # default
        for idx, name in enumerate(self.csv_header):
            if damage_state in name and loss_type in name and 'mean' in name:
                field_idx = idx
        # FIXME: remove prints
        print self.csv_header
        print [field.name() for field in layer.dataProvider().fields()]
        print 'field_idx = %s' % field_idx
        field_name = layer.dataProvider().fields()[field_idx].name()
        self.style_layer(layer, field_name)
        super(LoadCsvAsLayerDialog, self).accept()
