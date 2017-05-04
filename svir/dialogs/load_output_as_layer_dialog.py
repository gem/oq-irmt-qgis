# -*- coding: utf-8 -*-
# /***************************************************************************
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

import numpy
from qgis.core import (QgsVectorLayer,
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
from PyQt4.QtCore import pyqtSlot, QDir, QSettings, QFileInfo

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         QComboBox,
                         QSpinBox,
                         QLabel,
                         QCheckBox,
                         QHBoxLayout,
                         )


from svir.utilities.shared import (OQ_CSV_LOADABLE_TYPES,
                                   OQ_NPZ_LOADABLE_TYPES,
                                   OQ_ALL_LOADABLE_TYPES,
                                   )
from svir.utilities.utils import (get_ui_class,
                                  get_style,
                                  clear_widgets_from_layout,
                                  )

FORM_CLASS = get_ui_class('ui_load_output_as_layer.ui')


class LoadOutputAsLayerDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to load an oq-engine output as layer
    """

    def __init__(self, iface, output_type=None, path=None, mode=None):

        # sanity check
        if output_type not in OQ_ALL_LOADABLE_TYPES:
            raise NotImplementedError(output_type)
        self.iface = iface
        self.path = path
        self.output_type = output_type
        self.mode = mode  # if 'testing' it will avoid some user interaction
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all user options are set
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.file_browser_tbn.setEnabled(True)
        if self.path:
            self.path_le.setText(self.path)
        clear_widgets_from_layout(self.output_dep_vlayout)

    def create_rlz_selector(self):
        self.rlz_cbx = QComboBox()
        self.rlz_cbx.setEnabled(False)
        self.rlz_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_changed)
        self.num_sites_msg = 'Number of sites: %s'
        self.rlz_num_sites_lbl = QLabel(self.num_sites_msg % '')
        self.rlz_h_layout = QHBoxLayout()
        self.rlz_h_layout.addWidget(self.rlz_cbx)
        self.rlz_h_layout.addWidget(self.rlz_num_sites_lbl)
        self.output_dep_vlayout.addLayout(self.rlz_h_layout)

    def create_imt_selector(self):
        self.imt_lbl = QLabel('Intensity Measure Type')
        self.imt_cbx = QComboBox()
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.output_dep_vlayout.addWidget(self.imt_lbl)
        self.output_dep_vlayout.addWidget(self.imt_cbx)

    def create_poe_selector(self):
        self.poe_lbl = QLabel('Probability of Exceedance')
        self.poe_cbx = QComboBox()
        self.poe_cbx.setEnabled(False)
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        self.output_dep_vlayout.addWidget(self.poe_lbl)
        self.output_dep_vlayout.addWidget(self.poe_cbx)

    def create_loss_type_selector(self):
        self.loss_type_lbl = QLabel('Loss Type')
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.setEnabled(False)
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.output_dep_vlayout.addWidget(self.loss_type_lbl)
        self.output_dep_vlayout.addWidget(self.loss_type_cbx)

    def create_eid_selector(self):
        self.eid_lbl = QLabel('Event ID')
        self.eid_sbx = QSpinBox()
        self.eid_sbx.setEnabled(False)
        self.output_dep_vlayout.addWidget(self.eid_lbl)
        self.output_dep_vlayout.addWidget(self.eid_sbx)

    def create_dmg_state_selector(self):
        self.dmg_state_lbl = QLabel('Damage state')
        self.dmg_state_cbx = QComboBox()
        self.dmg_state_cbx.setEnabled(False)
        self.dmg_state_cbx.currentIndexChanged['QString'].connect(
            self.on_dmg_state_changed)
        self.output_dep_vlayout.addWidget(self.dmg_state_lbl)
        self.output_dep_vlayout.addWidget(self.dmg_state_cbx)

    def create_taxonomy_selector(self):
        self.taxonomy_lbl = QLabel('Taxonomy')
        self.taxonomy_cbx = QComboBox()
        self.taxonomy_cbx.setEnabled(False)
        # TODO: it might be needed when npz risk outputs are available
        # self.taxonomy_cbx.currentIndexChanged['QString'].connect(
        #     self.on_taxonomy_changed)
        self.output_dep_vlayout.addWidget(self.taxonomy_lbl)
        self.output_dep_vlayout.addWidget(self.taxonomy_cbx)

    def create_load_selected_only_ckb(self):
        self.load_selected_only_ckb = QCheckBox("Load only the selected items")
        self.load_selected_only_ckb.setChecked(True)
        self.output_dep_vlayout.addWidget(self.load_selected_only_ckb)

    def create_save_as_shp_ckb(self):
        self.save_as_shp_ckb = QCheckBox("Save the loaded layer as shapefile")
        self.save_as_shp_ckb.setChecked(False)
        self.output_dep_vlayout.addWidget(self.save_as_shp_ckb)

    def on_output_type_changed(self):
        if self.output_type in OQ_NPZ_LOADABLE_TYPES:
            self.create_load_selected_only_ckb()
        elif self.output_type in OQ_CSV_LOADABLE_TYPES:
            self.create_save_as_shp_ckb()
        # elif self.output_type == 'loss_maps':
        #     self.setWindowTitle('Load loss maps from NPZ, as layer')
        #     self.create_rlz_selector()
        #     self.create_loss_type_selector()
        #     self.create_poe_selector()
        #     self.adjustSize()
        # elif self.output_type == 'loss_curves':
        #     self.setWindowTitle('Load loss curves from NPZ, as layer')
        #     self.create_rlz_selector()
        #     self.adjustSize()
        self.set_ok_button()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        path = self.open_file_dialog()
        if path:
            if self.output_type in OQ_NPZ_LOADABLE_TYPES:
                self.npz_file = numpy.load(self.path, 'r')
            self.populate_out_dep_widgets()
        self.set_ok_button()

    def on_rlz_changed(self):
        self.dataset = self.npz_file[self.rlz_cbx.currentText()]
        # TODO: change as soon as npz files for these become available
        # if self.output_type in ('loss_maps'):
        #     # FIXME: likely, self.npz_file.keys()
        #     self.loss_types = self.npz_file.dtype.fields
        #     self.loss_type_cbx.clear()
        #     self.loss_type_cbx.setEnabled(True)
        #     self.loss_type_cbx.addItems(self.loss_types.keys())
        # elif self.output_type == 'loss_curves':
        #     # FIXME: likely, self.npz_file.keys()
        #     self.loss_types = self.npz_file.dtype.names
        self.set_ok_button()

    def on_loss_type_changed(self):
        # TODO: change as soon as npz becomes available
        # self.loss_type = self.loss_type_cbx.currentText()
        # if self.output_type == 'loss_maps':
        #     poe_names = self.loss_types[self.loss_type][0].names
        #     poe_thresholds = [name.split('poe-')[1] for name in poe_names]
        #     self.poe_cbx.clear()
        #     self.poe_cbx.setEnabled(True)
        #     self.poe_cbx.addItems(poe_thresholds)
        self.set_ok_button()

    def on_imt_changed(self):
        self.set_ok_button()

    def on_poe_changed(self):
        self.set_ok_button()

    def on_eid_changed(self):
        self.set_ok_button()

    def on_dmg_state_changed(self):
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select the OQ-Engine output file to import')
        if self.output_type in OQ_NPZ_LOADABLE_TYPES:
            filters = self.tr('NPZ files (*.npz)')
        elif self.output_type in OQ_CSV_LOADABLE_TYPES:
            filters = self.tr('CSV files (*.csv)')
        else:
            raise NotImplementedError(self.output_type)
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        path = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if not path:
            return
        selected_dir = QFileInfo(path).dir().path()
        QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
        self.path = path
        self.path_le.setText(self.path)
        return path

    def populate_out_dep_widgets(self):
        # TODO: change as soon as npz risk outputs are available
        # self.get_taxonomies()
        # self.populate_taxonomy_cbx()
        self.populate_rlz_cbx()
        self.show_num_sites()
        # self.populate_dmg_states()

    def get_taxonomies(self):
        raise NotImplementedError()
        # TODO: change as soon as npz risk outputs are available
        # if self.output_type in (
        #         'loss_curves', 'loss_maps'):
        #     self.taxonomies = self.npz_file[
        #         'assetcol/taxonomies'][:].tolist()

    def populate_rlz_cbx(self):
        # TODO: change as soon as npz files for these become available
        # if self.output_type in ('loss_curves', 'loss_maps'):
        #     if self.output_type == 'loss_curves':
        #         self.hdata = self.npz_file['loss_curves-rlzs']
        #     elif self.output_type == 'loss_maps':
        #         self.hdata = self.npz_file['loss_maps-rlzs']
        #     _, n_rlzs = self.hdata.shape
        #     self.rlzs = [str(i+1) for i in range(n_rlzs)]
        self.rlzs = [key for key in self.npz_file.keys() if key != 'imtls']
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        self.rlz_cbx.addItems(self.rlzs)

    def populate_dmg_state_cbx(self, dmg_states):
        self.dmg_state_cbx.clear()
        self.dmg_state_cbx.setEnabled(True)
        self.dmg_state_cbx.addItems(dmg_states)

    def populate_loss_type_cbx(self, loss_types):
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(loss_types)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which currently is always true.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_changed()
        rlz_data = self.npz_file[self.rlz_cbx.currentText()]
        self.rlz_num_sites_lbl.setText(self.num_sites_msg % rlz_data.shape)

    def set_ok_button(self):
        raise NotImplementedError()
        # TODO: change as soon as npz files for these become available
        # if self.output_type == 'loss_maps':
        #     self.ok_button.setEnabled(self.poe_cbx.currentIndex() != -1)
        # elif self.output_type == 'loss_curves':
        #     self.ok_button.setEnabled(self.rlz_cbx.currentIndex() != -1)

    def get_layer_group(self, rlz):
        # get the root of layerTree, in order to add groups of layers
        # (one group for each realization)
        root = QgsProject.instance().layerTreeRoot()
        rlz_group = root.findGroup(rlz)
        if not rlz_group:
            rlz_group = root.addGroup(rlz)
        return rlz_group

    def build_layer_name(self, rlz, **kwargs):
        raise NotImplementedError()
        # TODO: change as soon as npz files for these become available
        # elif self.output_type == 'loss_curves':
        #     layer_name = "loss_curves_%s_%s" % (rlz, taxonomy)
        # elif self.output_type == 'loss_maps':
        #     layer_name = "loss_maps_%s_%s" % (rlz, taxonomy)
        # elif self.output_type == 'dmg_by_asset':
        #     # TODO: probably to be removed
        #     layer_name = "dmg_by_asset_%s_%s" % (rlz, taxonomy)
        # return layer_name

    def get_field_names(self, **kwargs):
        raise NotImplementedError()
        # TODO: change as soon as npz files for these become available
        # if self.output_type == 'loss_maps':
        #     field_names = self.loss_types.keys()
        # elif self.output_type == 'loss_curves':
        #     field_names = list(self.loss_types)
        # if self.output_type in ('loss_curves', 'loss_maps'):
        #     self.taxonomy_idx = self.taxonomies.index(self.taxonomy)
        # return field_names

    def add_field_to_layer(self, field_name):
        raise NotImplementedError()
        # TODO: change as soon as npz files for these become available
        # if self.output_type == 'loss_maps':
        #     # NOTE: add_numeric_attribute uses LayerEditingManager
        #     added_field_name = add_numeric_attribute(
        #         field_name, self.layer)
        # elif self.output_type == 'loss_curves':
        #     # NOTE: probably we need a different type with more capacity
        #     added_field_name = add_textual_attribute(
        #         field_name, self.layer)
        # else:
        #     raise NotImplementedError(self.output_type)
        # return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        raise NotImplementedError()
        # TODO: change as soon as npz files for these become available
        # with LayerEditingManager(self.layer, 'Reading npz', DEBUG):
        #     feats = []
        #     TODO: change as soon as npz files for these become available
        #     elif self.output_type == 'loss_curves':
        #         # We need to select rows from loss_curves-rlzs where the
        #         # row index (the asset idx) has the given taxonomy. The
        #         # taxonomy is found in the assetcol/array, together with
        #         # the coordinates lon and lat of the asset.
        #         # From the selected rows, we extract loss_type -> losses
        #         #                                and loss_type -> poes
        #         asset_array = self.npz_file['assetcol/array']
        #         loss_curves = self.npz_file['loss_curves-rlzs'][:, rlz_idx]
        #         for asset_idx, row in enumerate(loss_curves):
        #             asset = asset_array[asset_idx]
        #             if asset['taxonomy_id'] != taxonomy_idx:
        #                 continue
        #             else:
        #                 lon = asset['lon']
        #                 lat = asset['lat']
        #             # add a feature
        #             feat = QgsFeature(self.layer.pendingFields())
        #             # NOTE: field names are loss types
        #             #       (normalized to 10 chars)
        #             for field_name_idx, field_name in enumerate(field_names):
        #                 losses = row[field_name_idx]['losses'].tolist()
        #                 poes = row[field_name_idx]['poes'].tolist()
        #                 dic = dict(losses=losses, poes=poes)
        #                 value = json.dumps(dic)
        #                 feat.setAttribute(field_name, value)
        #             feat.setGeometry(QgsGeometry.fromPoint(
        #                 QgsPoint(lon, lat)))
        #             feats.append(feat)
        #     elif self.output_type == 'loss_maps':
        #         # We need to select rows from loss_maps-rlzs where the
        #         # row index (the asset idx) has the given taxonomy. The
        #         # taxonomy is found in the assetcol/array, together with
        #         # the coordinates lon and lat of the asset.
        #         # From the selected rows, we extract loss_type -> poes
        #         # TODO: with npz, the following needs to be changed
        #         asset_array = self.npz_file['assetcol/array']
        #         loss_maps = self.npz_file['loss_maps-rlzs'][:, rlz_idx]
        #         for asset_idx, row in enumerate(loss_maps):
        #             asset = asset_array[asset_idx]
        #             if asset['taxonomy_id'] != taxonomy_idx:
        #                 continue
        #             else:
        #                 lon = asset['lon']
        #                 lat = asset['lat']
        #             # add a feature
        #             feat = QgsFeature(self.layer.pendingFields())
        #             # NOTE: field names are loss types
        #             #       (normalized to 10 chars)
        #             for field_name_idx, field_name in enumerate(field_names):
        #                 loss = row[field_name_idx][poe]
        #                 feat.setAttribute(field_name, float(loss))
        #             feat.setGeometry(QgsGeometry.fromPoint(
        #                 QgsPoint(lon, lat)))
        #             feats.append(feat)
        #     added_ok = self.layer.addFeatures(feats, makeSelected=False)
        #     if not added_ok:
        #         msg = 'There was a problem adding features to the layer.'
        #         log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_npz(self):
        raise NotImplementedError()
        # for rlz in self.rlzs:
        #     if (self.load_selected_only_ckb.isChecked()
        #             and rlz != self.rlz_cbx.currentText()):
        #         continue
        #     # TODO: change as soon as the npz outputs are available
        #     if self.output_type in ('loss_curves', 'loss_maps'):
        #         for taxonomy in self.taxonomies:
        #             if (self.load_selected_only_ckb.isChecked()
        #                     and taxonomy != self.taxonomy_cbx.currentText()):
        #                 continue
        #             with WaitCursorManager(
        #                     'Creating layer for realization "%s" '
        #                     ' and taxonomy "%s"...' % (rlz, taxonomy),
        #                     self.iface):
        #                 self.build_layer(rlz, taxonomy=taxonomy)
        #                 if self.output_type == 'loss_curves':
        #                     self.style_curves()
        #                 elif self.output_type == 'loss_maps':
        #                     self.style_maps()
        #     else:
        #         with WaitCursorManager('Creating layer for '
        #                                ' realization "%s"...' % rlz,
        #                                self.iface):
        #             self.build_layer(rlz)
        # if self.npz_file is not None:
        #     self.npz_file.close()

    def build_layer(self, rlz, taxonomy=None, poe=None, loss_type=None):
        rlz_group = self.get_layer_group(rlz)
        layer_name = self.build_layer_name(
            rlz, taxonomy=taxonomy, poe=poe, loss_type=loss_type)
        # TODO: change as soon as npz files for these become available
        # if self.output_type in ('loss_maps',
        #                         'loss_curves'):
        #                         # 'dmg_by_asset'):
        #     # NOTE: realizations in the npz file start counting from 1, but
        #     #       we need to refer to column indices that start from 0
        #     rlz_idx = int(rlz) - 1
        # if self.output_type == 'loss_maps':
        #     loss_type = self.loss_type_cbx.currentText()
        #     poe = "poe-%s" % self.poe_cbx.currentText()
        #     self.default_field_name = loss_type
        field_names = self.get_field_names(
            rlz=rlz, taxonomy=taxonomy, poe=poe, loss_type=loss_type)

        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        for field_name in field_names:
            if field_name in ['lon', 'lat']:
                continue
            added_field_name = self.add_field_to_layer(field_name)
            if field_name != added_field_name:
                if field_name == self.default_field_name:
                    self.default_field_name = added_field_name
                # replace field_name with the actual added_field_name
                field_name_idx = field_names.index(field_name)
                field_names.remove(field_name)
                field_names.insert(field_name_idx, added_field_name)

        self.read_npz_into_layer(
            field_names, rlz=rlz, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type)
        # add self.layer to the legend
        QgsMapLayerRegistry.instance().addMapLayer(self.layer, False)
        rlz_group.addLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()

    def style_maps(self):
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol = symbol.createSimple({'outline_width': '0.000001'})
        symbol.setAlpha(1)  # opacity

        style = get_style(self.layer, self.iface.messageBar())
        ramp = QgsVectorGradientColorRampV2(
            style['color_from'], style['color_to'])
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            self.layer,
            self.default_field_name,
            style['classes'],
            style['mode'],
            symbol,
            ramp)
        graduated_renderer.updateRangeLowerValue(0, 0.0)
        symbol_zeros = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol_zeros = symbol_zeros.createSimple({'outline_width': '0.000001'})
        symbol_zeros.setColor(QColor(222, 255, 222))
        zeros_min = 0.0
        zeros_max = 0.0
        range_zeros = QgsRendererRangeV2(
            zeros_min, zeros_max, symbol_zeros,
            " %.4f - %.4f" % (zeros_min, zeros_max), True)
        graduated_renderer.addClassRange(range_zeros)
        graduated_renderer.moveClass(style['classes'], 0)
        self.layer.setRendererV2(graduated_renderer)
        self.layer.setLayerTransparency(30)  # percent
        self.layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(self.layer)
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
        if self.output_type in OQ_NPZ_LOADABLE_TYPES:
            self.load_from_npz()
        elif self.output_type in OQ_CSV_LOADABLE_TYPES:
            self.load_from_csv()
        super(LoadOutputAsLayerDialog, self).accept()

    def reject(self):
        if (self.output_type in OQ_NPZ_LOADABLE_TYPES
                and self.npz_file is not None):
            self.npz_file.close()
        super(LoadOutputAsLayerDialog, self).reject()
