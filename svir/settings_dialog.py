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
        self.usernameEdit.setText(
            mySettings.value('svir/platform_username', ''))
        self.passwordEdit.setText(
            mySettings.value('svir/platform_password', ''))
        self.hostnameEdit.setText(
            mySettings.value('svir/platform_hostname',
                             'https://platform.openquake.org'))
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
