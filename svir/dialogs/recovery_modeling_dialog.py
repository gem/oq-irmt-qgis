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

import os
import csv
from PyQt4.QtCore import pyqtSlot, QSettings, QDir
from PyQt4.QtGui import (QDialog,
                         QFileDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayer, QgsMapLayerRegistry, QGis
from svir.calculations.aggregate_loss_by_zone import add_zone_id_to_points
from svir.utilities.utils import (get_ui_class,
                                  reload_attrib_cbx,
                                  WaitCursorManager,
                                  log_msg,
                                  )
from svir.utilities.shared import DEBUG
from svir.recovery_modeling.recovery_modeling import (
    RecoveryModeling, fill_fields_multiselect)
from svir.ui.list_multiselect_widget import ListMultiSelectWidget

FORM_CLASS = get_ui_class('ui_recovery_modeling.ui')


class RecoveryModelingDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to perform recovery modeling analysis.
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        # Set up the user interface from Designer.
        self.setupUi(self)
        title = (
            'Select fields containing loss-based damage state probabilities')
        self.fields_multiselect = ListMultiSelectWidget(title=title)
        self.vLayout.insertWidget(2, self.fields_multiselect)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        approach_explanation = (
            'Aggregate: building-level recovery model as a single process\n'
            'Disaggregate: Building-level recovery modelled using four'
            ' processes: inspection, assessment, mobilization and repair.')
        self.approach_cbx.addItems(['Disaggregate', 'Aggregate'])
        self.approach_cbx.setToolTip(approach_explanation)
        self.approach_lbl.setToolTip(approach_explanation)
        simulations_explanation = (
            'Number of damage realizations used in Monte Carlo Simulation')
        n_simulations = int(
            QSettings().value('irmt/n_simulations_per_building', 1))
        self.n_simulations_sbx.setValue(n_simulations)
        self.n_simulations_lbl.setToolTip(simulations_explanation)
        self.n_simulations_sbx.setToolTip(simulations_explanation)
        self.save_bldg_curves_check.setChecked(False)
        self.populate_layers_in_combos()
        self.restoreState()
        self.set_ok_button()

    def populate_layers_in_combos(self):
        for key, layer in \
                QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            if layer.geometryType() == QGis.Point:
                self.dmg_by_asset_layer_cbx.addItem(layer.name(), layer)
            if layer.geometryType() == QGis.Polygon:
                self.svi_layer_cbx.addItem(layer.name(), layer)
        # if the active layer contains points, preselect it
        active_layer = self.iface.activeLayer()
        if active_layer is not None:
            idx = self.dmg_by_asset_layer_cbx.findData(active_layer)
            if idx != -1:
                self.dmg_by_asset_layer_cbx.setCurrentIndex(idx)

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QSettings()
        self.output_data_dir = mySettings.value(
            'irmt/recovery_output_data_dir', '')
        # hack for strange mac behaviour
        if not self.output_data_dir:
            self.output_data_dir = ''
        self.output_data_dir_le.setText(self.output_data_dir)

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QSettings()
        mySettings.setValue('irmt/recovery_output_data_dir',
                            self.output_data_dir_le.text())

    def set_ok_button(self):
        self.ok_button.setEnabled(
            os.path.isdir(self.output_data_dir_le.text())
            and self.approach_cbx.currentIndex != -1
            and self.dmg_by_asset_layer_cbx.currentIndex != -1)
        # and self.svi_layer_cbx.currentIndex != -1
        # and self.svi_field_name_cbx.currentIndex != -1
        # and self.zone_field_name_cbx.currentIndex != -1)

    @pyqtSlot(str)
    def on_output_data_dir_le_textChanged(self, text):
        self.output_data_dir = self.output_data_dir_le.text()
        self.set_ok_button()

    @pyqtSlot(str)
    def on_approach_cbx_currentIndexChanged(self, selected_text):
        # TODO: we might need to ask the user to provide the necessary files
        self.set_ok_button()

    @pyqtSlot(int)
    def on_dmg_by_asset_layer_cbx_currentIndexChanged(self, selected_index):
        self.dmg_by_asset_layer = self.dmg_by_asset_layer_cbx.itemData(
            selected_index)
        self.fields_multiselect.selected_widget.clear()
        self.fields_multiselect.unselected_widget.clear()
        fill_fields_multiselect(
            self.fields_multiselect, self.dmg_by_asset_layer)

    @pyqtSlot(int)
    def on_svi_layer_cbx_currentIndexChanged(self, selected_index):
        self.svi_layer = self.svi_layer_cbx.itemData(selected_index)
        # FIXME self.svi_field_name is temporarily ignored
        # reload_attrib_cbx(self.svi_field_name_cbx, self.svi_layer)
        reload_attrib_cbx(self.zone_field_name_cbx, self.svi_layer)

    @pyqtSlot()
    def on_output_data_dir_btn_clicked(self):
        default_dir = QSettings().value('irmt/output_data_dir',
                                        QDir.homePath())
        path = QFileDialog.getExistingDirectory(
            self, self.tr('Choose output directory'), default_dir)
        if path:
            QSettings().setValue('irmt/output_data_dir', path)
            self.output_data_dir_le.setText(path)

    def calculate_community_level_recovery_curve(
            self, point_attrs_dict, integrate_svi=True):
        # Developed By: Henry Burton
        # Edited by: Hua Kang
        # Reimplemented for this plugin by: Paolo Tormene and Marco Bernasocchi
        # Objective: GenerateCommunityLevelRecoveryCurve
        # Initial date: August 26, 2016

        zone_field_name = None
        if integrate_svi:
            self.svi_layer = self.svi_layer_cbx.itemData(
                    self.svi_layer_cbx.currentIndex())
            # FIXME self.svi_field_name is temporarily ignored
            # self.svi_field_name = self.svi_field_name_cbx.currentText()
            zone_field_name = self.zone_field_name_cbx.currentText()

        approach = self.approach_cbx.currentText()
        dmg_by_asset_features = list(self.dmg_by_asset_layer.getFeatures())
        recovery = RecoveryModeling(
            dmg_by_asset_features, approach, self.iface, self.svi_layer,
            self.output_data_dir, self.save_bldg_curves_check.isChecked())

        probs_field_names = list(self.fields_multiselect.get_selected_items())
        for i, fieldname in enumerate(probs_field_names):
            probs_field_names[i] = point_attrs_dict[fieldname]
        zonal_dmg_by_asset_probs, zonal_asset_refs = \
            recovery.collect_zonal_data(
                probs_field_names, integrate_svi, zone_field_name)

        # Incorporate Napa Data to community recovery model
        summary_filename = os.path.join(
            self.output_data_dir, 'summary.csv')
        summary = open(summary_filename, 'w')
        writer = csv.writer(summary)
        header = ['zone_id', 'days_to_recover_95_perc', 'event_time',
                  'after_6_months', 'after_12_months', 'after_18_months']
        writer.writerow(header)
        n_simulations = self.n_simulations_sbx.value()
        n_zones = len(zonal_dmg_by_asset_probs)
        # for each zone, calculate a zone-level recovery function
        for zone_index, zone_id in enumerate(
                zonal_dmg_by_asset_probs.keys(), start=1):
            seed = None
            if DEBUG:
                seed = 42
            recovery.generate_community_level_recovery_curve(
                zone_id, zonal_dmg_by_asset_probs,
                zonal_asset_refs, writer, integrate_svi, seed,
                n_simulations=n_simulations, n_zones=n_zones,
                zone_index=zone_index)
        summary.close()

    def accept(self):
        if self.integrate_svi_check.isChecked():
            self.zone_field_name = self.zone_field_name_cbx.currentText()
            (point_attrs_dict, self.dmg_by_asset_layer, self.svi_layer,
             self.zone_field_name) = add_zone_id_to_points(
                self.iface, self.dmg_by_asset_layer,
                self.svi_layer, None, self.zone_field_name)
        with WaitCursorManager('Generating recovery curves...', self.iface):
            self.calculate_community_level_recovery_curve(
                point_attrs_dict,
                self.integrate_svi_check.isChecked())
        msg = 'Recovery curves have been saved to [%s]' % self.output_data_dir
        log_msg(msg, level='I', message_bar=self.iface.messageBar())
        self.saveState()
        super(RecoveryModelingDialog, self).accept()
