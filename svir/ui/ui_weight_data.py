# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_weight_data.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_WeightDataDialog(object):
    def setupUi(self, WeightDataDialog):
        WeightDataDialog.setObjectName("WeightDataDialog")
        WeightDataDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        WeightDataDialog.resize(800, 700)
        WeightDataDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(WeightDataDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.on_the_fly_ckb = QtWidgets.QCheckBox(WeightDataDialog)
        self.on_the_fly_ckb.setChecked(True)
        self.on_the_fly_ckb.setObjectName("on_the_fly_ckb")
        self.gridLayout.addWidget(self.on_the_fly_ckb, 4, 0, 1, 1)
        self.style_by_field_cbx = QtWidgets.QComboBox(WeightDataDialog)
        self.style_by_field_cbx.setObjectName("style_by_field_cbx")
        self.gridLayout.addWidget(self.style_by_field_cbx, 3, 0, 1, 1)
        self.web_view = QtWebKitWidgets.QWebView(WeightDataDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.web_view.sizePolicy().hasHeightForWidth())
        self.web_view.setSizePolicy(sizePolicy)
        self.web_view.setObjectName("web_view")
        self.gridLayout.addWidget(self.web_view, 0, 0, 1, 1)
        self.label = QtWidgets.QLabel(WeightDataDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.print_btn = QtWidgets.QPushButton(WeightDataDialog)
        self.print_btn.setObjectName("print_btn")
        self.horizontalLayout.addWidget(self.print_btn)
        self.buttonBox = QtWidgets.QDialogButtonBox(WeightDataDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 5, 0, 1, 1)
        self.web_view.raise_()
        self.label.raise_()
        self.on_the_fly_ckb.raise_()
        self.style_by_field_cbx.raise_()

        self.retranslateUi(WeightDataDialog)
        self.buttonBox.accepted.connect(WeightDataDialog.accept)
        self.buttonBox.rejected.connect(WeightDataDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(WeightDataDialog)

    def retranslateUi(self, WeightDataDialog):
        _translate = QtCore.QCoreApplication.translate
        WeightDataDialog.setWindowTitle(_translate("WeightDataDialog", "Weight Data"))
        self.on_the_fly_ckb.setText(_translate("WeightDataDialog", "Run calculations on-the-fly"))
        self.label.setText(_translate("WeightDataDialog", "Style the layer by"))
        self.print_btn.setText(_translate("WeightDataDialog", "Save as PDF"))

from qgis.PyQt import QtWebKitWidgets
