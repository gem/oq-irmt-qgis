# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_sv_variables.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_SelectSvVariablesDialog(object):
    def setupUi(self, SelectSvVariablesDialog):
        SelectSvVariablesDialog.setObjectName("SelectSvVariablesDialog")
        SelectSvVariablesDialog.resize(1024, 765)
        SelectSvVariablesDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(SelectSvVariablesDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QtWidgets.QScrollArea(SelectSvVariablesDialog)
        self.scrollArea.setMouseTracking(True)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1004, 712))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filters_group = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.filters_group.setObjectName("filters_group")
        self.verticalLayout.addWidget(self.filters_group)
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.name_filter_lbl = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.name_filter_lbl.setObjectName("name_filter_lbl")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.name_filter_lbl)
        self.name_filter_le = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.name_filter_le.setObjectName("name_filter_le")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.name_filter_le)
        self.keywords_lbl = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.keywords_lbl.setObjectName("keywords_lbl")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.keywords_lbl)
        self.keywords_le = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.keywords_le.setObjectName("keywords_le")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.keywords_le)
        self.theme_lbl = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.theme_lbl.setObjectName("theme_lbl")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.theme_lbl)
        self.theme_cbx = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.theme_cbx.setObjectName("theme_cbx")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.theme_cbx)
        self.subtheme_lbl = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.subtheme_lbl.setObjectName("subtheme_lbl")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.subtheme_lbl)
        self.subtheme_cbx = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.subtheme_cbx.setObjectName("subtheme_cbx")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.subtheme_cbx)
        self.verticalLayout.addLayout(self.formLayout)
        self.filter_btn = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.filter_btn.setObjectName("filter_btn")
        self.verticalLayout.addWidget(self.filter_btn)
        self.list_multiselect = ListMultiSelectWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_multiselect.sizePolicy().hasHeightForWidth())
        self.list_multiselect.setSizePolicy(sizePolicy)
        self.list_multiselect.setObjectName("list_multiselect")
        self.verticalLayout.addWidget(self.list_multiselect)
        self.indicator_info = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.indicator_info.setObjectName("indicator_info")
        self.verticalLayout.addWidget(self.indicator_info)
        self.indicator_details = QtWidgets.QTextBrowser(self.scrollAreaWidgetContents)
        self.indicator_details.setObjectName("indicator_details")
        self.verticalLayout.addWidget(self.indicator_details)
        self.country_select = ListMultiSelectWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.country_select.sizePolicy().hasHeightForWidth())
        self.country_select.setSizePolicy(sizePolicy)
        self.country_select.setObjectName("country_select")
        self.verticalLayout.addWidget(self.country_select)
        self.list_multiselect.raise_()
        self.filter_btn.raise_()
        self.indicator_info.raise_()
        self.filters_group.raise_()
        self.indicator_details.raise_()
        self.country_select.raise_()
        self.label.raise_()
        self.list_multiselect.raise_()
        self.filter_btn.raise_()
        self.indicator_info.raise_()
        self.filters_group.raise_()
        self.indicator_details.raise_()
        self.country_select.raise_()
        self.label.raise_()
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(SelectSvVariablesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.retranslateUi(SelectSvVariablesDialog)
        self.buttonBox.accepted.connect(SelectSvVariablesDialog.accept)
        self.buttonBox.rejected.connect(SelectSvVariablesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectSvVariablesDialog)

    def retranslateUi(self, SelectSvVariablesDialog):
        _translate = QtCore.QCoreApplication.translate
        SelectSvVariablesDialog.setWindowTitle(_translate("SelectSvVariablesDialog", "Select socioeconomic indicators"))
        self.filters_group.setTitle(_translate("SelectSvVariablesDialog", "Filters"))
        self.label.setText(_translate("SelectSvVariablesDialog", "All filters are optional. If no filter is set, the whole set of indicators will be retrieved."))
        self.name_filter_lbl.setText(_translate("SelectSvVariablesDialog", "Name"))
        self.name_filter_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type the name of an indicator, or part of it"))
        self.keywords_lbl.setText(_translate("SelectSvVariablesDialog", "Keywords"))
        self.keywords_le.setPlaceholderText(_translate("SelectSvVariablesDialog", "Type one or more keywords (comma-separated)"))
        self.theme_lbl.setText(_translate("SelectSvVariablesDialog", "Theme"))
        self.subtheme_lbl.setText(_translate("SelectSvVariablesDialog", "Subtheme"))
        self.filter_btn.setText(_translate("SelectSvVariablesDialog", "Get indicators"))
        self.list_multiselect.setTitle(_translate("SelectSvVariablesDialog", "Select indicators"))
        self.indicator_info.setTitle(_translate("SelectSvVariablesDialog", "Indicator details"))
        self.country_select.setTitle(_translate("SelectSvVariablesDialog", "Select countries"))

from list_multiselect_widget import ListMultiSelectWidget
