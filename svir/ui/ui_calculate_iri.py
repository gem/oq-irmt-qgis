# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_calculate_iri.ui'
#
# Created: Mon Sep  1 21:18:47 2014
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

class Ui_CalculateIRIDialog(object):
    def setupUi(self, CalculateIRIDialog):
        CalculateIRIDialog.setObjectName(_fromUtf8("CalculateIRIDialog"))
        CalculateIRIDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        CalculateIRIDialog.resize(389, 178)
        self.formLayout = QtGui.QFormLayout(CalculateIRIDialog)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.recalculate_svi_check = QtGui.QCheckBox(CalculateIRIDialog)
        self.recalculate_svi_check.setChecked(False)
        self.recalculate_svi_check.setObjectName(_fromUtf8("recalculate_svi_check"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.recalculate_svi_check)
        self.label_4 = QtGui.QLabel(CalculateIRIDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_4)
        self.svi_field_cbx = QtGui.QComboBox(CalculateIRIDialog)
        self.svi_field_cbx.setObjectName(_fromUtf8("svi_field_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.svi_field_cbx)
        self.label_5 = QtGui.QLabel(CalculateIRIDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_5)
        self.risk_field = QtGui.QComboBox(CalculateIRIDialog)
        self.risk_field.setObjectName(_fromUtf8("risk_field"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.risk_field)
        self.label = QtGui.QLabel(CalculateIRIDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label)
        self.iri_combination_type = QtGui.QComboBox(CalculateIRIDialog)
        self.iri_combination_type.setObjectName(_fromUtf8("iri_combination_type"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.iri_combination_type)
        self.buttonBox = QtGui.QDialogButtonBox(CalculateIRIDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.buttonBox)

        self.retranslateUi(CalculateIRIDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CalculateIRIDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CalculateIRIDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CalculateIRIDialog)

    def retranslateUi(self, CalculateIRIDialog):
        CalculateIRIDialog.setWindowTitle(_translate("CalculateIRIDialog", "Calculate IRI", None))
        self.recalculate_svi_check.setText(_translate("CalculateIRIDialog", "Recalculate SVI", None))
        self.label_4.setText(_translate("CalculateIRIDialog", "SVI field", None))
        self.label_5.setText(_translate("CalculateIRIDialog", "Risk field", None))
        self.label.setText(_translate("CalculateIRIDialog", "IRI combination type", None))

