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


from PyQt4.QtCore import pyqtSlot, QSettings, Qt
from PyQt4.QtGui import QDialog, QPalette, QColorDialog, QMessageBox

from qgis.core import QgsGraduatedSymbolRendererV2, QgsProject

from svir.utilities.utils import get_ui_class, get_style
from svir.utilities.shared import PLATFORM_REGISTRATION_URL, DEFAULT_SETTINGS

FORM_CLASS = get_ui_class('ui_settings.ui')


class SettingsDialog(QDialog, FORM_CLASS):
    """
    Dialog used to specify the connection settings used to interact with the
    OpenQuake Platform or the OpenQuake Engine, and to toggle the
    developer mode option.
    """
    def __init__(self, iface, irmt_main=None, parent=None):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        # in order to reset login when new credentials are saved
        self.irmt_main = irmt_main
        # Set up the user interface from Designer.
        self.setupUi(self)
        link_text = ('<a href="%s">Register to the OpenQuake Platform</a>'
                     % PLATFORM_REGISTRATION_URL)
        self.registration_link_lbl.setText(link_text)

        self.style_color_from.setFocusPolicy(Qt.NoFocus)
        self.style_color_to.setFocusPolicy(Qt.NoFocus)

        modes = {
            QgsGraduatedSymbolRendererV2.EqualInterval: self.tr(
                'Equal Interval'),
            QgsGraduatedSymbolRendererV2.Quantile: self.tr(
                'Quantile (Equal Count)'),
            QgsGraduatedSymbolRendererV2.Jenks: self.tr(
                'Natural Breaks (Jenks)'),
            QgsGraduatedSymbolRendererV2.StdDev: self.tr('Standard Deviation'),
            QgsGraduatedSymbolRendererV2.Pretty: self.tr('Pretty Breaks'),
        }
        for key in modes:
            self.style_mode.addItem(modes[key], key)
        self.restore_state()

    def restore_state(self, restore_defaults=False):
        """
        Reinstate the options based on the user's stored session info.

        :param restore_defaults: if True, settings will be reset to the default
            values, instead of reading them from the user's stored info
        """
        mySettings = QSettings()

        platform_username = (DEFAULT_SETTINGS['platform_username']
                             if restore_defaults
                             else mySettings.value(
                                 'irmt/platform_username',
                                 DEFAULT_SETTINGS['platform_username']))
        platform_password = (DEFAULT_SETTINGS['platform_password']
                             if restore_defaults
                             else mySettings.value(
                                 'irmt/platform_password',
                                 DEFAULT_SETTINGS['platform_password']))
        platform_hostname = (DEFAULT_SETTINGS['platform_hostname']
                             if restore_defaults
                             else mySettings.value(
                                'irmt/platform_hostname',
                                DEFAULT_SETTINGS['platform_hostname']))

        engine_username = (DEFAULT_SETTINGS['engine_username']
                           if restore_defaults
                           else mySettings.value(
                               'irmt/engine_username',
                               DEFAULT_SETTINGS['engine_username']))
        engine_password = (DEFAULT_SETTINGS['engine_password']
                           if restore_defaults
                           else mySettings.value(
                               'irmt/engine_password',
                               DEFAULT_SETTINGS['engine_password']))
        engine_hostname = (DEFAULT_SETTINGS['engine_hostname']
                           if restore_defaults
                           else mySettings.value(
                               'irmt/engine_hostname',
                               DEFAULT_SETTINGS['engine_hostname']))
        developer_mode = (DEFAULT_SETTINGS['developer_mode']
                          if restore_defaults
                          else mySettings.value(
                              'irmt/developer_mode', False, type=bool))
        experimental_enabled = (DEFAULT_SETTINGS['experimental_enabled']
                                if restore_defaults
                                else mySettings.value(
                                    'irmt/experimental_enabled',
                                    False, type=bool))

        # hack for strange mac behaviour
        if not platform_username:
            platform_username = ''
        if not platform_password:
            platform_password = ''
        if not platform_hostname:
            platform_hostname = ''
        if not engine_username:
            engine_username = ''
        if not engine_password:
            engine_password = ''
        if not engine_hostname:
            engine_hostname = ''

        self.platformUsernameEdit.setText(platform_username)
        self.platformPasswordEdit.setText(platform_password)
        self.platformHostnameEdit.setText(platform_hostname)
        self.engineUsernameEdit.setText(engine_username)
        self.enginePasswordEdit.setText(engine_password)
        self.engineHostnameEdit.setText(engine_hostname)

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

    def set_button_color(self, button, color):
        button.setStyleSheet("background-color: %s" % color.name())

    def save_state(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QSettings()
        # if the (stripped) hostname ends with '/', remove it
        platform_hostname = \
            self.platformHostnameEdit.text().strip().rstrip('/')

        # if the (stripped) engine hostname ends with '/engine/', remove it
        engine_hostname = self.engineHostnameEdit.text(
            ).strip().rstrip('/')
        engine_hostname = (
            engine_hostname[:-7] if engine_hostname.endswith('/engine')
            else engine_hostname)

        mySettings.setValue('irmt/developer_mode',
                            self.developer_mode_ckb.isChecked())
        mySettings.setValue('irmt/experimental_enabled',
                            self.enable_experimental_ckb.isChecked())
        mySettings.setValue('irmt/platform_hostname', platform_hostname)
        mySettings.setValue('irmt/platform_username',
                            self.platformUsernameEdit.text())
        mySettings.setValue('irmt/platform_password',
                            self.platformPasswordEdit.text())
        mySettings.setValue('irmt/engine_hostname', engine_hostname)
        mySettings.setValue('irmt/engine_username',
                            self.engineUsernameEdit.text())
        mySettings.setValue('irmt/engine_password',
                            self.enginePasswordEdit.text())

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
            self.irmt_main.reset_engine_login()
        super(SettingsDialog, self).accept()
