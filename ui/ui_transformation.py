# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_transformation.ui'
#
# Created: Mon Jan 26 11:16:10 2015
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
        TransformationDialog.resize(539, 260)
        TransformationDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(TransformationDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.layer_lbl = QtGui.QLabel(TransformationDialog)
        self.layer_lbl.setObjectName(_fromUtf8("layer_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.layer_lbl)
        self.attrib_lbl = QtGui.QLabel(TransformationDialog)
        self.attrib_lbl.setObjectName(_fromUtf8("attrib_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.attrib_lbl)
        self.algorithm_lbl = QtGui.QLabel(TransformationDialog)
        self.algorithm_lbl.setObjectName(_fromUtf8("algorithm_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.algorithm_lbl)
        self.layer_cbx = QtGui.QComboBox(TransformationDialog)
        self.layer_cbx.setObjectName(_fromUtf8("layer_cbx"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.layer_cbx)
        self.attrib_cbx = QtGui.QComboBox(TransformationDialog)
        self.attrib_cbx.setObjectName(_fromUtf8("attrib_cbx"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.attrib_cbx)
        self.algorithm_cbx = QtGui.QComboBox(TransformationDialog)
        self.algorithm_cbx.setObjectName(_fromUtf8("algorithm_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.algorithm_cbx)
        self.variant_lbl = QtGui.QLabel(TransformationDialog)
        self.variant_lbl.setObjectName(_fromUtf8("variant_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.variant_lbl)
        self.variant_cbx = QtGui.QComboBox(TransformationDialog)
        self.variant_cbx.setObjectName(_fromUtf8("variant_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.variant_cbx)
        self.inverse_ckb = QtGui.QCheckBox(TransformationDialog)
        self.inverse_ckb.setObjectName(_fromUtf8("inverse_ckb"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.inverse_ckb)
        self.new_field_name_lbl = QtGui.QLabel(TransformationDialog)
        self.new_field_name_lbl.setObjectName(_fromUtf8("new_field_name_lbl"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.new_field_name_lbl)
        self.new_field_name_txt = QtGui.QLineEdit(TransformationDialog)
        self.new_field_name_txt.setMaxLength(10)
        self.new_field_name_txt.setPlaceholderText(_fromUtf8(""))
        self.new_field_name_txt.setObjectName(_fromUtf8("new_field_name_txt"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.new_field_name_txt)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 2)
        self.calc_btn = QtGui.QPushButton(TransformationDialog)
        self.calc_btn.setObjectName(_fromUtf8("calc_btn"))
        self.gridLayout.addWidget(self.calc_btn, 1, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(TransformationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.retranslateUi(TransformationDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), TransformationDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), TransformationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TransformationDialog)

    def retranslateUi(self, TransformationDialog):
        TransformationDialog.setWindowTitle(_translate("TransformationDialog", "Field transformation", None))
        self.layer_lbl.setText(_translate("TransformationDialog", "Layer", None))
        self.attrib_lbl.setText(_translate("TransformationDialog", "Field", None))
        self.algorithm_lbl.setText(_translate("TransformationDialog", "Transformation function", None))
        self.variant_lbl.setText(_translate("TransformationDialog", "Variant", None))
        self.inverse_ckb.setText(_translate("TransformationDialog", "Inverse", None))
        self.new_field_name_lbl.setText(_translate("TransformationDialog", "New field name", None))
        self.calc_btn.setText(_translate("TransformationDialog", "Advanced Calculator", None))

