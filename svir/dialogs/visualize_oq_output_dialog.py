
# -*- coding: utf-8 -*-
#/***************************************************************************
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
import h5py
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsPoint,
                       QgsGeometry,
                       QgsMapLayerRegistry,
                       QgsSymbolV2,
                       QgsVectorGradientColorRampV2,
                       QgsGraduatedSymbolRendererV2,
                       QgsRendererRangeV2,
                       )
from PyQt4.QtCore import pyqtSlot, QDir

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         )
# from openquake.baselib import h5py  # FIXME: we should import this instead
from svir.ui.ui_visualize_oq_output import Ui_VisualizeOqOutputDialog
from svir.utilities.shared import DEBUG
from svir.utilities.utils import LayerEditingManager
from svir.calculations.calculate_utils import add_numeric_attribute


class VisualizeOqOutputDialog(QDialog):
    """
    FIXME
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_VisualizeOqOutputDialog()
        self.ui.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.ui.open_hdfview_btn.setDisabled(True)

    @pyqtSlot(str)
    def on_hdf5_path_le_textChanged(self):
        self.ui.open_hdfview_btn.setDisabled(
            self.ui.hdf5_path_le.text() == '')

    @pyqtSlot()
    def on_open_hdfview_btn_clicked(self):
        file_path = self.ui.hdf5_path_le.text()
        if file_path:
            to_run = "hdfview " + file_path
            # FIXME make system independent
            os.system(to_run)

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.hdf5_path = self.open_file_dialog()

    @pyqtSlot(str)
    def on_rlz_cbx_currentIndexChanged(self):
        self.dataset = self.hmaps.get(self.ui.rlz_cbx.currentText())
        self.imts = {}
        for name in self.dataset.dtype.names[2:]:
            imt, poe = name.split('~')
            if imt not in self.imts:
                self.imts[imt] = [poe]
            else:
                self.imts[imt].append(poe)
        self.ui.imt_cbx.addItems(self.imts.keys())

    @pyqtSlot(str)
    def on_imt_cbx_currentIndexChanged(self):
        imt = self.ui.imt_cbx.currentText()
        self.ui.poe_cbx.addItems(self.imts[imt])

    @pyqtSlot(str)
    def on_poe_cbx_currentIndexChanged(self):
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select oq-engine output to import')
        filters = self.tr('HDF5 files (*.hdf5)')
        self.hdf5_path, _ = QFileDialog.getOpenFileNameAndFilter(
            self, text, QDir.homePath(), filters)
        self.ui.hdf5_path_le.setText(self.hdf5_path)
        self.populate_rlz_cbx()

    def populate_rlz_cbx(self):
        # with h5py.File(self.hdf5_path, 'r') as hf:
        self.hfile = h5py.File(self.hdf5_path, 'r')
        self.hmaps = self.hfile.get('hmaps')
        self.rlzs = self.hmaps.keys()
        self.ui.rlz_cbx.addItems(self.rlzs)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.ui.poe_cbx.currentIndex != -1)

    def build_layer(self):
        rlz = self.ui.rlz_cbx.currentText()
        imt = self.ui.imt_cbx.currentText()
        poe = self.ui.poe_cbx.currentText()
        self.field_name = '%s~%s' % (imt, poe)
        array = self.dataset.value[['lon', 'lat', self.field_name]]

        layer_name = "%s_%s_%s" % (rlz, imt, poe)
        # create layer
        self.layer = QgsVectorLayer("Point", layer_name, "memory")
        # NOTE: if we use shapefiles, we need to make sure ~ is fine,
        #       otherwise we have to replace it with something like _
        # NOTE: add_numeric_attribute uses LayerEditingManager
        add_numeric_attribute(self.field_name, self.layer)
        pr = self.layer.dataProvider()
        with LayerEditingManager(self.layer, 'Reading hdf5', DEBUG):
            feats = []
            for row in array:
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                lon, lat, value = row
                # NOTE: without casting to float, it produces a null
                #       because it does not recognize the numpy type
                feat.setAttribute(self.field_name, float(value))
                feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(lon, lat)))
                feats.append(feat)
            (res, outFeats) = pr.addFeatures(feats)
        # add self.layer to the legend
        QgsMapLayerRegistry.instance().addMapLayer(self.layer)

    def style_layer(self):
        color1 = QColor("#FFEBEB")
        color2 = QColor("red")
        classes_count = 10
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol.setAlpha(1)  # opacity
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            self.layer,
            self.field_name,
            classes_count,
            # QgsGraduatedSymbolRendererV2.Quantile,
            QgsGraduatedSymbolRendererV2.EqualInterval,
            symbol,
            ramp)
        graduated_renderer.updateRangeLowerValue(0, 0.0001)
        symbol_zeros = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol_zeros.setColor(QColor("green"))
        symbol_zeros.setAlpha(0.4)  # opacity
        zeros_min = 0.0
        zeros_max = 0.0001
        range_zeros = QgsRendererRangeV2(
            zeros_min, zeros_max, symbol_zeros,
            " %.4f - %.4f" % (zeros_min, zeros_max), True)
        graduated_renderer.addClassRange(range_zeros)
        graduated_renderer.moveClass(classes_count, 0)
        self.layer.setRendererV2(graduated_renderer)
        self.iface.legendInterface().refreshLayerSymbology(
            self.layer)
        self.iface.mapCanvas().refresh()

    def accept(self):
        self.build_layer()
        self.style_layer()
        self.close()
