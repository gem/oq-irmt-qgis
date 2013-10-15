# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'completeness_dialog.ui'
#
# Created: Wed Sep 11 16:47:50 2013
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(290, 20, 81, 241))
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.tableWidget = QtGui.QTableWidget(Dialog)
        self.tableWidget.setGeometry(QtCore.QRect(10, 40, 256, 192))
        self.tableWidget.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed|QtGui.QAbstractItemView.DoubleClicked|QtGui.QAbstractItemView.EditKeyPressed|QtGui.QAbstractItemView.SelectedClicked)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableWidget.setWordWrap(True)
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.addRowButton = QtGui.QPushButton(Dialog)
        self.addRowButton.setGeometry(QtCore.QRect(10, 240, 114, 32))
        self.addRowButton.setObjectName(_fromUtf8("addRowButton"))
        self.removeRowButton = QtGui.QPushButton(Dialog)
        self.removeRowButton.setGeometry(QtCore.QRect(120, 240, 131, 32))
        self.removeRowButton.setObjectName(_fromUtf8("removeRowButton"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 251, 16))
        self.label.setObjectName(_fromUtf8("label"))

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(QtGui.QApplication.translate("Dialog", "Year", None, QtGui.QApplication.UnicodeUTF8))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(QtGui.QApplication.translate("Dialog", "Magnitude", None, QtGui.QApplication.UnicodeUTF8))
        self.addRowButton.setText(QtGui.QApplication.translate("Dialog", "Add Row", None, QtGui.QApplication.UnicodeUTF8))
        self.removeRowButton.setText(QtGui.QApplication.translate("Dialog", "Remove selected", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Input your custom completeness table", None, QtGui.QApplication.UnicodeUTF8))

