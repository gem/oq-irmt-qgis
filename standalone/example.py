import re
import sys
from PyQt4 import QtGui, QtCore
from ui_process_manager import Ui_MainWindow

PERCENT = re.compile(r'(\d+)%')


class MainWindow(Ui_MainWindow, QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.qproc = QtCore.QProcess(self)
        self.qproc.finished.connect(self.finished)
        self.qproc.error.connect(self.error)
        self.qproc.setReadChannel(QtCore.QProcess.StandardError)
        self.qproc.readyReadStandardError.connect(self.displayLine)

    @QtCore.pyqtSlot()
    def on_startBtn_clicked(self):
        self.outputTbr.setPlainText('starting...')
        self.progressBar.setValue(0)
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)
        self.qproc.start(sys.executable, ['externalprocess.py'])

    @QtCore.pyqtSlot()
    def on_stopBtn_clicked(self):
        self.outputTbr.append('killing...')
        self.qproc.kill()

    def finished(self, exitcode, killed):
        self.stopBtn.setEnabled(False)
        self.startBtn.setEnabled(True)
        if killed:
            self.outputTbr.append('Process killed prematurely')
        elif exitcode:
            self.outputTbr.append(str(self.qproc.readAllStandardError()))
            self.outputTbr.append('Finished with error code %d' % exitcode)
        else:
            self.outputTbr.append('Finished correctly')

    def error(self, err):
        self.outputTbr.append('Process died, error type=%d' % err)

    def displayLine(self):
        line = str(self.qproc.readLine())
        match = PERCENT.search(line)
        if match:
            percent = int(match.group(1))
            self.progressBar.setValue(percent)
        self.outputTbr.append(line)


def main():
    app = QtGui.QApplication(sys.argv, True)
    mw = MainWindow()
    try:
        mw.show()
        app.exec_()
    finally:
        pass

if __name__ == '__main__':
    main()
