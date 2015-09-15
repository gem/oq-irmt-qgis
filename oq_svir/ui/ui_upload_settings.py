# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_upload_settings.ui'
#
# Created: Mon May 18 15:55:36 2015
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
        UploadSettingsDialog.resize(509, 369)
        self.verticalLayout = QtGui.QVBoxLayout(UploadSettingsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.situation_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.situation_lbl.setObjectName(_fromUtf8("situation_lbl"))
        self.verticalLayout.addWidget(self.situation_lbl)
        self.question_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.question_lbl.setObjectName(_fromUtf8("question_lbl"))
        self.verticalLayout.addWidget(self.question_lbl)
        self.new_layer_radio = QtGui.QRadioButton(UploadSettingsDialog)
        self.new_layer_radio.setChecked(True)
        self.new_layer_radio.setObjectName(_fromUtf8("new_layer_radio"))
        self.upload_action = QtGui.QButtonGroup(UploadSettingsDialog)
        self.upload_action.setObjectName(_fromUtf8("upload_action"))
        self.upload_action.addButton(self.new_layer_radio)
        self.verticalLayout.addWidget(self.new_layer_radio)
        self.update_radio = QtGui.QRadioButton(UploadSettingsDialog)
        self.update_radio.setObjectName(_fromUtf8("update_radio"))
        self.upload_action.addButton(self.update_radio)
        self.verticalLayout.addWidget(self.update_radio)
        self.explaination_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.explaination_lbl.setText(_fromUtf8(""))
        self.explaination_lbl.setObjectName(_fromUtf8("explaination_lbl"))
        self.verticalLayout.addWidget(self.explaination_lbl)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.title_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.title_lbl.setObjectName(_fromUtf8("title_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.title_lbl)
        self.title_le = QtGui.QLineEdit(UploadSettingsDialog)
        self.title_le.setObjectName(_fromUtf8("title_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.title_le)
        self.description_lbl = QtGui.QLabel(UploadSettingsDialog)
        self.description_lbl.setObjectName(_fromUtf8("description_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.description_lbl)
        self.description_te = QtGui.QTextEdit(UploadSettingsDialog)
        self.description_te.setObjectName(_fromUtf8("description_te"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.description_te)
        self.zone_label_field_cbx = QtGui.QComboBox(UploadSettingsDialog)
        self.zone_label_field_cbx.setObjectName(_fromUtf8("zone_label_field_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.zone_label_field_cbx)
        self.label = QtGui.QLabel(UploadSettingsDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label)
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
        UploadSettingsDialog.setWindowTitle(_translate("UploadSettingsDialog", "Upload", None))
        self.situation_lbl.setText(_translate("UploadSettingsDialog", "It looks like this layer was downloaded from the OpenQuake Platform\n"
"or an older version was previously uploaded there.\n"
"You can create a new layer or just upload the current project definition.", None))
        self.question_lbl.setText(_translate("UploadSettingsDialog", "What would you like to do?", None))
        self.new_layer_radio.setText(_translate("UploadSettingsDialog", "Create a new layer on the platform", None))
        self.update_radio.setText(_translate("UploadSettingsDialog", "Update the existing layer on the platform", None))
        self.title_lbl.setText(_translate("UploadSettingsDialog", "Title", None))
        self.description_lbl.setText(_translate("UploadSettingsDialog", "Description", None))
        self.label.setText(_translate("UploadSettingsDialog", "Zone labels field", None))
        self.label_6.setText(_translate("UploadSettingsDialog", "License", None))
        self.license_info_btn.setText(_translate("UploadSettingsDialog", "Info", None))
        self.confirm_chk.setText(_translate("UploadSettingsDialog", "I confirm I have read the license conditions", None))

