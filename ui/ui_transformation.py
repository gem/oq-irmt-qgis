# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_transformation.ui'
#
# Created: Fri Jul  3 10:56:45 2015
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

class Ui_TransformationDialog(object):
    def setupUi(self, TransformationDialog):
        TransformationDialog.setObjectName(_fromUtf8("TransformationDialog"))
        TransformationDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        TransformationDialog.resize(472, 355)
        TransformationDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(TransformationDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.calc_btn = QtGui.QPushButton(TransformationDialog)
        self.calc_btn.setObjectName(_fromUtf8("calc_btn"))
        self.gridLayout.addWidget(self.calc_btn, 2, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.fields_multiselect = ListMultiSelectWidget(TransformationDialog)
        self.fields_multiselect.setObjectName(_fromUtf8("fields_multiselect"))
        self.verticalLayout.addWidget(self.fields_multiselect)
        self.groupBox = QtGui.QGroupBox(TransformationDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.overwrite_ckb = QtGui.QCheckBox(self.groupBox)
        self.overwrite_ckb.setChecked(False)
        self.overwrite_ckb.setObjectName(_fromUtf8("overwrite_ckb"))
        self.verticalLayout_2.addWidget(self.overwrite_ckb)
        self.warning_lbl = QtGui.QLabel(self.groupBox)
        self.warning_lbl.setMinimumSize(QtCore.QSize(0, 35))
        self.warning_lbl.setWordWrap(True)
        self.warning_lbl.setObjectName(_fromUtf8("warning_lbl"))
        self.verticalLayout_2.addWidget(self.warning_lbl)
        self.fieldname_layout = QtGui.QHBoxLayout()
        self.fieldname_layout.setObjectName(_fromUtf8("fieldname_layout"))
        self.new_field_name_lbl = QtGui.QLabel(self.groupBox)
        self.new_field_name_lbl.setObjectName(_fromUtf8("new_field_name_lbl"))
        self.fieldname_layout.addWidget(self.new_field_name_lbl)
        self.new_field_name_txt = QtGui.QLineEdit(self.groupBox)
        self.new_field_name_txt.setEnabled(True)
        self.new_field_name_txt.setMaxLength(10)
        self.new_field_name_txt.setPlaceholderText(_fromUtf8(""))
        self.new_field_name_txt.setObjectName(_fromUtf8("new_field_name_txt"))
        self.fieldname_layout.addWidget(self.new_field_name_txt)
        self.verticalLayout_2.addLayout(self.fieldname_layout)
        self.track_new_field_ckb = QtGui.QCheckBox(self.groupBox)
        self.track_new_field_ckb.setEnabled(True)
        self.track_new_field_ckb.setChecked(True)
        self.track_new_field_ckb.setObjectName(_fromUtf8("track_new_field_ckb"))
        self.verticalLayout_2.addWidget(self.track_new_field_ckb)
        self.verticalLayout.addWidget(self.groupBox)
        self.formGroupBox = QtGui.QGroupBox(TransformationDialog)
        self.formGroupBox.setObjectName(_fromUtf8("formGroupBox"))
        self.formLayout = QtGui.QFormLayout(self.formGroupBox)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.algorithm_lbl = QtGui.QLabel(self.formGroupBox)
        self.algorithm_lbl.setObjectName(_fromUtf8("algorithm_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.algorithm_lbl)
        self.algorithm_cbx = QtGui.QComboBox(self.formGroupBox)
        self.algorithm_cbx.setObjectName(_fromUtf8("algorithm_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.algorithm_cbx)
        self.variant_lbl = QtGui.QLabel(self.formGroupBox)
        self.variant_lbl.setObjectName(_fromUtf8("variant_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.variant_lbl)
        self.variant_cbx = QtGui.QComboBox(self.formGroupBox)
        self.variant_cbx.setObjectName(_fromUtf8("variant_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.variant_cbx)
        self.inverse_ckb = QtGui.QCheckBox(self.formGroupBox)
        self.inverse_ckb.setObjectName(_fromUtf8("inverse_ckb"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.inverse_ckb)
        self.verticalLayout.addWidget(self.formGroupBox)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(TransformationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 1, 1, 1)

        self.retranslateUi(TransformationDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), TransformationDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), TransformationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TransformationDialog)

    def retranslateUi(self, TransformationDialog):
        TransformationDialog.setWindowTitle(_translate("TransformationDialog", "Field transformation", None))
        self.calc_btn.setText(_translate("TransformationDialog", "Advanced Calculator", None))
        self.fields_multiselect.setTitle(_translate("TransformationDialog", "Select fields to transform", None))
        self.groupBox.setTitle(_translate("TransformationDialog", "New field(s)", None))
        self.overwrite_ckb.setText(_translate("TransformationDialog", "Overwrite the field(s)", None))
        self.warning_lbl.setText(_translate("TransformationDialog", "WarningLabel", None))
        self.new_field_name_lbl.setText(_translate("TransformationDialog", "Name", None))
        self.track_new_field_ckb.setText(_translate("TransformationDialog", "Let the project definitions\' references track the new field(s)", None))
        self.formGroupBox.setTitle(_translate("TransformationDialog", "Transformation", None))
        self.algorithm_lbl.setText(_translate("TransformationDialog", "Function", None))
        self.variant_lbl.setText(_translate("TransformationDialog", "Variant", None))
        self.inverse_ckb.setText(_translate("TransformationDialog", "Inverse", None))

from list_multiselect_widget import ListMultiSelectWidget
