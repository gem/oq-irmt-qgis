# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_sv_variables.ui'
#
# Created: Thu Oct 16 10:20:23 2014
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

class Ui_SelectSvVariablesDialog(object):
    def setupUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setObjectName(_fromUtf8("SelectSvVariablesDialog"))
        SelectSvVariablesDialog.resize(754, 401)
        SelectSvVariablesDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectSvVariablesDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.theme_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.theme_lbl.setObjectName(_fromUtf8("theme_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.theme_lbl)
        self.theme_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.theme_cbx.setObjectName(_fromUtf8("theme_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.theme_cbx)
        self.subtheme_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.subtheme_lbl.setObjectName(_fromUtf8("subtheme_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.subtheme_lbl)
        self.subtheme_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.subtheme_cbx.setObjectName(_fromUtf8("subtheme_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.subtheme_cbx)
        self.name_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.name_lbl.setObjectName(_fromUtf8("name_lbl"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.name_lbl)
        self.name_cbx = QtGui.QComboBox(SelectSvVariablesDialog)
        self.name_cbx.setObjectName(_fromUtf8("name_cbx"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.name_cbx)
        self.add_name_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.add_name_btn.setObjectName(_fromUtf8("add_name_btn"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.add_name_btn)
        self.clear_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.clear_btn.setObjectName(_fromUtf8("clear_btn"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.LabelRole, self.clear_btn)
        self.selected_names_lst = QtGui.QListWidget(SelectSvVariablesDialog)
        self.selected_names_lst.setObjectName(_fromUtf8("selected_names_lst"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.FieldRole, self.selected_names_lst)
        self.remove_name_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.remove_name_btn.setObjectName(_fromUtf8("remove_name_btn"))
        self.formLayout.setWidget(9, QtGui.QFormLayout.FieldRole, self.remove_name_btn)
        self.name_filter_le = QtGui.QLineEdit(SelectSvVariablesDialog)
        self.name_filter_le.setObjectName(_fromUtf8("name_filter_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.name_filter_le)
        self.name_filter_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.name_filter_lbl.setObjectName(_fromUtf8("name_filter_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.name_filter_lbl)
        self.keywords_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.keywords_lbl.setObjectName(_fromUtf8("keywords_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.keywords_lbl)
        self.keywords_le = QtGui.QLineEdit(SelectSvVariablesDialog)
        self.keywords_le.setObjectName(_fromUtf8("keywords_le"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.keywords_le)
        self.filter_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.filter_btn.setObjectName(_fromUtf8("filter_btn"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.filter_btn)
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
        SelectSvVariablesDialog.setWindowTitle(_translate("SelectSvVariablesDialog", "Select socioeconomic indicators", None))
        self.theme_lbl.setText(_translate("SelectSvVariablesDialog", "Theme", None))
        self.subtheme_lbl.setText(_translate("SelectSvVariablesDialog", "Subtheme", None))
        self.name_lbl.setText(_translate("SelectSvVariablesDialog", "Indicator", None))
        self.add_name_btn.setText(_translate("SelectSvVariablesDialog", "Add indicator", None))
        self.clear_btn.setText(_translate("SelectSvVariablesDialog", "Clear", None))
        self.remove_name_btn.setText(_translate("SelectSvVariablesDialog", "Remove selected indicators", None))
        self.name_filter_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type the name of an indicator, or part of it", None))
        self.name_filter_lbl.setText(_translate("SelectSvVariablesDialog", "Name", None))
        self.keywords_lbl.setText(_translate("SelectSvVariablesDialog", "Keywords", None))
        self.keywords_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type one or more keywords (comma-separated)", None))
        self.filter_btn.setText(_translate("SelectSvVariablesDialog", "Filter indicators by the above criteria", None))

