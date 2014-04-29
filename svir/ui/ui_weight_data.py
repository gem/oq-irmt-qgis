# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_weight_data.ui'
#
# Created: Mon Apr 28 16:36:01 2014
#      by: PyQt4 UI code generator 4.10.3
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
        WeightDataDialog.resize(900, 551)
        self.gridLayout = QtGui.QGridLayout(WeightDataDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(WeightDataDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.web_view = QtWebKit.QWebView(WeightDataDialog)
        self.web_view.setObjectName(_fromUtf8("web_view"))
        self.gridLayout.addWidget(self.web_view, 0, 0, 1, 1)

        self.retranslateUi(WeightDataDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), WeightDataDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), WeightDataDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(WeightDataDialog)

    def retranslateUi(self, WeightDataDialog):
        WeightDataDialog.setWindowTitle(_translate("WeightDataDialog", "Dialog", None))

from PyQt4 import QtWebKit
