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

from qgis.core import QgsGraduatedSymbolRenderer, QgsProject
from qgis.gui import QgsMessageBar

from requests import Session
from svir.dialogs.connection_profile_dialog import ConnectionProfileDialog
from svir.utilities.utils import (
                                  get_ui_class,
                                  get_style,
                                  platform_login,
                                  geoviewer_login,
                                  engine_login,
                                  log_msg,
                                  WaitCursorManager,
                                  check_is_lockdown,
                                  )
from svir.utilities.shared import (
                                   PLATFORM_REGISTRATION_URL,
                                   DEFAULT_SETTINGS,
                                   DEFAULT_PLATFORM_PROFILES,
                                   DEFAULT_GEOVIEWER_PROFILES,
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
        self.layout().insertWidget(0, self.message_bar)
        link_text = ('<a href="%s">Register to the OpenQuake Platform</a>'
                     % PLATFORM_REGISTRATION_URL)
        self.registration_link_lbl.setText(link_text)

        self.style_color_from.setFocusPolicy(Qt.NoFocus)
        self.style_color_to.setFocusPolicy(Qt.NoFocus)

        modes = {
            QgsGraduatedSymbolRenderer.EqualInterval: self.tr(
                'Equal Interval'),
            QgsGraduatedSymbolRenderer.Quantile: self.tr(
                'Quantile (Equal Count)'),
            QgsGraduatedSymbolRenderer.Jenks: self.tr(
                'Natural Breaks (Jenks)'),
            QgsGraduatedSymbolRenderer.StdDev: self.tr('Standard Deviation'),
            QgsGraduatedSymbolRenderer.Pretty: self.tr('Pretty Breaks'),
        }
        for key in modes:
            self.style_mode.addItem(modes[key], key)

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

        self.refresh_profile_cbxs('platform', restore_defaults)
        self.refresh_profile_cbxs('geoviewer', restore_defaults)
        self.refresh_profile_cbxs('engine', restore_defaults)

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

        self.set_button_color(self.style_color_from, style['color_from'])
        self.set_button_color(self.style_color_to, style['color_to'])

        mode_idx = self.style_mode.findData(style['mode'])
        self.style_mode.setCurrentIndex(mode_idx)

        self.style_classes.setValue(style['classes'])
        self.force_restyling_ckb.setChecked(style['force_restyling'])

        self.developer_mode_ckb.setChecked(developer_mode)
        self.enable_experimental_ckb.setChecked(experimental_enabled)

    def refresh_profile_cbxs(self, server, restore_defaults=False):
        assert server in ('platform', 'engine', 'geoviewer'), server
        if server == 'platform':
            self.platform_profile_cbx.blockSignals(True)
            self.platform_profile_cbx.clear()
            self.platform_profile_cbx.blockSignals(False)
            default_profiles = DEFAULT_PLATFORM_PROFILES
        elif server == 'geoviewer':
            self.geoviewer_profile_cbx.blockSignals(True)
            self.geoviewer_profile_cbx.clear()
            self.geoviewer_profile_cbx.blockSignals(False)
            default_profiles = DEFAULT_GEOVIEWER_PROFILES
        else:  # 'engine'
            self.engine_profile_cbx.blockSignals(True)
            self.engine_profile_cbx.clear()
            self.engine_profile_cbx.blockSignals(False)
            default_profiles = DEFAULT_ENGINE_PROFILES
        mySettings = QSettings()
        if restore_defaults:
            profiles = json.loads(default_profiles)
            cur_profile = list(profiles.keys())[0]
        else:
            profiles = json.loads(
                mySettings.value(
                    'irmt/%s_profiles' % server, default_profiles))
            cur_profile = mySettings.value(
                'irmt/current_%s_profile' % server)
        for profile in sorted(profiles, key=str.lower):
            if server == 'platform':
                self.platform_profile_cbx.blockSignals(True)
                self.platform_profile_cbx.addItem(profile)
                self.platform_profile_cbx.blockSignals(False)
            elif server == 'geoviewer':
                self.geoviewer_profile_cbx.blockSignals(True)
                self.geoviewer_profile_cbx.addItem(profile)
                self.geoviewer_profile_cbx.blockSignals(False)
            else:  # engine
                self.engine_profile_cbx.blockSignals(True)
                self.engine_profile_cbx.addItem(profile)
                self.engine_profile_cbx.blockSignals(False)
        if cur_profile is None:
            cur_profile = list(profiles.keys())[0]
            mySettings.setValue(
                'irmt/current_%s_profile' % server,
                cur_profile)
        if server == 'platform':
            self.platform_profile_cbx.setCurrentIndex(
                self.platform_profile_cbx.findText(cur_profile))
            self.pla_remove_btn.setEnabled(
                self.platform_profile_cbx.count() > 1)
        elif server == 'geoviewer':
            self.geoviewer_profile_cbx.setCurrentIndex(
                self.geoviewer_profile_cbx.findText(cur_profile))
            self.gv_remove_btn.setEnabled(
                self.geoviewer_profile_cbx.count() > 1)
        else:  # engine
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

        cur_pla_profile = self.platform_profile_cbx.currentText()
        cur_gv_profile = self.geoviewer_profile_cbx.currentText()
        cur_eng_profile = self.engine_profile_cbx.currentText()

        platform_profiles = json.loads(mySettings.value(
            'irmt/platform_profiles', DEFAULT_PLATFORM_PROFILES))
        platform_profile = platform_profiles[cur_pla_profile]
        geoviewer_profiles = json.loads(mySettings.value(
            'irmt/geoviewer_profiles', DEFAULT_GEOVIEWER_PROFILES))
        geoviewer_profile = geoviewer_profiles[cur_gv_profile]
        engine_profiles = json.loads(mySettings.value(
            'irmt/engine_profiles', DEFAULT_ENGINE_PROFILES))
        engine_profile = engine_profiles[cur_eng_profile]

        mySettings.setValue('irmt/platform_hostname',
                            platform_profile['hostname'])
        mySettings.setValue('irmt/platform_username',
                            platform_profile['username'])
        mySettings.setValue('irmt/platform_password',
                            platform_profile['password'])
        mySettings.setValue('irmt/geoviewer_hostname',
                            geoviewer_profile['hostname'])
        mySettings.setValue('irmt/geoviewer_username',
                            geoviewer_profile['username'])
        mySettings.setValue('irmt/geoviewer_password',
                            geoviewer_profile['password'])
        mySettings.setValue('irmt/engine_hostname',
                            engine_profile['hostname'])
        mySettings.setValue('irmt/engine_username',
                            engine_profile['username'])
        mySettings.setValue('irmt/engine_password',
                            engine_profile['password'])

        color_from = self.style_color_from.palette().color(QPalette.Button)
        mySettings.setValue(
            'irmt/style_color_from',
            color_from.rgba())
        color_to = self.style_color_to.palette().color(QPalette.Button)
        mySettings.setValue(
            'irmt/style_color_to',
            color_to.rgba())

        mySettings.setValue('irmt/style_mode', self.style_mode.itemData(
            self.style_mode.currentIndex()))

        mySettings.setValue('irmt/style_classes', self.style_classes.value())
        active_layer = self.iface.activeLayer()
        # at project level, save the setting associated to the layer if
        # available
        if active_layer is not None:
            # NOTE: We can't use %s/%s instead of %s_%s, because / is a special
            #       character
            QgsProject.instance().writeEntry(
                'irmt', '%s_%s' % (active_layer.id(), 'force_restyling'),
                self.force_restyling_ckb.isChecked())
        else:  # no layer is selected
            QgsProject.instance().writeEntry(
                'irmt', 'force_restyling',
                self.force_restyling_ckb.isChecked())
        # keep the latest setting saved also into the general settings
        mySettings.setValue('irmt/force_restyling',
                            self.force_restyling_ckb.isChecked())

    @pyqtSlot()
    def on_style_color_from_clicked(self):
        self.select_color(self.style_color_from)

    @pyqtSlot()
    def on_style_color_to_clicked(self):
        self.select_color(self.style_color_to)

    @pyqtSlot()
    def on_restore_default_settings_btn_clicked(self):
        msg = ("All current settings will be deleted and replaced by defaults."
               " Are you sure?")
        reply = QMessageBox.question(
            self, 'Warning', msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.restore_state(restore_defaults=True)

    @pyqtSlot(int)
    def on_platform_profile_cbx_currentIndexChanged(self, idx):
        profile = self.platform_profile_cbx.itemText(idx)
        QSettings().setValue('irmt/current_platform_profile', profile)

    @pyqtSlot(int)
    def on_geoviewer_profile_cbx_currentIndexChanged(self, idx):
        profile = self.geoviewer_profile_cbx.itemText(idx)
        QSettings().setValue('irmt/current_geoviewer_profile', profile)

    @pyqtSlot(int)
    def on_engine_profile_cbx_currentIndexChanged(self, idx):
        profile = self.engine_profile_cbx.itemText(idx)
        QSettings().setValue('irmt/current_engine_profile', profile)

    def edit_profile(self, profile_name, server):
        self.profile_dlg = ConnectionProfileDialog(
            server, profile_name, parent=self)
        if self.profile_dlg.exec_():
            self.refresh_profile_cbxs(server)

    def new_profile(self, server):
        self.profile_dlg = ConnectionProfileDialog(server, parent=self)
        if self.profile_dlg.exec_():
            self.refresh_profile_cbxs(server)

    def test_profile(self, profile_name, server):
        with WaitCursorManager('Logging in...', self.message_bar):
            self._attempt_login(server, profile_name)

    @pyqtSlot()
    def on_pla_edit_btn_clicked(self):
        self.edit_profile(
            self.platform_profile_cbx.currentText(), 'platform')

    @pyqtSlot()
    def on_gv_edit_btn_clicked(self):
        self.edit_profile(
            self.geoviewer_profile_cbx.currentText(), 'geoviewer')

    @pyqtSlot()
    def on_eng_edit_btn_clicked(self):
        self.edit_profile(
            self.engine_profile_cbx.currentText(), 'engine')

    @pyqtSlot()
    def on_pla_new_btn_clicked(self):
        self.new_profile('platform')

    @pyqtSlot()
    def on_gv_new_btn_clicked(self):
        self.new_profile('geoviewer')

    @pyqtSlot()
    def on_eng_new_btn_clicked(self):
        self.new_profile('engine')

    @pyqtSlot()
    def on_pla_test_btn_clicked(self):
        self.test_profile(
             self.platform_profile_cbx.currentText(), 'platform')

    @pyqtSlot()
    def on_gv_test_btn_clicked(self):
        self.test_profile(
             self.geoviewer_profile_cbx.currentText(), 'geoviewer')

    @pyqtSlot()
    def on_eng_test_btn_clicked(self):
        self.test_profile(
             self.engine_profile_cbx.currentText(), 'engine')

    def _attempt_login(self, server, profile_name):
        if server == 'platform':
            default_profiles = DEFAULT_PLATFORM_PROFILES
            login_func = platform_login
        elif server == 'geoviewer':
            default_profiles = DEFAULT_GEOVIEWER_PROFILES
            login_func = geoviewer_login
        elif server == 'engine':
            default_profiles = DEFAULT_ENGINE_PROFILES
            login_func = engine_login
        else:
            raise NotImplementedError(server)
        mySettings = QSettings()
        profiles = json.loads(mySettings.value(
            'irmt/%s_profiles' % server, default_profiles))
        profile = profiles[profile_name]
        session = Session()
        hostname, username, password = (profile['hostname'],
                                        profile['username'],
                                        profile['password'])
        if server == 'engine':
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
    def on_pla_remove_btn_clicked(self):
        self.remove_selected_profile('platform')

    @pyqtSlot()
    def on_gv_remove_btn_clicked(self):
        self.remove_selected_profile('geoviewer')

    @pyqtSlot()
    def on_eng_remove_btn_clicked(self):
        self.remove_selected_profile('engine')

    def remove_selected_profile(self, server):
        assert server in ('platform', 'geoviewer', 'engine'), server
        if QMessageBox.question(
                self,
                'Remove connection profile',
                ('If you continue, the selected profile will be permanently'
                 ' deleted. Are you sure?'),
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        profiles = json.loads(
            QSettings().value('irmt/%s_profiles' % server))
        if server == 'platform':
            cur_profile = self.platform_profile_cbx.currentText()
        elif server == 'geoviewer':
            cur_profile = self.geoviewer_profile_cbx.currentText()
        else:  # engine
            cur_profile = self.engine_profile_cbx.currentText()
        del profiles[cur_profile]
        QSettings().remove('irmt/current_%s_profile' % server)
        self.save_profiles(server, profiles)
        self.refresh_profile_cbxs(server)

    def save_profiles(self, server, profiles):
        assert server in ('platform', 'geoviewer', 'engine'), server
        QSettings().setValue('irmt/%s_profiles' % server,
                             json.dumps(profiles))

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
