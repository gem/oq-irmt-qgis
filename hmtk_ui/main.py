import os
import sys
import imp
import sip

for api in ['QString', 'QDate', 'QDateTime', 'QTextStream',
            'QTime', 'QUrl', 'QVariant']:
    sip.setapi(api, 2)

from PyQt4 import QtGui, QtCore

from qgis.core import QgsApplication

from main_window import MainWindow
from utils import excepthook


# A plugin file is a python source coded loaded at init time meant to
# register new hmtk algorithms to the hmtk registries.
PLUGIN_FILE = os.environ.get('HMTK_PLUGIN_FILE',
                             os.path.expanduser("~/hmtk-plugin.py"))


# Main entry to program.  Sets up the main app and create a new window.
def main(argv):

    # load plugins
    if os.path.exists(PLUGIN_FILE):
        imp.load_source('hmtk.plugin', PLUGIN_FILE)

    # create Qt application

    # Claim to be QGIS2 so that used plugins that tries to access
    # QSettings will get the QGIS2 settings
    QtGui.QApplication.setApplicationName('QGIS2')
    QtGui.QApplication.setOrganizationDomain('qgis.org')

    if QtCore.QSettings().value('locale/userLocale') is None:
        QtGui.QApplication.setOrganizationDomain('QGIS')

    app = QtGui.QApplication(argv, True)

    # setup QGIS
    QgsApplication.setPrefixPath(os.environ['QGIS_PREFIX_PATH'], True)
    QgsApplication.initQgis()

    # Install a custom exception hook that prints exception into a
    # MessageBox
    sys.excepthook = excepthook

    # create main window
    wnd = MainWindow()  # classname
    wnd.show()

    if sys.platform == "darwin":
        wnd.raise_()

    wnd.load_catalogue()

    # Connect signal for app finish
    def on_quit():
        QgsApplication.exitQgis()
        app.quit()

    app.lastWindowClosed.connect(on_quit)

    # Start the app up
    ret = app.exec_()

    sys.exit(ret)


if __name__ == "__main__":
    main(sys.argv)
