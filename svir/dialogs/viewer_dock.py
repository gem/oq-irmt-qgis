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


from PyQt4.QtCore import pyqtSlot, QSettings
from PyQt4.QtGui import (QColor,
                         QLabel,
                         QComboBox,
                         QSizePolicy,
                         QSpinBox,
                         QPushButton,
                         )
from qgis.gui import QgsVertexMarker
from qgis.core import QGis, QgsMapLayer, QgsFeatureRequest

from svir.utilities.shared import NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES
from svir.utilities.utils import get_ui_class, reload_attrib_cbx
from svir.recovery_modeling.recovery_modeling import (
    RecoveryModeling, fill_fields_multiselect)
from svir.ui.list_multiselect_widget import ListMultiSelectWidget

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

        self.output_type = None
        self.loss_type_lbl = None
        self.loss_type_cbx = None
        self.imt_lbl = None
        self.imt_cbx = None
        self.poe_lbl = None
        self.poe_cbx = None
        self.approach_lbl = None
        self.approach_cbx = None
        self.n_simulations_lbl = None
        self.n_simulations_sbx = None
        self.warning_n_simulations_lbl = None
        self.recalculate_curve_btn = None
        self.fields_multiselect = None

        self.current_selection = {}
        self.current_imt = None
        self.current_loss_type = None
        self.was_imt_switched = False
        self.was_loss_type_switched = False
        self.was_poe_switched = False
        self.current_abscissa = []
        self.color_names = [
            name for name in QColor.colorNames() if name != 'white']
        self.line_styles = ["-", "--", "-.", ":"]

        # Marker for hovering
        self.vertex_marker = QgsVertexMarker(iface.mapCanvas())
        self.vertex_marker.hide()
        self.vertex_marker.setColor(QColor('cyan'))
        self.vertex_marker.setIconSize(6)
        self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self.vertex_marker.setPenWidth(6)

        self.iface.mapCanvas().setSelectionColor(QColor('magenta'))

        self.output_type_cbx.addItems(
            ['', 'Hazard Curves', 'Uniform Hazard Spectra', 'Loss Curves',
             'Recovery Curves'])

        self.plot_figure = Figure()
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self)
        self.plot = self.plot_figure.add_subplot(111)
        self.legend = None

        self.plot_layout.addWidget(self.plot_canvas)
        self.toolbar_layout.insertWidget(0, self.plot_toolbar)

        self.plot_canvas.mpl_connect('motion_notify_event', self.on_plot_hover)

    def create_loss_type_selector(self):
        self.loss_type_lbl = QLabel('Loss Type')
        self.loss_type_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.typeDepHLayout1.addWidget(self.loss_type_lbl)
        self.typeDepHLayout1.addWidget(self.loss_type_cbx)

    def create_imt_selector(self):
        self.imt_lbl = QLabel('Intensity Measure Type')
        self.imt_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.imt_cbx = QComboBox()
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.typeDepHLayout1.addWidget(self.imt_lbl)
        self.typeDepHLayout1.addWidget(self.imt_cbx)

    def create_poe_selector(self):
        self.poe_lbl = QLabel('Probability of Exceedance')
        self.poe_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.poe_cbx = QComboBox()
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        self.typeDepHLayout1.addWidget(self.poe_lbl)
        self.typeDepHLayout1.addWidget(self.poe_cbx)

    def create_approach_selector(self):
        self.approach_lbl = QLabel('Recovery time approach')
        self.approach_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.approach_cbx = QComboBox()
        self.approach_cbx.addItems(['Disaggregate', 'Aggregate'])
        self.approach_cbx.currentIndexChanged['QString'].connect(
            self.on_approach_changed)
        self.typeDepHLayout1.addWidget(self.approach_lbl)
        self.typeDepHLayout1.addWidget(self.approach_cbx)

    def create_n_simulations_spinbox(self):
        self.n_simulations_lbl = QLabel('Simulations per building')
        self.approach_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.n_simulations_sbx = QSpinBox()
        self.n_simulations_sbx.setRange(1, 500)
        n_simulations = int(
            QSettings().value('irmt/n_simulations_per_building', 1))
        self.n_simulations_sbx.setValue(n_simulations)
        self.n_simulations_sbx.valueChanged['int'].connect(
            self.on_n_simulations_changed)
        self.typeDepHLayout2.addWidget(self.n_simulations_lbl)
        self.typeDepHLayout2.addWidget(self.n_simulations_sbx)
        self.warning_n_simulations_lbl = QLabel(
            'Warning: increasing the number of simulations per building,'
            ' the application might become irresponsive or run out of memory')
        self.warning_n_simulations_lbl.setWordWrap(True)
        self.typeDepVLayout.addWidget(self.warning_n_simulations_lbl)

    def create_recalculate_curve_btn(self):
        self.recalculate_curve_btn = QPushButton('Calculate recovery curve')
        self.typeDepVLayout.addWidget(self.recalculate_curve_btn)
        self.recalculate_curve_btn.clicked.connect(
            self.on_recalculate_curve_btn_clicked)

    def create_fields_multiselect(self):
        self.fields_multiselect = ListMultiSelectWidget(
            title='Select fields containing damage state probabilities')
        self.typeDepVLayout.addWidget(self.fields_multiselect)
        fill_fields_multiselect(
            self.fields_multiselect, self.iface.activeLayer())

    def remove_widgets_from_layout(self, widgets, layout):
        for widget in widgets:
            if widget is not None:
                widget.hide()
                layout.removeWidget(widget)

    def set_output_type_and_its_gui(self, new_output_type):
        if (self.output_type is not None
                and self.output_type == new_output_type):
            return
        self.clear_type_dependent_widgets()
        if new_output_type == 'hcurves':
            self.create_imt_selector()
        elif new_output_type == 'loss_curves':
            self.create_loss_type_selector()
        elif new_output_type == 'uhs':
            # Currently we are creating a layer for each poe
            # self.create_poe_selector()
            pass
        elif new_output_type == 'recovery_curves':
            self.create_approach_selector()
            self.create_n_simulations_spinbox()
            self.create_fields_multiselect()
            self.create_recalculate_curve_btn()
        self.adjustSize()
        self.output_type = new_output_type

    def clear_type_dependent_widgets(self):
        self.remove_widgets_from_layout(
            [self.loss_type_lbl, self.loss_type_cbx,
                self.imt_lbl, self.imt_cbx,
                self.poe_lbl, self.poe_cbx,
                self.approach_lbl, self.approach_cbx],
            self.typeDepHLayout1)
        self.remove_widgets_from_layout(
            [self.n_simulations_lbl, self.n_simulations_sbx],
            self.typeDepHLayout2)
        self.remove_widgets_from_layout(
            [self.warning_n_simulations_lbl,
             self.fields_multiselect,
             self.recalculate_curve_btn],
            self.typeDepVLayout)
        self.adjustSize()

    def draw(self):
        marker = "None"
        if self.output_type != 'recovery_curves':
            marker = '.'
        self.plot.clear()
        gids = self.current_selection.keys()
        count_selected = len(gids)
        if count_selected == 0:
            return
        i = 0
        for site, curve in self.current_selection.iteritems():
            # FIXME: we associated the same cumulative curve to all the
            # selected points (ugly), and here we need to get only one
            if self.output_type == 'recovery_curves' and i > 1:
                break
            feature = next(self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFid(site)))

            lon = feature.geometry().asPoint().x()
            lat = feature.geometry().asPoint().y()

            self.plot.plot(
                curve['abscissa'],
                curve['ordinates'],
                color=curve['color'],
                linestyle=curve['line_style'],
                marker=marker,
                label='%.4f, %.4f' % (lon, lat),
                gid=str(site),  # matplotlib needs a string when exporting svg
                picker=5  # 5 points tolerance
            )
            i += 1
        if self.output_type == 'hcurves':
            self.plot.set_xscale('log')
            self.plot.set_yscale('log')
            self.plot.set_xlabel('Intensity measure level')
            self.plot.set_ylabel('Probability of exceedance')
            imt = self.imt_cbx.currentText()
            if count_selected == 0:
                title = ''
            elif count_selected == 1:
                title = 'Hazard Curve for %s' % imt
            else:
                title = 'Hazard Curves for %s' % imt
        elif self.output_type == 'loss_curves':
            self.plot.set_xscale('log')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Losses')
            self.plot.set_ylabel('Probability of exceedance')
            loss_type = self.loss_type_cbx.currentText()
            if count_selected == 0:
                title = ''
            elif count_selected == 1:
                title = 'Loss Curve for %s' % loss_type
            else:
                title = 'Loss Curves for %s' % loss_type
        elif self.output_type == 'uhs':
            self.plot.set_xscale('linear')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Period [s]')
            self.plot.set_ylabel('Spectral acceleration [g]')
            if count_selected == 0:
                title = ''
            elif count_selected == 1:
                title = 'Uniform hazard spectrum'
            else:
                title = 'Uniform hazard spectra'
        elif self.output_type == 'recovery_curves':
            self.plot.set_xscale('linear')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Time [days]')
            self.plot.set_ylabel('Normalized recovery level')
            self.plot.set_ylim((0.0, 1.2))
            if count_selected == 0:
                title = ''
            elif count_selected == 1:
                title = 'Building level recovery curve'
            else:
                title = 'Community level recovery curve'
        self.plot.set_title(title)
        self.plot.grid()
        if self.output_type == 'hcurves':
            ylim_bottom, ylim_top = self.plot.get_ylim()
            self.plot.set_ylim(ylim_bottom, ylim_top * 1.5)
            xlim_left, xlim_right = self.plot.get_xlim()
            self.plot.set_xlim(xlim_left, xlim_right * 1.1)

        if self.output_type != 'recovery_curves' and count_selected <= 20:
            if self.output_type == 'uhs':
                location = 'upper right'
            else:
                location = 'lower left'
            self.legend = self.plot.legend(
                loc=location, fancybox=True, shadow=True,
                fontsize='small')
        if hasattr(self.legend, 'get_lines'):
            for i, legend_line in enumerate(self.legend.get_lines()):
                legend_line.set_picker(5)  # 5 points tolerance
                # matplotlib needs a string when exporting to svg
                legend_line.set_gid(str(gids[i]))
        self.plot_canvas.draw()

    def redraw(self, selected, deselected, _):
        if self.output_type is None:
            return
        for fid in deselected:
            try:
                del self.current_selection[fid]
            except KeyError:
                pass
        if self.output_type == 'recovery_curves':
            if len(selected) > 0:
                self.redraw_recovery_curve(selected)
            return
        self.current_abscissa = []
        for feature in self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFids(selected)):
            if self.output_type == 'hcurves':
                data_dic = json.loads(feature[self.current_imt])
                self.current_abscissa = data_dic['imls']
                # for a single intensity measure type, the imls are always
                # the same, so we can break the loop after the first feature
                break
            elif self.output_type == 'loss_curves':
                data_dic = json.loads(feature[self.current_loss_type])
                self.current_abscissa = data_dic['losses']
                # for a single loss type, the losses are always
                # the same, so we can break the loop after the first feature
                break
            elif self.output_type == 'uhs':
                field_names = [field.name() for field in feature.fields()]
                # reading from something like
                # [u'PGA', u'SA(0.025)', u'SA(0.05)', ...]
                periods = [0.0]  # Use 0.0 for PGA
                # get the number between parenthesis
                periods.extend([float(name[name.find("(") + 1: name.find(")")])
                               for name in field_names[1:]])
                self.current_abscissa = periods
                break

        for i, feature in enumerate(self.active_layer.getFeatures(
                QgsFeatureRequest().setFilterFids(selected))):
            if self.output_type == 'hcurves':
                data_dic = json.loads(feature[self.current_imt])
            elif self.output_type == 'loss_curves':
                data_dic = json.loads(feature[self.current_loss_type])
            if self.output_type in ['hcurves', 'loss_curves']:
                ordinates = data_dic['poes']
            elif self.output_type == 'uhs':
                ordinates = [value for value in feature]
            if (self.was_imt_switched
                    or self.was_loss_type_switched
                    or feature.id() not in self.current_selection
                    or self.output_type == 'uhs'):
                if self.bw_chk.isChecked():
                    line_styles_whole_cycles = i / len(self.line_styles)
                    # NOTE: 85 is approximately 256 / 3
                    r = g = b = format(
                        (85 * line_styles_whole_cycles) % 256, '02x')
                    color_hex = "#%s%s%s" % (r, g, b)
                    # here I am using i in order to cycle through all the
                    # line styles, regardless from the feature id
                    # (otherwise I might easily repeat styles, that are a
                    # small set of 4 items)
                    line_style = self.line_styles[
                        i % len(self.line_styles)]
                else:
                    # here I am using the feature id in order to keep a
                    # matching between a curve and the corresponding point
                    # in the map
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
        self.was_loss_type_switched = False

        self.draw()

    def redraw_recovery_curve(self, selected):
        features = list(self.active_layer.getFeatures(
            QgsFeatureRequest().setFilterFids(selected)))
        approach = self.approach_cbx.currentText()
        recovery = RecoveryModeling(features, approach, self.iface)
        integrate_svi = False
        probs_field_names = list(self.fields_multiselect.get_selected_items())
        zonal_dmg_by_asset_probs, zonal_asset_refs = \
            recovery.collect_zonal_data(probs_field_names, integrate_svi)
        n_simulations = self.n_simulations_sbx.value()
        recovery_function = \
            recovery.generate_community_level_recovery_curve(
                'ALL', zonal_dmg_by_asset_probs, zonal_asset_refs,
                n_simulations=n_simulations)
        self.current_abscissa = range(len(recovery_function))
        color = QColor('black')
        color_hex = color.name()
        line_style = "-"  # solid
        # FIXME: only for the sake of consistency with other approaches, we are
        # associating all features with the same curve, instead of picking one
        # single feature and a single curve. This is inefficient.
        for feature in features:
            self.current_selection[feature.id()] = {
                'abscissa': self.current_abscissa,
                'ordinates': recovery_function,
                'color': color_hex,
                'line_style': line_style,
            }
        self.draw()

    def layer_changed(self):
        self.current_selection = {}
        self.clear_plot()
        if hasattr(self, 'self.imt_cbx'):
            self.clear_imt_cbx()
        if hasattr(self, 'loss_type_cbx'):
            self.clear_loss_type_cbx()

        self.remove_connects()

        self.active_layer = self.iface.activeLayer()

        if (self.active_layer is not None
                and self.active_layer.type() == QgsMapLayer.VectorLayer
                and self.active_layer.geometryType() == QGis.Point):
            self.active_layer.selectionChanged.connect(self.redraw)
            self.setEnabled(True)

            if self.output_type == 'hcurves':
                reload_attrib_cbx(self.imt_cbx,
                                  self.active_layer,
                                  False,
                                  TEXTUAL_FIELD_TYPES)
            elif self.output_type == 'loss_curves':
                reload_attrib_cbx(self.loss_type_cbx,
                                  self.active_layer,
                                  False,
                                  TEXTUAL_FIELD_TYPES)
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
        if hasattr(self, 'plot'):
            self.plot.clear()
            self.plot_canvas.draw()
            self.vertex_marker.hide()

    def clear_imt_cbx(self):
        if self.imt_cbx is not None:
            self.imt_cbx.blockSignals(True)
            self.imt_cbx.clear()
            self.imt_cbx.blockSignals(False)

    def clear_loss_type_cbx(self):
        if self.loss_type_cbx is not None:
            self.loss_type_cbx.blockSignals(True)
            self.loss_type_cbx.clear()
            self.loss_type_cbx.blockSignals(False)

    def on_plot_hover(self, event):
        if not self.on_container_hover(event, self.plot):
            if hasattr(self.legend, 'get_lines'):
                self.on_container_hover(event, self.legend)

    def on_container_hover(self, event, container):
        for line in container.get_lines():
            if line.contains(event)[0]:
                # matplotlib needs a string when exporting to svg, so here we
                # must cast back to long
                fid = long(line.get_gid())
                feature = next(self.active_layer.getFeatures(
                        QgsFeatureRequest().setFilterFid(fid)))

                self.vertex_marker.setCenter(feature.geometry().asPoint())
                self.vertex_marker.show()
                return True
            else:
                self.vertex_marker.hide()
        return False

    def on_imt_changed(self):
        self.current_imt = self.imt_cbx.currentText()
        self.was_imt_switched = True
        self.set_selection(self.current_selection.keys())

    def on_loss_type_changed(self):
        self.current_loss_type = self.loss_type_cbx.currentText()
        self.was_loss_type_switched = True
        self.set_selection(self.current_selection.keys())

    def on_poe_changed(self):
        self.current_poe = self.poe_cbx.currentText()
        self.was_poe_switched = True
        self.set_selection(self.current_selection.keys())

    def on_approach_changed(self):
        self.current_approach = self.approach_cbx.currentText()
        self.set_selection(self.current_selection.keys())

    def on_recalculate_curve_btn_clicked(self):
        self.layer_changed()

    def on_n_simulations_changed(self):
        QSettings().setValue('irmt/n_simulations_per_building',
                             self.n_simulations_sbx.value())

    @pyqtSlot()
    def on_export_data_button_clicked(self):
        if self.output_type == 'hcurves':
            filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/hazard_curves_%s.csv' % self.current_imt),
                '*.csv')
        elif self.output_type == 'loss_curves':
            filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/loss_curves_%s.csv' % self.current_loss_type),
                '*.csv')
        elif self.output_type == 'recovery_curves':
            filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/recovery_curves_%s.csv' %
                    self.approach_cbx.currentText()),
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

                if self.output_type == 'recovery_curves':
                    # FIXME: taking the first element, because they are all the
                    # same
                    curve = self.current_selection.values()[0]
                    csv_file.write(str(curve['ordinates']))
                else:
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

    @pyqtSlot(int)
    def on_output_type_cbx_currentIndexChanged(self):
        otype = self.output_type_cbx.currentText()
        if otype == 'Hazard Curves':
            output_type = 'hcurves'
        elif otype == 'Loss Curves':
            output_type = 'loss_curves'
        elif otype == 'Uniform Hazard Spectra':
            output_type = 'uhs'
        elif otype == 'Recovery Curves':
            output_type = 'recovery_curves'
        else:
            output_type = None
        self.set_output_type_and_its_gui(output_type)
        self.layer_changed()

    def closeEvent(self, event):
        self.action.setChecked(False)
        event.accept()

    def change_output_type(self, output_type):
        # get the index of the item that has the given string
        # and set the combobox to that item
        index = self.output_type_cbx.findText(output_type)
        if index != -1:
            self.output_type_cbx.setCurrentIndex(index)
