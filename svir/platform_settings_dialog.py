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
            mySettings.value('download_sv/username', ''))
        self.passwordEdit.setText(
            mySettings.value('download_sv/password', ''))
        self.hostnameEdit.setText(
            mySettings.value('download_sv/hostname',
                             'https://platform.openquake.org'))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        mySettings.setValue('download_sv/hostname',
                            self.hostnameEdit.text())
        mySettings.setValue('download_sv/username',
                            self.usernameEdit.text())
        mySettings.setValue('download_sv/password',
                            self.passwordEdit.text())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        self.close()
