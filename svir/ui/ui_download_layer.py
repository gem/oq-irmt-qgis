# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_download_layer.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_DownloadLayerDialog(object):
    def setupUi(self, DownloadLayerDialog):
        DownloadLayerDialog.setObjectName("DownloadLayerDialog")
        DownloadLayerDialog.resize(700, 700)
        DownloadLayerDialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(DownloadLayerDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(DownloadLayerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(DownloadLayerDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.layers_lst = QtWidgets.QListWidget(DownloadLayerDialog)
        self.layers_lst.setObjectName("layers_lst")
        self.gridLayout.addWidget(self.layers_lst, 1, 0, 1, 1)
        self.layer_detail = QtWidgets.QTextEdit(DownloadLayerDialog)
        self.layer_detail.setReadOnly(True)
        self.layer_detail.setObjectName("layer_detail")
        self.gridLayout.addWidget(self.layer_detail, 3, 0, 1, 1)
        self.layer_lbl = QtWidgets.QLabel(DownloadLayerDialog)
        self.layer_lbl.setObjectName("layer_lbl")
        self.gridLayout.addWidget(self.layer_lbl, 2, 0, 1, 1)

        self.retranslateUi(DownloadLayerDialog)
        self.buttonBox.accepted.connect(DownloadLayerDialog.accept)
        self.buttonBox.rejected.connect(DownloadLayerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DownloadLayerDialog)

    def retranslateUi(self, DownloadLayerDialog):
        _translate = QtCore.QCoreApplication.translate
        DownloadLayerDialog.setWindowTitle(_translate("DownloadLayerDialog", "Download project from the OpenQuake Platform"))
        self.label.setText(_translate("DownloadLayerDialog", "Please select one of the available projects"))
        self.layer_detail.setHtml(_translate("DownloadLayerDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.layer_lbl.setText(_translate("DownloadLayerDialog", "Project details"))

