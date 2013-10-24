# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_svir.ui'
#
# Created: Thu Oct 24 14:43:04 2013
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
        SvirDialog.resize(309, 113)
        self.verticalLayout_2 = QtGui.QVBoxLayout(SvirDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.input_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.input_layer_tbn.setObjectName(_fromUtf8("input_layer_tbn"))
        self.gridLayout.addWidget(self.input_layer_tbn, 0, 2, 1, 1)
        self.input_layer_lbl = QtGui.QLabel(SvirDialog)
        self.input_layer_lbl.setObjectName(_fromUtf8("input_layer_lbl"))
        self.gridLayout.addWidget(self.input_layer_lbl, 0, 0, 1, 1)
        self.input_layer_le = QtGui.QLineEdit(SvirDialog)
        self.input_layer_le.setObjectName(_fromUtf8("input_layer_le"))
        self.gridLayout.addWidget(self.input_layer_le, 0, 1, 1, 1)
        self.aggregation_layer_lbl = QtGui.QLabel(SvirDialog)
        self.aggregation_layer_lbl.setObjectName(_fromUtf8("aggregation_layer_lbl"))
        self.gridLayout.addWidget(self.aggregation_layer_lbl, 1, 0, 1, 1)
        self.aggregation_layer_le = QtGui.QLineEdit(SvirDialog)
        self.aggregation_layer_le.setObjectName(_fromUtf8("aggregation_layer_le"))
        self.gridLayout.addWidget(self.aggregation_layer_le, 1, 1, 1, 1)
        self.aggregation_layer_tbn = QtGui.QToolButton(SvirDialog)
        self.aggregation_layer_tbn.setObjectName(_fromUtf8("aggregation_layer_tbn"))
        self.gridLayout.addWidget(self.aggregation_layer_tbn, 1, 2, 1, 1)
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
        self.input_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.input_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Input Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.aggregation_layer_lbl.setText(QtGui.QApplication.translate("SvirDialog", "Aggregation Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.aggregation_layer_tbn.setText(QtGui.QApplication.translate("SvirDialog", "...", None, QtGui.QApplication.UnicodeUTF8))

