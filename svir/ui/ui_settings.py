# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_settings.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.resize(399, 280)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(SettingsDialog)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.hostnameEdit = QtWidgets.QLineEdit(self.groupBox)
        self.hostnameEdit.setObjectName("hostnameEdit")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.hostnameEdit)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.usernameEdit = QtWidgets.QLineEdit(self.groupBox)
        self.usernameEdit.setObjectName("usernameEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.usernameEdit)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.passwordEdit = QtWidgets.QLineEdit(self.groupBox)
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordEdit.setObjectName("passwordEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.passwordEdit)
        self.verticalLayout.addWidget(self.groupBox)
        self.registration_link_lbl = QtWidgets.QLabel(SettingsDialog)
        self.registration_link_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.registration_link_lbl.setOpenExternalLinks(True)
        self.registration_link_lbl.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.registration_link_lbl.setObjectName("registration_link_lbl")
        self.verticalLayout.addWidget(self.registration_link_lbl)
        self.groupBox_2 = QtWidgets.QGroupBox(SettingsDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.developermodeCheck = QtWidgets.QCheckBox(self.groupBox_2)
        self.developermodeCheck.setObjectName("developermodeCheck")
        self.verticalLayout_2.addWidget(self.developermodeCheck)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SettingsDialog)
        self.buttonBox.accepted.connect(SettingsDialog.accept)
        self.buttonBox.rejected.connect(SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "OpenQuake Platform settings"))
        self.groupBox.setTitle(_translate("SettingsDialog", "OpenQuake Platform connection settings"))
        self.label_3.setText(_translate("SettingsDialog", "Host"))
        self.label.setText(_translate("SettingsDialog", "User"))
        self.label_2.setText(_translate("SettingsDialog", "Password"))
        self.registration_link_lbl.setText(_translate("SettingsDialog", "Link to the OQ-Platform registration"))
        self.groupBox_2.setTitle(_translate("SettingsDialog", "SVIR settings"))
        self.developermodeCheck.setText(_translate("SettingsDialog", "Developer mode (requires restart)"))

