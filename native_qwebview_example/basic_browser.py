#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Basic web browser in PyQt4.
"""

import sys
from PyQt4 import QtCore, QtGui, QtWebKit


class BasicBrowser(QtGui.QWidget):
    def __init__(self, parent=None):
        super(BasicBrowser, self).__init__(parent)
        self.initGui()
        self.loadURL()

    def initGui(self):
        self.setWindowTitle('Browser')
        self.lineEdit = QtGui.QLineEdit()
        self.lineEdit.setText('http://www.google.it')
        self.qwebview = QtWebKit.QWebView()
        self.vlayout = QtGui.QVBoxLayout()
        self.vlayout.addWidget(self.lineEdit)
        self.vlayout.addWidget(self.qwebview)
        self.setLayout(self.vlayout)
        self.lineEdit.returnPressed.connect(self.loadURL)

    def loadURL(self):
        url = self.lineEdit.text()
        self.qwebview.load(QtCore.QUrl(url))
        self.show()


def main():

    app = QtGui.QApplication(sys.argv)
    browser = BasicBrowser()
    browser.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
