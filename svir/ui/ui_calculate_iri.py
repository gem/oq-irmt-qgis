# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_calculate_iri.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_CalculateIRIDialog(object):
    def setupUi(self, CalculateIRIDialog):
        CalculateIRIDialog.setObjectName("CalculateIRIDialog")
        CalculateIRIDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        CalculateIRIDialog.resize(389, 178)
        self.formLayout = QtWidgets.QFormLayout(CalculateIRIDialog)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.recalculate_svi_check = QtWidgets.QCheckBox(CalculateIRIDialog)
        self.recalculate_svi_check.setChecked(False)
        self.recalculate_svi_check.setObjectName("recalculate_svi_check")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.recalculate_svi_check)
        self.label_4 = QtWidgets.QLabel(CalculateIRIDialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.svi_field_cbx = QtWidgets.QComboBox(CalculateIRIDialog)
        self.svi_field_cbx.setObjectName("svi_field_cbx")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.svi_field_cbx)
        self.label_5 = QtWidgets.QLabel(CalculateIRIDialog)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.aal_field = QtWidgets.QComboBox(CalculateIRIDialog)
        self.aal_field.setObjectName("aal_field")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.aal_field)
        self.label = QtWidgets.QLabel(CalculateIRIDialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label)
        self.iri_combination_type = QtWidgets.QComboBox(CalculateIRIDialog)
        self.iri_combination_type.setObjectName("iri_combination_type")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.iri_combination_type)
        self.buttonBox = QtWidgets.QDialogButtonBox(CalculateIRIDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.buttonBox)

        self.retranslateUi(CalculateIRIDialog)
        self.buttonBox.accepted.connect(CalculateIRIDialog.accept)
        self.buttonBox.rejected.connect(CalculateIRIDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CalculateIRIDialog)

    def retranslateUi(self, CalculateIRIDialog):
        _translate = QtCore.QCoreApplication.translate
        CalculateIRIDialog.setWindowTitle(_translate("CalculateIRIDialog", "Calculate IRI"))
        self.recalculate_svi_check.setText(_translate("CalculateIRIDialog", "Recalculate SVI"))
        self.label_4.setText(_translate("CalculateIRIDialog", "SVI field"))
        self.label_5.setText(_translate("CalculateIRIDialog", "Risk field"))
        self.label.setText(_translate("CalculateIRIDialog", "IRI combination type"))

