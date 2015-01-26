# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_upload_settings.ui'
#
# Created: Wed Dec 24 16:05:28 2014
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

class Ui_UploadSettingsDialog(object):
    def setupUi(self, UploadSettingsDialog):
        UploadSettingsDialog.setObjectName(_fromUtf8("UploadSettingsDialog"))
        UploadSettingsDialog.resize(454, 265)
        self.verticalLayout = QtGui.QVBoxLayout(UploadSettingsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.head_msg_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.head_msg_lbl.setObjectName(_fromUtf8("head_msg_lbl"))
        self.verticalLayout.addWidget(self.head_msg_lbl)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label_4 = QtGui.QLabel(UploadSettingsDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_4)
        self.title_le = QtGui.QLineEdit(UploadSettingsDialog)
        self.title_le.setObjectName(_fromUtf8("title_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.title_le)
        self.verticalLayout.addLayout(self.formLayout)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_6 = QtGui.QLabel(UploadSettingsDialog)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 0, 0, 1, 1)
        self.license_cbx = QtGui.QComboBox(UploadSettingsDialog)
        self.license_cbx.setObjectName(_fromUtf8("license_cbx"))
        self.gridLayout.addWidget(self.license_cbx, 0, 1, 1, 1)
        self.license_info_btn = QtGui.QToolButton(UploadSettingsDialog)
        self.license_info_btn.setObjectName(_fromUtf8("license_info_btn"))
        self.gridLayout.addWidget(self.license_info_btn, 0, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.confirm_chk = QtGui.QCheckBox(UploadSettingsDialog)
        self.confirm_chk.setObjectName(_fromUtf8("confirm_chk"))
        self.verticalLayout.addWidget(self.confirm_chk)
        self.buttonBox = QtGui.QDialogButtonBox(UploadSettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UploadSettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UploadSettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UploadSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UploadSettingsDialog)

    def retranslateUi(self, UploadSettingsDialog):
        UploadSettingsDialog.setWindowTitle(_translate("UploadSettingsDialog", "Upload Settings", None))
        self.head_msg_lbl.setText(_translate("UploadSettingsDialog", "The active layer will be uploaded to the Openquake Platform", None))
        self.label_4.setText(_translate("UploadSettingsDialog", "Project title", None))
        self.label_6.setText(_translate("UploadSettingsDialog", "License", None))
        self.license_info_btn.setText(_translate("UploadSettingsDialog", "Info", None))
        self.confirm_chk.setText(_translate("UploadSettingsDialog", "I confirm I have read the license conditions", None))

