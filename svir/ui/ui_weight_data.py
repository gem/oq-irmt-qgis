# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_weight_data.ui'
#
# Created: Thu Jul  3 14:48:23 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

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
        WeightDataDialog.setWindowTitle(QtGui.QApplication.translate("WeightDataDialog", "Weight Data", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
