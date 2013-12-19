#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

# Adapted from extentSelector.py by Giuseppe Sucameli

from PyQt4 import QtCore
from qgis import core
from qgis import gui


class ExtentSelector(QtCore.QObject):
    selectionStopped = QtCore.pyqtSignal()
    selectionStarted = QtCore.pyqtSignal()

    def __init__(self, canvas, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.canvas = canvas
        self.isStarted = False
        self.tool = RectangleMapTool(canvas)
        self.previousMapTool = canvas.mapTool()

    def stop(self):
        if not self.isStarted:
            return
        self.isStarted = False
        self.tool.reset()
        self.canvas.unsetMapTool(self.tool)
        if self.previousMapTool != self.tool:
            self.canvas.setMapTool(self.previousMapTool)
        self.selectionStopped.emit()

    def start(self):
        prevMapTool = self.canvas.mapTool()
        if prevMapTool != self.tool:
            self.previousMapTool = prevMapTool
        self.canvas.setMapTool(self.tool)
        self.isStarted = True
        self.selectionStarted.emit()

    def getExtent(self):
        return self.tool.rectangle()


class RectangleMapTool(gui.QgsMapToolEmitPoint):
    rectangleCreated = QtCore.pyqtSignal()

    def __init__(self, canvas):
        self.canvas = canvas
        gui.QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.rubberBand = gui.QgsRubberBand(self.canvas, core.QGis.Polygon)
        # QGis.Polygon shades the region covered by the rubber band
        self.rubberBand.setColor(QtCore.Qt.red)
        self.rubberBand.setWidth(1)
        self.rubberBand.setBrushStyle(QtCore.Qt.Dense7Pattern)
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(core.QGis.Polygon)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showRect(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        self.rectangleCreated.emit()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(core.QGis.Polygon)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = core.QgsPoint(startPoint.x(), startPoint.y())
        point2 = core.QgsPoint(startPoint.x(), endPoint.y())
        point3 = core.QgsPoint(endPoint.x(), endPoint.y())
        point4 = core.QgsPoint(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)  # true to update canvas
        self.rubberBand.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None \
                or self.startPoint.x() == self.endPoint.x() \
                or self.startPoint.y() == self.endPoint.y():
            return None
        return core.QgsRectangle(self.startPoint, self.endPoint)
