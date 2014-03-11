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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox
from qgis.core import QgsMapLayerRegistry

from ui.ui_select_layers_to_merge import Ui_SelectLayersToMergeDialog
from globals import (NUMERIC_FIELD_TYPES,
                     TEXTUAL_FIELD_TYPES)


class SelectLayersToMergeDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    a layer containing loss data and one containing SVI data, that will be
    joined in the SVIR layer
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SelectLayersToMergeDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

    @pyqtSlot(str)
    def on_loss_layer_cbox_currentIndexChanged(self):
        self.reload_aggr_loss_attrib_and_merge_attr_cbx()

    def reload_aggr_loss_attrib_and_merge_attr_cbx(self):
        self.ui.aggr_loss_attr_cbox.clear()
        self.ui.merge_attr_cbx.clear()
        # populate attribute combo boxes with the list of attributes of the
        # layer specified in the loss_layer combo box
        layer = QgsMapLayerRegistry.instance().mapLayers().values()[
            self.ui.loss_layer_cbox.currentIndex()]
        # populate combo boxes with field names taken by layers
        dp = layer.dataProvider()
        fields = list(dp.fields())
        no_numeric_fields = True
        no_string_fields = True
        for field in fields:
            # add to loss attribute cbx numeric fields only
            if field.typeName() in NUMERIC_FIELD_TYPES:
                self.ui.aggr_loss_attr_cbox.addItem(field.name())
                no_numeric_fields = False
            # add to merge attribute cbx string fields only
            if field.typeName() in TEXTUAL_FIELD_TYPES:
                self.ui.merge_attr_cbx.addItem(field.name())
                no_string_fields = False
        self.ok_button.setDisabled(no_numeric_fields)
        self.ok_button.setDisabled(no_string_fields)
