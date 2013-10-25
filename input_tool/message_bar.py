from PyQt4 import QtGui, QtCore


class MessageBar(QtGui.QWidget):
    def __init__(self, default_message, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.default_message = default_message
        self.message = QtGui.QLabel(default_message)
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.message)
        line = QtGui.QWidget()
        line.setFixedHeight(1)
        line.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Fixed)
        line.setStyleSheet(
            "background-color: #c0c0c0;")
        #line = QtGui.QFrame()
        #line.setFrameShadow(QtGui.QFrame.Sunken)
        #line.setHeight(3)
        #line.setLineWidth(1)
        layout.addWidget(line)
        #self.message.setFrameStyle(QtGui.QFrame.Panel)

    def show_message(self, message):
        self.message.setText(message)
        QtCore.QTimer.singleShot(5000, self.restore_default)

    def restore_default(self):
        self.message.setText(self.default_message)

