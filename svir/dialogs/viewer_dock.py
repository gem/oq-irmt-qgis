# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2015 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import json

from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    #NavigationToolbar2QT as NavigationToolbar
)

from qgis.core import QgsFeatureRequest

from svir.utilities.utils import get_ui_class

FORM_CLASS = get_ui_class('ui_viewer_dock.ui')


class ViewerDock(QtGui.QDockWidget, FORM_CLASS):
    def __init__(self, iface):
        """Constructor for the viewer dock.

        :param iface: A QGisAppInterface instance we use to access QGIS via.
        :type iface: QgsAppInterface
        .. note:: We use the multiple inheritance approach from Qt4 so that
            for elements are directly accessible in the form context and we can
            use autoconnect to set up slots. See article below:
            http://doc.qt.nokia.com/4.7-snapshot/designer-using-a-ui-file.html
        """
        QtGui.QDockWidget.__init__(self, None)
        self.setupUi(self)
        self.iface = iface

        self.active_layer = self.iface.activeLayer()

        self.current_selection = {}

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)
        self.plot = self.figure.add_subplot(111)

    def draw(self):
        self.plot.clear()
        for index, line in self.current_selection.iteritems():
            # print (index, line)
            self.plot.plot(line['ordinates'])

        self.canvas.draw()

    def layer_changed(self):
        self.current_selection = {}

        try:
            self.active_layer.selectionChanged.disconnect(
                self.selection_changed)
        except (TypeError, AttributeError):
            pass

        self.active_layer = self.iface.activeLayer()

        if self.active_layer is not None:
            self.active_layer.selectionChanged.connect(self.selection_changed)

    def selection_changed(self, selected, deselected, _):
        arg = 'PGA'
        selected_features = self.active_layer.getFeatures(
            QgsFeatureRequest().setFilterFids(selected))

        for fid in deselected:
            try:
                del self.current_selection[fid]
            except KeyError:
                pass

        for feature in selected_features:
            ordinates = json.loads(feature[arg])
            if feature.id() not in self.current_selection:
                self.current_selection[feature.id()] = {
                    'ordinates': ordinates,
                    'color': 'blue'
                }

        self.draw()
