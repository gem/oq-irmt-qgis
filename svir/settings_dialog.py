# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from ui.ui_settings import Ui_SettingsDialog


class SettingsDialog(QtGui.QDialog, Ui_SettingsDialog):
    def __init__(self, iface, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.setupUi(self)

        self.restoreState()

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        platform_username = mySettings.value('svir/platform_username', '')
        platform_password = mySettings.value('svir/platform_password', '')
        platform_hostname = mySettings.value(
            'svir/platform_hostname', 'https://platform.openquake.org')

        # hack for strange mac behaviour
        platform_username = (
            platform_username if platform_username is not None else '')
        platform_password = (
            platform_password if platform_password is not None else '')
        platform_hostname = (
            platform_hostname if platform_hostname is not None else '')
        self.passwordEdit.setText(platform_password)
        self.usernameEdit.setText(platform_username)
        self.hostnameEdit.setText(platform_hostname)
        
        self.developermodeCheck.setChecked(
            mySettings.value('svir/developer_mode', False, type=bool))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        mySettings.setValue('svir/platform_hostname',
                            self.hostnameEdit.text())
        mySettings.setValue('svir/platform_username',
                            self.usernameEdit.text())
        mySettings.setValue('svir/platform_password',
                            self.passwordEdit.text())
        mySettings.setValue('svir/developer_mode',
                            self.developermodeCheck.isChecked())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        self.close()
