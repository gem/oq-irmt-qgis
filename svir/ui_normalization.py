# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_normalization.ui'
#
# Created: Fri Dec  6 15:29:35 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_NormalizationDialog(object):
    def setupUi(self, NormalizationDialog):
        NormalizationDialog.setObjectName(_fromUtf8("NormalizationDialog"))
        NormalizationDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        NormalizationDialog.resize(400, 206)
        NormalizationDialog.setModal(True)
        self.buttonBox = QtGui.QDialogButtonBox(NormalizationDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 160, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayoutWidget = QtGui.QWidget(NormalizationDialog)
        self.formLayoutWidget.setGeometry(QtCore.QRect(19, 19, 361, 128))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setMargin(0)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.layer_lbl.setObjectName(_fromUtf8("layer_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.layer_lbl)
        self.attrib_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.attrib_lbl.setObjectName(_fromUtf8("attrib_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.attrib_lbl)
        self.algorithm_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.algorithm_lbl.setObjectName(_fromUtf8("algorithm_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.algorithm_lbl)
        self.layer_cbx = QtGui.QComboBox(self.formLayoutWidget)
        self.layer_cbx.setObjectName(_fromUtf8("layer_cbx"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.layer_cbx)
        self.attrib_cbx = QtGui.QComboBox(self.formLayoutWidget)
        self.attrib_cbx.setObjectName(_fromUtf8("attrib_cbx"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.attrib_cbx)
        self.algorithm_cbx = QtGui.QComboBox(self.formLayoutWidget)
        self.algorithm_cbx.setObjectName(_fromUtf8("algorithm_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.algorithm_cbx)
        self.variant_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.variant_lbl.setObjectName(_fromUtf8("variant_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.variant_lbl)
        self.variant_cbx = QtGui.QComboBox(self.formLayoutWidget)
        self.variant_cbx.setObjectName(_fromUtf8("variant_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.variant_cbx)

        self.retranslateUi(NormalizationDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), NormalizationDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), NormalizationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NormalizationDialog)

    def retranslateUi(self, NormalizationDialog):
        NormalizationDialog.setWindowTitle(QtGui.QApplication.translate("NormalizationDialog", "Normalize Attribute", None, QtGui.QApplication.UnicodeUTF8))
        self.layer_lbl.setText(QtGui.QApplication.translate("NormalizationDialog", "Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.attrib_lbl.setText(QtGui.QApplication.translate("NormalizationDialog", "Attribute", None, QtGui.QApplication.UnicodeUTF8))
        self.algorithm_lbl.setText(QtGui.QApplication.translate("NormalizationDialog", "Algorithm", None, QtGui.QApplication.UnicodeUTF8))
        self.variant_lbl.setText(QtGui.QApplication.translate("NormalizationDialog", "Variant", None, QtGui.QApplication.UnicodeUTF8))

