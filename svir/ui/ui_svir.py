# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_svir.ui'
#
# Created: Tue Jan 28 14:17:40 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SvirDialog(object):
    def setupUi(self, SvirDialog):
        SvirDialog.setObjectName(_fromUtf8("SvirDialog"))
        SvirDialog.resize(530, 161)
        self.formLayout = QtGui.QFormLayout(SvirDialog)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_layer_lbl = QtGui.QLabel(SvirDialog)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.loss_layer_cbx = QtGui.QComboBox(SvirDialog)
        self.loss_layer_cbx.setObjectName(_fromUtf8("loss_layer_cbx"))
        self.horizontalLayout_3.addWidget(self.loss_layer_cbx)
        self.loss_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.loss_layer_tbn.setObjectName(_fromUtf8("loss_layer_tbn"))
        self.horizontalLayout_3.addWidget(self.loss_layer_tbn)
        self.formLayout.setLayout(0, QtGui.QFormLayout.FieldRole, self.horizontalLayout_3)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.zonal_layer_cbx = QtGui.QComboBox(SvirDialog)
        self.zonal_layer_cbx.setObjectName(_fromUtf8("zonal_layer_cbx"))
        self.horizontalLayout_2.addWidget(self.zonal_layer_cbx)
        self.zonal_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.zonal_layer_tbn.setObjectName(_fromUtf8("zonal_layer_tbn"))
        self.horizontalLayout_2.addWidget(self.zonal_layer_tbn)
        self.formLayout.setLayout(1, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.zonal_layer_lbl = QtGui.QLabel(SvirDialog)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.zonal_layer_lbl)
        self.purge_chk = QtGui.QCheckBox(SvirDialog)
        self.purge_chk.setObjectName(_fromUtf8("purge_chk"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.purge_chk)
        self.buttonBox = QtGui.QDialogButtonBox(SvirDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(SvirDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SvirDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SvirDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SvirDialog)

    def retranslateUi(self, SvirDialog):
        SvirDialog.setWindowTitle(QtGui.QApplication.translate("SvirDialog", "Svir", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Loss layer", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Zonal layer", None, QtGui.QApplication.UnicodeUTF8))
        self.purge_chk.setText(QtGui.QApplication.translate("SvirDialog", "Purge zones containing no loss points", None, QtGui.QApplication.UnicodeUTF8))

