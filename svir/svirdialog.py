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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QFileDialog,
                         QDialog,
                         QDialogButtonBox)
from ui_svir import Ui_SvirDialog


class SvirDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the regions for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SvirDialog()
        self.ui.setupUi(self)
        # Disable ok_button until loss and regions layers are selected
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.loss_map_is_vector = True

    def open_file_dialog(self, dialog_type):
        """
        Open a file dialog to select the data file to be loaded
        :param string dialog_type:
            Valid types are 'loss_map' or 'regions_layer'
        :returns:
            file_name
            file_type:
                e.g. "Geojson vector loss maps (*.geojson)"
        """
        if dialog_type == 'loss_map':
            text = self.tr('Select loss map')
            # FIXME: What should be the format of the raster maps?
            filters = self.tr('Geojson vector loss maps (*.geojson);; '
                              'Shapefile vector loss maps (*.shp);; '
                              'Raster loss maps (*.*)')
        elif dialog_type == 'regions_layer':
            text = self.tr('Select regions layer')
            filters = self.tr('Vector shapefiles (*.shp);; SQLite (*.sqlite);;'
                              ' All files (*.*)')
        else:
            raise RuntimeError('Invalid dialog_type: {}'.format(dialog_type))
        dialog = QFileDialog(self, text, os.path.expanduser('~'), filters)
        dialog.setFileMode(QFileDialog.ExistingFile)
        if dialog.exec_():
            file_name = dialog.selectedFiles()[0]
            file_type = dialog.selectedNameFilter()
        return file_name, file_type

    @pyqtSlot()
    def on_loss_layer_tbn_clicked(self):
        file_loss_map, file_loss_map_type = self.open_file_dialog('loss_map')
        self.ui.loss_layer_le.setText(file_loss_map)
        if file_loss_map_type == 'Raster loss maps (*.*)':
            self.loss_map_is_vector = False
        self.enable_ok_button_if_both_layers_are_specified()

    @pyqtSlot()
    def on_regions_layer_tbn_clicked(self):
        file_regions_layer, _ = self.open_file_dialog('regions_layer')
        self.ui.regions_layer_le.setText(file_regions_layer)
        self.enable_ok_button_if_both_layers_are_specified()

    def enable_ok_button_if_both_layers_are_specified(self):
        if (os.path.isfile(self.ui.loss_layer_le.text())
                and os.path.isfile(self.ui.regions_layer_le.text())):
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)