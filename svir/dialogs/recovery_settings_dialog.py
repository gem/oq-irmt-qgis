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
from qgis.PyQt.QtCore import pyqtSlot, QSettings, Qt
from qgis.PyQt.QtWidgets import QDialog, QTableWidgetItem, QDialogButtonBox
from qgis.core import QgsProject
from svir.utilities.utils import (get_ui_class,
                                  get_layer_setting,
                                  save_layer_setting)
from svir.utilities.shared import RECOVERY_DEFAULTS
from svir.utilities.utils import log_msg

FORM_CLASS = get_ui_class('ui_recovery_settings.ui')


class RecoverySettingsDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to set parameters for recovery modeling analysis.
    """
    def __init__(self, iface):
        self.iface = iface
        self.layer = self.iface.activeLayer()
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.restore_state(restore_defaults=False)
        self.set_ok_button()

    def restore_state(self, restore_defaults=False):
        """
        Reinstate the options based on the user's stored session info.
        """
        # TODO: add some sanity checks on array dimensions

        if restore_defaults:
            for scope, setting in (
                    ('irmt', 'n_loss_based_dmg_states'),
                    ('irmt', 'n_loss_based_dmg_states'),
                    ('irmt', 'n_recovery_based_dmg_states'),
                    ('irmt', 'transfer_probabilities'),
                    ('irmt', 'assessment_times'),
                    ('irmt', 'inspection_times'),
                    ('irmt', 'mobilization_times'),
                    ('irmt', 'recovery_times'),
                    ('irmt', 'repair_times'),
                    ('irmt', 'lead_time_dispersion'),
                    ('irmt', 'repair_time_dispersion')):
                QSettings().remove('%s/%s' % (scope, setting))
                if self.layer:
                    QgsProject.instance().removeEntry(
                        scope, '%s/%s' % (self.layer.id(), setting))

        self.restore_setting_number(
            'n_loss_based_dmg_states', self.n_loss_based_dmg_states_sbx, int)
        self.restore_setting_number('n_recovery_based_dmg_states',
                                    self.n_recovery_based_dmg_states_sbx, int)
        self.restore_setting_2d_table(
            'transfer_probabilities', self.transfer_probabilities_tbl)
        self.restore_setting_1d_table(
            'assessment_times', self.assessment_times_tbl)
        self.restore_setting_1d_table(
            'inspection_times', self.inspection_times_tbl)
        self.restore_setting_1d_table(
            'mobilization_times', self.mobilization_times_tbl)
        self.restore_setting_1d_table(
            'recovery_times', self.recovery_times_tbl)
        self.restore_setting_1d_table(
            'repair_times', self.repair_times_tbl)
        self.restore_setting_number(
            'lead_time_dispersion', self.lead_time_dispersion_sbx, float)
        self.restore_setting_number(
            'repair_time_dispersion', self.repair_time_dispersion_sbx, float)

    def save_state(self):
        """
        Store the options into the user's stored session info.
        """
        n_loss_based_dmg_states = self.n_loss_based_dmg_states_sbx.value()
        self.save_setting_number(
            'n_loss_based_dmg_states', n_loss_based_dmg_states, int)
        n_recovery_based_dmg_states = \
            self.n_recovery_based_dmg_states_sbx.value()
        self.save_setting_number(
            'n_recovery_based_dmg_states', n_recovery_based_dmg_states, int)
        self.save_setting_2d_table(
            'transfer_probabilities', self.transfer_probabilities_tbl, float,
            check_row_sum_to_1=True)
        self.save_setting_1d_table(
            'assessment_times', self.assessment_times_tbl, int)
        self.save_setting_1d_table(
            'inspection_times', self.inspection_times_tbl, int)
        self.save_setting_1d_table(
            'mobilization_times', self.mobilization_times_tbl, int)
        self.save_setting_1d_table(
            'recovery_times', self.recovery_times_tbl, int)
        self.save_setting_1d_table(
            'repair_times', self.repair_times_tbl, int)
        lead_time_dispersion = self.lead_time_dispersion_sbx.value()
        self.save_setting_number(
            'lead_time_dispersion', lead_time_dispersion, float)
        repair_time_dispersion = self.repair_time_dispersion_sbx.value()
        self.save_setting_number(
            'repair_time_dispersion', repair_time_dispersion, float)

    def save_setting_number(self, name, value, val_type):
        QSettings().setValue('irmt/%s' % name, value)
        save_layer_setting(self.layer, name, value)

    def save_setting_1d_table(self, name, table, val_type):
        elements = [0 for col in range(table.columnCount())]
        for col in range(table.columnCount()):
            elements[col] = val_type(table.item(0, col).text())
        QSettings().setValue('irmt/%s' % name, json.dumps(elements))
        save_layer_setting(self.layer, name, elements)

    def save_setting_2d_table(self, name, table, val_type,
                              check_row_sum_to_1=False):
        elements = [
            [0 for col in range(table.columnCount())]
            for row in range(table.rowCount())]
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                elements[row][col] = val_type(table.item(row, col).text())
            if check_row_sum_to_1:
                if abs(1 - sum(elements[row])) > 1e-15:
                    raise ValueError(
                        'In table %s, the elements of row %s do not sum to 1'
                        % (name, row + 1))
        QSettings().setValue('irmt/%s' % name, json.dumps(elements))
        save_layer_setting(self.layer, name, elements)

    def restore_setting_number(self, name, widget, val_type):
        value = get_layer_setting(self.layer, name)
        if value is None:
            value = val_type(QSettings().value(
                'irmt/%s' % name,
                RECOVERY_DEFAULTS[name]))
        widget.setValue(value)

    def restore_setting_1d_table(self, name, table):
        elements = get_layer_setting(self.layer, name)
        if elements is None:
            array_str = QSettings().value('irmt/%s' % name, None)
            if array_str:
                elements = json.loads(array_str)
            else:
                elements = list(RECOVERY_DEFAULTS[name])
        table.setRowCount(1)
        table.setColumnCount(len(elements))
        for col in range(table.columnCount()):
            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, elements[col])
            table.setItem(0, col, item)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()

    def restore_setting_2d_table(self, name, table):
        elements = get_layer_setting(self.layer, name)
        if elements is None:
            table_str = QSettings().value('irmt/%s' % name, None)
            if table_str:
                elements = json.loads(table_str)
            else:
                elements = list(RECOVERY_DEFAULTS[name])
        table.setRowCount(len(elements))
        table.setColumnCount(len(elements[0]))
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, elements[row][col])
                table.setItem(row, col, item)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def accept(self):
        try:
            self.save_state()
        except ValueError as exc:
            log_msg(str(exc), level='C',
                    message_bar=self.iface.messageBar(),
                    duration=5, exception=exc)
        else:
            super(RecoverySettingsDialog, self).accept()

    @pyqtSlot()
    def on_restore_defaults_btn_clicked(self):
        self.restore_state(restore_defaults=True)

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
