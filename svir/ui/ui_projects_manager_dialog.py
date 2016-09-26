# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_projects_manager_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_ProjectsManagerDialog(object):
    def setupUi(self, ProjectsManagerDialog):
        ProjectsManagerDialog.setObjectName("ProjectsManagerDialog")
        ProjectsManagerDialog.resize(624, 520)
        ProjectsManagerDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(ProjectsManagerDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(ProjectsManagerDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.proj_def_cbx = QtWidgets.QComboBox(ProjectsManagerDialog)
        self.proj_def_cbx.setObjectName("proj_def_cbx")
        self.horizontalLayout.addWidget(self.proj_def_cbx)
        self.add_proj_def_btn = QtWidgets.QToolButton(ProjectsManagerDialog)
        self.add_proj_def_btn.setObjectName("add_proj_def_btn")
        self.horizontalLayout.addWidget(self.add_proj_def_btn)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.proj_def_title = QtWidgets.QLineEdit(ProjectsManagerDialog)
        self.proj_def_title.setObjectName("proj_def_title")
        self.gridLayout.addWidget(self.proj_def_title, 10, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(ProjectsManagerDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 9, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(ProjectsManagerDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 11, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(ProjectsManagerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 15, 0, 1, 1)
        self.proj_def_raw = QtWidgets.QPlainTextEdit(ProjectsManagerDialog)
        self.proj_def_raw.setObjectName("proj_def_raw")
        self.gridLayout.addWidget(self.proj_def_raw, 14, 0, 1, 1)
        self.proj_def_descr = QtWidgets.QPlainTextEdit(ProjectsManagerDialog)
        self.proj_def_descr.setObjectName("proj_def_descr")
        self.gridLayout.addWidget(self.proj_def_descr, 12, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(ProjectsManagerDialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 13, 0, 1, 1)
        self.clone_btn = QtWidgets.QPushButton(ProjectsManagerDialog)
        self.clone_btn.setObjectName("clone_btn")
        self.gridLayout.addWidget(self.clone_btn, 3, 0, 1, 1)

        self.retranslateUi(ProjectsManagerDialog)
        self.buttonBox.accepted.connect(ProjectsManagerDialog.accept)
        self.buttonBox.rejected.connect(ProjectsManagerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProjectsManagerDialog)

    def retranslateUi(self, ProjectsManagerDialog):
        _translate = QtCore.QCoreApplication.translate
        ProjectsManagerDialog.setWindowTitle(_translate("ProjectsManagerDialog", "Project definitions manager"))
        self.label.setText(_translate("ProjectsManagerDialog", "Please select one of the available project definitions"))
        self.add_proj_def_btn.setText(_translate("ProjectsManagerDialog", "+"))
        self.label_2.setText(_translate("ProjectsManagerDialog", "Title"))
        self.label_3.setText(_translate("ProjectsManagerDialog", "Description"))
        self.label_4.setText(_translate("ProjectsManagerDialog", "Raw textual representation"))
        self.clone_btn.setText(_translate("ProjectsManagerDialog", "Make a copy of the selected project definition"))

