# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_select_layers_to_join.ui'
#
# Created: Wed Jan 29 10:55:13 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SelectLayersToJoinDialog(object):
    def setupUi(self, SelectLayersToJoinDialog):
        SelectLayersToJoinDialog.setObjectName(_fromUtf8("SelectLayersToJoinDialog"))
        SelectLayersToJoinDialog.setWindowModality(QtCore.Qt.WindowModal)
        SelectLayersToJoinDialog.resize(671, 171)
        SelectLayersToJoinDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectLayersToJoinDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_layer_lbl = QtGui.QLabel(SelectLayersToJoinDialog)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.loss_layer_cbox = QtGui.QComboBox(SelectLayersToJoinDialog)
        self.loss_layer_cbox.setObjectName(_fromUtf8("loss_layer_cbox"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.loss_layer_cbox)
        self.zonal_layer_lbl = QtGui.QLabel(SelectLayersToJoinDialog)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.zonal_layer_lbl)
        self.zonal_layer_cbox = QtGui.QComboBox(SelectLayersToJoinDialog)
        self.zonal_layer_cbox.setObjectName(_fromUtf8("zonal_layer_cbox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.zonal_layer_cbox)
        self.aggr_loss_attr_lbl = QtGui.QLabel(SelectLayersToJoinDialog)
        self.aggr_loss_attr_lbl.setObjectName(_fromUtf8("aggr_loss_attr_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.aggr_loss_attr_lbl)
        self.aggr_loss_attr_cbox = QtGui.QComboBox(SelectLayersToJoinDialog)
        self.aggr_loss_attr_cbox.setObjectName(_fromUtf8("aggr_loss_attr_cbox"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.aggr_loss_attr_cbox)
        self.label = QtGui.QLabel(SelectLayersToJoinDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label)
        self.merge_attr_cbx = QtGui.QComboBox(SelectLayersToJoinDialog)
        self.merge_attr_cbx.setObjectName(_fromUtf8("merge_attr_cbx"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.merge_attr_cbx)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SelectLayersToJoinDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(SelectLayersToJoinDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectLayersToJoinDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectLayersToJoinDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectLayersToJoinDialog)

    def retranslateUi(self, SelectLayersToJoinDialog):
        SelectLayersToJoinDialog.setWindowTitle(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Select layers to merge", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Layer containing loss data", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Layer containing zonal data", None, QtGui.QApplication.UnicodeUTF8))
        self.aggr_loss_attr_lbl.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Attribute for aggregated losses", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Merge by attribute", None, QtGui.QApplication.UnicodeUTF8))

