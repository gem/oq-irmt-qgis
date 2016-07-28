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
import os

from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)


from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QColor
from qgis.gui import QgsVertexMarker
from qgis.core import QGis, QgsMapLayer, QgsFeatureRequest

from svir.utilities.shared import TEXTUAL_FIELD_TYPES
from svir.utilities.utils import get_ui_class, reload_attrib_cbx

FORM_CLASS = get_ui_class('ui_viewer_dock.ui')


class ViewerDock(QtGui.QDockWidget, FORM_CLASS):
    def __init__(self, iface, action):
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

        # this is the action in the plugin (i.e. the button in the toolbar)
        self.action = action

        self.active_layer = self.iface.activeLayer()

        self.current_selection = {}
        self.current_imt = None
        self.was_imt_switched = False
        self.current_abscissa = []
        self.color_names = [
            name for name in QColor.colorNames() if name != 'white']
        # shuffle(self.color_names)  # NOTE: this works in place, returning None
        self.line_styles = ["-", "--", "-.", ":"]

        # Marker for hovering
        self.vertex_marker = QgsVertexMarker(iface.mapCanvas())
        self.vertex_marker.hide()
        self.vertex_marker.setColor(QColor('cyan'))
        self.vertex_marker.setIconSize(6)
        self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self.vertex_marker.setPenWidth(6)

        self.iface.mapCanvas().setSelectionColor(QColor('magenta'))

        self.plot_figure = Figure()
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self)
        self.plot = self.plot_figure.add_subplot(111)
        self.legend = None

        self.plot_layout.addWidget(self.plot_canvas)
        self.toolbar_layout.insertWidget(0, self.plot_toolbar)

        self.plot_canvas.mpl_connect('pick_event', self.on_plot_pick)
        self.plot_canvas.mpl_connect('motion_notify_event', self.on_plot_hover)

    def draw(self):
        self.plot.clear()
        gids = self.current_selection.keys()
        count_selected = len(gids)
        if count_selected == 0:
            return
        for site, curve in self.current_selection.iteritems():
            feature = next(self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFid(site)))

            lon = feature.geometry().asPoint().x()
            lat = feature.geometry().asPoint().y()

            self.plot.plot(
                curve['abscissa'],
                curve['ordinates'],
                color=curve['color'],
                linestyle=curve['line_style'],
                label='%.4f, %.4f' % (lon, lat),
                gid=str(site),  # matplotlib needs a string when exporting svg
                picker=5  # 5 points tolerance
            )
        self.plot.set_xscale('log')
        self.plot.set_yscale('log')
        self.plot.set_xlabel('Intensity Measure Level')
        self.plot.set_ylabel('Probability of Exceedance')
        imt = self.imt_cbx.currentText()
        if count_selected == 0:
            title = ''
        elif count_selected == 1:
            title = 'Hazard Curve for %s' % imt
        else:
            title = 'Hazard Curves for %s' % imt
        self.plot.set_title(title)
        self.plot.grid()
        ylim_bottom, ylim_top = self.plot.get_ylim()
        self.plot.set_ylim(ylim_bottom, ylim_top * 1.5)
        xlim_left, xlim_right = self.plot.get_xlim()
        self.plot.set_xlim(xlim_left, xlim_right * 1.1)

        if count_selected <= 20:
            self.legend = self.plot.legend(
                loc='lower left', fancybox=True, shadow=True,
                fontsize='small')
        if hasattr(self.legend, 'get_lines'):
            for i, legend_line in enumerate(self.legend.get_lines()):
                legend_line.set_picker(5)  # 5 points tolerance
                legend_line.set_gid(str(gids[i]))  # matplotlib needs a string
                                                   # when exporting to svg
        self.plot_canvas.draw()

    def redraw(self, selected, deselected, _):
        for fid in deselected:
            try:
                del self.current_selection[fid]
            except KeyError:
                pass
        # try:
        self.current_abscissa = []
        for feature in self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFids(selected)):
            data_dic = json.loads(feature[self.current_imt])
            self.current_abscissa = data_dic['imls']
            # for a single intensity measure type, the imls are always
            # the same, so we can break the loop after the first feature
            break

        for i, feature in enumerate(self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFids(selected))):
            data_dic = json.loads(feature[self.current_imt])
            ordinates = data_dic['poes']
            if (self.was_imt_switched
                    or feature.id() not in self.current_selection):
                if self.bw_chk.isChecked():
                    line_styles_whole_cycles = i / len(self.line_styles)
                    # NOTE: 85 is approximately 256 / 3
                    r = g = b = format(
                        (85 * line_styles_whole_cycles) % 256, '02x')
                    color_hex = "#%s%s%s" % (r, g, b)
                    line_style = self.line_styles[i % len(self.line_styles)]
                else:
                    color_name = self.color_names[
                        feature.id() % len(self.color_names)]
                    color = QColor(color_name)
                    color_hex = color.darker(120).name()
                    line_style = "-"  # solid
                self.current_selection[feature.id()] = {
                    'abscissa': self.current_abscissa,
                    'ordinates': ordinates,
                    'color': color_hex,
                    'line_style': line_style,
                }
        self.was_imt_switched = False

        self.draw()
        # except (TypeError, ValueError):
        #     self.clear_plot()
        #     self.iface.messageBar().pushWarning(
        #         self.tr('Invalid IMT: %s') % self.current_imt,
        #         self.tr('The selected IMT seems to contain invalid data')
        #     )

    def layer_changed(self):
        self.current_selection = {}
        self.clear_plot()
        self.clear_imt_cbx()

        self.remove_connects()

        self.active_layer = self.iface.activeLayer()

        if (self.active_layer is not None
                and self.active_layer.type() == QgsMapLayer.VectorLayer
                and self.active_layer.geometryType() == QGis.Point):
            self.active_layer.selectionChanged.connect(self.redraw)
            self.setEnabled(True)

            reload_attrib_cbx(
                    self.imt_cbx, self.active_layer, False, TEXTUAL_FIELD_TYPES)

            if self.active_layer.selectedFeatureCount() > 0:
                self.set_selection(self.active_layer.selectedFeaturesIds())
        else:
            self.setDisabled(True)

    def remove_connects(self):
        try:
            self.active_layer.selectionChanged.disconnect(self.redraw)
        except (TypeError, AttributeError):
            pass

    def set_selection(self, selected):
        self.redraw(selected, [], None)

    def clear_plot(self):
        self.plot.clear()
        self.plot_canvas.draw()
        self.vertex_marker.hide()

    def clear_imt_cbx(self):
        self.imt_cbx.blockSignals(True)
        self.imt_cbx.clear()
        self.imt_cbx.blockSignals(False)

    def on_plot_hover(self, event):
        if not self.on_container_hover(event, self.plot):
            if hasattr(self.legend, 'get_lines'):
                self.on_container_hover(event, self.legend)

    def on_container_hover(self, event, container):
        for line in container.get_lines():
            if line.contains(event)[0]:
                fid = long(line.get_gid())  # matplotlib needs a string when
                                            # exporting to svg, so here we
                                            # must cast back to long
                feature = next(self.active_layer.getFeatures(
                        QgsFeatureRequest().setFilterFid(fid)))

                self.vertex_marker.setCenter(feature.geometry().asPoint())
                self.vertex_marker.show()
            else:
                self.vertex_marker.hide()
        return False

    @pyqtSlot(int)
    def on_imt_cbx_currentIndexChanged(self):
        self.current_imt = self.imt_cbx.currentText()
        self.was_imt_switched = True
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
                line = 'lon,lat,%s' % (
                    ','.join(map(str, list(self.current_abscissa))))
                csv_file.write(line + os.linesep)

                for site, curve in self.current_selection.iteritems():
                    poes = ','.join(map(str, curve['ordinates']))
                    feature = next(self.active_layer.getFeatures(
                            QgsFeatureRequest().setFilterFid(site)))

                    lon = feature.geometry().asPoint().x()
                    lat = feature.geometry().asPoint().y()
                    line = '%s,%s,%s' % (lon, lat, poes)
                    csv_file.write(line + os.linesep)

    @pyqtSlot()
    def on_bw_chk_clicked(self):
        self.layer_changed()

    def closeEvent(self, event):
        self.action.setChecked(False)
        event.accept()
