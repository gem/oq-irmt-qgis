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
from qgis.gui import QgsMessageBar
from svir.calculations.aggregate_loss_by_zone import add_zone_id_to_points
from svir.utilities.utils import (get_ui_class,
                                  reload_attrib_cbx,
                                  WaitCursorManager,
                                  create_progress_message_bar,
                                  clear_progress_message_bar,
                                  tr,
                                  TraceTimeManager,
                                  )
from svir.utilities.shared import DEBUG
from svir.recovery_modeling.recovery_modeling import RecoveryModeling

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
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.populate_approach_cbx()
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

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QSettings()
        output_data_dir = mySettings.value('irmt/recovery_output_data_dir', '')
        # hack for strange mac behaviour
        if not output_data_dir:
            output_data_dir = ''
        self.output_data_dir_le.setText(output_data_dir)

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
            and self.approach_cbx.currentIndex != -1)
        # and self.dmg_by_asset_layer_cbx.currentIndex != -1
        # and self.svi_layer_cbx.currentIndex != -1
        # and self.svi_field_name_cbx.currentIndex != -1
        # and self.zone_field_name_cbx.currentIndex != -1)

    def populate_approach_cbx(self):
        self.approach_cbx.addItems(['Disaggregate', 'Aggregate'])

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

    @pyqtSlot(int)
    def on_svi_layer_cbx_currentIndexChanged(self, selected_index):
        self.svi_layer = self.svi_layer_cbx.itemData(selected_index)
        # FIXME self.svi_field_name is temporarily ignored
        # reload_attrib_cbx(self.svi_field_name_cbx, self.svi_layer)
        reload_attrib_cbx(self.zone_field_name_cbx, self.svi_layer)

    @pyqtSlot()
    def on_output_data_dir_btn_clicked(self):
        path = QFileDialog.getExistingDirectory(
            self, self.tr('Choose output directory'), QDir.homePath())
        if path:
            self.output_data_dir_le.setText(path)

    def calculate_community_level_recovery_curve(self, integrate_svi=True):
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
            self.output_data_dir)

        zonal_dmg_by_asset_probs, zonal_asset_refs = \
            recovery.collect_zonal_data(integrate_svi, zone_field_name)

        # Incorporate Napa Data to community recovery model
        tot_zones = len(zonal_dmg_by_asset_probs)
        msg = 'Calculating zone-level recovery curves...'
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)
        summary_filename = os.path.join(
            self.output_data_dir, 'summary.csv')
        summary = open(summary_filename, 'w')
        writer = csv.writer(summary)
        header = ['zone_id', 'days_to_recover_95_perc', 'event_time',
                  'after_6_months', 'after_12_months', 'after_18_months']
        writer.writerow(header)
        # for each zone, calculate a zone-level recovery function
        for idx, zone_id in enumerate(zonal_dmg_by_asset_probs.keys(),
                                      start=1):
            msg = ('Generating community level recovery curve for zone "%s"'
                   % zone_id)
            seed = None
            if DEBUG:
                seed = 42
            with TraceTimeManager(msg):
                recovery.generate_community_level_recovery_curve(
                    zone_id, zonal_dmg_by_asset_probs,
                    zonal_asset_refs, writer, integrate_svi, seed)

            progress_perc = idx / float(tot_zones) * 100
            progress.setValue(progress_perc)

        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        summary.close()

    def accept(self):
        if self.integrate_svi_check.isChecked():
            self.zone_field_name = self.zone_field_name_cbx.currentText()
            (_, self.dmg_by_asset_layer, self.svi_layer,
             self.zone_field_name) = add_zone_id_to_points(
                self.iface, None, self.dmg_by_asset_layer,
                self.svi_layer, None, self.zone_field_name)
        with WaitCursorManager('Generating recovery curves...', self.iface):
            self.calculate_community_level_recovery_curve(
                self.integrate_svi_check.isChecked())
        self.iface.messageBar().pushMessage(
            tr("Info"),
            'Recovery curves have been saved to [%s]' % self.output_data_dir,
            level=QgsMessageBar.INFO, duration=0)
        self.saveState()
        super(RecoveryModelingDialog, self).accept()
