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
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SvirDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)

    def open_file_dialog(self, dialog_type):
        print 'here'
        if dialog_type == 'loss_map':
            text = self.tr('Select loss map')
            filters = self.tr('Loss maps (*.shp);; All files (*.*)')
        elif dialog_type == 'aggregation_layer':
            text = self.tr('Select aggregation layer')
            filters = self.tr('Aggregation layers (*.shp);; All files (*.*)')
        else:
            raise RuntimeError

        return QFileDialog.getOpenFileName(self,
                                               text,
                                               os.path.expanduser('~'),
                                               filters)

    @pyqtSlot()
    def on_input_layer_tbn_clicked(self):
        file_loss_map = self.open_file_dialog('loss_map')
        self.ui.input_layer_le.setText(file_loss_map)
        self.enable_ok_button()

    @pyqtSlot()
    def on_aggregation_layer_tbn_clicked(self):
        file_aggregation_layer = self.open_file_dialog('aggregation_layer')
        self.ui.aggregation_layer_le.setText(file_aggregation_layer)
        self.enable_ok_button()

    def enable_ok_button(self):
        if (os.path.isfile(self.ui.input_layer_le.text())
                and os.path.isfile(self.ui.aggregation_layer_le.text())):
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)