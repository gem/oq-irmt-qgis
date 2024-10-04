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
from qgis.PyQt.QtWidgets import QDialog, QColorDialog, QMessageBox
from qgis.PyQt.QtGui import QPalette

from qgis.core import (
    QgsGraduatedSymbolRenderer, QgsProject, Qgis, QgsApplication)
from qgis.gui import QgsMessageBar

from requests import Session
from svir.dialogs.connection_profile_dialog import ConnectionProfileDialog
from svir.utilities.utils import (
                                  get_irmt_version,
                                  get_ui_class,
                                  get_style,
                                  engine_login,
                                  log_msg,
                                  WaitCursorManager,
                                  check_is_lockdown,
                                  )
from svir.utilities.shared import (
                                   DEFAULT_SETTINGS,
                                   DEFAULT_ENGINE_PROFILES,
                                   LOG_LEVELS,
                                   )

FORM_CLASS = get_ui_class('ui_settings.ui')


class SettingsDialog(QDialog, FORM_CLASS):
    """
    Dialog used to edit the plugin settings
    """
    def __init__(self, iface, irmt_main=None, parent=None):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        # in order to reset login when new credentials are saved
        self.irmt_main = irmt_main
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.message_bar = QgsMessageBar(self)
        irmt_version = get_irmt_version()
        self.setWindowTitle('OpenQuake IRMT v%s Settings' % irmt_version)
        self.layout().insertWidget(0, self.message_bar)

        for log_level in sorted(LOG_LEVELS):
            self.log_level_cbx.addItem(LOG_LEVELS[log_level], log_level)

        self.restore_state()
        self.initial_engine_hostname = QSettings().value(
            'irmt/engine_hostname')

    def restore_state(self, restore_defaults=False):
        """
        Reinstate the options based on the user's stored session info.

        :param restore_defaults: if True, settings will be reset to the default
            values, instead of reading them from the user's stored info
        """
        mySettings = QSettings()

        self.refresh_profile_cbxs(restore_defaults=restore_defaults)

        developer_mode = (DEFAULT_SETTINGS['developer_mode']
                          if restore_defaults
                          else mySettings.value(
                              'irmt/developer_mode', False, type=bool))
        experimental_enabled = (DEFAULT_SETTINGS['experimental_enabled']
                                if restore_defaults
                                else mySettings.value(
                                    'irmt/experimental_enabled',
                                    False, type=bool))

        log_level = (DEFAULT_SETTINGS['log_level']
                     if restore_defaults
                     else mySettings.value(
                         'irmt/log_level',
                         DEFAULT_SETTINGS['log_level']))
        self.log_level_cbx.setCurrentIndex(
            self.log_level_cbx.findData(log_level))

        style = get_style(
            self.iface.activeLayer(),
            self.iface.messageBar(),
            restore_defaults)

        self.developer_mode_ckb.setChecked(developer_mode)
        self.enable_experimental_ckb.setChecked(experimental_enabled)

    def refresh_profile_cbxs(self, restore_defaults=False):
        self.engine_profile_cbx.blockSignals(True)
        self.engine_profile_cbx.clear()
        self.engine_profile_cbx.blockSignals(False)
        mySettings = QSettings()
        if restore_defaults:
            profiles = json.loads(DEFAULT_ENGINE_PROFILES)
            cur_profile = list(profiles.keys())[0]
        else:
            profiles = json.loads(
                mySettings.value(
                    'irmt/engine_profiles', DEFAULT_ENGINE_PROFILES))
            cur_profile = mySettings.value(
                'irmt/current_engine_profile')
        for profile in sorted(profiles, key=str.lower):
            self.engine_profile_cbx.blockSignals(True)
            self.engine_profile_cbx.addItem(profile)
            self.engine_profile_cbx.blockSignals(False)
        if cur_profile is None:
            cur_profile = list(profiles.keys())[0]
            mySettings.setValue(
                'irmt/current_engine_profile', cur_profile)
        self.engine_profile_cbx.setCurrentIndex(
            self.engine_profile_cbx.findText(cur_profile))
        self.eng_remove_btn.setEnabled(
            self.engine_profile_cbx.count() > 1)

    def set_button_color(self, button, color):
        button.setStyleSheet("background-color: %s" % color.name())

    def save_state(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QSettings()

        mySettings.setValue('irmt/developer_mode',
                            self.developer_mode_ckb.isChecked())
        mySettings.setValue('irmt/experimental_enabled',
                            self.enable_experimental_ckb.isChecked())
        mySettings.setValue(
            'irmt/log_level',
            self.log_level_cbx.itemData(self.log_level_cbx.currentIndex()))

        cur_eng_profile = self.engine_profile_cbx.currentText()

        engine_profiles = json.loads(mySettings.value(
            'irmt/engine_profiles', DEFAULT_ENGINE_PROFILES))
        engine_profile = engine_profiles[cur_eng_profile]

        mySettings.setValue('irmt/engine_hostname',
                            engine_profile['hostname'])
        mySettings.setValue('irmt/engine_username',
                            engine_profile['username'])
        mySettings.setValue('irmt/engine_password',
                            engine_profile['password'])

    @pyqtSlot()
    def on_restore_default_settings_btn_clicked(self):
        msg = ("All current settings will be deleted and replaced by defaults."
               " Are you sure?")
        reply = QMessageBox.question(
            self, 'Warning', msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.restore_state(restore_defaults=True)

    @pyqtSlot(int)
    def on_engine_profile_cbx_currentIndexChanged(self, idx):
        profile = self.engine_profile_cbx.itemText(idx)
        QSettings().setValue('irmt/current_engine_profile', profile)

    @pyqtSlot()
    def on_eng_edit_btn_clicked(self):
        profile_name = self.engine_profile_cbx.currentText()
        self.profile_dlg = ConnectionProfileDialog(profile_name, parent=self)
        if self.profile_dlg.exec_():
            self.refresh_profile_cbxs()

    @pyqtSlot()
    def on_eng_test_btn_clicked(self):
        profile_name = self.engine_profile_cbx.currentText()
        with WaitCursorManager('Logging in...', self.message_bar):
            self._attempt_login(profile_name)

    def _attempt_login(self, profile_name):
        default_profiles = DEFAULT_ENGINE_PROFILES
        login_func = engine_login
        mySettings = QSettings()
        profiles = json.loads(mySettings.value(
            'irmt/engine_profiles', default_profiles))
        profile = profiles[profile_name]
        session = Session()
        hostname, username, password = (profile['hostname'],
                                        profile['username'],
                                        profile['password'])
        try:
            is_lockdown = check_is_lockdown(hostname, session)
        except Exception as exc:
            err_msg = ("Unable to connect")
            log_msg(err_msg, level='C', message_bar=self.message_bar,
                    exception=exc)
            return
        else:
            if not is_lockdown:
                msg = 'Able to connect'
                log_msg(msg, level='S', message_bar=self.message_bar,
                        duration=3)
                return
        try:
            login_func(hostname, username, password, session)
        except Exception as exc:
            err_msg = "Unable to connect (see Log Message Panel for details)"
            log_msg(err_msg, level='C', message_bar=self.message_bar,
                    exception=exc)
        else:
            msg = 'Able to connect'
            log_msg(msg, level='S', message_bar=self.message_bar, duration=3)

    @pyqtSlot()
    def on_eng_new_btn_clicked(self):
        self.profile_dlg = ConnectionProfileDialog(parent=self)
        if self.profile_dlg.exec_():
            self.refresh_profile_cbxs()

    @pyqtSlot()
    def on_eng_remove_btn_clicked(self):
        self.remove_selected_profile()

    def remove_selected_profile(self):
        if QMessageBox.question(
                self,
                'Remove connection profile',
                ('If you continue, the selected profile will be permanently'
                 ' deleted. Are you sure?'),
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        profiles = json.loads(
            QSettings().value('irmt/engine_profiles'))
        cur_profile = self.engine_profile_cbx.currentText()
        del profiles[cur_profile]
        QSettings().remove('irmt/current_engine_profile')
        self.save_profiles(profiles)
        self.refresh_profile_cbxs()

    def save_profiles(self, profiles):
        QSettings().setValue('irmt/engine_profiles', json.dumps(profiles))

    def select_color(self, button):
        initial = button.palette().color(QPalette.Button)
        color = QColorDialog.getColor(initial)
        if color.isValid():
            self.set_button_color(button, color)

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.save_state()
        if self.irmt_main is not None:
            self.irmt_main.reset_drive_oq_engine_server_dlg()
        current_engine_hostname = QSettings().value('irmt/engine_hostname')
        # in case the engine hostname was modified, the embedded web apps that
        # were using the old hostname must be refreshed using the new one
        # (set_host is called in their __init__ when dialogs are created, and
        # it needs to be called again here if those dialogs are already
        # initialized and pointing to a previous engine server)
        if (current_engine_hostname != self.initial_engine_hostname
                and self.irmt_main is not None):
            for dlg in (self.irmt_main.ipt_dlg,
                        self.irmt_main.taxtweb_dlg,
                        self.irmt_main.taxonomy_dlg):
                if dlg is not None:
                    dlg.set_host()
                    dlg.load_homepage()
        super(SettingsDialog, self).accept()
