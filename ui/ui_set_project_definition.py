# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_set_project_definition.ui'
#
# Created: Tue Jan 27 11:45:05 2015
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

class Ui_SetProjectDefinitionDialog(object):
    def setupUi(self, SetProjectDefinitionDialog):
        SetProjectDefinitionDialog.setObjectName(_fromUtf8("SetProjectDefinitionDialog"))
        SetProjectDefinitionDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SetProjectDefinitionDialog.resize(539, 260)
        SetProjectDefinitionDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SetProjectDefinitionDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.layer_lbl = QtGui.QLabel(SetProjectDefinitionDialog)
        self.layer_lbl.setObjectName(_fromUtf8("layer_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.layer_lbl)
        self.new_field_name_lbl = QtGui.QLabel(SetProjectDefinitionDialog)
        self.new_field_name_lbl.setObjectName(_fromUtf8("new_field_name_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.new_field_name_lbl)
        self.project_definition_ta = QtGui.QTextEdit(SetProjectDefinitionDialog)
        self.project_definition_ta.setObjectName(_fromUtf8("project_definition_ta"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.project_definition_ta)
        self.layer_name = QtGui.QLabel(SetProjectDefinitionDialog)
        self.layer_name.setObjectName(_fromUtf8("layer_name"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.layer_name)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(SetProjectDefinitionDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.retranslateUi(SetProjectDefinitionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SetProjectDefinitionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SetProjectDefinitionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SetProjectDefinitionDialog)

    def retranslateUi(self, SetProjectDefinitionDialog):
        SetProjectDefinitionDialog.setWindowTitle(_translate("SetProjectDefinitionDialog", "Field transformation", None))
        self.layer_lbl.setText(_translate("SetProjectDefinitionDialog", "Layer", None))
        self.new_field_name_lbl.setText(_translate("SetProjectDefinitionDialog", "JSON", None))
        self.layer_name.setText(_translate("SetProjectDefinitionDialog", "TextLabel", None))

