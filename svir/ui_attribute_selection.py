# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_attribute_selection.ui'
#
# Created: Wed Nov 13 17:27:21 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_AttributeSelctionDialog(object):
    def setupUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setObjectName(_fromUtf8("AttributeSelctionDialog"))
        AttributeSelctionDialog.setWindowModality(QtCore.Qt.WindowModal)
        AttributeSelctionDialog.resize(399, 300)
        AttributeSelctionDialog.setModal(True)
        self.buttonBox = QtGui.QDialogButtonBox(AttributeSelctionDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayoutWidget = QtGui.QWidget(AttributeSelctionDialog)
        self.formLayoutWidget.setGeometry(QtCore.QRect(9, 10, 381, 221))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setMargin(0)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_attr_name_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.loss_attr_name_lbl.setObjectName(_fromUtf8("loss_attr_name_lbl"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.loss_attr_name_lbl)
        self.loss_attr_name_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.loss_attr_name_cbox.setObjectName(_fromUtf8("loss_attr_name_cbox"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.loss_attr_name_cbox)
        self.reg_id_attr_name_loss_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.reg_id_attr_name_loss_lbl.setObjectName(_fromUtf8("reg_id_attr_name_loss_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.reg_id_attr_name_loss_lbl)
        self.reg_id_attr_name_loss_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.reg_id_attr_name_loss_cbox.setObjectName(_fromUtf8("reg_id_attr_name_loss_cbox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.reg_id_attr_name_loss_cbox)
        self.reg_id_attr_name_region_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.reg_id_attr_name_region_lbl.setObjectName(_fromUtf8("reg_id_attr_name_region_lbl"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.reg_id_attr_name_region_lbl)
        self.reg_id_attr_name_region_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.reg_id_attr_name_region_cbox.setObjectName(_fromUtf8("reg_id_attr_name_region_cbox"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.reg_id_attr_name_region_cbox)
        self.regions_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.regions_layer_lbl.setObjectName(_fromUtf8("regions_layer_lbl"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.regions_layer_lbl)
        self.loss_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.loss_layer_lbl)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.formLayout.setItem(4, QtGui.QFormLayout.FieldRole, spacerItem)

        self.retranslateUi(AttributeSelctionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AttributeSelctionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AttributeSelctionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AttributeSelctionDialog)

    def retranslateUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setWindowTitle(QtGui.QApplication.translate("AttributeSelctionDialog", "Attribute Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_attr_name_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Loss attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.reg_id_attr_name_loss_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Region ID attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.reg_id_attr_name_region_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Region ID attriubute name", None, QtGui.QApplication.UnicodeUTF8))
        self.regions_layer_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Regions layer", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Loss layer", None, QtGui.QApplication.UnicodeUTF8))

