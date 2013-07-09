# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_process_manager.ui'
#
# Created: Tue Jul  9 15:56:17 2013
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(290, 442)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.stopBtn = QtGui.QPushButton(self.centralwidget)
        self.stopBtn.setEnabled(False)
        self.stopBtn.setObjectName(_fromUtf8("stopBtn"))
        self.gridLayout.addWidget(self.stopBtn, 3, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(779, 48, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 3, 2, 1, 1)
        self.label = QtGui.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 1, 1, 3)
        self.startBtn = QtGui.QPushButton(self.centralwidget)
        self.startBtn.setObjectName(_fromUtf8("startBtn"))
        self.gridLayout.addWidget(self.startBtn, 3, 1, 1, 1)
        self.outputTbr = QtGui.QTextBrowser(self.centralwidget)
        self.outputTbr.setObjectName(_fromUtf8("outputTbr"))
        self.gridLayout.addWidget(self.outputTbr, 1, 1, 1, 3)
        self.progressBar = QtGui.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 4, 1, 1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 290, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.stopBtn.setText(QtGui.QApplication.translate("MainWindow", "Stop Subprocess", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Process manager", None, QtGui.QApplication.UnicodeUTF8))
        self.startBtn.setText(QtGui.QApplication.translate("MainWindow", "Start Subprocess", None, QtGui.QApplication.UnicodeUTF8))

