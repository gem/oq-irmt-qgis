# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_projects_manager_dialog.ui'
#
# Created: Wed May  6 17:13:11 2015
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

class Ui_ProjectsManagerDialog(object):
    def setupUi(self, ProjectsManagerDialog):
        ProjectsManagerDialog.setObjectName(_fromUtf8("ProjectsManagerDialog"))
        ProjectsManagerDialog.resize(624, 520)
        ProjectsManagerDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(ProjectsManagerDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(ProjectsManagerDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
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
        self.proj_def_title = QtGui.QLineEdit(ProjectsManagerDialog)
        self.proj_def_title.setObjectName(_fromUtf8("proj_def_title"))
        self.gridLayout.addWidget(self.proj_def_title, 10, 0, 1, 1)
        self.label_2 = QtGui.QLabel(ProjectsManagerDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 9, 0, 1, 1)
        self.label_3 = QtGui.QLabel(ProjectsManagerDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 11, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ProjectsManagerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 15, 0, 1, 1)
        self.proj_def_raw = QtGui.QPlainTextEdit(ProjectsManagerDialog)
        self.proj_def_raw.setObjectName(_fromUtf8("proj_def_raw"))
        self.gridLayout.addWidget(self.proj_def_raw, 14, 0, 1, 1)
        self.proj_def_descr = QtGui.QPlainTextEdit(ProjectsManagerDialog)
        self.proj_def_descr.setObjectName(_fromUtf8("proj_def_descr"))
        self.gridLayout.addWidget(self.proj_def_descr, 12, 0, 1, 1)
        self.label_4 = QtGui.QLabel(ProjectsManagerDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 13, 0, 1, 1)

        self.retranslateUi(ProjectsManagerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ProjectsManagerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ProjectsManagerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProjectsManagerDialog)

    def retranslateUi(self, ProjectsManagerDialog):
        ProjectsManagerDialog.setWindowTitle(_translate("ProjectsManagerDialog", "Project definitions manager", None))
        self.label.setText(_translate("ProjectsManagerDialog", "Please select one of the available project definitions", None))
        self.add_proj_def_btn.setText(_translate("ProjectsManagerDialog", "+", None))
        self.label_2.setText(_translate("ProjectsManagerDialog", "Title", None))
        self.label_3.setText(_translate("ProjectsManagerDialog", "Description", None))
        self.label_4.setText(_translate("ProjectsManagerDialog", "Raw textual representation", None))

