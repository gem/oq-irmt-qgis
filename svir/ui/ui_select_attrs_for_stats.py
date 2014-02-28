# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_select_attrs_for_stats.ui'
#
# Created: Fri Feb 28 11:32:34 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SelectAttrsForStatsDialog(object):
    def setupUi(self, SelectAttrsForStatsDialog):
        SelectAttrsForStatsDialog.setObjectName(_fromUtf8("SelectAttrsForStatsDialog"))
        SelectAttrsForStatsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SelectAttrsForStatsDialog.resize(517, 184)
        SelectAttrsForStatsDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(SelectAttrsForStatsDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.layer_lbl = QtGui.QLabel(SelectAttrsForStatsDialog)
        self.layer_lbl.setObjectName(_fromUtf8("layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.layer_lbl)
        self.layer_cbx = QtGui.QComboBox(SelectAttrsForStatsDialog)
        self.layer_cbx.setObjectName(_fromUtf8("layer_cbx"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.layer_cbx)
        self.svi_attr_lbl = QtGui.QLabel(SelectAttrsForStatsDialog)
        self.svi_attr_lbl.setObjectName(_fromUtf8("svi_attr_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.svi_attr_lbl)
        self.svi_attr_cbx = QtGui.QComboBox(SelectAttrsForStatsDialog)
        self.svi_attr_cbx.setObjectName(_fromUtf8("svi_attr_cbx"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.svi_attr_cbx)
        self.aggr_loss_attr_lbl = QtGui.QLabel(SelectAttrsForStatsDialog)
        self.aggr_loss_attr_lbl.setObjectName(_fromUtf8("aggr_loss_attr_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.aggr_loss_attr_lbl)
        self.aggr_loss_attr_cbx = QtGui.QComboBox(SelectAttrsForStatsDialog)
        self.aggr_loss_attr_cbx.setObjectName(_fromUtf8("aggr_loss_attr_cbx"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.aggr_loss_attr_cbx)
        self.gridLayout.addLayout(self.formLayout, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.calc_btn = QtGui.QPushButton(SelectAttrsForStatsDialog)
        self.calc_btn.setObjectName(_fromUtf8("calc_btn"))
        self.horizontalLayout.addWidget(self.calc_btn)
        self.normalize_btn = QtGui.QPushButton(SelectAttrsForStatsDialog)
        self.normalize_btn.setObjectName(_fromUtf8("normalize_btn"))
        self.horizontalLayout.addWidget(self.normalize_btn)
        self.buttonBox = QtGui.QDialogButtonBox(SelectAttrsForStatsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(SelectAttrsForStatsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectAttrsForStatsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectAttrsForStatsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectAttrsForStatsDialog)

    def retranslateUi(self, SelectAttrsForStatsDialog):
        SelectAttrsForStatsDialog.setWindowTitle(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "Select attributes for statistical computations", None, QtGui.QApplication.UnicodeUTF8))
        self.layer_lbl.setText(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.svi_attr_lbl.setText(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "SVI attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.aggr_loss_attr_lbl.setText(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "Aggregated loss attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.calc_btn.setText(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "Advanced Calculator", None, QtGui.QApplication.UnicodeUTF8))
        self.normalize_btn.setText(QtGui.QApplication.translate("SelectAttrsForStatsDialog", "Normalize Attribute", None, QtGui.QApplication.UnicodeUTF8))

