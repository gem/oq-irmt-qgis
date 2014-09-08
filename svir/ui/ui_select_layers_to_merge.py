# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_layers_to_merge.ui'
#
# Created: Mon Sep  8 16:21:26 2014
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

class Ui_SelectLayersToMergeDialog(object):
    def setupUi(self, SelectLayersToMergeDialog):
        SelectLayersToMergeDialog.setObjectName(_fromUtf8("SelectLayersToMergeDialog"))
        SelectLayersToMergeDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SelectLayersToMergeDialog.resize(671, 153)
        SelectLayersToMergeDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectLayersToMergeDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_layer_lbl = QtGui.QLabel(SelectLayersToMergeDialog)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.loss_layer_cbox = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.loss_layer_cbox.setObjectName(_fromUtf8("loss_layer_cbox"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.loss_layer_cbox)
        self.aggr_loss_attr_lbl = QtGui.QLabel(SelectLayersToMergeDialog)
        self.aggr_loss_attr_lbl.setObjectName(_fromUtf8("aggr_loss_attr_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.aggr_loss_attr_lbl)
        self.aggr_loss_attr_cbox = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.aggr_loss_attr_cbox.setObjectName(_fromUtf8("aggr_loss_attr_cbox"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.aggr_loss_attr_cbox)
        self.label = QtGui.QLabel(SelectLayersToMergeDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label)
        self.merge_attr_cbx = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.merge_attr_cbx.setObjectName(_fromUtf8("merge_attr_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.merge_attr_cbx)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SelectLayersToMergeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(SelectLayersToMergeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectLayersToMergeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectLayersToMergeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectLayersToMergeDialog)

    def retranslateUi(self, SelectLayersToMergeDialog):
        SelectLayersToMergeDialog.setWindowTitle(_translate("SelectLayersToMergeDialog", "Copy loss data into selected layer", None))
        self.loss_layer_lbl.setText(_translate("SelectLayersToMergeDialog", "Layer containing loss data", None))
        self.aggr_loss_attr_lbl.setText(_translate("SelectLayersToMergeDialog", "Attribute for aggregated losses", None))
        self.label.setText(_translate("SelectLayersToMergeDialog", "Merge by attribute", None))

