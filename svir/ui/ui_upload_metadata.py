# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_upload_metadata.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtGui, QtWidgets

class Ui_UploadMetadataDialog(object):
    def setupUi(self, UploadMetadataDialog):
        UploadMetadataDialog.setObjectName("UploadMetadataDialog")
        UploadMetadataDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        UploadMetadataDialog.resize(900, 551)
        self.verticalLayout = QtWidgets.QVBoxLayout(UploadMetadataDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.web_view = QtWebKitWidgets.QWebView(UploadMetadataDialog)
        self.web_view.setObjectName("web_view")
        self.verticalLayout.addWidget(self.web_view)
        self.buttonBox = QtWidgets.QDialogButtonBox(UploadMetadataDialog)
        self.buttonBox.setEnabled(False)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UploadMetadataDialog)
        self.buttonBox.accepted.connect(UploadMetadataDialog.accept)
        self.buttonBox.rejected.connect(UploadMetadataDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UploadMetadataDialog)

    def retranslateUi(self, UploadMetadataDialog):
        _translate = QtCore.QCoreApplication.translate
        UploadMetadataDialog.setWindowTitle(_translate("UploadMetadataDialog", "Upload project"))

from qgis.PyQt import QtWebKitWidgets
