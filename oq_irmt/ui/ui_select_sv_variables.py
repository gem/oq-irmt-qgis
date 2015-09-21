# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_sv_variables.ui'
#
# Created: Mon Sep 21 10:49:56 2015
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
        SelectSvVariablesDialog.resize(1024, 765)
        SelectSvVariablesDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectSvVariablesDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.scrollArea = QtGui.QScrollArea(SelectSvVariablesDialog)
        self.scrollArea.setMouseTracking(True)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1004, 712))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout_3 = QtGui.QFormLayout()
        self.formLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.formLayout_3.setObjectName(_fromUtf8("formLayout_3"))
        self.study_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.study_lbl.setObjectName(_fromUtf8("study_lbl"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.study_lbl)
        self.study_cbx = QtGui.QComboBox(self.scrollAreaWidgetContents)
        self.study_cbx.setObjectName(_fromUtf8("study_cbx"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.study_cbx)
        self.verticalLayout.addLayout(self.formLayout_3)
        self.zone_select = ListMultiSelectWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.zone_select.sizePolicy().hasHeightForWidth())
        self.zone_select.setSizePolicy(sizePolicy)
        self.zone_select.setObjectName(_fromUtf8("zone_select"))
        self.verticalLayout.addWidget(self.zone_select)
        self.filters_group = QtGui.QGroupBox(self.scrollAreaWidgetContents)
        self.filters_group.setObjectName(_fromUtf8("filters_group"))
        self.verticalLayout.addWidget(self.filters_group)
        self.filters_help_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.filters_help_lbl.setObjectName(_fromUtf8("filters_help_lbl"))
        self.verticalLayout.addWidget(self.filters_help_lbl)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.name_filter_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.name_filter_lbl.setObjectName(_fromUtf8("name_filter_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.name_filter_lbl)
        self.name_filter_le = QtGui.QLineEdit(self.scrollAreaWidgetContents)
        self.name_filter_le.setObjectName(_fromUtf8("name_filter_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.name_filter_le)
        self.keywords_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.keywords_lbl.setObjectName(_fromUtf8("keywords_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.keywords_lbl)
        self.keywords_le = QtGui.QLineEdit(self.scrollAreaWidgetContents)
        self.keywords_le.setObjectName(_fromUtf8("keywords_le"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.keywords_le)
        self.theme_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.theme_lbl.setObjectName(_fromUtf8("theme_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.theme_lbl)
        self.theme_cbx = QtGui.QComboBox(self.scrollAreaWidgetContents)
        self.theme_cbx.setObjectName(_fromUtf8("theme_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.theme_cbx)
        self.subtheme_lbl = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.subtheme_lbl.setObjectName(_fromUtf8("subtheme_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.subtheme_lbl)
        self.subtheme_cbx = QtGui.QComboBox(self.scrollAreaWidgetContents)
        self.subtheme_cbx.setObjectName(_fromUtf8("subtheme_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.subtheme_cbx)
        self.verticalLayout.addLayout(self.formLayout)
        self.filter_btn = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.filter_btn.setObjectName(_fromUtf8("filter_btn"))
        self.verticalLayout.addWidget(self.filter_btn)
        self.list_multiselect = ListMultiSelectWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_multiselect.sizePolicy().hasHeightForWidth())
        self.list_multiselect.setSizePolicy(sizePolicy)
        self.list_multiselect.setObjectName(_fromUtf8("list_multiselect"))
        self.verticalLayout.addWidget(self.list_multiselect)
        self.indicator_info = QtGui.QGroupBox(self.scrollAreaWidgetContents)
        self.indicator_info.setObjectName(_fromUtf8("indicator_info"))
        self.verticalLayout.addWidget(self.indicator_info)
        self.indicator_details = QtGui.QTextBrowser(self.scrollAreaWidgetContents)
        self.indicator_details.setObjectName(_fromUtf8("indicator_details"))
        self.verticalLayout.addWidget(self.indicator_details)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SelectSvVariablesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.retranslateUi(SelectSvVariablesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectSvVariablesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectSvVariablesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectSvVariablesDialog)

    def retranslateUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setWindowTitle(_translate("SelectSvVariablesDialog", "Select socioeconomic indicators", None))
        self.study_lbl.setText(_translate("SelectSvVariablesDialog", "Study", None))
        self.zone_select.setTitle(_translate("SelectSvVariablesDialog", "Select zones", None))
        self.filters_group.setTitle(_translate("SelectSvVariablesDialog", "Filter indicators", None))
        self.filters_help_lbl.setText(_translate("SelectSvVariablesDialog", "All filters are optional. If no filter is set, the whole set of indicators will be retrieved.", None))
        self.name_filter_lbl.setText(_translate("SelectSvVariablesDialog", "Name", None))
        self.name_filter_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type the name of an indicator, or part of it", None))
        self.keywords_lbl.setText(_translate("SelectSvVariablesDialog", "Keywords", None))
        self.keywords_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type one or more keywords (comma-separated)", None))
        self.theme_lbl.setText(_translate("SelectSvVariablesDialog", "Theme", None))
        self.subtheme_lbl.setText(_translate("SelectSvVariablesDialog", "Subtheme", None))
        self.filter_btn.setText(_translate("SelectSvVariablesDialog", "Get indicators", None))
        self.list_multiselect.setTitle(_translate("SelectSvVariablesDialog", "Select indicators", None))
        self.indicator_info.setTitle(_translate("SelectSvVariablesDialog", "Indicator details", None))

from list_multiselect_widget import ListMultiSelectWidget
