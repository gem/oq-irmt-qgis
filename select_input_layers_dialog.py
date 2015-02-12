# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014-2015 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/
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
"""

# create the dialog for zoom to point
import os.path
from PyQt4.QtCore import pyqtSlot, QDir
from PyQt4.QtGui import (QFileDialog,
                         QDialog,
                         QDialogButtonBox,
                         QMessageBox)
from qgis.core import (QgsVectorLayer,
                       QGis,
                       QgsRasterLayer,
                       QgsMapLayerRegistry,
                       QgsVectorFileWriter,
                       )
from qgis.gui import QgsMessageBar
from process_layer import ProcessLayer
from ui.ui_select_input_layers import Ui_SelectInputLayersDialog
from utils import tr, count_heading_commented_lines


class SelectInputLayersDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SelectInputLayersDialog()
        self.ui.setupUi(self)
        # Disable ok_button until loss and zonal layers are selected
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.loss_layer_is_vector = True
        self.populate_cbx()

    def open_file_dialog(self, dialog_type):
        """
        Open a file dialog to select the data file to be loaded
        :param string dialog_type:
            Valid types are 'loss_layer' or 'zonal_layer'
        :returns:
        """
        if dialog_type == 'loss_layer':
            text = self.tr('Select loss map to import')
            # FIXME: What should be the format of the raster maps?
            filters = self.tr('Geojson vector loss maps (*.geojson);;'
                              'Shapefile vector loss maps (*.shp);;'
                              'Loss maps from the OpenQuake-engine (*.csv);;'
                              'Raster loss maps (*.*)')
        elif dialog_type == 'zonal_layer':
            text = self.tr('Select zonal layer to import')
            filters = self.tr('Vector shapefiles (*.shp);;SQLite (*.sqlite);;'
                              'All files (*.*)')
        else:
            raise RuntimeError('Invalid dialog_type: {}'.format(dialog_type))
        file_name, file_type = QFileDialog.getOpenFileNameAndFilter(
            self, text, QDir.homePath(), filters)
        if file_name:
            if dialog_type == 'zonal_layer':
                layer = self.load_zonal_layer(file_name)
            elif dialog_type == 'loss_layer':
                if file_type == 'Raster loss maps (*.*)':
                    self.loss_layer_is_vector = False
                if file_type == 'Loss maps from the OpenQuake-engine (*.csv)':
                    layer = self.import_loss_layer_from_csv(file_name)
                else:
                    layer = self.load_loss_layer(file_name)
            else:
                raise RuntimeError
            return layer
        else:
            return None

    @pyqtSlot(int)
    def on_purge_chk_stateChanged(self, state):
        if state:
            reply = QMessageBox.question(
                self, 'Warning!',
                "Are you sure to delete the empty zones from the zonal layer?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.ui.purge_chk.setCheckState(0)

    @pyqtSlot()
    def on_loss_layer_tbn_clicked(self):
        layer = self.open_file_dialog('loss_layer')
        if layer and ProcessLayer(layer).is_type_in(["point", "multipoint"]):
            cbx = self.ui.loss_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    @pyqtSlot()
    def on_zonal_layer_tbn_clicked(self):
        layer = self.open_file_dialog('zonal_layer')
        if layer and ProcessLayer(layer).is_type_in(
                ["polygon", "multipolygon"]):
            cbx = self.ui.zonal_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    def populate_cbx(self):
        for key, layer in \
                QgsMapLayerRegistry.instance().mapLayers().iteritems():
            # populate loss cbx only with layers containing points
            if ProcessLayer(layer).is_type_in(["point", "multipoint"]):
                self.ui.loss_layer_cbx.addItem(layer.name())
                self.ui.loss_layer_cbx.setItemData(
                    self.ui.loss_layer_cbx.count()-1, layer.id())
            if ProcessLayer(layer).is_type_in(["polygon", "multipolygon"]):
                self.ui.zonal_layer_cbx.addItem(layer.name())
                self.ui.zonal_layer_cbx.setItemData(
                    self.ui.zonal_layer_cbx.count()-1, layer.id())
        self.enable_ok_button_if_both_layers_are_specified()

    def enable_ok_button_if_both_layers_are_specified(self):
        if self.ui.loss_layer_cbx.currentText() and \
                self.ui.zonal_layer_cbx.currentText():
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def import_loss_layer_from_csv(self, csv_file_path):
        lines_to_skip_count = count_heading_commented_lines(csv_file_path)
        # FIXME: Use the actual attribute names exported by the engine
        longitude_field = 'LON'
        latitude_field = 'LAT'
        uri = ("file://%s?"
               "type=csv"
               "&xField=%s"
               "&yField=%s"
               "&spatialIndex=no"
               "&subsetIndex=no"
               "&watchFile=no"
               "&delimiter=,"
               "&crs=epsg:4326"
               "&skipLines=%s"
               "&trimFields=yes") % (csv_file_path,
                                     longitude_field,
                                     latitude_field,
                                     lines_to_skip_count)
        csv_layer = QgsVectorLayer(uri, 'Loss', "delimitedtext")
        dest_filename = QFileDialog.getSaveFileName(
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
            dest_filename, 'Loss data', 'ogr')
        ProcessLayer(shp_layer).delete_attributes(
            [longitude_field, latitude_field]),
        if shp_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(shp_layer)
        else:
            msg = 'Invalid loss map'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return None
        return shp_layer

    def load_loss_layer(self, loss_layer_path):
        # Load loss layer
        if self.loss_layer_is_vector:
            loss_layer = QgsVectorLayer(loss_layer_path, tr('Loss map'), 'ogr')
            if not loss_layer.geometryType() == QGis.Point:
                msg = 'Loss map must contain points'
                self.iface.messageBar().pushMessage(
                    tr("Error"),
                    tr(msg),
                    level=QgsMessageBar.CRITICAL)
                return False
        else:
            loss_layer = QgsRasterLayer(loss_layer_path, tr('Loss map'))
        # Add loss layer to registry
        if loss_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(loss_layer)
        else:
            msg = 'Invalid loss map'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return None
        # Zoom depending on the zonal layer's extent
        return loss_layer

    def load_zonal_layer(self, zonal_layer_path):
        # Load zonal layer
        zonal_layer = QgsVectorLayer(zonal_layer_path, tr('Zonal data'), 'ogr')
        if not zonal_layer.geometryType() == QGis.Polygon:
            msg = 'Zonal layer must contain zone polygons'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return False
        # Add zonal layer to registry
        if zonal_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(zonal_layer)
        else:
            msg = 'Invalid zonal layer'
            self.iface.messageBar().pushMessage(
                tr("Error"),
                tr(msg),
                level=QgsMessageBar.CRITICAL)
            return None
        return zonal_layer
