# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_svir.ui'
#
# Created: Thu Oct 24 11:00:28 2013
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
        SvirDialog.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(SvirDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(SvirDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SvirDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SvirDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SvirDialog)

    def retranslateUi(self, SvirDialog):
        SvirDialog.setWindowTitle(QtGui.QApplication.translate("SvirDialog", "Svir", None, QtGui.QApplication.UnicodeUTF8))

