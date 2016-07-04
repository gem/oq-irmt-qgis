# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_drive_engine_server.ui'
#
# Created: Mon Jul  4 14:37:00 2016
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

class Ui_DriveEngineServerDialog(object):
    def setupUi(self, DriveEngineServerDialog):
        DriveEngineServerDialog.setObjectName(_fromUtf8("DriveEngineServerDialog"))
        DriveEngineServerDialog.resize(1222, 480)
        self.verticalLayout = QtGui.QVBoxLayout(DriveEngineServerDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.list_of_calcs_lbl = QtGui.QLabel(DriveEngineServerDialog)
        self.list_of_calcs_lbl.setObjectName(_fromUtf8("list_of_calcs_lbl"))
        self.verticalLayout.addWidget(self.list_of_calcs_lbl)
        self.reload_calcs_btn = QtGui.QPushButton(DriveEngineServerDialog)
        self.reload_calcs_btn.setObjectName(_fromUtf8("reload_calcs_btn"))
        self.verticalLayout.addWidget(self.reload_calcs_btn)
        self.calc_list_tbl = QtGui.QTableWidget(DriveEngineServerDialog)
        self.calc_list_tbl.setObjectName(_fromUtf8("calc_list_tbl"))
        self.calc_list_tbl.setColumnCount(0)
        self.calc_list_tbl.setRowCount(0)
        self.verticalLayout.addWidget(self.calc_list_tbl)
        self.list_of_outputs_lbl = QtGui.QLabel(DriveEngineServerDialog)
        self.list_of_outputs_lbl.setObjectName(_fromUtf8("list_of_outputs_lbl"))
        self.verticalLayout.addWidget(self.list_of_outputs_lbl)
        self.output_list_tbl = QtGui.QTableWidget(DriveEngineServerDialog)
        self.output_list_tbl.setObjectName(_fromUtf8("output_list_tbl"))
        self.output_list_tbl.setColumnCount(0)
        self.output_list_tbl.setRowCount(0)
        self.verticalLayout.addWidget(self.output_list_tbl)
        self.buttonBox = QtGui.QDialogButtonBox(DriveEngineServerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(DriveEngineServerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DriveEngineServerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DriveEngineServerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DriveEngineServerDialog)

    def retranslateUi(self, DriveEngineServerDialog):
        DriveEngineServerDialog.setWindowTitle(_translate("DriveEngineServerDialog", "Drive the OpenQuake Engine", None))
        self.list_of_calcs_lbl.setText(_translate("DriveEngineServerDialog", "List of calculations", None))
        self.reload_calcs_btn.setText(_translate("DriveEngineServerDialog", "Reload list of calculations", None))
        self.list_of_outputs_lbl.setText(_translate("DriveEngineServerDialog", "List of outputs", None))

