import time
import cStringIO
import traceback

from PyQt4 import QtGui


def excepthook(excType, excValue, tracebackobj):
    separator = '-' * 80
    notice = "An unhandled exception occurred. Error:"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = cStringIO.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    alert(str(notice) + str(msg))


def alert(msg):
    errorbox = QtGui.QMessageBox()
    errorbox.setText(msg)
    errorbox.exec_()
