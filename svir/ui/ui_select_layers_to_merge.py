# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_layers_to_merge.ui'
#
# Created: Thu Jul  3 14:48:22 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SelectLayersToMergeDialog(object):
    def setupUi(self, SelectLayersToMergeDialog):
        SelectLayersToMergeDialog.setObjectName(_fromUtf8("SelectLayersToMergeDialog"))
        SelectLayersToMergeDialog.setWindowModality(QtCore.Qt.WindowModal)
        SelectLayersToMergeDialog.resize(671, 185)
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
        self.zonal_layer_lbl = QtGui.QLabel(SelectLayersToMergeDialog)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.zonal_layer_lbl)
        self.zonal_layer_cbox = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.zonal_layer_cbox.setObjectName(_fromUtf8("zonal_layer_cbox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.zonal_layer_cbox)
        self.aggr_loss_attr_lbl = QtGui.QLabel(SelectLayersToMergeDialog)
        self.aggr_loss_attr_lbl.setObjectName(_fromUtf8("aggr_loss_attr_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.aggr_loss_attr_lbl)
        self.aggr_loss_attr_cbox = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.aggr_loss_attr_cbox.setObjectName(_fromUtf8("aggr_loss_attr_cbox"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.aggr_loss_attr_cbox)
        self.label = QtGui.QLabel(SelectLayersToMergeDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label)
        self.merge_attr_cbx = QtGui.QComboBox(SelectLayersToMergeDialog)
        self.merge_attr_cbx.setObjectName(_fromUtf8("merge_attr_cbx"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.merge_attr_cbx)
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
        SelectLayersToMergeDialog.setWindowTitle(QtGui.QApplication.translate("SelectLayersToMergeDialog", "Merge loss and zonal data in a single layer", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToMergeDialog", "Layer containing loss data", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToMergeDialog", "Layer containing zonal data", None, QtGui.QApplication.UnicodeUTF8))
        self.aggr_loss_attr_lbl.setText(QtGui.QApplication.translate("SelectLayersToMergeDialog", "Attribute for aggregated losses", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SelectLayersToMergeDialog", "Merge by attribute", None, QtGui.QApplication.UnicodeUTF8))

