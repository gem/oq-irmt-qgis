# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_weight_data.ui'
#
# Created: Thu Dec 17 13:45:06 2015
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

class Ui_WeightDataDialog(object):
    def setupUi(self, WeightDataDialog):
        WeightDataDialog.setObjectName(_fromUtf8("WeightDataDialog"))
        WeightDataDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        WeightDataDialog.resize(800, 700)
        WeightDataDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(WeightDataDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.on_the_fly_ckb = QtGui.QCheckBox(WeightDataDialog)
        self.on_the_fly_ckb.setChecked(True)
        self.on_the_fly_ckb.setObjectName(_fromUtf8("on_the_fly_ckb"))
        self.gridLayout.addWidget(self.on_the_fly_ckb, 4, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(WeightDataDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 1)
        self.style_by_field_cbx = QtGui.QComboBox(WeightDataDialog)
        self.style_by_field_cbx.setObjectName(_fromUtf8("style_by_field_cbx"))
        self.gridLayout.addWidget(self.style_by_field_cbx, 3, 0, 1, 1)
        self.web_view = QtWebKit.QWebView(WeightDataDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.web_view.sizePolicy().hasHeightForWidth())
        self.web_view.setSizePolicy(sizePolicy)
        self.web_view.setObjectName(_fromUtf8("web_view"))
        self.gridLayout.addWidget(self.web_view, 0, 0, 1, 1)
        self.label = QtGui.QLabel(WeightDataDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.print_btn = QtGui.QPushButton(WeightDataDialog)
        self.print_btn.setObjectName(_fromUtf8("print_btn"))
        self.gridLayout.addWidget(self.print_btn, 1, 0, 1, 1)

        self.retranslateUi(WeightDataDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), WeightDataDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), WeightDataDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(WeightDataDialog)

    def retranslateUi(self, WeightDataDialog):
        WeightDataDialog.setWindowTitle(_translate("WeightDataDialog", "Weight Data", None))
        self.on_the_fly_ckb.setText(_translate("WeightDataDialog", "Run calculations on-the-fly", None))
        self.label.setText(_translate("WeightDataDialog", "Style the layer by", None))
        self.print_btn.setText(_translate("WeightDataDialog", "Save as PDF", None))

from PyQt4 import QtWebKit
