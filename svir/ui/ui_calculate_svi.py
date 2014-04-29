# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_calculate_svi.ui'
#
# Created: Tue Apr 29 17:32:31 2014
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

class Ui_CalculateSVIDialog(object):
    def setupUi(self, CalculateSVIDialog):
        CalculateSVIDialog.setObjectName(_fromUtf8("CalculateSVIDialog"))
        CalculateSVIDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        CalculateSVIDialog.resize(390, 144)
        self.formLayout = QtGui.QFormLayout(CalculateSVIDialog)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(CalculateSVIDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label)
        self.iri_combination_type = QtGui.QComboBox(CalculateSVIDialog)
        self.iri_combination_type.setEnabled(False)
        self.iri_combination_type.setObjectName(_fromUtf8("iri_combination_type"))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.iri_combination_type.addItem(_fromUtf8(""))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.iri_combination_type)
        self.label_2 = QtGui.QLabel(CalculateSVIDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_2)
        self.indicators_combination_type = QtGui.QComboBox(CalculateSVIDialog)
        self.indicators_combination_type.setEnabled(True)
        self.indicators_combination_type.setObjectName(_fromUtf8("indicators_combination_type"))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.indicators_combination_type.addItem(_fromUtf8(""))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.indicators_combination_type)
        self.label_3 = QtGui.QLabel(CalculateSVIDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_3)
        self.themes_combination_type = QtGui.QComboBox(CalculateSVIDialog)
        self.themes_combination_type.setEnabled(True)
        self.themes_combination_type.setObjectName(_fromUtf8("themes_combination_type"))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.themes_combination_type.addItem(_fromUtf8(""))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.themes_combination_type)
        self.buttonBox = QtGui.QDialogButtonBox(CalculateSVIDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(CalculateSVIDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CalculateSVIDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CalculateSVIDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CalculateSVIDialog)

    def retranslateUi(self, CalculateSVIDialog):
        CalculateSVIDialog.setWindowTitle(_translate("CalculateSVIDialog", "Dialog", None))
        self.label.setText(_translate("CalculateSVIDialog", "IRI combination type", None))
        self.iri_combination_type.setItemText(0, _translate("CalculateSVIDialog", "Average", None))
        self.iri_combination_type.setItemText(1, _translate("CalculateSVIDialog", "Sum", None))
        self.iri_combination_type.setItemText(2, _translate("CalculateSVIDialog", "Multiplication", None))
        self.label_2.setText(_translate("CalculateSVIDialog", "Indicators combination type", None))
        self.indicators_combination_type.setItemText(0, _translate("CalculateSVIDialog", "Average", None))
        self.indicators_combination_type.setItemText(1, _translate("CalculateSVIDialog", "Sum", None))
        self.indicators_combination_type.setItemText(2, _translate("CalculateSVIDialog", "Multiplication", None))
        self.label_3.setText(_translate("CalculateSVIDialog", "Theme combination type", None))
        self.themes_combination_type.setItemText(0, _translate("CalculateSVIDialog", "Average", None))
        self.themes_combination_type.setItemText(1, _translate("CalculateSVIDialog", "Sum", None))
        self.themes_combination_type.setItemText(2, _translate("CalculateSVIDialog", "Multiplication", None))

