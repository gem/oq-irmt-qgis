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
import numpy as np
import os

from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    # NavigationToolbar2QT as NavigationToolbar
)

from qgis.core import QgsFeatureRequest

from PyQt4.QtCore import pyqtSlot

from svir.utilities.shared import TEXTUAL_FIELD_TYPES
from svir.utilities.utils import get_ui_class, reload_attrib_cbx

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
        self.current_imt = None

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.central_layout.addWidget(self.canvas)
        self.plot = self.figure.add_subplot(111)

    def draw(self):
        self.plot.clear()
        for site, curve in self.current_selection.iteritems():

            ordinates = curve['ordinates']
            # FIXME use abscissa values from hdf5 file
            abscissa = np.linspace(0.0, 1.0, num=len(ordinates))

            self.plot.plot(
                    abscissa,
                    ordinates,
                    color=curve['color'],
                    linestyle='solid',
                    label='site ' + str(site)
            )
            self.plot.legend()

        self.canvas.draw()

    def layer_changed(self):
        self.current_selection = {}
        self.plot.clear()

        try:
            self.active_layer.selectionChanged.disconnect(
                    self.selection_changed)
        except (TypeError, AttributeError):
            pass

        self.active_layer = self.iface.activeLayer()

        if self.active_layer is not None:
            self.active_layer.selectionChanged.connect(self.selection_changed)

            reload_attrib_cbx(
                    self.imt_cbx, self.active_layer, False, TEXTUAL_FIELD_TYPES)

            if self.active_layer.selectedFeatureCount() > 0:
                self.set_selection(self.active_layer.selectedFeaturesIds())

    def set_selection(self, selected):
        self.selection_changed(selected, [], None)

    def selection_changed(self, selected, deselected, _):
        selected_features = self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFids(selected))

        for fid in deselected:
            try:
                del self.current_selection[fid]
            except KeyError:
                pass

        for feature in selected_features:
            ordinates = json.loads(feature[self.current_imt])
            if feature.id() not in self.current_selection:
                self.current_selection[feature.id()] = {
                    'ordinates': ordinates,
                    'color': 'blue'
                }

        self.draw()

    @pyqtSlot(int)
    def on_imt_cbx_currentIndexChanged(self):
        self.current_imt = self.imt_cbx.currentText()
        self.set_selection(self.current_selection.keys())

    @pyqtSlot()
    def on_export_data_button_clicked(self):

        filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser('~/hazard_curves_%s.csv' % self.current_imt),
                '*.csv')

        if filename:
            with open(filename, 'w') as csv_file:
                # csv_file.write(line + os.linesep)

                for site, curve in self.current_selection.iteritems():
                    line = '%s,%s' % (
                        site, ','.join(map(str, curve['ordinates'])))
                    csv_file.write(line + os.linesep)

    @pyqtSlot()
    def on_export_image_button_clicked(self):
        filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export plot'),
                os.path.expanduser('~/hazard_curves_%s.png' % self.current_imt),
                '*.png')

        if filename:
            self.figure.savefig(filename)
