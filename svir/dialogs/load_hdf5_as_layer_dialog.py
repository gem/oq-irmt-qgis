
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
import json
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsPoint,
                       QgsGeometry,
                       QgsMapLayerRegistry,
                       QgsSymbolV2,
                       QgsSymbolLayerV2Registry,
                       QgsOuterGlowEffect,
                       QgsSingleSymbolRendererV2,
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

from svir.utilities.shared import DEBUG
from svir.utilities.utils import (LayerEditingManager,
                                  WaitCursorManager,
                                  get_ui_class,
                                  )
from svir.calculations.calculate_utils import (add_numeric_attribute,
                                               add_textual_attribute,
                                               )

FORM_CLASS = get_ui_class('ui_load_hdf5_as_layer.ui')


class LoadHdf5AsLayerDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to load hazard maps or hazard curves from hdf5 files exported
    by the oq-engine
    """
    def __init__(self, iface, output_type, hdf5_path=None):
        # sanity check
        if output_type not in ['hcurves', 'hmaps']:
            raise NotImplementedError(output_type)
        self.iface = iface
        self.hdf5_path = hdf5_path
        self.output_type = output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.open_hdfview_btn.setDisabled(True)
        if output_type == 'hcurves':
            self.imt_lbl.hide()
            self.imt_cbx.hide()
            self.poe_lbl.hide()
            self.poe_cbx.hide()
            self.adjustSize()
        if self.hdf5_path:
            self.hdf5_path_le.setText(self.hdf5_path)
            self.rlz_cbx.setEnabled(True)
            self.imt_cbx.setEnabled(True)
            self.poe_cbx.setEnabled(True)
            self.populate_rlz_cbx()

    @pyqtSlot(str)
    def on_hdf5_path_le_textChanged(self):
        self.open_hdfview_btn.setDisabled(
            self.hdf5_path_le.text() == '')

    @pyqtSlot()
    def on_open_hdfview_btn_clicked(self):
        file_path = self.hdf5_path_le.text()
        if file_path:
            to_run = "hdfview " + file_path
            # FIXME make system independent
            os.system(to_run)

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.hdf5_path = self.open_file_dialog()

    @pyqtSlot(str)
    def on_rlz_cbx_currentIndexChanged(self):
        self.dataset = self.hdata.get(self.rlz_cbx.currentText())
        self.imts = {}
        for name in self.dataset.dtype.names[2:]:
            if self.output_type == 'hmaps':
                imt, poe = name.split('-')
                if imt not in self.imts:
                    self.imts[imt] = [poe]
                else:
                    self.imts[imt].append(poe)
            elif self.output_type == 'hcurves':
                imt = name
                self.imts[imt] = []
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(self.imts.keys())

    @pyqtSlot(str)
    def on_imt_cbx_currentIndexChanged(self):
        if self.output_type == 'hcurves':
            self.set_ok_button()
            return
        imt = self.imt_cbx.currentText()
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.imts[imt])

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
            self.hdf5_path_le.setText(self.hdf5_path)
            self.populate_rlz_cbx()

    def populate_rlz_cbx(self):
        # FIXME: will the file be closed correctly?
        # with hdf5.File(self.hdf5_path, 'r') as hf:
        self.hfile = hdf5.File(self.hdf5_path, 'r')
        self.hdata = self.hfile.get(self.output_type)
        self.rlzs = self.hdata.keys()
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        self.rlz_cbx.addItems(self.rlzs)

    def set_ok_button(self):
        if self.output_type == 'hmaps':
            self.ok_button.setEnabled(self.poe_cbx.currentIndex != -1)
        elif self.output_type == 'hcurves':
            self.ok_button.setEnabled(self.imt_cbx.currentIndex != -1)

    def build_layer(self):
        rlz = self.rlz_cbx.currentText()
        imt = self.imt_cbx.currentText()
        if self.output_type == 'hmaps':
            poe = self.poe_cbx.currentText()
            self.default_field_name = '%s-%s' % (imt, poe)
            layer_name = "hazard_map_%s" % rlz
        elif self.output_type == 'hcurves':
            self.default_field_name = imt
            layer_name = "hazard_curves_%s" % rlz
        field_names = list(self.dataset.dtype.names)
        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        for field_name in field_names:
            if field_name in ['lon', 'lat']:
                continue
            if self.output_type == 'hmaps':
                # NOTE: add_numeric_attribute uses LayerEditingManager
                added_field_name = add_numeric_attribute(
                    field_name, self.layer)
            elif self.output_type == 'hcurves':
                added_field_name = add_textual_attribute(
                    field_name, self.layer)
            if field_name != added_field_name:
                if field_name == self.default_field_name:
                    self.default_field_name = added_field_name
                # replace field_name with the actual added_field_name
                field_name_idx = field_names.index(field_name)
                field_names.remove(field_name)
                field_names.insert(field_name_idx, added_field_name)
        pr = self.layer.dataProvider()
        with LayerEditingManager(self.layer, 'Reading hdf5', DEBUG):
            feats = []
            for row in self.dataset:
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    if self.output_type == 'hmaps':
                        # NOTE: without casting to float, it produces a null
                        #       because it does not recognize the numpy type
                        value = float(row[field_name_idx])
                    elif self.output_type == 'hcurves':
                        value = json.dumps(list(row[field_name_idx]))
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPoint(
                    QgsPoint(row[0], row[1])))
                feats.append(feat)
            (res, outFeats) = pr.addFeatures(feats)
        # add self.layer to the legend
        QgsMapLayerRegistry.instance().addMapLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()

    def style_hmaps(self):
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
            self.default_field_name,
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

    def style_hcurves(self):
        registry = QgsSymbolLayerV2Registry.instance()
        cross = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer(
            {'name': 'cross2', 'color': '0,0,0', 'color_border': '0,0,0',
             'offset': '0,0', 'size': '1.5', 'angle': '0'})
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(cross)
        renderer = QgsSingleSymbolRendererV2(symbol)
        effect = QgsOuterGlowEffect()
        effect.setSpread(0.5)
        effect.setTransparency(0)
        effect.setColor(QColor(255, 255, 255))
        effect.setBlurLevel(1)
        renderer.paintEffect().appendEffect(effect)
        renderer.paintEffect().setEnabled(True)
        self.layer.setRendererV2(renderer)
        self.layer.setLayerTransparency(30)  # percent
        self.layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(
            self.layer)
        self.iface.mapCanvas().refresh()

    def accept(self):
        with WaitCursorManager('Creating layer...', self.iface):
            self.build_layer()
        self.hfile.close()
        if self.output_type == 'hmaps':
            self.style_hmaps()
        elif self.output_type == 'hcurves':
            self.style_hcurves()
        super(LoadHdf5AsLayerDialog, self).accept()

    # FIXME: also cancel should close the hdf5 file
