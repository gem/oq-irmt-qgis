# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_attribute_selection.ui'
#
# Created: Mon Nov 18 18:01:47 2013
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
        self.zone_id_attr_name_loss_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.zone_id_attr_name_loss_lbl.setObjectName(_fromUtf8("zone_id_attr_name_loss_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.zone_id_attr_name_loss_lbl)
        self.zone_id_attr_name_loss_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.zone_id_attr_name_loss_cbox.setObjectName(_fromUtf8("zone_id_attr_name_loss_cbox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.zone_id_attr_name_loss_cbox)
        self.zone_id_attr_name_zone_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.zone_id_attr_name_zone_lbl.setObjectName(_fromUtf8("zone_id_attr_name_zone_lbl"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.LabelRole, self.zone_id_attr_name_zone_lbl)
        self.zone_id_attr_name_zone_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.zone_id_attr_name_zone_cbox.setObjectName(_fromUtf8("zone_id_attr_name_zone_cbox"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.zone_id_attr_name_zone_cbox)
        self.zonal_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.zonal_layer_lbl)
        self.loss_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.loss_layer_lbl)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.formLayout.setItem(4, QtGui.QFormLayout.FieldRole, spacerItem)
        self.zonal_attr_name_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.zonal_attr_name_cbox.setObjectName(_fromUtf8("zonal_attr_name_cbox"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.zonal_attr_name_cbox)
        self.zonal_attr_name_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.zonal_attr_name_lbl.setObjectName(_fromUtf8("zonal_attr_name_lbl"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.zonal_attr_name_lbl)

        self.retranslateUi(AttributeSelctionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AttributeSelctionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AttributeSelctionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AttributeSelctionDialog)

    def retranslateUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setWindowTitle(QtGui.QApplication.translate("AttributeSelctionDialog", "Attribute Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_attr_name_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Loss attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.zone_id_attr_name_loss_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Zone ID attribute name", None, QtGui.QApplication.UnicodeUTF8))
        self.zone_id_attr_name_zone_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Zone ID attriubute name", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Zonal layer", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Losses layer", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_attr_name_lbl.setText(QtGui.QApplication.translate("AttributeSelctionDialog", "Zonal attribute name", None, QtGui.QApplication.UnicodeUTF8))

