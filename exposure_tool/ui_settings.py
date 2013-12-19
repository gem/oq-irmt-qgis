# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_settings.ui'
#
# Created: Thu Jul 11 12:37:51 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PlatformSettings(object):
    def setupUi(self, PlatformSettings):
        PlatformSettings.setObjectName(_fromUtf8("PlatformSettings"))
        PlatformSettings.resize(396, 148)
        self.formLayout = QtGui.QFormLayout(PlatformSettings)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(PlatformSettings)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.usernameEdit = QtGui.QLineEdit(PlatformSettings)
        self.usernameEdit.setObjectName(_fromUtf8("usernameEdit"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.usernameEdit)
        self.label_2 = QtGui.QLabel(PlatformSettings)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.passwordEdit = QtGui.QLineEdit(PlatformSettings)
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordEdit.setObjectName(_fromUtf8("passwordEdit"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.passwordEdit)
        self.label_3 = QtGui.QLabel(PlatformSettings)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.buttonBox = QtGui.QDialogButtonBox(PlatformSettings)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.buttonBox)
        self.hostnameEdit = QtGui.QLineEdit(PlatformSettings)
        self.hostnameEdit.setObjectName(_fromUtf8("hostnameEdit"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.hostnameEdit)

        self.retranslateUi(PlatformSettings)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PlatformSettings.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PlatformSettings.reject)
        QtCore.QMetaObject.connectSlotsByName(PlatformSettings)
        PlatformSettings.setTabOrder(self.usernameEdit, self.passwordEdit)
        PlatformSettings.setTabOrder(self.passwordEdit, self.hostnameEdit)
        PlatformSettings.setTabOrder(self.hostnameEdit, self.buttonBox)

    def retranslateUi(self, PlatformSettings):
        PlatformSettings.setWindowTitle(QtGui.QApplication.translate("PlatformSettings", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PlatformSettings", "User", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("PlatformSettings", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("PlatformSettings", "Host", None, QtGui.QApplication.UnicodeUTF8))

