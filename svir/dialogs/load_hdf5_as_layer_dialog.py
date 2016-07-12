
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

from openquake.baselib import hdf5

from svir.ui.ui_load_hdf5_as_layer import Ui_LoadHdf5AsLayerDialog
from svir.utilities.shared import DEBUG
from svir.utilities.utils import LayerEditingManager, WaitCursorManager
from svir.calculations.calculate_utils import add_numeric_attribute


class LoadHdf5AsLayerDialog(QDialog):
    """
    FIXME
    """
    def __init__(self, iface, hdf5_path=None):
        self.iface = iface
        self.hdf5_path = hdf5_path
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_LoadHdf5AsLayerDialog()
        self.ui.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.ui.open_hdfview_btn.setDisabled(True)
        if self.hdf5_path:
            self.ui.hdf5_path_le.setText(self.hdf5_path)
            self.ui.rlz_cbx.setEnabled(True)
            self.ui.imt_cbx.setEnabled(True)
            self.ui.poe_cbx.setEnabled(True)
            self.populate_rlz_cbx()

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
            imt, poe = name.split('-')
            if imt not in self.imts:
                self.imts[imt] = [poe]
            else:
                self.imts[imt].append(poe)
        self.ui.imt_cbx.clear()
        self.ui.imt_cbx.setEnabled(True)
        self.ui.imt_cbx.addItems(self.imts.keys())

    @pyqtSlot(str)
    def on_imt_cbx_currentIndexChanged(self):
        imt = self.ui.imt_cbx.currentText()
        self.ui.poe_cbx.clear()
        self.ui.poe_cbx.setEnabled(True)
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
        hdf5_path = QFileDialog.getOpenFileName(
            self, text, QDir.homePath(), filters)
        if hdf5_path:
            self.hdf5_path = hdf5_path
            self.ui.hdf5_path_le.setText(self.hdf5_path)
            self.populate_rlz_cbx()

    def populate_rlz_cbx(self):
        # FIXME: will the file be closed correctly?
        # with hdf5.File(self.hdf5_path, 'r') as hf:
        self.hfile = hdf5.File(self.hdf5_path, 'r')
        self.hmaps = self.hfile.get('hmaps')
        self.rlzs = self.hmaps.keys()
        self.ui.rlz_cbx.clear()
        self.ui.rlz_cbx.setEnabled(True)
        self.ui.rlz_cbx.addItems(self.rlzs)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.ui.poe_cbx.currentIndex != -1)

    def build_layer(self):
        rlz = self.ui.rlz_cbx.currentText()
        imt = self.ui.imt_cbx.currentText()
        poe = self.ui.poe_cbx.currentText()
        self.field_name = '%s-%s' % (imt, poe)
        array = self.dataset.value[['lon', 'lat', self.field_name]]

        layer_name = "%s_%s_%s" % (rlz, imt, poe)
        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        # NOTE: add_numeric_attribute uses LayerEditingManager
        self.field_name = add_numeric_attribute(self.field_name, self.layer)
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
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()

    def style_layer(self):
        color1 = QColor("#FFEBEB")
        color2 = QColor("red")
        classes_count = 10
        ramp = QgsVectorGradientColorRampV2(color1, color2)
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol = symbol.createSimple({'outline_width': '0.000001'})
        symbol.setAlpha(1)  # opacity
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            self.layer,
            self.field_name,
            classes_count,
            # QgsGraduatedSymbolRendererV2.Quantile,
            QgsGraduatedSymbolRendererV2.EqualInterval,
            symbol,
            ramp)
        graduated_renderer.updateRangeLowerValue(0, 0.0)
        symbol_zeros = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol_zeros = symbol.createSimple({'outline_width': '0.000001'})
        symbol_zeros.setColor(QColor(222, 255, 222))
        zeros_min = 0.0
        zeros_max = 0.0
        range_zeros = QgsRendererRangeV2(
            zeros_min, zeros_max, symbol_zeros,
            " %.4f - %.4f" % (zeros_min, zeros_max), True)
        graduated_renderer.addClassRange(range_zeros)
        graduated_renderer.moveClass(classes_count, 0)
        self.layer.setRendererV2(graduated_renderer)
        self.layer.setLayerTransparency(30)  # percent
        self.layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(
            self.layer)
        self.iface.mapCanvas().refresh()

    def accept(self):
        with WaitCursorManager('Creating layer...', self.iface):
            self.build_layer()
        self.hfile.close()
        self.style_layer()
        self.close()

    # FIXME: also cancel should close the hdf5 file
