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
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayerRegistry, QgsMapLayer

from ui.ui_transformation import Ui_TransformationDialog
from transformation_algs import (RANK_VARIANTS,
                                 QUADRATIC_VARIANTS,
                                 LOG10_VARIANTS,
                                 TRANSFORMATION_ALGS)

from globals import NUMERIC_FIELD_TYPES
from utils import reload_attrib_cbx, reload_layers_in_cbx
from process_layer import ProcessLayer


class TransformationDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    a layer and an attribute of the same layer, and then a transformation
    algorithm and one of its variants (if the algorithm has any).
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.attr_name_user_def = False
        self.use_advanced = False
        self.selected_layer = None
        # Set up the user interface from Designer.
        self.ui = Ui_TransformationDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        reload_layers_in_cbx(self.ui.layer_cbx, [QgsMapLayer.VectorLayer])

        # In case one of the available layers is active, preselect it
        if iface.activeLayer():
            active_layer_name = iface.activeLayer().name()
            active_layer_index = self.ui.layer_cbx.findText(active_layer_name)
            self.ui.layer_cbx.setCurrentIndex(active_layer_index)
            self.selected_layer = \
                QgsMapLayerRegistry.instance().mapLayers().values()[
                    self.ui.layer_cbx.currentIndex()]
        else:
            self.ui.layer_cbx.blockSignals(True)
            self.ui.layer_cbx.setCurrentIndex(-1)
            self.ui.layer_cbx.blockSignals(False)
            self.ui.attrib_cbx.clear()
            self.ok_button.setDisabled(True)
        alg_list = TRANSFORMATION_ALGS.keys()
        self.ui.algorithm_cbx.addItems(alg_list)
        if self.ui.algorithm_cbx.currentText() in ['RANK', 'QUADRATIC']:
            self.reload_variant_cbx()
        self.ui.inverse_ckb.setDisabled(
            self.ui.algorithm_cbx.currentText() in ['LOG10'])

    @pyqtSlot()
    def on_calc_btn_clicked(self):
        self.close()
        self.selected_layer = \
            QgsMapLayerRegistry.instance().mapLayers().values()[
                self.ui.layer_cbx.currentIndex()]
        self.iface.setActiveLayer(self.selected_layer)

        # layer is put in editing mode. If the user clicks on ok, the field
        # calculator will update the layers attributes.
        # if the user clicks cancel, the field calculator does nothing.
        # the layer stays in editing mode with the use_advanced flag set.
        # the calling code should take care of doing layer.commitChanges()
        # if the flag is set to true.
        self.use_advanced = True
        self.selected_layer.startEditing()
        self.iface.actionOpenFieldCalculator().trigger()

    @pyqtSlot(str)
    def on_layer_cbx_currentIndexChanged(self):
        self.selected_layer = \
            QgsMapLayerRegistry.instance().mapLayers().values()[
                self.ui.layer_cbx.currentIndex()]
        reload_attrib_cbx(self.ui.attrib_cbx,
                          self.selected_layer,
                          NUMERIC_FIELD_TYPES)
        if self.ui.attrib_cbx.count():
            self.ok_button.setEnabled(True)
            if self.ui.algorithm_cbx.count():
                self.update_default_fieldname()

    @pyqtSlot(str)
    def on_algorithm_cbx_currentIndexChanged(self):
        self.reload_variant_cbx()
        self.update_default_fieldname()

    @pyqtSlot(str)
    def on_variant_cbx_currentIndexChanged(self):
        self.update_default_fieldname()

    @pyqtSlot()
    def on_new_field_name_txt_editingFinished(self):
        self.attr_name_user_def = True
        if not self.ui.new_field_name_txt.text():
            self.update_default_fieldname()

    def reload_variant_cbx(self):
        self.ui.variant_cbx.clear()
        self.ui.variant_cbx.setEnabled(True)
        if self.ui.algorithm_cbx.currentText() == 'RANK':
            self.ui.variant_cbx.addItems(RANK_VARIANTS)
        elif self.ui.algorithm_cbx.currentText() == 'QUADRATIC':
            self.ui.variant_cbx.addItems(QUADRATIC_VARIANTS)
        elif self.ui.algorithm_cbx.currentText() == 'LOG10':
            self.ui.variant_cbx.addItems(LOG10_VARIANTS)
        else:
            self.ui.variant_cbx.setDisabled(True)
        self.ui.inverse_ckb.setDisabled(
            self.ui.algorithm_cbx.currentText() in ['LOG10'])

    def update_default_fieldname(self):
        if (not self.attr_name_user_def
                or not self.ui.new_field_name_txt.text()):
            attribute_name = self.ui.attrib_cbx.currentText()
            algorithm_name = self.ui.algorithm_cbx.currentText()
            variant = self.ui.variant_cbx.currentText()
            inverse = self.ui.inverse_ckb.isChecked()
            new_attr_name = \
                ProcessLayer(self.selected_layer).transform_attribute(
                    attribute_name, algorithm_name, variant,
                    inverse, simulate=True)
            self.ui.new_field_name_txt.setText(new_attr_name)
            self.attr_name_user_def = False
