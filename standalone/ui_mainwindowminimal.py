# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mainwindowminimal.ui'
#
# Created: Wed Jul 10 14:21:08 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindowMinimal(object):
    def setupUi(self, MainWindowMinimal):
        MainWindowMinimal.setObjectName(_fromUtf8("MainWindowMinimal"))
        MainWindowMinimal.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindowMinimal)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.canvas = QgsMapCanvas(self.centralwidget)
        self.canvas.setGeometry(QtCore.QRect(99, 19, 681, 521))
        self.canvas.setObjectName(_fromUtf8("canvas"))
        MainWindowMinimal.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindowMinimal)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindowMinimal.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindowMinimal)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindowMinimal.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindowMinimal)
        QtCore.QMetaObject.connectSlotsByName(MainWindowMinimal)

    def retranslateUi(self, MainWindowMinimal):
        MainWindowMinimal.setWindowTitle(QtGui.QApplication.translate("MainWindowMinimal", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))

from qgis.gui import QgsMapCanvas
