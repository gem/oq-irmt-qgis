# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_attribute_selection.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_AttributeSelctionDialog(object):
    def setupUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setObjectName("AttributeSelctionDialog")
        AttributeSelctionDialog.setWindowModality(QtCore.Qt.WindowModal)
        AttributeSelctionDialog.resize(700, 377)
        AttributeSelctionDialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(AttributeSelctionDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(AttributeSelctionDialog)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.loss_attrs_multisel = ListMultiSelectWidget(AttributeSelctionDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loss_attrs_multisel.sizePolicy().hasHeightForWidth())
        self.loss_attrs_multisel.setSizePolicy(sizePolicy)
        self.loss_attrs_multisel.setObjectName("loss_attrs_multisel")
        self.verticalLayout.addWidget(self.loss_attrs_multisel)
        self.groupBox = QtWidgets.QGroupBox(AttributeSelctionDialog)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.zone_id_attr_name_loss_cbox = QtWidgets.QComboBox(self.groupBox)
        self.zone_id_attr_name_loss_cbox.setObjectName("zone_id_attr_name_loss_cbox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.zone_id_attr_name_loss_cbox)
        self.zone_id_attr_name_loss_lbl = QtWidgets.QLabel(self.groupBox)
        self.zone_id_attr_name_loss_lbl.setObjectName("zone_id_attr_name_loss_lbl")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.zone_id_attr_name_loss_lbl)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(AttributeSelctionDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayout_2 = QtWidgets.QFormLayout(self.groupBox_2)
        self.formLayout_2.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName("formLayout_2")
        self.zone_id_attr_name_zone_lbl = QtWidgets.QLabel(self.groupBox_2)
        self.zone_id_attr_name_zone_lbl.setObjectName("zone_id_attr_name_zone_lbl")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.zone_id_attr_name_zone_lbl)
        self.zone_id_attr_name_zone_cbox = QtWidgets.QComboBox(self.groupBox_2)
        self.zone_id_attr_name_zone_cbox.setObjectName("zone_id_attr_name_zone_cbox")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.zone_id_attr_name_zone_cbox)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(AttributeSelctionDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(AttributeSelctionDialog)
        self.buttonBox.accepted.connect(AttributeSelctionDialog.accept)
        self.buttonBox.rejected.connect(AttributeSelctionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AttributeSelctionDialog)

    def retranslateUi(self, AttributeSelctionDialog):
        _translate = QtCore.QCoreApplication.translate
        AttributeSelctionDialog.setWindowTitle(_translate("AttributeSelctionDialog", "Aggregate loss by zone"))
        self.label.setText(_translate("AttributeSelctionDialog", "For each zone, the plugin will calculate the count of loss points and (for each of the selected loss variables) the sum and average values"))
        self.loss_attrs_multisel.setTitle(_translate("AttributeSelctionDialog", "Loss Layer"))
        self.zone_id_attr_name_loss_lbl.setText(_translate("AttributeSelctionDialog", "Zone ID attribute name"))
        self.groupBox_2.setTitle(_translate("AttributeSelctionDialog", "Zonal Layer"))
        self.zone_id_attr_name_zone_lbl.setText(_translate("AttributeSelctionDialog", "Zone ID attriubute name"))

from list_multiselect_widget import ListMultiSelectWidget
