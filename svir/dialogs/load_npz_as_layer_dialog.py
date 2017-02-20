
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

import json
import numpy
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
from PyQt4.QtCore import pyqtSlot, QDir, QSettings, QFileInfo

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         QComboBox,
                         QSpinBox,
                         QLabel,
                         )


from svir.utilities.shared import DEBUG
from svir.utilities.utils import (LayerEditingManager,
                                  WaitCursorManager,
                                  get_ui_class,
                                  log_msg,
                                  get_style)
from svir.calculations.calculate_utils import (add_numeric_attribute,
                                               add_textual_attribute,
                                               )

FORM_CLASS = get_ui_class('ui_load_npz_as_layer.ui')


class LoadNpzAsLayerDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to load hazard maps or hazard curves from npz files exported
    by the oq-engine
    """
    def __init__(self, iface, output_type, npz_path=None):

        # sanity check
        if output_type not in (
                'hcurves', 'hmaps', 'uhs', 'loss_maps', 'loss_curves',
                'gmf_data', 'scenario_damage_by_asset'):
            raise NotImplementedError(output_type)
        self.iface = iface
        self.npz_path = npz_path
        self.npz_file = None
        self.output_type = output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.define_gui_elements()
        self.adjust_gui_for_output_type()
        if self.npz_path:
            self.npz_path_le.setText(self.npz_path)
            self.rlz_cbx.setEnabled(True)
            self.imt_cbx.setEnabled(True)
            self.poe_cbx.setEnabled(True)
            self.loss_type_cbx.setEnabled(True)
            self.npz_file = self.get_npz_file_handler()
            self.get_taxonomies()
            self.populate_taxonomies()
            self.populate_rlz_cbx()
            self.populate_damage_states()
        self.default_field_name = None

    def define_gui_elements(self):
        self.rlz_lbl = QLabel('Realization (different realizations'
                              ' will be loaded into separate layer groups)')
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
        self.imt_lbl = QLabel(
            'IMTI (used for default styling)')  # FIXME: complete name?
        self.imt_cbx = QComboBox()
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.eid_lbl = QLabel(
            'Event ID (used for default styling)')
        self.eid_sbx = QSpinBox()
        self.eid_sbx.setEnabled(False)
        self.damage_state_lbl = QLabel(
            'Damage state')
        self.damage_state_cbx = QComboBox()
        self.damage_state_cbx.setEnabled(False)
        self.damage_state_cbx.currentIndexChanged['QString'].connect(
            self.on_damage_state_changed)
        self.taxonomy_lbl = QLabel('Taxonomy')
        self.taxonomy_cbx = QComboBox()
        self.taxonomy_cbx.setEnabled(False)
        # self.taxonomy_cbx.currentIndexChanged['QString'].connect(
        #     self.on_taxonomy_changed)

    def adjust_gui_for_output_type(self):
        if self.output_type == 'hmaps':
            self.setWindowTitle('Load hazard maps from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.imt_lbl)
            self.verticalLayout.addWidget(self.imt_cbx)
            self.verticalLayout.addWidget(self.poe_lbl)
            self.verticalLayout.addWidget(self.poe_cbx)
            self.adjustSize()
        elif self.output_type == 'hcurves':
            self.setWindowTitle('Load hazard curves from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.adjustSize()
        elif self.output_type == 'uhs':
            self.setWindowTitle(
                'Load uniform hazard spectra from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.adjustSize()
        elif self.output_type == 'loss_maps':
            self.setWindowTitle('Load loss maps from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.loss_type_lbl)
            self.verticalLayout.addWidget(self.loss_type_cbx)
            self.verticalLayout.addWidget(self.poe_lbl)
            self.verticalLayout.addWidget(self.poe_cbx)
            self.adjustSize()
        elif self.output_type == 'loss_curves':
            self.setWindowTitle('Load loss curves from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.adjustSize()
        elif self.output_type == 'gmf_data':
            self.setWindowTitle(
                'Load scenario damage GMFs from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.imt_lbl)
            self.verticalLayout.addWidget(self.imt_cbx)
            self.verticalLayout.addWidget(self.eid_lbl)
            self.verticalLayout.addWidget(self.eid_sbx)
            self.adjustSize()
        elif self.output_type == 'scenario_damage_by_asset':
            self.setWindowTitle(
                'Load scenario damage by asset from NPZ, as layer')
            self.verticalLayout.addWidget(self.rlz_lbl)
            self.verticalLayout.addWidget(self.rlz_cbx)
            self.verticalLayout.addWidget(self.loss_type_lbl)
            self.verticalLayout.addWidget(self.loss_type_cbx)
            self.verticalLayout.addWidget(self.taxonomy_lbl)
            self.verticalLayout.addWidget(self.taxonomy_cbx)
            self.verticalLayout.addWidget(self.damage_state_lbl)
            self.verticalLayout.addWidget(self.damage_state_cbx)
            self.adjustSize()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.npz_path = self.open_file_dialog()

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
            self.dataset = self.npz_file[self.rlz_cbx.currentText()]
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
        elif self.output_type == 'uhs':
            self.dataset = self.npz_file[self.rlz_cbx.currentText()]
            self.poes = self.dataset.dtype.names[2:]
        elif self.output_type in ('loss_maps', 'scenario_damage_by_asset'):
            # FIXME: likely, self.npz_file.keys()
            self.loss_types = self.npz_file.dtype.fields
            self.loss_type_cbx.clear()
            self.loss_type_cbx.setEnabled(True)
            self.loss_type_cbx.addItems(self.loss_types.keys())
        elif self.output_type == 'loss_curves':
            # FIXME: likely, self.npz_file.keys()
            self.loss_types = self.npz_file.dtype.names
        elif self.output_type == 'gmf_data':
            self.dataset = self.npz_file[self.rlz_cbx.currentText()]
            imts = self.dataset.dtype.names[2:]
            self.imt_cbx.clear()
            self.imt_cbx.setEnabled(True)
            self.imt_cbx.addItems(imts)
        if self.output_type in ('hcurves', 'loss_curves', 'uhs'):
            self.set_ok_button()

    def on_loss_type_changed(self):
        self.loss_type = self.loss_type_cbx.currentText()
        if self.output_type == 'loss_maps':
            poe_names = self.loss_types[self.loss_type][0].names
            poe_thresholds = [name.split('poe-')[1] for name in poe_names]
            self.poe_cbx.clear()
            self.poe_cbx.setEnabled(True)
            self.poe_cbx.addItems(poe_thresholds)
        elif self.output_type == 'scenario_damage_by_asset':
            self.set_ok_button()

    def on_imt_changed(self):
        if self.output_type == 'gmf_data':
            imt = self.imt_cbx.currentText()
            min_eid = 0
            max_eid = (self.dataset[imt].shape[1] - 1)
            self.eid_sbx.cleanText()
            self.eid_sbx.setEnabled(True)
            self.eid_lbl.setText(
                'Event ID (used for default styling) (range %d-%d)' % (
                    min_eid, max_eid))
            self.eid_sbx.setRange(min_eid, max_eid)
            self.set_ok_button()
        elif self.output_type == 'hmaps':
            imt = self.imt_cbx.currentText()
            self.poe_cbx.clear()
            self.poe_cbx.setEnabled(True)
            self.poe_cbx.addItems(self.imts[imt])

    def on_poe_changed(self):
        self.set_ok_button()

    # def on_eid_changed(self):
    #     self.set_ok_button()

    def on_damage_state_changed(self):
        pass

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select oq-engine output to import')
        filters = self.tr('NPZ files (*.npz)')
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        npz_path = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if npz_path:
            selected_dir = QFileInfo(npz_path).dir().path()
            QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
            self.npz_path = npz_path
            self.npz_path_le.setText(self.npz_path)
            self.npz_file = self.get_npz_file_handler()
            self.get_taxonomies()
            self.populate_taxonomies()
            self.populate_rlz_cbx()
            self.populate_damage_states()

    def get_npz_file_handler(self):
        return numpy.load(self.npz_path, 'r')

    def get_taxonomies(self):
        if self.output_type in (
                'loss_curves', 'loss_maps', 'scenario_damage_by_asset'):
            self.taxonomies = self.npz_file['assetcol/taxonomies'][:].tolist()

    def populate_taxonomies(self):
        if self.output_type == 'scenario_damage_by_asset':
            self.taxonomies.insert(0, 'Sum')
            self.taxonomy_cbx.clear()
            self.taxonomy_cbx.addItems(self.taxonomies)
            self.taxonomy_cbx.setEnabled(True)

    def populate_damage_states(self):
        if self.output_type == 'scenario_damage_by_asset':
            self.damage_states = ['no damage']
            self.damage_states.extend(self.npz_file['oqparam'].limit_states)
            self.damage_state_cbx.clear()
            self.damage_state_cbx.setEnabled(True)
            self.damage_state_cbx.addItems(self.damage_states)

    def populate_rlz_cbx(self):
        if self.output_type in ('hcurves', 'hmaps', 'uhs'):
            # self.hdata = self.npz_file[self.output_type]
            self.rlzs = [key for key in self.npz_file.keys()
                         if key.startswith('rlz')]
        elif self.output_type in ('loss_curves', 'loss_maps'):
            if self.output_type == 'loss_curves':
                self.hdata = self.npz_file['loss_curves-rlzs']
            elif self.output_type == 'loss_maps':
                self.hdata = self.npz_file['loss_maps-rlzs']
            _, n_rlzs = self.hdata.shape
            self.rlzs = [str(i+1) for i in range(n_rlzs)]
        elif self.output_type == 'gmf_data':
            self.rlzs = [item[0] for item in self.npz_file.items()]
        elif self.output_type == 'scenario_damage_by_asset':
            self.hdata = self.npz_file['dmg_by_asset']
            _, n_rlzs = self.hdata.shape
            self.rlzs = [str(i+1) for i in range(n_rlzs)]
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        # self.rlz_cbx.addItem('All')
        self.rlz_cbx.addItems(self.rlzs)

    def set_ok_button(self):
        if self.output_type == 'hmaps':
            self.ok_button.setEnabled(self.poe_cbx.currentIndex() != -1)
        elif self.output_type in ('hcurves', 'gmf_data'):
            self.ok_button.setEnabled(self.imt_cbx.currentIndex() != -1)
        elif self.output_type == 'loss_maps':
            self.ok_button.setEnabled(self.poe_cbx.currentIndex() != -1)
        elif self.output_type in ('loss_curves', 'uhs'):
            self.ok_button.setEnabled(self.rlz_cbx.currentIndex() != -1)
        elif self.output_type == 'scenario_damage_by_asset':
            self.ok_button.setEnabled(self.loss_type_cbx.currentIndex() != -1)

    def build_layer(self, rlz, taxonomy=None, poe=None):
        # get the root of layerTree, in order to add groups of layers
        # (one group for each realization)
        root = QgsProject.instance().layerTreeRoot()
        group_name = 'Realization %s' % rlz
        rlz_group = root.findGroup(group_name)
        if not rlz_group:
            rlz_group = root.addGroup('Realization %s' % rlz)
        # rlz = self.rlz_cbx.currentText()
        if self.output_type in ('loss_maps',
                                'loss_curves',
                                'scenario_damage_by_asset'):
            # NOTE: realizations in the npz file start counting from 1, but
            #       we need to refer to column indices that start from 0
            rlz_idx = int(rlz) - 1
        if self.output_type == 'loss_maps':
            loss_type = self.loss_type_cbx.currentText()
            poe = "poe-%s" % self.poe_cbx.currentText()
            self.default_field_name = loss_type
        # if self.output_type == 'uhs':
            # poe = self.poe_cbx.currentText()

        # build layer name
        if self.output_type == 'hmaps':
            imt = self.imt_cbx.currentText()
            poe = self.poe_cbx.currentText()
            self.default_field_name = '%s-%s' % (imt, poe)
            layer_name = "hazard_map_%s" % rlz
        elif self.output_type == 'hcurves':
            imt = self.imt_cbx.currentText()
            self.default_field_name = imt
            layer_name = "hazard_curves_rlz-%s" % rlz
        elif self.output_type == 'loss_curves':
            layer_name = "loss_curves_rlz-%s_%s" % (rlz, taxonomy)
        elif self.output_type == 'loss_maps':
            layer_name = "loss_maps_rlz-%s_%s" % (rlz, taxonomy)
        elif self.output_type == 'gmf_data':
            imt = self.imt_cbx.currentText()
            eid = self.eid_sbx.value()
            self.default_field_name = '%s-%s' % (imt, eid)
            layer_name = "scenario_damage_gmfs_rlz-%s_eid-%s" % (rlz, eid)
        elif self.output_type == 'scenario_damage_by_asset':
            layer_name = "scenario_damage_by_asset_rlz-%s_%s" % (rlz, taxonomy)
        elif self.output_type == 'uhs':
            layer_name = "uhs_rlz-%s_poe-%s" % (rlz, poe)

        # get field names
        if self.output_type in ['hcurves', 'hmaps', 'gmf_data']:
            field_names = list(self.dataset.dtype.names)
        elif self.output_type == 'loss_maps':
            field_names = self.loss_types.keys()
        elif self.output_type == 'loss_curves':
            field_names = list(self.loss_types)
        if self.output_type in ('loss_curves', 'loss_maps'):
            taxonomy_idx = self.taxonomies.index(taxonomy)
        if self.output_type == 'uhs':
            field_names = self.dataset[poe].dtype.names

        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        for field_name in field_names:
            if field_name in ['lon', 'lat']:
                continue
            if self.output_type in ('hmaps',
                                    'loss_maps',
                                    'uhs'):
                # NOTE: add_numeric_attribute uses LayerEditingManager
                added_field_name = add_numeric_attribute(
                    field_name, self.layer)
            elif self.output_type in ['hcurves', 'loss_curves']:
                # FIXME: probably we need a different type with more capacity
                added_field_name = add_textual_attribute(
                    field_name, self.layer)
            elif self.output_type == 'gmf_data':
                field_name = "%s-%s" % (field_name, eid)
                added_field_name = add_numeric_attribute(
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
        with LayerEditingManager(self.layer, 'Reading npz', DEBUG):
            feats = []
            if self.output_type == 'hcurves':
                imtls = self.npz_file['imtls']
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
                asset_array = self.npz_file['assetcol/array']
                loss_curves = self.npz_file['loss_curves-rlzs'][:, rlz_idx]
                for asset_idx, row in enumerate(loss_curves):
                    asset = asset_array[asset_idx]
                    if asset['taxonomy_id'] != taxonomy_idx:
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
                # FIXME: with npz, the following needs to be changed
                asset_array = self.npz_file['assetcol/array']
                loss_maps = self.npz_file['loss_maps-rlzs'][:, rlz_idx]
                for asset_idx, row in enumerate(loss_maps):
                    asset = asset_array[asset_idx]
                    if asset['taxonomy_id'] != taxonomy_idx:
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
            elif self.output_type == 'gmf_data':
                fields = self.layer.pendingFields()
                layer_field_names = [field.name() for field in fields]
                dataset_field_names = field_names
                d2l_field_names = dict(
                    zip(dataset_field_names[2:], layer_field_names))
                for row in self.dataset:
                    # add a feature
                    feat = QgsFeature(fields)
                    for field_name in dataset_field_names:
                        if field_name in ['lon', 'lat']:
                            continue
                        layer_field_name = d2l_field_names[field_name]
                        value = float(row[field_name][eid])
                        feat.setAttribute(layer_field_name, value)
                    feat.setGeometry(QgsGeometry.fromPoint(
                        QgsPoint(row[0], row[1])))
                    feats.append(feat)
            elif self.output_type == 'uhs':
                for row in self.dataset:
                    # add a feature
                    feat = QgsFeature(self.layer.pendingFields())
                    for field_name_idx, field_name in enumerate(field_names):
                        if field_name in ['lon', 'lat']:
                            continue
                        value = float(row[poe][field_name_idx])
                        feat.setAttribute(field_name, value)
                    feat.setGeometry(QgsGeometry.fromPoint(
                        QgsPoint(row['lon'], row['lat'])))
                    feats.append(feat)
            added_ok = self.layer.addFeatures(feats, makeSelected=False)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
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

        style = get_style(self.layer)
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
                        self.build_layer(rlz, taxonomy=taxonomy)
                        if self.output_type == 'loss_curves':
                            self.style_curves()
                        elif self.output_type == 'loss_maps':
                            self.style_maps()
            elif self.output_type == 'uhs':
                for poe in self.poes:
                    with WaitCursorManager(
                            'Creating layer for realization "%s" '
                            ' and poe "%s"...' % (rlz, poe),
                            self.iface):
                        self.build_layer(rlz, poe=poe)
                        self.style_curves()
            else:
                with WaitCursorManager('Creating layer for '
                                       ' realization "%s"...' % rlz,
                                       self.iface):
                    self.build_layer(rlz)
                    if self.output_type in ('hmaps', 'gmf_data'):
                        self.style_maps()
                    elif self.output_type == 'hcurves':
                        self.style_curves()
        self.npz_file.close()
        super(LoadNpzAsLayerDialog, self).accept()

    def reject(self):
        if self.npz_file is not None:
            self.npz_file.close()
        super(LoadNpzAsLayerDialog, self).reject()
