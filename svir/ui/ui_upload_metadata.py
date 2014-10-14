# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_upload_metadata.ui'
#
# Created: Tue Oct 14 11:14:54 2014
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

class Ui_UploadMetadataDialog(object):
    def setupUi(self, UploadMetadataDialog):
        UploadMetadataDialog.setObjectName(_fromUtf8("UploadMetadataDialog"))
        UploadMetadataDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        UploadMetadataDialog.resize(900, 551)
        self.gridLayout = QtGui.QGridLayout(UploadMetadataDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(UploadMetadataDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.web_view = QtWebKit.QWebView(UploadMetadataDialog)
        self.web_view.setObjectName(_fromUtf8("web_view"))
        self.gridLayout.addWidget(self.web_view, 0, 0, 1, 1)

        self.retranslateUi(UploadMetadataDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UploadMetadataDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UploadMetadataDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UploadMetadataDialog)

    def retranslateUi(self, UploadMetadataDialog):
        UploadMetadataDialog.setWindowTitle(_translate("UploadMetadataDialog", "Upload project", None))

from PyQt4 import QtWebKit
