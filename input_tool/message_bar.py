from PyQt4 import QtGui


class MessageBar(QtGui.QWidget):
    def __init__(self, default_message, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.default_message = default_message
        self.label = QtGui.QLabel(default_message)
        self.closeBtn = QtGui.QToolButton()
        self.closeBtn.setText('x')
        self.closeBtn.hide()
        self.closeBtn.clicked.connect(self.restore_default)

        layout = QtGui.QVBoxLayout(self)
        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.label)
        hlayout.addWidget(self.closeBtn)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        line = QtGui.QWidget()
        line.setFixedHeight(1)
        line.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Fixed)
        line.setStyleSheet("background-color: #c0c0c0;")
        layout.addWidget(line)

    def show_message(self, message):
        self.closeBtn.show()
        self.label.setText(message)
        self.setStyleSheet("background-color: #ff5050;")
        #QtCore.QTimer.singleShot(3000, self.restore_default)

    def restore_default(self):
        self.label.setText(self.default_message)
        self.label.setStyleSheet("background-color: none;")
        self.closeBtn.hide()
