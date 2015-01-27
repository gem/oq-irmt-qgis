# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_set_project_definition.ui'
#
# Created: Tue Jan 27 15:56:53 2015
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
        self.verticalLayout = QtGui.QVBoxLayout(SetProjectDefinitionDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.layer_name = QtGui.QLabel(SetProjectDefinitionDialog)
        self.layer_name.setText(_fromUtf8(""))
        self.layer_name.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.layer_name.setObjectName(_fromUtf8("layer_name"))
        self.verticalLayout.addWidget(self.layer_name)
        self.project_definition_te = QtGui.QTextEdit(SetProjectDefinitionDialog)
        self.project_definition_te.setObjectName(_fromUtf8("project_definition_te"))
        self.verticalLayout.addWidget(self.project_definition_te)
        self.buttonBox = QtGui.QDialogButtonBox(SetProjectDefinitionDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SetProjectDefinitionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SetProjectDefinitionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SetProjectDefinitionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SetProjectDefinitionDialog)

    def retranslateUi(self, SetProjectDefinitionDialog):
        SetProjectDefinitionDialog.setWindowTitle(_translate("SetProjectDefinitionDialog", "Set project definition", None))

