# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_download_layer.ui'
#
# Created: Wed Jun  3 11:39:11 2015
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

class Ui_DownloadLayerDialog(object):
    def setupUi(self, DownloadLayerDialog):
        DownloadLayerDialog.setObjectName(_fromUtf8("DownloadLayerDialog"))
        DownloadLayerDialog.resize(700, 700)
        DownloadLayerDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(DownloadLayerDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(DownloadLayerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtGui.QLabel(DownloadLayerDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.layers_lst = QtGui.QListWidget(DownloadLayerDialog)
        self.layers_lst.setObjectName(_fromUtf8("layers_lst"))
        self.gridLayout.addWidget(self.layers_lst, 1, 0, 1, 1)
        self.layer_detail = QtGui.QTextEdit(DownloadLayerDialog)
        self.layer_detail.setReadOnly(True)
        self.layer_detail.setObjectName(_fromUtf8("layer_detail"))
        self.gridLayout.addWidget(self.layer_detail, 3, 0, 1, 1)
        self.layer_lbl = QtGui.QLabel(DownloadLayerDialog)
        self.layer_lbl.setObjectName(_fromUtf8("layer_lbl"))
        self.gridLayout.addWidget(self.layer_lbl, 2, 0, 1, 1)

        self.retranslateUi(DownloadLayerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DownloadLayerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DownloadLayerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DownloadLayerDialog)

    def retranslateUi(self, DownloadLayerDialog):
        DownloadLayerDialog.setWindowTitle(_translate("DownloadLayerDialog", "Download project from the OpenQuake Platform", None))
        self.label.setText(_translate("DownloadLayerDialog", "Please select one of the available projects", None))
        self.layer_detail.setHtml(_translate("DownloadLayerDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.layer_lbl.setText(_translate("DownloadLayerDialog", "Project definition", None))

