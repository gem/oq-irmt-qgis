# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_input_layers.ui'
#
# Created: Mon Jan 26 11:16:10 2015
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

class Ui_SelectInputLayersDialog(object):
    def setupUi(self, SelectInputLayersDialog):
        SelectInputLayersDialog.setObjectName(_fromUtf8("SelectInputLayersDialog"))
        SelectInputLayersDialog.resize(530, 161)
        self.formLayout = QtGui.QFormLayout(SelectInputLayersDialog)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_layer_lbl = QtGui.QLabel(SelectInputLayersDialog)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.loss_layer_cbx = QtGui.QComboBox(SelectInputLayersDialog)
        self.loss_layer_cbx.setObjectName(_fromUtf8("loss_layer_cbx"))
        self.horizontalLayout_3.addWidget(self.loss_layer_cbx)
        self.loss_layer_tbn = QtGui.QToolButton(SelectInputLayersDialog)
        self.loss_layer_tbn.setObjectName(_fromUtf8("loss_layer_tbn"))
        self.horizontalLayout_3.addWidget(self.loss_layer_tbn)
        self.formLayout.setLayout(0, QtGui.QFormLayout.FieldRole, self.horizontalLayout_3)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.zonal_layer_cbx = QtGui.QComboBox(SelectInputLayersDialog)
        self.zonal_layer_cbx.setObjectName(_fromUtf8("zonal_layer_cbx"))
        self.horizontalLayout_2.addWidget(self.zonal_layer_cbx)
        self.zonal_layer_tbn = QtGui.QToolButton(SelectInputLayersDialog)
        self.zonal_layer_tbn.setObjectName(_fromUtf8("zonal_layer_tbn"))
        self.horizontalLayout_2.addWidget(self.zonal_layer_tbn)
        self.formLayout.setLayout(1, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.zonal_layer_lbl = QtGui.QLabel(SelectInputLayersDialog)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.zonal_layer_lbl)
        self.purge_chk = QtGui.QCheckBox(SelectInputLayersDialog)
        self.purge_chk.setObjectName(_fromUtf8("purge_chk"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.purge_chk)
        self.buttonBox = QtGui.QDialogButtonBox(SelectInputLayersDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(SelectInputLayersDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectInputLayersDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectInputLayersDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectInputLayersDialog)

    def retranslateUi(self, SelectInputLayersDialog):
        SelectInputLayersDialog.setWindowTitle(_translate("SelectInputLayersDialog", "Aggregate loss by zone", None))
        self.loss_layer_lbl.setText(_translate("SelectInputLayersDialog", "Loss layer", None))
        self.loss_layer_tbn.setText(_translate("SelectInputLayersDialog", "...", None))
        self.zonal_layer_tbn.setText(_translate("SelectInputLayersDialog", "...", None))
        self.zonal_layer_lbl.setText(_translate("SelectInputLayersDialog", "Zonal layer", None))
        self.purge_chk.setText(_translate("SelectInputLayersDialog", "Purge zones containing no loss points", None))

