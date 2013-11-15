# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_select_layers_to_join.ui'
#
# Created: Thu Nov 14 17:25:31 2013
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
        self.buttonBox = QtGui.QDialogButtonBox(SelectLayersToJoinDialog)
        self.buttonBox.setGeometry(QtCore.QRect(300, 130, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayoutWidget = QtGui.QWidget(SelectLayersToJoinDialog)
        self.formLayoutWidget.setGeometry(QtCore.QRect(29, 9, 611, 91))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setMargin(0)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.loss_layer_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.loss_layer_cbox.setObjectName(_fromUtf8("loss_layer_cbox"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.loss_layer_cbox)
        self.svi_layer_cbox = QtGui.QComboBox(self.formLayoutWidget)
        self.svi_layer_cbox.setObjectName(_fromUtf8("svi_layer_cbox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.svi_layer_cbox)
        self.loss_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.loss_layer_lbl)
        self.svi_layer_lbl = QtGui.QLabel(self.formLayoutWidget)
        self.svi_layer_lbl.setObjectName(_fromUtf8("svi_layer_lbl"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.svi_layer_lbl)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.formLayout.setItem(2, QtGui.QFormLayout.FieldRole, spacerItem)

        self.retranslateUi(SelectLayersToJoinDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SelectLayersToJoinDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SelectLayersToJoinDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectLayersToJoinDialog)

    def retranslateUi(self, SelectLayersToJoinDialog):
        SelectLayersToJoinDialog.setWindowTitle(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Select layers to join", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Layer containing loss data", None, QtGui.QApplication.UnicodeUTF8))
        self.svi_layer_lbl.setText(QtGui.QApplication.translate("SelectLayersToJoinDialog", "Layer containing SVI data", None, QtGui.QApplication.UnicodeUTF8))

