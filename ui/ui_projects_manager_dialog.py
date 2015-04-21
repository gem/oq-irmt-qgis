# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_projects_manager_dialog.ui'
#
# Created: Mon Apr 20 15:34:28 2015
#      by: PyQt4 UI code generator 4.11.2
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

class Ui_ProjectsManagerDialog(object):
    def setupUi(self, ProjectsManagerDialog):
        ProjectsManagerDialog.setObjectName(_fromUtf8("ProjectsManagerDialog"))
        ProjectsManagerDialog.resize(624, 520)
        ProjectsManagerDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(ProjectsManagerDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(ProjectsManagerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 1)
        self.label = QtGui.QLabel(ProjectsManagerDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.proj_def_detail = QtGui.QTextEdit(ProjectsManagerDialog)
        self.proj_def_detail.setReadOnly(False)
        self.proj_def_detail.setObjectName(_fromUtf8("proj_def_detail"))
        self.gridLayout.addWidget(self.proj_def_detail, 4, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.proj_def_cbx = QtGui.QComboBox(ProjectsManagerDialog)
        self.proj_def_cbx.setObjectName(_fromUtf8("proj_def_cbx"))
        self.horizontalLayout.addWidget(self.proj_def_cbx)
        self.add_proj_def_btn = QtGui.QToolButton(ProjectsManagerDialog)
        self.add_proj_def_btn.setObjectName(_fromUtf8("add_proj_def_btn"))
        self.horizontalLayout.addWidget(self.add_proj_def_btn)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.retranslateUi(ProjectsManagerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ProjectsManagerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ProjectsManagerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProjectsManagerDialog)

    def retranslateUi(self, ProjectsManagerDialog):
        ProjectsManagerDialog.setWindowTitle(_translate("ProjectsManagerDialog", "Projects manages", None))
        self.label.setText(_translate("ProjectsManagerDialog", "Please select one of the available project definitions", None))
        self.proj_def_detail.setHtml(_translate("ProjectsManagerDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.add_proj_def_btn.setText(_translate("ProjectsManagerDialog", "+", None))

