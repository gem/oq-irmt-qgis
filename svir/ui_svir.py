# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_svir.ui'
#
# Created: Mon Nov 18 17:49:40 2013
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
        SvirDialog.resize(491, 187)
        self.verticalLayout_2 = QtGui.QVBoxLayout(SvirDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.loss_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.loss_layer_tbn.setObjectName(_fromUtf8("loss_layer_tbn"))
        self.gridLayout.addWidget(self.loss_layer_tbn, 0, 2, 1, 1)
        self.loss_layer_lbl = QtGui.QLabel(SvirDialog)
        self.loss_layer_lbl.setObjectName(_fromUtf8("loss_layer_lbl"))
        self.gridLayout.addWidget(self.loss_layer_lbl, 0, 0, 1, 1)
        self.loss_layer_le = QtGui.QLineEdit(SvirDialog)
        self.loss_layer_le.setObjectName(_fromUtf8("loss_layer_le"))
        self.gridLayout.addWidget(self.loss_layer_le, 0, 1, 1, 1)
        self.zonal_layer_lbl = QtGui.QLabel(SvirDialog)
        self.zonal_layer_lbl.setObjectName(_fromUtf8("zonal_layer_lbl"))
        self.gridLayout.addWidget(self.zonal_layer_lbl, 1, 0, 1, 1)
        self.zonal_layer_le = QtGui.QLineEdit(SvirDialog)
        self.zonal_layer_le.setObjectName(_fromUtf8("zonal_layer_le"))
        self.gridLayout.addWidget(self.zonal_layer_le, 1, 1, 1, 1)
        self.zonal_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.zonal_layer_tbn.setObjectName(_fromUtf8("zonal_layer_tbn"))
        self.gridLayout.addWidget(self.zonal_layer_tbn, 1, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.buttonBox = QtGui.QDialogButtonBox(SvirDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(SvirDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SvirDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SvirDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SvirDialog)

    def retranslateUi(self, SvirDialog):
        SvirDialog.setWindowTitle(QtGui.QApplication.translate("SvirDialog", "Svir", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.loss_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Loss layer", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Zonal layer", None, QtGui.QApplication.UnicodeUTF8))
        self.zonal_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))

