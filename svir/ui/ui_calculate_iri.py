# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_calculate_iri.ui'
#
# Created: Wed Apr 30 15:18:25 2014
#      by: PyQt4 UI code generator 4.10.3
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
        CalculateIRIDialog.resize(407, 291)
        self.verticalLayout = QtGui.QVBoxLayout(CalculateIRIDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(CalculateIRIDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.themes_combination_type = QtGui.QComboBox(self.groupBox)
        self.themes_combination_type.setEnabled(True)
        self.themes_combination_type.setObjectName(_fromUtf8("themes_combination_type"))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.themes_combination_type)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_3)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.indicators_combination_type = QtGui.QComboBox(self.groupBox)
        self.indicators_combination_type.setEnabled(True)
        self.indicators_combination_type.setObjectName(_fromUtf8("indicators_combination_type"))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.indicators_combination_type)
        self.verticalLayout.addWidget(self.groupBox)
        self.calculate_iri_check = QtGui.QGroupBox(CalculateIRIDialog)
        self.calculate_iri_check.setCheckable(True)
        self.calculate_iri_check.setChecked(False)
        self.calculate_iri_check.setObjectName(_fromUtf8("calculate_iri_check"))
        self.formLayout_2 = QtGui.QFormLayout(self.calculate_iri_check)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.label = QtGui.QLabel(self.calculate_iri_check)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.label)
        self.label_4 = QtGui.QLabel(self.calculate_iri_check)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_4)
        self.aal_layer = QtGui.QComboBox(self.calculate_iri_check)
        self.aal_layer.setObjectName(_fromUtf8("aal_layer"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.aal_layer)
        self.label_5 = QtGui.QLabel(self.calculate_iri_check)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_5)
        self.aal_field = QtGui.QComboBox(self.calculate_iri_check)
        self.aal_field.setObjectName(_fromUtf8("aal_field"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.aal_field)
        self.iri_combination_type = QtGui.QComboBox(self.calculate_iri_check)
        self.iri_combination_type.setObjectName(_fromUtf8("iri_combination_type"))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.FieldRole, self.iri_combination_type)
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
        CalculateIRIDialog.setWindowTitle(_translate("CalculateIRIDialog", "Dialog", None))
        self.groupBox.setTitle(_translate("CalculateIRIDialog", "SVI", None))
        self.themes_combination_type.setItemText(0, _translate("CalculateIRIDialog", "Average", None))
        self.themes_combination_type.setItemText(1, _translate("CalculateIRIDialog", "Sum", None))
        self.themes_combination_type.setItemText(2, _translate("CalculateIRIDialog", "Multiplication", None))
        self.label_3.setText(_translate("CalculateIRIDialog", "Theme combination type", None))
        self.label_2.setText(_translate("CalculateIRIDialog", "Indicators combination type", None))
        self.indicators_combination_type.setItemText(0, _translate("CalculateIRIDialog", "Average", None))
        self.indicators_combination_type.setItemText(1, _translate("CalculateIRIDialog", "Sum", None))
        self.indicators_combination_type.setItemText(2, _translate("CalculateIRIDialog", "Multiplication", None))
        self.calculate_iri_check.setTitle(_translate("CalculateIRIDialog", "IRI", None))
        self.label.setText(_translate("CalculateIRIDialog", "IRI combination type", None))
        self.label_4.setText(_translate("CalculateIRIDialog", "AAL layer", None))
        self.label_5.setText(_translate("CalculateIRIDialog", "AAL field", None))
        self.iri_combination_type.setItemText(0, _translate("CalculateIRIDialog", "Average", None))
        self.iri_combination_type.setItemText(1, _translate("CalculateIRIDialog", "Sum", None))
        self.iri_combination_type.setItemText(2, _translate("CalculateIRIDialog", "Multiplication", None))

