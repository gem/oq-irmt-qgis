# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_choose_sv_data_source.ui'
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

class Ui_ChooseSvDataSourceDialog(object):
    def setupUi(self, ChooseSvDataSourceDialog):
        ChooseSvDataSourceDialog.setObjectName(_fromUtf8("ChooseSvDataSourceDialog"))
        ChooseSvDataSourceDialog.resize(407, 160)
        ChooseSvDataSourceDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(ChooseSvDataSourceDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.layer_rbn = QtGui.QRadioButton(ChooseSvDataSourceDialog)
        self.layer_rbn.setObjectName(_fromUtf8("layer_rbn"))
        self.gridLayout.addWidget(self.layer_rbn, 2, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ChooseSvDataSourceDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        self.platform_rbn = QtGui.QRadioButton(ChooseSvDataSourceDialog)
        self.platform_rbn.setObjectName(_fromUtf8("platform_rbn"))
        self.gridLayout.addWidget(self.platform_rbn, 1, 0, 1, 1)
        self.question_lbl = QtGui.QLabel(ChooseSvDataSourceDialog)
        self.question_lbl.setObjectName(_fromUtf8("question_lbl"))
        self.gridLayout.addWidget(self.question_lbl, 0, 0, 1, 1)

        self.retranslateUi(ChooseSvDataSourceDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ChooseSvDataSourceDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ChooseSvDataSourceDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ChooseSvDataSourceDialog)

    def retranslateUi(self, ChooseSvDataSourceDialog):
        ChooseSvDataSourceDialog.setWindowTitle(QtGui.QApplication.translate("ChooseSvDataSourceDialog", "Load socioeconomic indicators", None, QtGui.QApplication.UnicodeUTF8))
        self.layer_rbn.setText(QtGui.QApplication.translate("ChooseSvDataSourceDialog", "Use one of the available layers", None, QtGui.QApplication.UnicodeUTF8))
        self.platform_rbn.setText(QtGui.QApplication.translate("ChooseSvDataSourceDialog", "Load data from the OpenQuake Platform", None, QtGui.QApplication.UnicodeUTF8))
        self.question_lbl.setText(QtGui.QApplication.translate("ChooseSvDataSourceDialog", "Please select the source for the socioeconomic indicators", None, QtGui.QApplication.UnicodeUTF8))

