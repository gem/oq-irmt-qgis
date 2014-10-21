# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_sv_variables.ui'
#
# Created: Tue Oct 21 11:07:44 2014
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
        SelectSvVariablesDialog.resize(1024, 737)
        SelectSvVariablesDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectSvVariablesDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.indicator_info = QtGui.QGroupBox(SelectSvVariablesDialog)
        self.indicator_info.setObjectName(_fromUtf8("indicator_info"))
        self.gridLayout.addWidget(self.indicator_info, 4, 0, 1, 1)
        self.filters_group = QtGui.QGroupBox(SelectSvVariablesDialog)
        self.filters_group.setObjectName(_fromUtf8("filters_group"))
        self.gridLayout.addWidget(self.filters_group, 0, 0, 1, 1)
        self.filter_btn = QtGui.QPushButton(SelectSvVariablesDialog)
        self.filter_btn.setObjectName(_fromUtf8("filter_btn"))
        self.gridLayout.addWidget(self.filter_btn, 2, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SelectSvVariablesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 1)
        self.load_geometries_chk = QtGui.QCheckBox(SelectSvVariablesDialog)
        self.load_geometries_chk.setObjectName(_fromUtf8("load_geometries_chk"))
        self.gridLayout.addWidget(self.load_geometries_chk, 6, 0, 1, 1)
        self.indicator_details = QtGui.QTextBrowser(SelectSvVariablesDialog)
        self.indicator_details.setObjectName(_fromUtf8("indicator_details"))
        self.gridLayout.addWidget(self.indicator_details, 5, 0, 1, 1)
        self.list_multiselect = ListMultiSelectWidget(SelectSvVariablesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_multiselect.sizePolicy().hasHeightForWidth())
        self.list_multiselect.setSizePolicy(sizePolicy)
        self.list_multiselect.setObjectName(_fromUtf8("list_multiselect"))
        self.gridLayout.addWidget(self.list_multiselect, 3, 0, 1, 1)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.name_filter_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.name_filter_lbl.setObjectName(_fromUtf8("name_filter_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.name_filter_lbl)
        self.name_filter_le = QtGui.QLineEdit(SelectSvVariablesDialog)
        self.name_filter_le.setObjectName(_fromUtf8("name_filter_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.name_filter_le)
        self.keywords_lbl = QtGui.QLabel(SelectSvVariablesDialog)
        self.keywords_lbl.setObjectName(_fromUtf8("keywords_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.keywords_lbl)
        self.keywords_le = QtGui.QLineEdit(SelectSvVariablesDialog)
        self.keywords_le.setObjectName(_fromUtf8("keywords_le"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.keywords_le)
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
        self.gridLayout.addLayout(self.formLayout, 1, 0, 1, 1)

        self.retranslateUi(SelectSvVariablesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectSvVariablesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectSvVariablesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectSvVariablesDialog)

    def retranslateUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setWindowTitle(_translate("SelectSvVariablesDialog", "Select socioeconomic indicators", None))
        self.indicator_info.setTitle(_translate("SelectSvVariablesDialog", "Indicator details", None))
        self.filters_group.setTitle(_translate("SelectSvVariablesDialog", "Filters", None))
        self.filter_btn.setText(_translate("SelectSvVariablesDialog", "Filter indicators by the above criteria", None))
        self.load_geometries_chk.setText(_translate("SelectSvVariablesDialog", "Load geometries", None))
        self.list_multiselect.setTitle(_translate("SelectSvVariablesDialog", "Select indicators", None))
        self.name_filter_lbl.setText(_translate("SelectSvVariablesDialog", "Name", None))
        self.name_filter_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type the name of an indicator, or part of it", None))
        self.keywords_lbl.setText(_translate("SelectSvVariablesDialog", "Keywords", None))
        self.keywords_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type one or more keywords (comma-separated)", None))
        self.theme_lbl.setText(_translate("SelectSvVariablesDialog", "Theme", None))
        self.subtheme_lbl.setText(_translate("SelectSvVariablesDialog", "Subtheme", None))

from list_multiselect_widget import ListMultiSelectWidget
