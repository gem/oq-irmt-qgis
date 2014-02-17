# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from ui.ui_platform_settings import Ui_PlatformSettingsDialog


class PlatformSettingsDialog(QtGui.QDialog, Ui_PlatformSettingsDialog):
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
            mySettings.value('platform_settings/username', ''))
        self.passwordEdit.setText(
            mySettings.value('platform_settings/password', ''))
        self.hostnameEdit.setText(
            mySettings.value('platform_settings/hostname',
                             'https://platform.openquake.org'))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        mySettings.setValue('platform_settings/hostname',
                            self.hostnameEdit.text())
        mySettings.setValue('platform_settings/username',
                            self.usernameEdit.text())
        mySettings.setValue('platform_settings/password',
                            self.passwordEdit.text())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        self.close()
