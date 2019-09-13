# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2019 by GEM Foundation
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

from qgis.PyQt.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QRadioButton, QCheckBox, QWidget,
    QLabel)
from qgis.core import (
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication,)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import WaitCursorManager, log_msg
from svir.ui.multi_select_combo_box import MultiSelectComboBox
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadAssetRiskAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load asset_risk from an oq-engine output, as layer
    """
    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='asset_risk', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'asset_risk'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load Exposure/Risk as layer')
        self.extract_npz_task = ExtractNpzTask(
            'Extract exposure metadata', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'exposure_metadata',
            self.finalize_init, self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def finalize_init(self, extracted_npz):
        self.exposure_metadata = extracted_npz
        self.tag_names = sorted(self.exposure_metadata['tagnames'])
        self.exposure_categories = sorted(self.exposure_metadata['array'])
        self.risk_categories = sorted(self.exposure_metadata['multi_risk'])
        self.perils = set(
            [cat.rsplit('-', 1)[-1] for cat in self.risk_categories])

        self.populate_out_dep_widgets()

        self.adjustSize()
        self.taxonomies_gbx.toggled.emit(False)
        self.tag_gbx.toggled.emit(False)
        self.set_ok_button()
        self.show()
        self.init_done.emit()

    def populate_out_dep_widgets(self):
        self.visualize_gbx = QGroupBox('Visualize')
        self.visualize_gbx_h_layout = QHBoxLayout()
        self.exposure_rbn = QRadioButton('Exposure')
        self.risk_rbn = QRadioButton('Risk')
        self.exposure_rbn.toggled.connect(self.on_visualize_changed)
        self.risk_rbn.toggled.connect(self.on_visualize_changed)
        self.visualize_gbx_h_layout.addWidget(self.exposure_rbn)
        self.visualize_gbx_h_layout.addWidget(self.risk_rbn)
        self.visualize_gbx.setLayout(self.visualize_gbx_h_layout)
        self.vlayout.addWidget(self.visualize_gbx)
        self.create_selector(
            "peril", "Peril", filter_ckb=False,
            on_text_changed=self.on_peril_changed)
        self.peril_cbx.setDisabled(True)
        self.peril_lbl.setVisible(False)
        self.peril_cbx.setVisible(False)
        self.create_selector(
            "category", "Category", filter_ckb=False)
        self.peril_cbx.addItems(sorted(self.perils))
        self.taxonomies_gbx = QGroupBox()
        self.taxonomies_gbx.setTitle('Filter by taxonomy')
        self.taxonomies_gbx.setCheckable(True)
        self.taxonomies_gbx.setChecked(False)
        self.taxonomies_gbx_v_layout = QVBoxLayout()
        self.taxonomies_gbx.setLayout(self.taxonomies_gbx_v_layout)
        self.taxonomies_lbl = QLabel("Taxonomies")
        self.taxonomies_multisel = MultiSelectComboBox(self)
        self.taxonomies_multisel.add_unselected_items(
            sorted([taxonomy for taxonomy in self.exposure_metadata['taxonomy']
                    if taxonomy != '?']))
        self.taxonomies_gbx_v_layout.addWidget(self.taxonomies_lbl)
        self.taxonomies_gbx_v_layout.addWidget(self.taxonomies_multisel)
        self.taxonomies_gbx.toggled[bool].connect(
            self.on_taxonomies_gbx_toggled)
        self.vlayout.addWidget(self.taxonomies_gbx)
        self.tag_gbx = QGroupBox()
        self.tag_gbx.setTitle('Filter by tag')
        self.tag_gbx.setCheckable(True)
        self.tag_gbx.setChecked(False)
        self.tag_gbx_v_layout = QVBoxLayout()
        self.tag_gbx.setLayout(self.tag_gbx_v_layout)
        self.tag_values_lbl = QLabel("Tag values")
        self.tag_values_multisel = MultiSelectComboBox(self)
        self.create_selector(
            "tag", "Tag", add_to_layout=self.tag_gbx_v_layout,
            on_text_changed=self.on_tag_changed)
        self.tag_cbx.addItems([
            tag_name for tag_name in self.tag_names if tag_name != 'taxonomy'])
        self.tag_gbx_v_layout.addWidget(self.tag_values_lbl)
        self.tag_gbx_v_layout.addWidget(self.tag_values_multisel)
        self.tag_gbx.toggled[bool].connect(self.on_tag_gbx_toggled)
        self.vlayout.addWidget(self.tag_gbx)
        self.higher_on_top_chk = QCheckBox('Render higher values on top')
        self.higher_on_top_chk.setChecked(True)
        self.vlayout.addWidget(self.higher_on_top_chk)
        self.create_zonal_layer_selector()
        if self.zonal_layer_path:
            zonal_layer = self.load_zonal_layer(self.zonal_layer_path)
            self.populate_zonal_layer_cbx(zonal_layer)
        else:
            self.pre_populate_zonal_layer_cbx()
        self.exposure_rbn.setChecked(True)

    def on_taxonomies_gbx_toggled(self, is_checked):
        for widget in self.taxonomies_gbx.findChildren(QWidget):
            widget.setVisible(is_checked)

    def on_tag_gbx_toggled(self, is_checked):
        for widget in self.tag_gbx.findChildren(QWidget):
            widget.setVisible(is_checked)

    def on_visualize_changed(self):
        self.peril_cbx.setEnabled(self.risk_rbn.isChecked())
        self.peril_lbl.setVisible(self.risk_rbn.isChecked())
        self.peril_cbx.setVisible(self.risk_rbn.isChecked())
        if self.exposure_rbn.isChecked():
            self.category_cbx.clear()
            self.category_cbx.addItems(self.exposure_categories)
        else:  # 'Risk'
            self.peril_cbx.setCurrentIndex(0)
            self.peril_cbx.currentTextChanged.emit(
                self.peril_cbx.currentText())

    def on_peril_changed(self, peril):
        categories = [category.rsplit('-', 1)[0]
                      for category in self.risk_categories
                      if peril in category]
        self.category_cbx.clear()
        self.category_cbx.addItems(sorted(categories))

    def on_tag_changed(self, tag_name):
        tag_values = sorted([
            value for value in self.exposure_metadata[tag_name]
            if value != '?'])
        self.tag_values_multisel.clear()
        self.tag_values_multisel.add_unselected_items(tag_values)

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.category_cbx.currentIndex() != -1)

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        if self.exposure_rbn.isChecked():
            self.default_field_name = self.category_cbx.currentText()
        else:  # 'Risk'
            self.default_field_name = "%s-%s" % (
                self.category_cbx.currentText(), self.peril_cbx.currentText())
        if self.exposure_rbn.isChecked():
            layer_name = 'Exposure: %s' % self.category_cbx.currentText()
        else:  # Risk
            layer_name = 'Risk: %s %s' % (
                self.peril_cbx.currentText(),
                self.category_cbx.currentText())
        return layer_name

    def get_field_names(self, **kwargs):
        field_names = [name for name in self.dataset.dtype.names
                       if name not in self.tag_names and
                       name not in ['lon', 'lat']]
        return field_names

    def add_field_to_layer(self, field_name):
        try:
            # NOTE: add_numeric_attribute uses the native qgis editing manager
            added_field_name = add_numeric_attribute(field_name, self.layer)
        except TypeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            return
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            lons = self.dataset['lon']
            lats = self.dataset['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name in field_names:
                    value = float(row[field_name])
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(lons[row_idx], lats[row_idx])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def accept(self):
        self.iface.layerTreeView().currentLayerChanged.disconnect(
            self.on_currentLayerChanged)
        self.hide()
        extract_params = self.get_extract_params()
        self.download_asset_risk(extract_params)

    def get_extract_params(self):
        params = {}
        if self.tag_gbx.isChecked():
            tag_name = self.tag_cbx.currentText()
            params[tag_name] = self.tag_values_multisel.get_selected_items()
        if self.taxonomies_gbx.isChecked():
            params['taxonomy'] = self.taxonomies_multisel.get_selected_items()
        return params

    def download_asset_risk(self, extract_params):
        self.extract_npz_task = ExtractNpzTask(
            'Extract asset_risk', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'asset_risk',
            self.on_asset_risk_downloaded, self.on_extract_error,
            params=extract_params)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def on_asset_risk_downloaded(self, extracted_npz):
        self.npz_file = extracted_npz
        self.dataset = self.npz_file['array']
        with WaitCursorManager('Creating layer...', self.iface.messageBar()):
            self.build_layer()
            self.style_maps(
                self.layer, self.default_field_name,
                self.iface, self.output_type, perils=self.perils,
                render_higher_on_top=self.higher_on_top_chk.isChecked())
        if (self.zonal_layer_cbx.currentText()
                and self.zonal_layer_gbx.isChecked()):
            self.aggregate_by_zone()
        else:
            self.loading_completed.emit()
