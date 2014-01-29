# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
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
import os
from PyQt4.QtCore import pyqtSlot, QDir
from PyQt4.QtGui import (QFileDialog,
                         QDialog,
                         QDialogButtonBox)
from qgis.core import QgsVectorLayer, QGis, QgsRasterLayer, QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from ui_svir import Ui_SvirDialog
from utils import tr

class SvirDialog(QDialog):
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
        self.ui = Ui_SvirDialog()
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
            filters = self.tr('Geojson vector loss maps (*.geojson);; '
                              'Shapefile vector loss maps (*.shp);; '
                              'Raster loss maps (*.*)')
        elif dialog_type == 'zonal_layer':
            text = self.tr('Select zonal layer to import')
            filters = self.tr('Vector shapefiles (*.shp);; SQLite (*.sqlite);;'
                              ' All files (*.*)')
        else:
            raise RuntimeError('Invalid dialog_type: {}'.format(dialog_type))
        file_name, file_type = QFileDialog.getOpenFileNameAndFilter(
            self, text, QDir.homePath(), filters)
        if file_name is not None:
            if dialog_type == 'zonal_layer':
                layer = self.load_zonal_layer(file_name)
            elif dialog_type == 'loss_layer':
                if file_type == 'Raster loss maps (*.*)':
                    self.loss_layer_is_vector = False
                layer = self.load_loss_layer(file_name)
            else:
                raise RuntimeError
            return layer
        else:
            return None

    @pyqtSlot()
    def on_loss_layer_tbn_clicked(self):
        layer = self.open_file_dialog('loss_layer')
        if layer:
            cbx = self.ui.loss_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    @pyqtSlot()
    def on_zonal_layer_tbn_clicked(self):
        layer = self.open_file_dialog('zonal_layer')
        if layer:
            cbx = self.ui.zonal_layer_cbx
            cbx.addItem(layer.name())
            last_index = cbx.count() - 1
            cbx.setItemData(last_index, layer.id())
            cbx.setCurrentIndex(last_index)
        self.enable_ok_button_if_both_layers_are_specified()

    def populate_cbx(self):
        for key, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            self.ui.loss_layer_cbx.addItem(layer.name())
            self.ui.loss_layer_cbx.setItemData(
                self.ui.loss_layer_cbx.count()-1, layer.id())
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

    def load_loss_layer(self, loss_layer_path):
        # Load loss layer
        if self.loss_layer_is_vector:
            loss_layer = QgsVectorLayer(loss_layer_path,
                                             tr('Loss map'), 'ogr')
            if not loss_layer.geometryType() == QGis.Point:
                msg = 'Loss map must contain points'
                self.iface.messageBar().pushMessage(
                    tr("Error"),
                    tr(msg),
                    level=QgsMessageBar.CRITICAL)
                return False
        else:
            loss_layer = QgsRasterLayer(loss_layer_path,
                                             tr('Loss map'))
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
        zonal_layer = QgsVectorLayer(zonal_layer_path,
                                          tr('Zonal data'), 'ogr')
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
