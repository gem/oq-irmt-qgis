import sys
from qgis.core import QgsApplication
from PyQt4 import QtGui
from qgis.gui import QgsMapCanvas


def main():
    app = QtGui.QApplication(sys.argv, True)
    # supply path to where is your qgis installed
    QgsApplication.setPrefixPath("/usr/lib", True)
    # load providers
    QgsApplication.initQgis()

    canvas = QgsMapCanvas()
    canvas.setCanvasColor(QtGui.QColor(255, 255, 255))
    canvas.enableAntiAliasing(True)
    try:
        canvas.show()
        app.exec_()
    finally:
        QgsApplication.exitQgis()

if __name__ == '__main__':
    main()
    # launch with PYTHONPATH=/usr/share/qgis/python python example.py
