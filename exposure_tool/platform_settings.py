# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from ui_settings import Ui_PlatformSettings


class PlatformSettingsDialog(QtGui.QDialog, Ui_PlatformSettings):
    def __init__(self, iface, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle(self.tr('Openquake Platform Settings'))
        self.iface = iface

        self.restoreState()

    def restoreState(self):
        """
        Reinstate the options based on the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        self.usernameEdit.setText(
            mySettings.value('download_exposure/username', ''))
        self.passwordEdit.setText(
            mySettings.value('download_exposure/password', ''))
        self.hostnameEdit.setText(
            mySettings.value('download_exposure/hostname',
                             'https://platform.openquake.org'))

    def saveState(self):
        """
        Store the options into the user's stored session info.
        """
        mySettings = QtCore.QSettings()
        mySettings.setValue('download_exposure/hostname',
                            self.hostnameEdit.text())
        mySettings.setValue('download_exposure/username',
                            self.usernameEdit.text())
        mySettings.setValue('download_exposure/password',
                            self.passwordEdit.text())

    def accept(self):
        """
        Method invoked when OK button is clicked.
        """
        self.saveState()
        self.close()
