# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_project_definition.ui'
#
# Created: Thu Apr 16 14:51:36 2015
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

class Ui_SelectProjectDefinitionDialog(object):
    def setupUi(self, SelectProjectDefinitionDialog):
        SelectProjectDefinitionDialog.setObjectName(_fromUtf8("SelectProjectDefinitionDialog"))
        SelectProjectDefinitionDialog.resize(624, 520)
        SelectProjectDefinitionDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectProjectDefinitionDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(SelectProjectDefinitionDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        self.label = QtGui.QLabel(SelectProjectDefinitionDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.proj_def_cbx = QtGui.QComboBox(SelectProjectDefinitionDialog)
        self.proj_def_cbx.setObjectName(_fromUtf8("proj_def_cbx"))
        self.gridLayout.addWidget(self.proj_def_cbx, 1, 0, 1, 1)
        self.proj_def_detail = QtGui.QTextEdit(SelectProjectDefinitionDialog)
        self.proj_def_detail.setReadOnly(True)
        self.proj_def_detail.setObjectName(_fromUtf8("proj_def_detail"))
        self.gridLayout.addWidget(self.proj_def_detail, 2, 0, 1, 1)

        self.retranslateUi(SelectProjectDefinitionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectProjectDefinitionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectProjectDefinitionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectProjectDefinitionDialog)

    def retranslateUi(self, SelectProjectDefinitionDialog):
        SelectProjectDefinitionDialog.setWindowTitle(_translate("SelectProjectDefinitionDialog", "Project definition", None))
        self.label.setText(_translate("SelectProjectDefinitionDialog", "Please select one of the available project definitions", None))
        self.proj_def_detail.setHtml(_translate("SelectProjectDefinitionDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))

