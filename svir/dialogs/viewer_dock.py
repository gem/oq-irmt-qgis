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
from collections import OrderedDict

from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.lines import Line2D


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

from svir.utilities.shared import TEXTUAL_FIELD_TYPES
from svir.utilities.utils import (get_ui_class,
                                  reload_attrib_cbx,
                                  log_msg,
                                  clear_widgets_from_layout,
                                  warn_scipy_missing,
                                  )
from svir.recovery_modeling.recovery_modeling import (
    RecoveryModeling, fill_fields_multiselect)
from svir.ui.list_multiselect_widget import ListMultiSelectWidget

from svir import IS_SCIPY_INSTALLED

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
        self.stats_multiselect = None

        # self.current_selection[None] is for recovery curves
        self.current_selection = {}  # rlz_or_stat -> feature_id -> curve
        self.current_imt = None
        self.current_loss_type = None
        self.was_imt_switched = False
        self.was_loss_type_switched = False
        self.was_poe_switched = False
        self.current_abscissa = []
        self.color_names = [
            name for name in QColor.colorNames() if name != 'white']
        self.line_styles = ["-", "--", "-.", ":"]
        self.markers = Line2D.filled_markers
        # # uncomment the following to get all available markers, including
        # # unfilled ones
        # self.markers = [code for code, name in Line2D.markers.items()
        #                 if name != 'nothing']

        # Marker for hovering
        self.vertex_marker = QgsVertexMarker(iface.mapCanvas())
        self.vertex_marker.hide()
        self.vertex_marker.setColor(QColor('cyan'))
        self.vertex_marker.setIconSize(6)
        self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self.vertex_marker.setPenWidth(6)

        self.iface.mapCanvas().setSelectionColor(QColor('magenta'))

        # TODO: re-add 'Loss Curves' when the corresponding npz is available
        self.output_types_names = OrderedDict([
            ('', ''),
            ('hcurves', 'Hazard Curves'),
            ('uhs', 'Uniform Hazard Spectra'),
            ('recovery_curves', 'Recovery Curves')])
        self.output_type_cbx.addItems(self.output_types_names.values())

        self.plot_figure = Figure()
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_canvas.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
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
        approach_explanation = (
            'Aggregate: building-level recovery model as a single process\n'
            'Disaggregate: Building-level recovery modelled using four'
            ' processes: inspection, assessment, mobilization and repair.')
        self.approach_lbl.setToolTip(approach_explanation)
        self.approach_cbx = QComboBox()
        self.approach_cbx.setToolTip(approach_explanation)
        self.approach_cbx.addItems(['Disaggregate', 'Aggregate'])
        self.approach_cbx.currentIndexChanged['QString'].connect(
            self.on_approach_changed)
        self.typeDepHLayout1.addWidget(self.approach_lbl)
        self.typeDepHLayout1.addWidget(self.approach_cbx)

    def create_n_simulations_spinbox(self):
        simulations_explanation = (
            'Number of damage realizations used in Monte Carlo Simulation')
        self.n_simulations_lbl = QLabel('Simulations per building')
        self.n_simulations_lbl.setToolTip(simulations_explanation)
        self.approach_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.n_simulations_sbx = QSpinBox()
        self.n_simulations_sbx.setToolTip(simulations_explanation)
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
        title = (
            'Select fields containing loss-based damage state probabilities')
        self.fields_multiselect = ListMultiSelectWidget(title=title)
        self.fields_multiselect.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.typeDepVLayout.addWidget(self.fields_multiselect)
        fill_fields_multiselect(
            self.fields_multiselect, self.iface.activeLayer())

    def create_stats_multiselect(self):
        title = 'Select statistics to plot'
        self.stats_multiselect = ListMultiSelectWidget(title=title)
        self.stats_multiselect.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.typeDepVLayout.addWidget(self.stats_multiselect)
        self.stats_multiselect.selection_changed.connect(
            self.refresh_feature_selection)

    def refresh_feature_selection(self):
        if not list(self.stats_multiselect.get_selected_items()):
            self.clear_plot()
            return
        # feature selection triggers the redrawing of plots
        layer = self.iface.activeLayer()
        selected_feats = layer.selectedFeaturesIds()
        layer.blockSignals(True)
        layer.removeSelection()
        layer.blockSignals(False)
        layer.selectByIds(selected_feats)

    def set_output_type_and_its_gui(self, new_output_type):
        if (self.output_type is not None
                and self.output_type == new_output_type):
            return

        # clear type dependent widgets
        # NOTE: typeDepVLayout contains typeDepHLayout1 and typeDepHLayout2,
        #       that will be cleared recursively
        clear_widgets_from_layout(self.typeDepVLayout)

        if new_output_type == 'hcurves':
            self.create_imt_selector()
            self.create_stats_multiselect()
        elif new_output_type == 'loss_curves':
            self.create_loss_type_selector()
        elif new_output_type == 'uhs':
            self.create_stats_multiselect()
        elif new_output_type == 'recovery_curves':
            if not IS_SCIPY_INSTALLED:
                warn_scipy_missing(self.iface.messageBar())
                self.output_type = None
                return
            self.create_approach_selector()
            self.create_n_simulations_spinbox()
            self.create_fields_multiselect()
            self.create_recalculate_curve_btn()
        # NOTE: the window's size is automatically adjusted even without
        # calling self.adjustSize(). If that method is called, it might cause
        # the window to shrink unexpectedly until the focus is moved somewhere
        # else.
        self.output_type = new_output_type

    def draw(self):
        self.plot.clear()
        gids = dict()
        if self.stats_multiselect is not None:
            selected_rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            selected_rlzs_or_stats = [None]
        selected_features_ids = [
            feature.id()
            for feature in self.iface.activeLayer().selectedFeatures()]
        for rlz_or_stat in selected_rlzs_or_stats:
            gids[rlz_or_stat] = selected_features_ids
        count_selected_feats = len(selected_features_ids)
        count_selected_stats = len(selected_rlzs_or_stats)
        count_lines = count_selected_feats * count_selected_stats
        if count_lines == 0:
            self.clear_plot()
            return

        for rlz_or_stat in selected_rlzs_or_stats:
            for i, (site, curve) in enumerate(
                    self.current_selection[rlz_or_stat].iteritems()):
                # NOTE: we associated the same cumulative curve to all the
                # selected points (ugly), and here we need to get only one
                if self.output_type == 'recovery_curves' and i > 0:
                    break
                feature = next(self.iface.activeLayer().getFeatures(
                    QgsFeatureRequest().setFilterFid(site)))

                lon = feature.geometry().asPoint().x()
                lat = feature.geometry().asPoint().y()

                self.plot.plot(
                    curve['abscissa'],
                    curve['ordinates'],
                    color=curve['color'],
                    linestyle=curve['line_style'],
                    marker=curve['marker'],
                    label='(%.3f, %.3f) %s' % (lon, lat, rlz_or_stat),
                    # matplotlib needs a string to export to svg
                    gid=str(site),
                    picker=5  # 5 points tolerance
                )
        if self.output_type == 'hcurves':
            self.plot.set_xscale('log')
            self.plot.set_yscale('log')
            self.plot.set_xlabel('Intensity measure level')
            self.plot.set_ylabel('Probability of exceedance')
            imt = self.imt_cbx.currentText()
            if count_lines == 0:
                title = ''
            elif count_lines == 1:
                title = 'Hazard curve for %s' % imt
            else:
                title = 'Hazard curves for %s' % imt
        elif self.output_type == 'loss_curves':
            self.plot.set_xscale('log')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Losses')
            self.plot.set_ylabel('Probability of exceedance')
            loss_type = self.loss_type_cbx.currentText()
            if count_lines == 0:
                title = ''
            elif count_lines == 1:
                title = 'Loss curve for %s' % loss_type
            else:
                title = 'Loss curves for %s' % loss_type
        elif self.output_type == 'uhs':
            self.plot.set_xscale('linear')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Period [s]')
            self.plot.set_ylabel('Spectral acceleration [g]')
            if count_lines == 0:
                title = ''
            elif count_lines == 1:
                title = 'Uniform hazard spectrum'
            else:
                title = 'Uniform hazard spectra'
        elif self.output_type == 'recovery_curves':
            self.plot.set_xscale('linear')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Time [days]')
            self.plot.set_ylabel('Normalized recovery level')
            self.plot.set_ylim((0.0, 1.2))
            if count_lines == 0:
                title = ''
            elif count_lines == 1:
                title = 'Building level recovery curve'
            else:
                title = 'Community level recovery curve'
        if self.output_type == 'hcurves':
            ylim_bottom, ylim_top = self.plot.get_ylim()
            self.plot.set_ylim(ylim_bottom, ylim_top * 1.5)
            xlim_left, xlim_right = self.plot.get_xlim()
            self.plot.set_xlim(xlim_left, xlim_right * 1.1)
        elif self.output_type == 'uhs':
            ylim_bottom, ylim_top = self.plot.get_ylim()
            ylim_bottom_margin = (ylim_top-ylim_bottom)/20.0
            self.plot.set_ylim(ylim_bottom-ylim_bottom_margin, ylim_top)

        investigation_time = self.iface.activeLayer().customProperty(
            'investigation_time', None)
        if investigation_time is not None:
            title += ' (%s years)' % investigation_time
        self.plot.set_title(title)
        self.plot.grid()
        if self.output_type != 'recovery_curves' and 1 <= count_lines <= 20:
            if self.output_type == 'uhs':
                location = 'upper right'
            else:
                location = 'lower left'
            self.legend = self.plot.legend(
                loc=location, fancybox=True, shadow=True,
                fontsize='small')
            for rlz_or_stat in selected_rlzs_or_stats:
                if hasattr(self.legend, 'get_lines'):
                    # We have blocks of legend lines, where each block refers
                    # to all selected stats for one of the selected points.
                    point_idx = 0
                    for i, legend_line in enumerate(self.legend.get_lines()):
                        legend_line.set_picker(5)  # 5 points tolerance
                        gid = gids[rlz_or_stat][point_idx]
                        legend_line.set_gid(str(gid))
                        # check if from the next iteration we will have to
                        # refer to the next selected point
                        if (i + 1) % len(selected_rlzs_or_stats) == 0:
                            point_idx += 1

        self.plot_canvas.draw()

    def redraw(self, selected, deselected, _):
        """
        Accepting parameters from QgsVectorLayer selectionChanged signal

        :param selected: newly selected feature ids
            NOTE - if you add features to the selection, the list contains all
            features, including those that were already selected before
        :param deselected: ids of all features which have previously been
            selected but are not any more
        :param _: ignored (in case this is set to true, the old selection
            was dismissed and the new selection corresponds to selected
        """
        if not self.output_type:
            return

        if self.stats_multiselect is not None:
            selected_rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            selected_rlzs_or_stats = None
        for fid in deselected:
            if hasattr(self, 'rlzs_or_stats'):
                for rlz_or_stat in self.rlzs_or_stats:
                    try:
                        # self.current_selection is a dictionary associating
                        # (for each selected rlz or stat) a curve to each
                        # feature id
                        del self.current_selection[rlz_or_stat][fid]
                    except KeyError:
                        pass
            else:
                try:
                    del self.current_selection[None][fid]
                except KeyError:
                    pass
        if self.output_type == 'recovery_curves':
            if len(selected) > 0:
                self.redraw_recovery_curve(selected)
            return
        if not selected_rlzs_or_stats or not self.current_selection:
            return
        self.current_abscissa = []
        for feature in self.iface.activeLayer().getFeatures(
                QgsFeatureRequest().setFilterFids(selected)):
            if self.output_type == 'hcurves':
                imt = self.imt_cbx.currentText()
                imls = [field_name.split('_')[2]
                        for field_name in self.field_names
                        if (field_name.split('_')[0]
                            == selected_rlzs_or_stats[0])
                        and field_name.split('_')[1] == imt]
                self.current_abscissa = imls
            elif self.output_type == 'loss_curves':
                err_msg = ("The selected layer does not contain loss"
                           " curves in the expected format.")
                try:
                    data_str = feature[self.current_loss_type]
                except KeyError:
                    log_msg(err_msg, level='C',
                            message_bar=self.iface.messageBar())
                    self.output_type_cbx.setCurrentIndex(-1)
                    return
                data_dic = json.loads(data_str)
                try:
                    self.current_abscissa = data_dic['losses']
                except KeyError:
                    log_msg(err_msg, level='C',
                            message_bar=self.iface.messageBar())
                    self.output_type_cbx.setCurrentIndex(-1)
                    return
                # for a single loss type, the losses are always
                # the same, so we can break the loop after the first feature
                break
            elif self.output_type == 'uhs':
                err_msg = ("The selected layer does not contain uniform"
                           " hazard spectra in the expected format.")
                self.field_names = [field.name() for field in feature.fields()]
                # reading from something like
                # [u'rlz-000_PGA', u'rlz-000_SA(0.025)', ...]
                unique_periods = [0.0]  # Use 0.0 for PGA
                # get the number between parenthesis
                try:
                    periods = [
                        float(name[name.find("(") + 1: name.find(")")])
                        for name in self.field_names
                        if "(" in name]
                    for period in periods:
                        if period not in unique_periods:
                            unique_periods.append(period)
                except ValueError:
                    log_msg(err_msg, level='C',
                            message_bar=self.iface.messageBar())
                    self.output_type_cbx.setCurrentIndex(-1)
                    return
                self.current_abscissa = unique_periods
                break
            else:
                raise NotImplementedError(self.output_type)

        for i, feature in enumerate(self.iface.activeLayer().getFeatures(
                QgsFeatureRequest().setFilterFids(selected))):
            if (self.was_imt_switched
                    or self.was_loss_type_switched
                    or (feature.id() not in
                        self.current_selection[selected_rlzs_or_stats[0]])
                    or self.output_type == 'uhs'):
                self.field_names = [
                    field.name()
                    for field in self.iface.activeLayer().fields()]
                ordinates = dict()
                marker = dict()
                line_style = dict()
                color_hex = dict()
                for rlz_or_stat_idx, rlz_or_stat in enumerate(
                        selected_rlzs_or_stats):
                    if self.output_type == 'hcurves':
                        imt = self.imt_cbx.currentText()
                        ordinates[rlz_or_stat] = [
                            feature[field_name]
                            for field_name in self.field_names
                            if field_name.split('_')[0] == rlz_or_stat
                            and field_name.split('_')[1] == imt]
                    elif self.output_type == 'uhs':
                        ordinates[rlz_or_stat] = [
                            feature[field_name]
                            for field_name in self.field_names
                            if field_name.split('_')[0] == rlz_or_stat]
                    marker[rlz_or_stat] = self.markers[
                        (i + rlz_or_stat_idx) % len(self.markers)]
                    if self.bw_chk.isChecked():
                        line_styles_whole_cycles = (
                            (i + rlz_or_stat_idx) / len(self.line_styles))
                        # NOTE: 85 is approximately 256 / 3
                        r = g = b = format(
                            (85 * line_styles_whole_cycles) % 256, '02x')
                        color_hex_str = "#%s%s%s" % (r, g, b)
                        color = QColor(color_hex_str)
                        color_hex[rlz_or_stat] = color.darker(120).name()
                        # here I am using i in order to cycle through all the
                        # line styles, regardless from the feature id
                        # (otherwise I might easily repeat styles, that are a
                        # small set of 4 items)
                        line_style[rlz_or_stat] = self.line_styles[
                            (i + rlz_or_stat_idx) % len(self.line_styles)]
                    else:
                        # here I am using the feature id in order to keep a
                        # matching between a curve and the corresponding point
                        # in the map
                        color_name = self.color_names[
                            (feature.id() + rlz_or_stat_idx)
                            % len(self.color_names)]
                        color = QColor(color_name)
                        color_hex[rlz_or_stat] = color.darker(120).name()
                        line_style[rlz_or_stat] = "-"  # solid
                    self.current_selection[rlz_or_stat][feature.id()] = {
                        'abscissa': self.current_abscissa,
                        'ordinates': ordinates[rlz_or_stat],
                        'color': color_hex[rlz_or_stat],
                        'line_style': line_style[rlz_or_stat],
                        'marker': marker[rlz_or_stat],
                    }
        self.was_imt_switched = False
        self.was_loss_type_switched = False
        self.draw()

    def redraw_recovery_curve(self, selected):
        features = list(self.iface.activeLayer().getFeatures(
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
        # NOTE: differently with respect to the other approaches, we are
        # associating only a single feature with the cumulative recovery curve.
        # It might be a little ugly, but otherwise it would be inefficient.
        if len(features) > 0:
            self.current_selection[None] = {}
            self.current_selection[None][features[0].id()] = {
                'abscissa': self.current_abscissa,
                'ordinates': recovery_function,
                'color': color_hex,
                'line_style': "-",  # solid
                'marker': "None",
            }
        self.draw()

    def layer_changed(self):
        self.clear_plot()
        if hasattr(self, 'self.imt_cbx'):
            self.clear_imt_cbx()
        if hasattr(self, 'loss_type_cbx'):
            self.clear_loss_type_cbx()

        self.remove_connects()

        if (self.iface.activeLayer() is not None
                and self.iface.activeLayer().type() == QgsMapLayer.VectorLayer
                and self.iface.activeLayer().geometryType() == QGis.Point):
            self.iface.activeLayer().selectionChanged.connect(self.redraw)

            if self.output_type in ['hcurves', 'uhs']:
                for rlz_or_stat in self.stats_multiselect.get_selected_items():
                    self.current_selection[rlz_or_stat] = {}
                self.stats_multiselect.set_selected_items([])
                self.stats_multiselect.set_unselected_items([])
                if self.output_type == 'hcurves':
                    # fields names are like 'max_PGA_0.005'
                    imts = sorted(set(
                        [field.name().split('_')[1]
                         for field in self.iface.activeLayer().fields()]))
                    self.imt_cbx.clear()
                    self.imt_cbx.addItems(imts)
                self.field_names = [
                    field.name()
                    for field in self.iface.activeLayer().fields()]
                self.rlzs_or_stats = sorted(set(
                    [field_name.split('_')[0]
                     for field_name in self.field_names]))
                # Select all stats by default
                self.stats_multiselect.add_selected_items(self.rlzs_or_stats)
                self.stats_multiselect.setEnabled(len(self.rlzs_or_stats) > 1)
            elif self.output_type == 'loss_curves':
                reload_attrib_cbx(self.loss_type_cbx,
                                  self.iface.activeLayer(),
                                  False,
                                  TEXTUAL_FIELD_TYPES)
            elif self.output_type == 'recovery_curves':
                fill_fields_multiselect(
                    self.fields_multiselect, self.iface.activeLayer())
            if self.iface.activeLayer().selectedFeatureCount() > 0:
                self.set_selection()

    def remove_connects(self):
        try:
            self.iface.activeLayer().selectionChanged.disconnect(self.redraw)
        except (TypeError, AttributeError):
            pass

    def set_selection(self):
        selected = self.iface.activeLayer().selectedFeaturesIds()
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
                feature = next(self.iface.activeLayer().getFeatures(
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
        self.set_selection()

    def on_loss_type_changed(self):
        self.current_loss_type = self.loss_type_cbx.currentText()
        self.was_loss_type_switched = True
        self.set_selection()

    def on_poe_changed(self):
        self.current_poe = self.poe_cbx.currentText()
        self.was_poe_switched = True
        self.set_selection()

    def on_approach_changed(self):
        self.current_approach = self.approach_cbx.currentText()
        self.set_selection()

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
        elif self.output_type == 'uhs':
            filename = QtGui.QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser('~/uniform_hazard_spectra.csv'),
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
            self.write_export_file(filename)

    def write_export_file(self, filename):
        with open(filename, 'w') as csv_file:
            if self.output_type == 'recovery_curves':
                # write header
                line = 'lon,lat,%s' % (
                    ','.join(map(str, self.current_abscissa)))
                csv_file.write(line + os.linesep)
                # NOTE: taking the first element, because they are all the
                # same
                feature = self.iface.activeLayer().selectedFeatures()[0]
                lon = feature.geometry().asPoint().x()
                lat = feature.geometry().asPoint().y()
                line = '%s,%s' % (lon, lat)
                values = self.current_selection[None].values()[0]
                if values:
                    line += "," + ",".join([
                        str(value) for value in values['ordinates']])
                csv_file.write(line + os.linesep)
            elif self.output_type in ['hcurves', 'uhs']:
                selected_rlzs_or_stats = list(
                    self.stats_multiselect.get_selected_items())
                if self.output_type == 'hcurves':
                    selected_imt = self.imt_cbx.currentText()

                # write header
                field_names = []
                for field in self.iface.activeLayer().fields():
                    if self.output_type == 'hcurves':
                        # field names are like 'mean_PGA_0.005'
                        rlz_or_stat, imt, iml = field.name().split('_')
                        if imt != selected_imt:
                            continue
                    else:  # 'uhs'
                        # field names are like 'mean_PGA'
                        rlz_or_stat, _ = field.name().split('_')
                    if rlz_or_stat not in selected_rlzs_or_stats:
                        continue
                    field_names.append(field.name())
                header = 'lon,lat,%s' % ','.join(field_names)
                csv_file.write(header + os.linesep)

                # write selected data
                for feature in self.iface.activeLayer().getFeatures():
                    values = [feature.attribute(field_name)
                              for field_name in field_names]
                    lon = feature.geometry().asPoint().x()
                    lat = feature.geometry().asPoint().y()
                    line = '%s,%s' % (lon, lat)
                    if values:
                        line += "," + ",".join([
                            str(value) for value in values])
                    csv_file.write(line + os.linesep)
            else:
                raise NotImplementedError(self.output_type)
        msg = 'Data exported to %s' % filename
        log_msg(msg, level='I', message_bar=self.iface.messageBar())

    @pyqtSlot()
    def on_bw_chk_clicked(self):
        self.layer_changed()

    @pyqtSlot(int)
    def on_output_type_cbx_currentIndexChanged(self):
        otname = self.output_type_cbx.currentText()
        for output_type, output_type_name in self.output_types_names.items():
            if output_type_name == otname:
                self.set_output_type_and_its_gui(output_type)
                self.layer_changed()
                return
        output_type = None
        self.set_output_type_and_its_gui(output_type)
        self.layer_changed()

    def closeEvent(self, event):
        self.action.setChecked(False)
        event.accept()

    def change_output_type(self, output_type):
        if output_type not in self.output_types_names:
            output_type = ''
        # get the index of the item that has the given string
        # and set the combobox to that item
        index = self.output_type_cbx.findText(
            self.output_types_names[output_type])
        if index != -1:
            self.output_type_cbx.setCurrentIndex(index)
        layer = self.iface.activeLayer()
        if layer:
            layer_type = layer.customProperty('output_type')
            if layer_type:
                self.output_type_cbx.setDisabled(True)
                return
        self.output_type_cbx.setEnabled(True)
