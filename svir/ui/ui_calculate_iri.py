# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_calculate_iri.ui'
#
# Created: Tue Aug 19 16:01:01 2014
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
        CalculateIRIDialog.resize(389, 352)
        self.verticalLayout = QtGui.QVBoxLayout(CalculateIRIDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(CalculateIRIDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.indicators_combination_type = QtGui.QComboBox(self.groupBox)
        self.indicators_combination_type.setEnabled(True)
        self.indicators_combination_type.setObjectName(_fromUtf8("indicators_combination_type"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.indicators_combination_type)
        self.themes_combination_type = QtGui.QComboBox(self.groupBox)
        self.themes_combination_type.setEnabled(True)
        self.themes_combination_type.setObjectName(_fromUtf8("themes_combination_type"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.themes_combination_type)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_3)
        self.verticalLayout.addWidget(self.groupBox)
        self.calculate_iri_check = QtGui.QGroupBox(CalculateIRIDialog)
        self.calculate_iri_check.setCheckable(True)
        self.calculate_iri_check.setChecked(False)
        self.calculate_iri_check.setObjectName(_fromUtf8("calculate_iri_check"))
        self.formLayout_2 = QtGui.QFormLayout(self.calculate_iri_check)
        self.formLayout_2.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.aal_field = QtGui.QComboBox(self.calculate_iri_check)
        self.aal_field.setObjectName(_fromUtf8("aal_field"))
        self.formLayout_2.setWidget(5, QtGui.QFormLayout.FieldRole, self.aal_field)
        self.label_5 = QtGui.QLabel(self.calculate_iri_check)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout_2.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_5)
        self.iri_combination_type = QtGui.QComboBox(self.calculate_iri_check)
        self.iri_combination_type.setObjectName(_fromUtf8("iri_combination_type"))
        self.formLayout_2.setWidget(8, QtGui.QFormLayout.FieldRole, self.iri_combination_type)
        self.label = QtGui.QLabel(self.calculate_iri_check)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout_2.setWidget(8, QtGui.QFormLayout.LabelRole, self.label)
        self.svi_field_cbx = QtGui.QComboBox(self.calculate_iri_check)
        self.svi_field_cbx.setObjectName(_fromUtf8("svi_field_cbx"))
        self.formLayout_2.setWidget(4, QtGui.QFormLayout.FieldRole, self.svi_field_cbx)
        self.label_4 = QtGui.QLabel(self.calculate_iri_check)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout_2.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_4)
        self.recalculate_svi_check = QtGui.QCheckBox(self.calculate_iri_check)
        self.recalculate_svi_check.setChecked(False)
        self.recalculate_svi_check.setObjectName(_fromUtf8("recalculate_svi_check"))
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.LabelRole, self.recalculate_svi_check)
        self.verticalLayout.addWidget(self.calculate_iri_check)
        self.buttonBox = QtGui.QDialogButtonBox(CalculateIRIDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CalculateIRIDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CalculateIRIDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CalculateIRIDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CalculateIRIDialog)

    def retranslateUi(self, CalculateIRIDialog):
        CalculateIRIDialog.setWindowTitle(_translate("CalculateIRIDialog", "Calculate Indices", None))
        self.groupBox.setTitle(_translate("CalculateIRIDialog", "SVI", None))
        self.label_2.setText(_translate("CalculateIRIDialog", "Indicators combination type", None))
        self.label_3.setText(_translate("CalculateIRIDialog", "Theme combination type", None))
        self.calculate_iri_check.setTitle(_translate("CalculateIRIDialog", "IRI", None))
        self.label_5.setText(_translate("CalculateIRIDialog", "Risk field", None))
        self.label.setText(_translate("CalculateIRIDialog", "IRI combination type", None))
        self.label_4.setText(_translate("CalculateIRIDialog", "SVI field", None))
        self.recalculate_svi_check.setText(_translate("CalculateIRIDialog", "Recalculate SVI", None))

