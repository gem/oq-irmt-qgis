# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_platform_settings.ui'
#
# Created: Fri Feb 14 16:18:26 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PlatformSettingsDialog(object):
    def setupUi(self, PlatformSettingsDialog):
        PlatformSettingsDialog.setObjectName(_fromUtf8("PlatformSettingsDialog"))
        PlatformSettingsDialog.resize(396, 148)
        self.formLayout = QtGui.QFormLayout(PlatformSettingsDialog)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(PlatformSettingsDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.usernameEdit = QtGui.QLineEdit(PlatformSettingsDialog)
        self.usernameEdit.setObjectName(_fromUtf8("usernameEdit"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.usernameEdit)
        self.label_2 = QtGui.QLabel(PlatformSettingsDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.passwordEdit = QtGui.QLineEdit(PlatformSettingsDialog)
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordEdit.setObjectName(_fromUtf8("passwordEdit"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.passwordEdit)
        self.label_3 = QtGui.QLabel(PlatformSettingsDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.hostnameEdit = QtGui.QLineEdit(PlatformSettingsDialog)
        self.hostnameEdit.setObjectName(_fromUtf8("hostnameEdit"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.hostnameEdit)
        self.buttonBox = QtGui.QDialogButtonBox(PlatformSettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(PlatformSettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PlatformSettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PlatformSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PlatformSettingsDialog)
        PlatformSettingsDialog.setTabOrder(self.usernameEdit, self.passwordEdit)
        PlatformSettingsDialog.setTabOrder(self.passwordEdit, self.hostnameEdit)
        PlatformSettingsDialog.setTabOrder(self.hostnameEdit, self.buttonBox)

    def retranslateUi(self, PlatformSettingsDialog):
        PlatformSettingsDialog.setWindowTitle(QtGui.QApplication.translate("PlatformSettingsDialog", "Openquake Platform Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PlatformSettingsDialog", "User", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("PlatformSettingsDialog", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("PlatformSettingsDialog", "Host", None, QtGui.QApplication.UnicodeUTF8))

