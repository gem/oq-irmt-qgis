# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_settings.ui'
#
# Created: Mon Mar 16 14:59:29 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName(_fromUtf8("SettingsDialog"))
        SettingsDialog.resize(399, 280)
        self.verticalLayout = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(SettingsDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.hostnameEdit = QtGui.QLineEdit(self.groupBox)
        self.hostnameEdit.setObjectName(_fromUtf8("hostnameEdit"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.hostnameEdit)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.usernameEdit = QtGui.QLineEdit(self.groupBox)
        self.usernameEdit.setObjectName(_fromUtf8("usernameEdit"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.usernameEdit)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.passwordEdit = QtGui.QLineEdit(self.groupBox)
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordEdit.setObjectName(_fromUtf8("passwordEdit"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.passwordEdit)
        self.verticalLayout.addWidget(self.groupBox)
        self.registration_link_lbl = QtGui.QLabel(SettingsDialog)
        self.registration_link_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.registration_link_lbl.setOpenExternalLinks(True)
        self.registration_link_lbl.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.registration_link_lbl.setObjectName(_fromUtf8("registration_link_lbl"))
        self.verticalLayout.addWidget(self.registration_link_lbl)
        self.groupBox_2 = QtGui.QGroupBox(SettingsDialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.developermodeCheck = QtGui.QCheckBox(self.groupBox_2)
        self.developermodeCheck.setObjectName(_fromUtf8("developermodeCheck"))
        self.verticalLayout_2.addWidget(self.developermodeCheck)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "OpenQuake Platform settings", None))
        self.groupBox.setTitle(_translate("SettingsDialog", "Openquake platform connection settings", None))
        self.label_3.setText(_translate("SettingsDialog", "Host", None))
        self.label.setText(_translate("SettingsDialog", "User", None))
        self.label_2.setText(_translate("SettingsDialog", "Password", None))
        self.registration_link_lbl.setText(_translate("SettingsDialog", "TextLabel", None))
        self.groupBox_2.setTitle(_translate("SettingsDialog", "SVIR settings", None))
        self.developermodeCheck.setText(_translate("SettingsDialog", "Developer mode (requires restart)", None))

