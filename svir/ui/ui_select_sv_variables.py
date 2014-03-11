# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_sv_variables.ui'
#
# Created: Mon Mar  3 14:47:19 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SelectSvVariablesDialog(object):
    def setupUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setObjectName(_fromUtf8("SelectSvVariablesDialog"))
        SelectSvVariablesDialog.resize(400, 329)
        SelectSvVariablesDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectSvVariablesDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.theme_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.theme_lbl.setObjectName(_fromUtf8("theme_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.theme_lbl)
        self.theme_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.theme_cbx.setObjectName(_fromUtf8("theme_cbx"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.theme_cbx)
        self.subtheme_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.subtheme_lbl.setObjectName(_fromUtf8("subtheme_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.subtheme_lbl)
        self.subtheme_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.subtheme_cbx.setObjectName(_fromUtf8("subtheme_cbx"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.subtheme_cbx)
        self.tag_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.tag_lbl.setObjectName(_fromUtf8("tag_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.tag_lbl)
        self.tag_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.tag_cbx.setObjectName(_fromUtf8("tag_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.tag_cbx)
        self.name_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.name_lbl.setObjectName(_fromUtf8("name_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.name_lbl)
        self.name_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.name_cbx.setObjectName(_fromUtf8("name_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.name_cbx)
        self.selected_names_lst = QtGui.QListWidget(SelectSvVariablesDialog)
        self.selected_names_lst.setObjectName(_fromUtf8("selected_names_lst"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.selected_names_lst)
        self.add_name_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.add_name_btn.setObjectName(_fromUtf8("add_name_btn"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.add_name_btn)
        self.remove_name_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.remove_name_btn.setObjectName(_fromUtf8("remove_name_btn"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.remove_name_btn)
        self.clear_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.clear_btn.setObjectName(_fromUtf8("clear_btn"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.clear_btn)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SelectSvVariablesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(SelectSvVariablesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectSvVariablesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectSvVariablesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectSvVariablesDialog)

    def retranslateUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setWindowTitle(QtGui.QApplication.translate("SelectSvVariablesDialog", "Select social vulnerability variables", None, QtGui.QApplication.UnicodeUTF8))
        self.theme_lbl.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Theme", None, QtGui.QApplication.UnicodeUTF8))
        self.subtheme_lbl.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Subtheme", None, QtGui.QApplication.UnicodeUTF8))
        self.tag_lbl.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.name_lbl.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.add_name_btn.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Add name", None, QtGui.QApplication.UnicodeUTF8))
        self.remove_name_btn.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Remove selected names", None, QtGui.QApplication.UnicodeUTF8))
        self.clear_btn.setText(QtGui.QApplication.translate("SelectSvVariablesDialog", "Clear", None, QtGui.QApplication.UnicodeUTF8))

