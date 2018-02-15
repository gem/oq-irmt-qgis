# -*- coding: utf-8 -*-
 
# Form implementation generated from reading ui file 'browser.ui'
#
# Created: Fri Jan 30 20:49:32 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!
 
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QUrl
from PyQt4.QtWebKit import QWebView
 
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
 
class BrowserDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(1024, 768)
        self.qwebview = QWebView(Dialog)
        self.qwebview.setGeometry(QtCore.QRect(0, 50, 1020, 711))
        self.qwebview.setObjectName(_fromUtf8("kwebview"))
        self.lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit.setGeometry(QtCore.QRect(10, 20, 1000, 25))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
 
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
 
    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Browser", "Browser", None))
