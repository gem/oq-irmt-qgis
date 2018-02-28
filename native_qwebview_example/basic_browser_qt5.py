#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Basic web browser in PyQt5.
"""

import sys
from PyQt5 import QtCore, QtWidgets, QtWebKitWidgets


class BasicBrowser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BasicBrowser, self).__init__(parent)
        self.initGui()
        self.loadURL()

    def initGui(self):
        self.setWindowTitle('Browser')
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setText('http://www.google.it')
        self.qwebview = QtWebKitWidgets.QWebView()
        self.vlayout = QtWidgets.QVBoxLayout()
        self.vlayout.addWidget(self.lineEdit)
        self.vlayout.addWidget(self.qwebview)
        self.setLayout(self.vlayout)
        self.lineEdit.returnPressed.connect(self.loadURL)

    def loadURL(self):
        url = self.lineEdit.text()
        self.qwebview.load(QtCore.QUrl(url))
        self.show()


def main():

    app = QtWidgets.QApplication(sys.argv)
    browser = BasicBrowser()
    browser.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
