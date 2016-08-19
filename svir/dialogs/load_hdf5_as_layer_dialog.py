
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
                       QgsProject,
                       )
from PyQt4.QtCore import pyqtSlot, QDir

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         QComboBox,
                         QLabel,
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
        if output_type not in (
                'hcurves', 'hmaps', 'loss_maps', 'loss_curves',
                'scenario_damage_gmfs'):
            raise NotImplementedError(output_type)
        self.iface = iface
        self.hdf5_path = hdf5_path
        self.hfile = None
        self.output_type = output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.open_hdfview_btn.setDisabled(True)
        self.define_gui_elements()
        self.adjust_gui_for_output_type()
        if self.hdf5_path:
            self.hdf5_path_le.setText(self.hdf5_path)
            self.rlz_cbx.setEnabled(True)
            self.imt_cbx.setEnabled(True)
            self.poe_cbx.setEnabled(True)
            self.loss_type_cbx.setEnabled(True)
            self.hfile = self.get_hdf5_file_handler()
            self.get_taxonomies()
            self.populate_rlz_cbx()
        self.default_field_name = None

    def define_gui_elements(self):
        self.rlz_lbl = QLabel('Realization (only the chosen realization'
                              ' will be loaded into the layer)')
        self.rlz_cbx = QComboBox()
        self.rlz_cbx.setEnabled(False)
        self.rlz_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_changed)
        self.imt_lbl = QLabel(
            'Intensity Measure Type (used for default styling)')
        self.imt_cbx = QComboBox()
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.poe_lbl = QLabel(
            'Probability of Exceedance (used for default styling)')
        self.poe_cbx = QComboBox()
        self.poe_cbx.setEnabled(False)
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        self.loss_type_lbl = QLabel(
            'Loss Type (used for default styling)')
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.setEnabled(False)
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.imti_lbl = QLabel(
            'IMTI (used for default styling)')  # FIXME: complete name?
        self.imti_cbx = QComboBox()
        self.imti_cbx.setEnabled(False)
        self.imti_cbx.currentIndexChanged['QString'].connect(
            self.on_imti_changed)
        self.eid_lbl = QLabel(
            'Event ID (used for default styling)')
        self.eid_cbx = QComboBox()  # FIXME: turn into a textbox
        self.eid_cbx.setEnabled(False)
        self.eid_cbx.currentIndexChanged['QString'].connect(
            self.on_eid_changed)

    def adjust_gui_for_output_type(self):
        if self.output_type == 'hmaps':
            self.setWindowTitle('Load hazard maps from HDF5, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.imt_lbl)
            self.verticalLayout.addWidget(self.imt_cbx)
            self.verticalLayout.addWidget(self.poe_lbl)
            self.verticalLayout.addWidget(self.poe_cbx)
            self.adjustSize()
        elif self.output_type == 'hcurves':
            self.setWindowTitle('Load hazard curves from HDF5, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.adjustSize()
        elif self.output_type == 'loss_maps':
            self.setWindowTitle('Load loss maps from HDF5, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.loss_type_lbl)
            self.verticalLayout.addWidget(self.loss_type_cbx)
            self.verticalLayout.addWidget(self.poe_lbl)
            self.verticalLayout.addWidget(self.poe_cbx)
            self.adjustSize()
        elif self.output_type == 'loss_curves':
            self.setWindowTitle('Load loss curves from HDF5, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.adjustSize()
        elif self.output_type == 'scenario_damage_gmfs':
            self.setWindowTitle(
                'Load scenario damage GMFs from HDF5, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.imti_lbl)
            self.verticalLayout.addWidget(self.imti_cbx)
            self.verticalLayout.addWidget(self.eid_lbl)
            self.verticalLayout.addWidget(self.eid_cbx)
            self.adjustSize()

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

    def on_rlz_changed(self):
        # rlz = self.rlz_cbx.currentText()
        # if rlz == 'All':
        #     self.imt_cbx.clear()
        #     self.imt_cbx.setEnabled(False)
        #     self.loss_type_cbx.clear()
        #     self.loss_type_cbx.setEnabled(False)
        #     self.poe_cbx.clear()
        #     self.poe_cbx.setEnabled(False)
        #     return
        if self.output_type in ['hcurves', 'hmaps']:
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
        elif self.output_type == 'loss_maps':
            self.loss_types = self.hdata.dtype.fields
            self.loss_type_cbx.clear()
            self.loss_type_cbx.setEnabled(True)
            self.loss_type_cbx.addItems(self.loss_types.keys())
        elif self.output_type == 'loss_curves':
            self.loss_types = self.hdata.dtype.names
        elif self.output_type == 'scenario_damage_gmfs':
            self.dataset = self.hdata.get(self.rlz_cbx.currentText())
            imtis = list(set(self.dataset['imti']))
            self.imti_cbx.clear()
            self.imti_cbx.setEnabled(True)
            self.imti_cbx.addItems([str(imti) for imti in imtis])
        if self.output_type in ('hcurves', 'loss_curves'):
            self.set_ok_button()

    def on_loss_type_changed(self):
        loss_type = self.loss_type_cbx.currentText()
        poe_names = self.loss_types[loss_type][0].names
        poe_thresholds = [name.split('poe-')[1] for name in poe_names]
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(poe_thresholds)

    def on_imt_changed(self):
        imt = self.imt_cbx.currentText()
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.imts[imt])

    def on_poe_changed(self):
        self.set_ok_button()

    def on_imti_changed(self):
        eids = list(set(self.dataset['eid']))  # FIXME: get only those that
                                               #        have the selected imti
        self.eid_cbx.clear()
        self.eid_cbx.setEnabled(True)
        self.eid_cbx.addItems([str(eid) for eid in eids])

    def on_eid_changed(self):
        pass

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
            self.hfile = self.get_hdf5_file_handler()
            self.get_taxonomies()
            self.populate_rlz_cbx()

    def get_hdf5_file_handler(self):
        # FIXME: will the file be closed correctly?
        # with hdf5.File(self.hdf5_path, 'r') as hf:
        return hdf5.File(self.hdf5_path, 'r')

    def get_taxonomies(self):
        if self.output_type in ('loss_curves', 'loss_maps'):
            self.taxonomies = self.hfile.get('assetcol/taxonomies')[:].tolist()

    def populate_rlz_cbx(self):
        if self.output_type in ('hcurves', 'hmaps'):
            self.hdata = self.hfile.get(self.output_type)
            self.rlzs = self.hdata.keys()
        elif self.output_type in ('loss_curves', 'loss_maps'):
            if self.output_type == 'loss_curves':
                self.hdata = self.hfile.get('loss_curves-rlzs')
            elif self.output_type == 'loss_maps':
                self.hdata = self.hfile.get('loss_maps-rlzs')
            _, n_rlzs = self.hdata.shape
            self.rlzs = [str(i+1) for i in range(n_rlzs)]
        elif self.output_type == 'scenario_damage_gmfs':
            self.hdata = self.hfile.get('gmf_data')
            self.rlzs = self.hdata.keys()
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        # self.rlz_cbx.addItem('All')
        self.rlz_cbx.addItems(self.rlzs)

    def set_ok_button(self):
        if self.output_type == 'hmaps':
            self.ok_button.setEnabled(self.poe_cbx.currentIndex != -1)
        elif self.output_type == 'hcurves':
            self.ok_button.setEnabled(self.imt_cbx.currentIndex != -1)
        elif self.output_type == 'loss_maps':
            self.ok_button.setEnabled(self.poe_cbx.currentIndex != -1)
        elif self.output_type == 'loss_curves':
            self.ok_button.setEnabled(self.rlz_cbx.currentIndex != -1)

    def build_layer(self, rlz, taxonomy=None):
        # get the root of layerTree, in order to add groups of layers
        # (one group for each realization)
        root = QgsProject.instance().layerTreeRoot()
        group_name = 'Realization %s' % rlz
        rlz_group = root.findGroup(group_name)
        if not rlz_group:
            rlz_group = root.addGroup('Realization %s' % rlz)
        # rlz = self.rlz_cbx.currentText()
        if self.output_type in ('loss_maps', 'loss_curves'):
            # NOTE: realizations in the hdf5 file start counting from 1, but
            #       we need to refer to column indices that start from 0
            rlz_idx = int(rlz) - 1
        if self.output_type == 'loss_maps':
            loss_type = self.loss_type_cbx.currentText()
            poe = "poe-%s" % self.poe_cbx.currentText()
            self.default_field_name = loss_type
        if self.output_type == 'hmaps':
            imt = self.imt_cbx.currentText()
            poe = self.poe_cbx.currentText()
            self.default_field_name = '%s-%s' % (imt, poe)
            layer_name = "hazard_map_rlz-%s" % rlz
        elif self.output_type == 'hcurves':
            imt = self.imt_cbx.currentText()
            self.default_field_name = imt
            layer_name = "hazard_curves_rlz-%s" % rlz
        elif self.output_type == 'loss_curves':
            layer_name = "loss_curves_rlz-%s_%s" % (rlz, taxonomy)
        elif self.output_type == 'loss_maps':
            layer_name = "loss_maps_rlz-%s_%s" % (rlz, taxonomy)
        if self.output_type in ['hcurves', 'hmaps']:
            field_names = list(self.dataset.dtype.names)
        elif self.output_type == 'loss_maps':
            field_names = self.loss_types.keys()
        elif self.output_type == 'loss_curves':
            field_names = list(self.loss_types)
        if self.output_type in ('loss_curves', 'loss_maps'):
            taxonomy_idx = self.taxonomies.index(taxonomy)
        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        for field_name in field_names:
            if field_name in ['lon', 'lat']:
                continue
            if self.output_type in ('hmaps', 'loss_maps'):
                # NOTE: add_numeric_attribute uses LayerEditingManager
                added_field_name = add_numeric_attribute(
                    field_name, self.layer)
            elif self.output_type in ['hcurves', 'loss_curves']:
                # FIXME: probably we need a different type with more capacity
                added_field_name = add_textual_attribute(
                    field_name, self.layer)
            else:
                raise NotImplementedError(self.output_type)
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
            if self.output_type == 'hcurves':
                imtls = self.hfile.get('imtls')
            if self.output_type in ['hcurves', 'hmaps']:
                for row in self.dataset:
                    # add a feature
                    feat = QgsFeature(self.layer.pendingFields())
                    for field_name_idx, field_name in enumerate(field_names):
                        if field_name in ['lon', 'lat']:
                            continue
                        if self.output_type == 'hmaps':
                            # NOTE: without casting to float, it produces a
                            #       null because it does not recognize the
                            #       numpy type
                            value = float(row[field_name_idx])
                        elif self.output_type == 'hcurves':
                            poes = row[field_name_idx].tolist()
                            imls = imtls[field_name].tolist()
                            dic = dict(poes=poes, imls=imls)
                            value = json.dumps(dic)
                        feat.setAttribute(field_name, value)
                    feat.setGeometry(QgsGeometry.fromPoint(
                        QgsPoint(row[0], row[1])))
                    feats.append(feat)
            elif self.output_type == 'loss_curves':
                # We need to select rows from loss_curves-rlzs where the
                # row index (the asset idx) has the given taxonomy. The
                # taxonomy is found in the assetcol/array, together with
                # the coordinates lon and lat of the asset.
                # From the selected rows, we extract loss_type -> losses
                #                                and loss_type -> poes
                asset_array = self.hfile.get('assetcol/array')
                loss_curves = self.hfile.get('loss_curves-rlzs')[:, rlz_idx]
                for asset_idx, row in enumerate(loss_curves):
                    asset = asset_array[asset_idx]
                    if asset['taxonomy'] != taxonomy_idx:
                        continue
                    else:
                        lon = asset['lon']
                        lat = asset['lat']
                    # add a feature
                    feat = QgsFeature(self.layer.pendingFields())
                    # NOTE: field names are loss types (normalized to 10 chars)
                    for field_name_idx, field_name in enumerate(field_names):
                        losses = row[field_name_idx]['losses'].tolist()
                        poes = row[field_name_idx]['poes'].tolist()
                        dic = dict(losses=losses, poes=poes)
                        value = json.dumps(dic)
                        feat.setAttribute(field_name, value)
                    feat.setGeometry(QgsGeometry.fromPoint(
                        QgsPoint(lon, lat)))
                    feats.append(feat)
            elif self.output_type == 'loss_maps':
                # We need to select rows from loss_maps-rlzs where the
                # row index (the asset idx) has the given taxonomy. The
                # taxonomy is found in the assetcol/array, together with
                # the coordinates lon and lat of the asset.
                # From the selected rows, we extract loss_type -> poes
                asset_array = self.hfile.get('assetcol/array')
                loss_maps = self.hfile.get('loss_maps-rlzs')[:, rlz_idx]
                for asset_idx, row in enumerate(loss_maps):
                    asset = asset_array[asset_idx]
                    if asset['taxonomy'] != taxonomy_idx:
                        continue
                    else:
                        lon = asset['lon']
                        lat = asset['lat']
                    # add a feature
                    feat = QgsFeature(self.layer.pendingFields())
                    # NOTE: field names are loss types (normalized to 10 chars)
                    for field_name_idx, field_name in enumerate(field_names):
                        loss = row[field_name_idx][poe]
                        feat.setAttribute(field_name, float(loss))
                    feat.setGeometry(QgsGeometry.fromPoint(
                        QgsPoint(lon, lat)))
                    feats.append(feat)
            (res, outFeats) = pr.addFeatures(feats)
        # add self.layer to the legend
        QgsMapLayerRegistry.instance().addMapLayer(self.layer, False)
        rlz_group.addLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()

    def style_maps(self):
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

    def style_curves(self):
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
        for rlz in self.rlzs:
            if self.output_type in ('loss_curves', 'loss_maps'):
                for taxonomy in self.taxonomies:
                    with WaitCursorManager(
                            'Creating layer for realization "%s" '
                            ' and taxonomy "%s"...' % (rlz, taxonomy),
                            self.iface):
                        self.build_layer(rlz, taxonomy)
                        if self.output_type == 'loss_curves':
                            self.style_curves()
                        elif self.output_type == 'loss_maps':
                            self.style_maps()  # FIXME rename called function
            else:
                with WaitCursorManager('Creating layer for '
                                       ' realization "%s"...' % rlz,
                                       self.iface):
                    self.build_layer(rlz)
                    if self.output_type == 'hmaps':
                        self.style_maps()
                    elif self.output_type == 'hcurves':
                        self.style_curves()
        self.hfile.close()
        super(LoadHdf5AsLayerDialog, self).accept()

    # FIXME: also cancel should close the hdf5 file
