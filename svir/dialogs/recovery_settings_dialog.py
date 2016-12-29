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
from PyQt4.QtCore import pyqtSlot, QSettings, Qt
from PyQt4.QtGui import (QDialog,
                         QTableWidgetItem,
                         QDialogButtonBox)
from svir.utilities.utils import get_ui_class
from svir.utilities.shared import RECOVERY_DEFAULTS

FORM_CLASS = get_ui_class('ui_recovery_settings.ui')


class RecoverySettingsDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to set parameters for recovery modeling analysis.
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.restoreState(restore_defaults=False)
        self.set_ok_button()

    def restoreState(self, restore_defaults=False):
        """
        Reinstate the options based on the user's stored session info.
        """
        # TODO: add some sanity checks on array dimensions

        mySettings = QSettings()
        if restore_defaults:
            for setting in ('irmt/n_loss_based_dmg_states',
                            'irmt/n_loss_based_dmg_states',
                            'irmt/n_recovery_based_dmg_states',
                            'irmt/transfer_probabilities',
                            'irmt/assessment_times',
                            'irmt/inspection_times',
                            'irmt/mobilization_times',
                            'irmt/recovery_times',
                            'irmt/repair_times',
                            'irmt/lead_time_dispersion',
                            'irmt/repair_time_dispersion'):
                mySettings.remove(setting)

        n_loss_based_dmg_states = int(mySettings.value(
            'irmt/n_loss_based_dmg_states',
            RECOVERY_DEFAULTS['n_loss_based_dmg_states']))
        self.n_loss_based_dmg_states_sbx.setValue(n_loss_based_dmg_states)

        n_recovery_based_dmg_states = int(mySettings.value(
            'irmt/n_recovery_based_dmg_states',
            RECOVERY_DEFAULTS['n_recovery_based_dmg_states']))
        self.n_recovery_based_dmg_states_sbx.setValue(
            n_recovery_based_dmg_states)

        transfer_probabilities_str = mySettings.value(
            'irmt/transfer_probabilities', None)
        if transfer_probabilities_str is None:
            transfer_probabilities = list(RECOVERY_DEFAULTS[
                'transfer_probabilities'])
        else:
            transfer_probabilities = json.loads(transfer_probabilities_str)
        self.transfer_probabilities_tbl.setRowCount(n_loss_based_dmg_states)
        self.transfer_probabilities_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        for row in range(n_loss_based_dmg_states):
            for col in range(n_recovery_based_dmg_states):
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, transfer_probabilities[row][col])
                self.transfer_probabilities_tbl.setItem(row, col, item)
        self.transfer_probabilities_tbl.resizeRowsToContents()
        self.transfer_probabilities_tbl.resizeColumnsToContents()

        self.restore_times('assessment_times', self.assessment_times_tbl)
        self.restore_times('inspection_times', self.inspection_times_tbl)
        self.restore_times('mobilization_times', self.mobilization_times_tbl)
        self.restore_times('recovery_times', self.recovery_times_tbl)
        self.restore_times('repair_times', self.repair_times_tbl)

        lead_time_dispersion = float(mySettings.value(
            'irmt/lead_time_dispersion',
            RECOVERY_DEFAULTS['lead_time_dispersion']))
        self.lead_time_dispersion_sbx.setValue(lead_time_dispersion)

        repair_time_dispersion = float(mySettings.value(
            'irmt/repair_time_dispersion',
            RECOVERY_DEFAULTS['repair_time_dispersion']))
        self.repair_time_dispersion_sbx.setValue(repair_time_dispersion)

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QSettings()
        n_loss_based_dmg_states = self.n_loss_based_dmg_states_sbx.value()
        mySettings.setValue('irmt/n_loss_based_dmg_states',
                            n_loss_based_dmg_states)
        n_recovery_based_dmg_states = \
            self.n_recovery_based_dmg_states_sbx.value()
        mySettings.setValue('irmt/n_recovery_based_dmg_states',
                            n_recovery_based_dmg_states)
        transfer_probabilities = [
            [0 for col in range(n_recovery_based_dmg_states)]
            for row in range(n_loss_based_dmg_states)]
        for row in range(n_loss_based_dmg_states):
            for col in range(n_recovery_based_dmg_states):
                transfer_probabilities[row][col] = float(
                    self.transfer_probabilities_tbl.item(row, col).text())
        mySettings.setValue('irmt/transfer_probabilities',
                            json.dumps(transfer_probabilities))
        self.save_times('assessment_times', self.assessment_times_tbl)
        self.save_times('inspection_times', self.inspection_times_tbl)
        self.save_times('mobilization_times', self.mobilization_times_tbl)
        self.save_times('recovery_times', self.recovery_times_tbl)
        self.save_times('repair_times', self.repair_times_tbl)
        lead_time_dispersion = self.lead_time_dispersion_sbx.value()
        mySettings.setValue('irmt/lead_time_dispersion', lead_time_dispersion)
        repair_time_dispersion = self.repair_time_dispersion_sbx.value()
        mySettings.setValue('irmt/repair_time_dispersion',
                            repair_time_dispersion)

    def save_times(self, times_type, times_table):
        mySettings = QSettings()
        times = [int(times_table.item(0, col).text())
                 for col in range(times_table.columnCount())]
        mySettings.setValue('irmt/%s' % times_type, json.dumps(times))

    def restore_times(self, times_type, times_table):
        mySettings = QSettings()
        times_str = mySettings.value('irmt/%s' % times_type, '')
        if times_str:
            times = json.loads(times_str)
        else:
            times = list(RECOVERY_DEFAULTS[times_type])
        times_table.setRowCount(1)
        times_table.setColumnCount(len(times))
        for col in range(len(times)):
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, times[col])
            times_table.setItem(0, col, item)
        times_table.resizeRowsToContents()
        times_table.resizeColumnsToContents()

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def accept(self):
        self.saveState()
        super(RecoverySettingsDialog, self).accept()

    @pyqtSlot()
    def on_restore_defaults_btn_clicked(self):
        self.restoreState(restore_defaults=True)

    @pyqtSlot(int)
    def on_n_loss_based_dmg_states_sbx_valueChanged(
            self, n_loss_based_dmg_states):
        self.transfer_probabilities_tbl.setRowCount(n_loss_based_dmg_states)

    @pyqtSlot(int)
    def on_n_recovery_based_dmg_states_sbx_valueChanged(
            self, n_recovery_based_dmg_states):
        self.transfer_probabilities_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        self.assessment_times_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        self.inspection_times_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        self.mobilization_times_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        self.recovery_times_tbl.setColumnCount(
            n_recovery_based_dmg_states)
        self.repair_times_tbl.setColumnCount(
            n_recovery_based_dmg_states)
