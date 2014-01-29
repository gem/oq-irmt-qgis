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
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayerRegistry

from ui_normalization import Ui_NormalizationDialog
from normalization_algs import RANK_VARIANTS

from globals import NUMERIC_FIELD_TYPES

class NormalizationDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    a layer and an attribute of the same layer, and then a normalization
    algorithm.
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        # Set up the user interface from Designer.
        self.ui = Ui_NormalizationDialog()
        self.ui.setupUi(self)
        if self.ui.algorithm_cbx.currentText() == 'RANK':
            self.reload_variant_cbx()
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.use_advanced = False

    @pyqtSlot()
    def on_calc_btn_clicked(self):
        self.close()
        layer = QgsMapLayerRegistry.instance().mapLayers().values()[
            self.ui.layer_cbx.currentIndex()]
        self.iface.setActiveLayer(layer)

        # layer is put in editing mode. If the user clicks on ok, the field
        # calculator will update the layers attributes.
        # if the user clicks cancel, the field calculator does nothing.
        # the layer stays in editing mode with the use_advanced flag set.
        # the calling code should take care of doing layer.commitChanges()
        # if the flag is set to true.
        self.use_advanced = True
        layer.startEditing()
        self.iface.actionOpenFieldCalculator().trigger()

    @pyqtSlot(str)
    def on_layer_cbx_currentIndexChanged(self):
        self.reload_attrib_cbx()

    @pyqtSlot(str)
    def on_algorithm_cbx_currentIndexChanged(self):
        self.reload_variant_cbx()

    def reload_attrib_cbx(self):
        # reset combo box
        self.ui.attrib_cbx.clear()
        # populate attribute combo box with the list of attributes of the
        # layer specified in the other combo box
        layer = QgsMapLayerRegistry.instance().mapLayers().values()[
            self.ui.layer_cbx.currentIndex()]
        # populate combo boxes with field names taken by layers
        dp = layer.dataProvider()
        fields = list(dp.fields())
        no_numeric_fields = True
        for field in fields:
            # add numeric fields only
            if field.typeName() in NUMERIC_FIELD_TYPES:
                self.ui.attrib_cbx.addItem(field.name())
                no_numeric_fields = False
        self.ok_button.setDisabled(no_numeric_fields)

    def reload_variant_cbx(self):
        self.ui.variant_cbx.clear()
        if self.ui.algorithm_cbx.currentText() == 'RANK':
            self.ui.variant_cbx.addItems(RANK_VARIANTS)
        else:
            self.ui.variant_cbx.setDisabled(True)
