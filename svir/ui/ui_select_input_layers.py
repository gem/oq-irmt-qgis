# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_input_layers.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_SelectInputLayersDialog(object):
    def setupUi(self, SelectInputLayersDialog):
        SelectInputLayersDialog.setObjectName("SelectInputLayersDialog")
        SelectInputLayersDialog.resize(530, 161)
        self.formLayout = QtWidgets.QFormLayout(SelectInputLayersDialog)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.loss_layer_lbl = QtWidgets.QLabel(SelectInputLayersDialog)
        self.loss_layer_lbl.setObjectName("loss_layer_lbl")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.loss_layer_cbx = QtWidgets.QComboBox(SelectInputLayersDialog)
        self.loss_layer_cbx.setObjectName("loss_layer_cbx")
        self.horizontalLayout_3.addWidget(self.loss_layer_cbx)
        self.loss_layer_tbn = QtWidgets.QToolButton(SelectInputLayersDialog)
        self.loss_layer_tbn.setObjectName("loss_layer_tbn")
        self.horizontalLayout_3.addWidget(self.loss_layer_tbn)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.zonal_layer_cbx = QtWidgets.QComboBox(SelectInputLayersDialog)
        self.zonal_layer_cbx.setObjectName("zonal_layer_cbx")
        self.horizontalLayout_2.addWidget(self.zonal_layer_cbx)
        self.zonal_layer_tbn = QtWidgets.QToolButton(SelectInputLayersDialog)
        self.zonal_layer_tbn.setObjectName("zonal_layer_tbn")
        self.horizontalLayout_2.addWidget(self.zonal_layer_tbn)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.zonal_layer_lbl = QtWidgets.QLabel(SelectInputLayersDialog)
        self.zonal_layer_lbl.setObjectName("zonal_layer_lbl")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.zonal_layer_lbl)
        self.purge_chk = QtWidgets.QCheckBox(SelectInputLayersDialog)
        self.purge_chk.setObjectName("purge_chk")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.purge_chk)
        self.buttonBox = QtWidgets.QDialogButtonBox(SelectInputLayersDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(SelectInputLayersDialog)
        self.buttonBox.accepted.connect(SelectInputLayersDialog.accept)
        self.buttonBox.rejected.connect(SelectInputLayersDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectInputLayersDialog)

    def retranslateUi(self, SelectInputLayersDialog):
        _translate = QtCore.QCoreApplication.translate
        SelectInputLayersDialog.setWindowTitle(_translate("SelectInputLayersDialog", "Aggregate loss by zone"))
        self.loss_layer_lbl.setText(_translate("SelectInputLayersDialog", "Loss layer"))
        self.loss_layer_tbn.setText(_translate("SelectInputLayersDialog", "..."))
        self.zonal_layer_tbn.setText(_translate("SelectInputLayersDialog", "..."))
        self.zonal_layer_lbl.setText(_translate("SelectInputLayersDialog", "Zonal layer"))
        self.purge_chk.setText(_translate("SelectInputLayersDialog", "Purge zones containing no loss points"))

