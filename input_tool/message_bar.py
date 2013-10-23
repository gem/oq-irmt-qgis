from PyQt4 import QtGui, QtCore


class MessageBar(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.message = QtGui.QLabel()

        layout = QtGui.QHBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.message)
        self.setVisible(False)

    def show_message(self, message):
        self.message.setText(message)
        self.show()
        QtCore.QTimer.singleShot(2000, self.hide);