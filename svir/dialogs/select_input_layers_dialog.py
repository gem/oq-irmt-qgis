from builtins import str
# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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

# create the dialog for zoom to point
import os.path
from qgis.core import (QgsVectorLayer,
                       QGis,
                       QgsRasterLayer,
                       QgsMapLayerRegistry,
                       QgsVectorFileWriter,
                       QgsMapLayer,
                       )

from qgis.PyQt.QtCore import pyqtSlot, QDir, QUrl, QSettings, QFileInfo

from qgis.PyQt.QtWidgets import QFileDialog, QDialog, QDialogButtonBox, QMessageBox
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats,
    purge_zones_without_loss_points)

from svir.calculations.process_layer import ProcessLayer
from svir.dialogs.attribute_selection_dialog import AttributeSelectionDialog
from svir.utilities.utils import (tr,
                                  count_heading_commented_lines,
                                  get_ui_class,
                                  log_msg,
                                  save_layer_as_shapefile,
                                  )

FORM_CLASS = get_ui_class('ui_select_input_layers.ui')


class SelectInputLayersDialog(QDialog, FORM_CLASS):
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
        self.setupUi(self)
        # Disable ok_button until loss and zonal layers are selected
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.loss_layer_is_vector = True
        self.populate_cbx()

    def open_file_dialog(self, dialog_type):
        """
        Open a file dialog to select the data file to be loaded
        :param string dialog_type: 'loss_layer' or 'zonal_layer'
        :returns: a layer
        """
        if dialog_type == 'loss_layer':
            text = self.tr('Select loss map to import')
            # FIXME: What should be the format of the raster maps?
            filters = self.tr('Loss curves from the OpenQuake-engine (*.csv);;'
                              'Shapefile vector loss curves (*.shp);;'
                              'Geojson vector loss curves (*.geojson);;'
                              'Raster loss curves (*.*)')
        elif dialog_type == 'zonal_layer':
            text = self.tr('Select zonal layer to import')
            filters = self.tr('Vector shapefiles (*.shp);;SQLite (*.sqlite);;'
                              'All files (*.*)')
        else:
            raise RuntimeError('Invalid dialog_type: {}'.format(dialog_type))
        default_dir = QSettings().value('irmt/select_layer_dir',
                                        QDir.homePath())
        file_name, file_type = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if dialog_type == 'zonal_layer':
            if not file_name:
                return None
            selected_dir = QFileInfo(file_name).dir().path()
            QSettings().setValue('irmt/select_layer_dir', selected_dir)
            layer = self.load_zonal_layer(file_name)
        elif dialog_type == 'loss_layer':
            if not file_name:
                return None
            selected_dir = QFileInfo(file_name).dir().path()
            QSettings().setValue('irmt/select_layer_dir', selected_dir)
            if file_type == 'Raster loss curves (*.*)':
                self.loss_layer_is_vector = False
            if file_type == 'Loss curves from the OpenQuake-engine (*.csv)':
                layer = self.import_loss_layer_from_csv(file_name)
            else:
                layer = self.load_loss_layer(file_name)
        else:
            raise RuntimeError
        return layer

    def accept(self):
        loss_layer_id = self.loss_layer_cbx.itemData(
            self.loss_layer_cbx.currentIndex())
        loss_layer = QgsMapLayerRegistry.instance().mapLayer(
            loss_layer_id)
        zonal_layer_id = self.zonal_layer_cbx.itemData(
            self.zonal_layer_cbx.currentIndex())
        zonal_layer = QgsMapLayerRegistry.instance().mapLayer(
            zonal_layer_id)

        # if the two layers have different projections, display an error
        # message and return
        have_same_projection, check_projection_msg = ProcessLayer(
            loss_layer).has_same_projection_as(zonal_layer)
        if not have_same_projection:
            log_msg(check_projection_msg, level='C',
                    message_bar=self.iface.messageBar())
            return

        # check if loss layer is raster or vector (aggregating by zone
        # is different in the two cases)
        loss_layer_is_vector = self.loss_layer_is_vector

        # Open dialog to ask the user to specify attributes
        # * loss from loss_layer
        # * zone_id from loss_layer
        # * svi from zonal_layer
        # * zone_id from zonal_layer
        ret_val = self.attribute_selection(
            loss_layer, zonal_layer)
        if not ret_val:
            return
        (loss_attr_names,
         zone_id_in_losses_attr_name,
         zone_id_in_zones_attr_name) = ret_val
        # aggregate losses by zone (calculate count of points in the
        # zone, sum and average loss values for the same zone)
        try:
            res = calculate_zonal_stats(loss_layer,
                                        zonal_layer,
                                        loss_attr_names,
                                        loss_layer_is_vector,
                                        zone_id_in_losses_attr_name,
                                        zone_id_in_zones_attr_name,
                                        self.iface)
        except TypeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar())
            return
        (loss_layer, zonal_layer, loss_attrs_dict) = res

        if self.purge_chk.isChecked():
            purge_zones_without_loss_points(
                zonal_layer, loss_attrs_dict, self.iface)
        super(SelectInputLayersDialog, self).accept()

    @staticmethod
    def attribute_selection(loss_layer, zonal_layer):
        """
        Open a modal dialog containing combo boxes, allowing the user
        to select what are the attribute names for
        * loss values (from loss layer)
        * zone id (from loss layer)
        * zone id (from zonal layer)
        """
        dlg = AttributeSelectionDialog(loss_layer, zonal_layer)
        # if the user presses OK
        if dlg.exec_():
            return dlg.selected_attributes
        else:
            return False

    @pyqtSlot(int)
    def on_purge_chk_stateChanged(self, state):
        if state:
            reply = QMessageBox.question(
                self, 'Warning!',
                "Are you sure to delete the empty zones from the zonal layer?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.purge_chk.setCheckState(0)

    @pyqtSlot()
    def on_loss_layer_tbn_clicked(self):
        layer = self.open_file_dialog('loss_layer')
        if layer and layer.geometryType() == QGis.Point:
            cbx = self.loss_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    @pyqtSlot()
    def on_zonal_layer_tbn_clicked(self):
        layer = self.open_file_dialog('zonal_layer')
        if layer and layer.geometryType() == QGis.Polygon:
            cbx = self.zonal_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    def populate_cbx(self):
        for key, layer in \
                QgsMapLayerRegistry.instance().mapLayers().items():
            # populate loss cbx only with layers containing points
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            if layer.geometryType() == QGis.Point:
                self.loss_layer_cbx.addItem(layer.name())
                self.loss_layer_cbx.setItemData(
                    self.loss_layer_cbx.count()-1, layer.id())
            if layer.geometryType() == QGis.Polygon:
                self.zonal_layer_cbx.addItem(layer.name())
                self.zonal_layer_cbx.setItemData(
                    self.zonal_layer_cbx.count()-1, layer.id())
        self.enable_ok_button_if_both_layers_are_specified()

    def enable_ok_button_if_both_layers_are_specified(self):
        if self.loss_layer_cbx.currentText() and \
                self.zonal_layer_cbx.currentText():
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def import_loss_layer_from_csv(self,
                                   csv_file_path,
                                   dest_shp=None,
                                   delete_lon_lat=False):
        # FIXME: hardcoded field names
        longitude_field = 'LON'
        latitude_field = 'LAT'
        lines_to_skip_count = count_heading_commented_lines(csv_file_path)
        url = QUrl.fromLocalFile(csv_file_path)
        url.addQueryItem('type', 'csv')
        url.addQueryItem('xField', longitude_field)
        url.addQueryItem('yField', latitude_field)
        url.addQueryItem('spatialIndex', 'no')
        url.addQueryItem('subsetIndex', 'no')
        url.addQueryItem('watchFile', 'no')
        url.addQueryItem('delimiter', ',')
        url.addQueryItem('crs', 'epsg:4326')
        url.addQueryItem('skipLines', str(lines_to_skip_count))
        url.addQueryItem('trimFields', 'yes')
        layer_uri = str(url.toEncoded())
        csv_layer = QgsVectorLayer(layer_uri, 'Loss', "delimitedtext")
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
        result = save_layer_as_shapefile(csv_layer, dest_filename)
        if result != QgsVectorFileWriter.NoError:
            raise RuntimeError('Could not save shapefile')
        shp_layer = QgsVectorLayer(
            dest_filename, 'Loss data', 'ogr')
        if delete_lon_lat:
            ProcessLayer(shp_layer).delete_attributes(
                [longitude_field, latitude_field]),
        if shp_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(shp_layer)
        else:
            msg = 'Invalid loss map'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        return shp_layer

    def load_loss_layer(self, loss_layer_path):
        # Load loss layer
        if self.loss_layer_is_vector:
            loss_layer = QgsVectorLayer(loss_layer_path, tr('Loss map'), 'ogr')
            if not loss_layer.geometryType() == QGis.Point:
                msg = 'Loss map must contain points'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
                return False
        else:
            loss_layer = QgsRasterLayer(loss_layer_path, tr('Loss map'))
        # Add loss layer to registry
        if loss_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(loss_layer)
        else:
            msg = 'Invalid loss map'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        # Zoom depending on the zonal layer's extent
        return loss_layer

    def load_zonal_layer(self, zonal_layer_path):
        # Load zonal layer
        zonal_layer = QgsVectorLayer(zonal_layer_path, tr('Zonal data'), 'ogr')
        if not zonal_layer.geometryType() == QGis.Polygon:
            msg = 'Zonal layer must contain zone polygons'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return False
        # Add zonal layer to registry
        if zonal_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(zonal_layer)
        else:
            msg = 'Invalid zonal layer'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        return zonal_layer
