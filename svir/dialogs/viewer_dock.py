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

import sys
import traceback
import os
import csv
import numpy
import urllib
from datetime import datetime
from collections import OrderedDict

from qgis.PyQt.QtCore import pyqtSlot, QSettings  # , Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
                                 QLabel,
                                 QComboBox,
                                 QSizePolicy,
                                 QSpinBox,
                                 QCheckBox,
                                 QDockWidget,
                                 QFileDialog,
                                 QAbstractItemView,
                                 QTableWidget,
                                 QTableWidgetItem,
                                 )
from qgis.gui import QgsVertexMarker
from qgis.core import QgsMapLayer, QgsFeatureRequest, QgsWkbTypes

from svir.utilities.shared import (
                                   OQ_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_VIEW_TYPES,
                                   )
from svir.utilities.utils import (get_ui_class,
                                  log_msg,
                                  clear_widgets_from_layout,
                                  extract_npz,
                                  get_loss_types,
                                  get_irmt_version,
                                  WaitCursorManager,
                                  )
from svir.ui.multi_select_combo_box import MultiSelectComboBox

from svir import IS_MATPLOTLIB_INSTALLED

if IS_MATPLOTLIB_INSTALLED:
    import matplotlib
    matplotlib.use('Qt5Agg')  # NOQA
    from matplotlib.backends.qt_compat import QtCore, QtWidgets  # NOQA
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D


FORM_CLASS = get_ui_class('ui_viewer_dock.ui')


class ViewerDock(QDockWidget, FORM_CLASS):

    def __init__(self, iface, action):
        """Constructor for the viewer dock.

        :param iface: A QgisAppInterface instance we use to access QGIS via.
        :param action: needed to uncheck the toolbar button on close
        .. note:: We use the multiple inheritance approach from Qt4 so that
            for elements are directly accessible in the form context and we can
            use autoconnect to set up slots. See article below:
            http://doc.qt.nokia.com/4.7-snapshot/designer-using-a-ui-file.html
        """
        QDockWidget.__init__(self, None)
        self.setupUi(self)

        if not IS_MATPLOTLIB_INSTALLED:
            # the warning should be called by irmt.py
            return

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
        self.rlzs_multiselect = None

        self.type_dep_widget_names = []

        self.calc_id = None

        self.engine_version = None

        # self.current_selection[None] was for recovery curves
        self.current_selection = {}  # rlz_or_stat -> feature_id -> curve
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

        self.output_types_names = OrderedDict([
            ('', ''),
            ('hcurves', 'Hazard Curves'),
            ('uhs', 'Uniform Hazard Spectra'),
            ('aggcurves', 'Aggregate Risk Curves'),
            ('aggcurves-stats', 'Aggregate Risk Curves Statistics'),
            ('damages-rlzs_aggr', 'Asset Risk Distributions'),
            ('damages-stats_aggr', 'Asset Risk Statistics'),
            ('avg_losses-rlzs_aggr', 'Average Asset Losses'),
            ('avg_losses-stats_aggr', 'Average Asset Losses Statistics'),
        ])

        if QSettings().value('/irmt/experimental_enabled', False, type=bool):
            pass  # it was used for recovery_curves and it might be useful
        self.output_type_cbx.addItems(list(self.output_types_names.values()))

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

        self.table = QTableWidget()
        self.table.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_layout.addWidget(self.table)
        self.table.hide()

    def create_annot(self):
        self.annot = self.plot.annotate(
            "", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

    def update_annot(self, ind):
        x, y = self.line.get_data()
        xlab = x[ind["ind"][0]]
        ylab = y[ind["ind"][0]]
        self.annot.xy = (xlab, ylab)
        self.annot.set_text("%.0f days, %.0f%%" % (xlab, ylab))
        self.annot.get_bbox_patch().set_alpha(0.4)

    def create_loss_type_selector(self):
        self.loss_type_lbl = QLabel('Loss Category')
        self.loss_type_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.add_widget_to_type_dep_layout(
            self.loss_type_lbl, 'loss_type_lbl', self.typeDepHLayout2)
        self.add_widget_to_type_dep_layout(
            self.loss_type_cbx, 'loss_type_cbx', self.typeDepHLayout2)

    def create_tag_name_selector(self, values=None, preselect_first=True):
        self.multivalue_tag_lbl = QLabel('Multivalue tag')
        self.multivalue_tag_cbx = QComboBox(self)
        self.add_widget_to_type_dep_layout(
            self.multivalue_tag_lbl, "multivalue_tag_lbl", self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            self.multivalue_tag_cbx, "multivalue_tag_cbx", self.typeDepVLayout)
        if values:
            self.multivalue_tag_cbx.addItems(self.tags.keys())
        self.multivalue_tag_cbx.currentIndexChanged.connect(
            self.on_multivalue_tag_name_changed)
        if preselect_first:
            self.multivalue_tag_cbx.setCurrentIndex(0)

    def create_tag_values_selector(
            self, tag_name, tag_values=None, monovalue=False,
            preselect_first=False):
        setattr(self, "%s_lbl" % tag_name, QLabel(tag_name))
        setattr(self, "%s_values_multiselect" % tag_name,
                MultiSelectComboBox(self, mono=monovalue))
        lbl = getattr(self, "%s_lbl" % tag_name)
        cbx = getattr(self, "%s_values_multiselect" % tag_name)
        if tag_values is not None:
            cbx.addItems(tag_values)
        self.add_widget_to_type_dep_layout(
            lbl, "%s_lbl" % tag_name, self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            cbx, "%s_values_multiselect" % tag_name, self.typeDepVLayout)
        if monovalue:
            cbx.currentIndexChanged.connect(
                lambda idx: self.update_selected_tag_values(tag_name))
            if preselect_first:
                cbx.setCurrentIndex(0)
        else:
            cbx.selection_changed.connect(
                lambda: self.update_selected_tag_values(tag_name))
            if preselect_first:
                cbx.set_idxs_selection([0], checked=True)

    def create_imt_selector(self):
        self.imt_lbl = QLabel('Intensity Measure Type')
        self.imt_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.imt_cbx = QComboBox()
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.add_widget_to_type_dep_layout(
            self.imt_lbl, 'imt_lbl', self.typeDepHLayout1)
        self.add_widget_to_type_dep_layout(
            self.imt_cbx, 'imt_cbx', self.typeDepHLayout1)

    def create_ep_selector(self):
        self.ep_lbl = QLabel('Exceedance Probability')
        self.ep_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.ep_cbx = QComboBox()
        self.ep_cbx.currentIndexChanged['QString'].connect(
            self.on_ep_changed)
        self.add_widget_to_type_dep_layout(
            self.ep_lbl, "ep_lbl", self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            self.ep_cbx, "ep_cbx", self.typeDepVLayout)

    def create_abs_rel_selector(self):
        self.abs_rel_lbl = QLabel('Absolute or relative')
        self.abs_rel_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.abs_rel_cbx = QComboBox()
        self.abs_rel_cbx.addItems(['Absolute', 'Relative'])
        self.abs_rel_cbx.currentIndexChanged['QString'].connect(
            self.on_abs_rel_changed)
        self.add_widget_to_type_dep_layout(
            self.abs_rel_lbl, 'abs_rel_lbl', self.typeDepHLayout1)
        self.add_widget_to_type_dep_layout(
            self.abs_rel_cbx, 'abs_rel_cbx', self.typeDepHLayout1)

    def create_poe_selector(self):
        self.poe_lbl = QLabel('Probability of Exceedance')
        self.poe_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.poe_cbx = QComboBox()
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        self.add_widget_to_type_dep_layout(
            self.poe_lbl, 'poe_lbl', self.typeDepHLayout1)
        self.add_widget_to_type_dep_layout(
            self.poe_cbx, 'poe_cbx', self.typeDepHLayout1)

    def create_rlz_or_stat_selector(self):
        self.rlz_or_stat_lbl = QLabel('Realization or statistic')
        self.rlz_or_stat_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.rlz_or_stat_cbx = QComboBox()
        self.rlz_or_stat_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_or_stat_changed)
        self.add_widget_to_type_dep_layout(
            self.rlz_or_stat_lbl, 'rlz_or_stat_lbl', self.typeDepHLayout1)
        self.add_widget_to_type_dep_layout(
            self.rlz_or_stat_cbx, 'rlz_or_stat_cbx', self.typeDepHLayout1)

    def create_exclude_no_dmg_ckb(self):
        self.exclude_no_dmg_ckb = QCheckBox('Exclude "no damage"')
        self.exclude_no_dmg_ckb.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.exclude_no_dmg_ckb.setChecked(True)
        self.exclude_no_dmg_ckb.stateChanged[int].connect(
            self.on_exclude_no_dmg_ckb_state_changed)
        self.plot_layout.insertWidget(0, self.exclude_no_dmg_ckb)
        # NOTE: this widget has to be inserted and handled differently with
        # respect to the other type dependent widgets
        self.type_dep_widget_names.append('exclude_no_dmg_ckb')

    def add_widget_to_type_dep_layout(self, widget, widget_name, layout):
        layout.addWidget(widget)
        self.type_dep_widget_names.append(widget_name)

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
        self.add_widget_to_type_dep_layout(
            self.n_simulations_lbl, 'n_simulations_lbl', self.typeDepHLayout2)
        self.add_widget_to_type_dep_layout(
            self.n_simulations_sbx, 'n_simulations_sbx', self.typeDepHLayout2)
        self.warning_n_simulations_lbl = QLabel(
            'Warning: increasing the number of simulations per building,'
            ' the application might become irresponsive or run out of memory')
        self.warning_n_simulations_lbl.setWordWrap(True)
        self.add_widget_to_type_dep_layout(
            self.warning_n_simulations_lbl, 'warning_n_simulations_lbl',
            self.typeDepVLayout)

    def create_select_assets_at_same_site_chk(self):
        self.select_assets_at_same_site_chk = QCheckBox(
            'Select all assets at the same site')
        self.select_assets_at_same_site_chk.setChecked(True)
        self.add_widget_to_type_dep_layout(
            self.select_assets_at_same_site_chk,
            'select_assets_at_same_site_chk', self.typeDepVLayout)

    def create_recalculate_on_the_fly_chk(self):
        self.recalculate_on_the_fly_chk = QCheckBox('Recalculate on-the-fly')
        self.recalculate_on_the_fly_chk.setChecked(True)
        self.add_widget_to_type_dep_layout(
            self.recalculate_on_the_fly_chk, 'recalculate_on_the_fly_chk',
            self.typeDepVLayout)
        self.recalculate_on_the_fly_chk.toggled.connect(
            self.on_recalculate_on_the_fly_chk_toggled)

    def create_rlzs_multiselect(self):
        self.rlzs_lbl = QLabel('Realizations')
        self.rlzs_multiselect = MultiSelectComboBox(self)
        self.add_widget_to_type_dep_layout(
            self.rlzs_lbl, 'rlzs_lbl', self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            self.rlzs_multiselect, 'rlzs_multiselect', self.typeDepVLayout)

    def create_stats_multiselect(self):
        self.stats_lbl = QLabel('Statistics')
        self.stats_multiselect = MultiSelectComboBox(self)
        self.add_widget_to_type_dep_layout(
            self.stats_lbl, 'stats_lbl', self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            self.stats_multiselect, 'stats_multiselect', self.typeDepVLayout)

    def create_tag_names_multiselect(self, mononame=False, monovalue=False):
        self.tag_names_lbl = QLabel('Tag names')
        self.tag_names_multiselect = MultiSelectComboBox(self, mono=mononame)
        self.add_widget_to_type_dep_layout(
            self.tag_names_lbl, 'tag_names_lbl', self.typeDepVLayout)
        self.add_widget_to_type_dep_layout(
            self.tag_names_multiselect, 'tag_names_multiselect',
            self.typeDepVLayout)
        self.tag_names_multiselect.item_was_clicked.connect(
            lambda tag_name, tag_name_is_checked:
            self.toggle_tag_values_multiselect(
                tag_name, tag_name_is_checked, monovalue=monovalue))
        self.tag_names_multiselect.selection_changed.connect(
            self.update_selected_tag_names)

    def toggle_tag_values_multiselect(
            self, tag_name, tag_name_is_checked, monovalue=False):
        lbl_name = "%s_values_lbl" % tag_name
        cbx_name = "%s_values_multiselect" % tag_name
        lbl = getattr(self, lbl_name, None)
        cbx = getattr(self, cbx_name, None)
        if lbl is not None:
            delattr(self, lbl_name)
            lbl.setParent(None)
        if cbx is not None:
            delattr(self, cbx_name)
            cbx.setParent(None)
        if tag_name_is_checked:
            setattr(self, lbl_name,
                    QLabel('%s value' % tag_name + ('' if monovalue else 's')))
            setattr(self, cbx_name,
                    MultiSelectComboBox(self, mono=monovalue))
            lbl = getattr(self, lbl_name)
            cbx = getattr(self, cbx_name)
            self.add_widget_to_type_dep_layout(
                lbl, lbl_name, self.typeDepVLayout)
            self.add_widget_to_type_dep_layout(
                cbx, cbx_name, self.typeDepVLayout)
            if monovalue:
                cbx.currentIndexChanged.connect(
                    lambda idx: self.update_selected_tag_values(tag_name))
            else:
                cbx.selection_changed.connect(
                    lambda: self.update_selected_tag_values(tag_name))
            self.populate_tag_values_multiselect(tag_name)

    def populate_tag_values_multiselect(self, tag_name):
        tag_values = self.tags[tag_name]['values']
        selected_tag_values = [tag_value for tag_value in tag_values
                               if tag_values[tag_value]]
        unselected_tag_values = [tag_value for tag_value in tag_values
                                 if not tag_values[tag_value]]
        cbx = getattr(self, "%s_values_multiselect" % tag_name)
        cbx.clear()
        if cbx.mono:
            cbx.add_selected_items([''])
        cbx.add_selected_items(sorted(selected_tag_values))
        cbx.add_unselected_items(sorted(unselected_tag_values))
        # if self.tag_with_all_values:
        #     for value in cbx.get_unselected_items():
        #         if value == "*":
        #             value.setFlags(Qt.ItemIsEnabled)
        #             value.setBackground(QColor('darkGray'))
        cbx.setEnabled(
            tag_name in self.tag_names_multiselect.get_selected_items())

    def filter_damages_aggr(self):
        # NOTE: self.tags is structured like:
        # {'taxonomy': {
        #     'selected': True,
        #     'values': {
        #         'Wood': False,
        #         'Adobe': False,
        #         'Stone-Masonry': False,
        #         'Unreinforced-Brick-Masonry': False,
        #         'Concrete': True
        #     }
        #  },
        #  'NAME_1': {
        #      'selected': False,
        #      'values': {
        #          'Mid-Western': False,
        #          'Far-Western': False,
        #          'West': False,
        #          'East': False,
        #          'Central': False
        #      }
        #  },
        # }
        params = {}
        for tag_name in self.tags:
            if self.tags[tag_name]['selected']:
                for value in self.tags[tag_name]['values']:
                    if self.tags[tag_name]['values'][value]:
                        if tag_name in params:
                            params[tag_name].append(value)
                        else:
                            params[tag_name] = [value]
        output_type = 'agg_damages/%s' % self.loss_type_cbx.currentText()
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.damages_aggr = extract_npz(
                self.session, self.hostname, self.calc_id, output_type,
                message_bar=self.iface.messageBar(), params=params)
        if (self.damages_aggr is None
                or 'array' not in self.damages_aggr):
            msg = 'No data corresponds to the current selection'
            log_msg(msg, level='W', message_bar=self.iface.messageBar(),
                    duration=5)
            self.clear_plot()
            return
        self.draw_damages_aggr()

    def filter_agg_curves(self):
        params = {}
        params['loss_type'] = self.loss_type_cbx.currentText()
        params['absolute'] = (
            True if self.abs_rel_cbx.currentText() == 'Absolute' else False)
        if self.output_type == 'aggcurves':
            params['kind'] = 'rlzs'
        elif self.output_type == 'aggcurves-stats':
            params['kind'] = 'stats'
        else:
            raise NotImplementedError(self.output_type)
        if self.aggregate_by is not None and len(self.aggregate_by):
            for tag_name in sorted(self.aggregate_by):
                tag_value = [val for val in self.tags[tag_name]['values']
                             if self.tags[tag_name]['values'][val]][0]
                # NOTE: the oq-engine makes a urlencode on tag values
                params[tag_name] = urllib.parse.quote_plus(tag_value)
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.agg_curves = extract_npz(
                self.session, self.hostname, self.calc_id, 'agg_curves',
                message_bar=self.iface.messageBar(), params=params)
        self.draw_agg_curves(self.output_type)

    def filter_avg_losses_aggr(self):
        star_count = 0
        params = {}
        for tag_name in self.tags:
            if self.tags[tag_name]['selected']:
                for value in self.tags[tag_name]['values']:
                    if self.tags[tag_name]['values'][value]:
                        if value == '*':
                            star_count += 1
                        if star_count > 1:
                            msg = '"*" can be selected for only one tag'
                            log_msg(msg, level='W',
                                    message_bar=self.iface.messageBar(),
                                    duration=5)
                            self.table.clear()
                            self.table.setRowCount(0)
                            self.table.setColumnCount(0)
                            return
                        if tag_name in params:
                            params[tag_name].append(value)
                        else:
                            params[tag_name] = [value]
        to_extract = 'agg_losses/%s' % self.loss_type_cbx.currentText()
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.avg_losses_rlzs_aggr = extract_npz(
                self.session, self.hostname, self.calc_id, to_extract,
                message_bar=self.iface.messageBar(), params=params)
        if (self.avg_losses_rlzs_aggr is None
                or 'array' not in self.avg_losses_rlzs_aggr):
            msg = 'No data corresponds to the current selection'
            log_msg(msg, level='W', message_bar=self.iface.messageBar(),
                    duration=5)
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        self.draw_avg_losses_rlzs_aggr()

    def update_selected_tag_names(self):
        for tag_name in self.tag_names_multiselect.get_selected_items():
            self.tags[tag_name]['selected'] = True
        for tag_name in self.tag_names_multiselect.get_unselected_items():
            self.tags[tag_name]['selected'] = False
            if self.output_type != 'ebrisk':
                # deselect all tag values for tags that are unselected
                for value in self.tags[tag_name]['values']:
                    self.tags[tag_name]['values'][value] = False
                    if self.tag_with_all_values == tag_name:
                        self.tag_with_all_values = None
        if self.output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.filter_damages_aggr()
        elif self.output_type in ('avg_losses-rlzs_aggr',
                                  'avg_losses-stats_aggr'):
            self.filter_avg_losses_aggr()
        elif self.output_type in ('aggcurves', 'aggcurves-stats'):
            self.filter_agg_curves()

    def update_selected_tag_values(self, tag_name):
        cbx = getattr(self, "%s_values_multiselect" % tag_name)
        for tag_value in cbx.get_selected_items():
            self.tags[tag_name]['values'][tag_value] = True
        for tag_value in cbx.get_unselected_items():
            self.tags[tag_name]['values'][tag_value] = False
        if self.output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.filter_damages_aggr()
        elif self.output_type in ('avg_losses-rlzs_aggr',
                                  'avg_losses-stats_aggr',
                                  'aggcurves', 'aggcurves-stats'):
            if "*" in cbx.get_selected_items():
                self.tag_with_all_values = tag_name
            elif (self.tag_with_all_values == tag_name and
                    "*" in cbx.get_unselected_items()):
                self.tag_with_all_values = None
            if self.output_type in ('avg_losses-rlzs_aggr',
                                    'avg_losses-stats_aggr'):
                self.filter_avg_losses_aggr()
            elif self.output_type in ('aggcurves', 'aggcurves-stats'):
                self.filter_agg_curves()

    def get_list_selected_tags_str(self):
        selected_tags = {tag_name: self.tags[tag_name]['values']
                         for tag_name in self.tags
                         if self.tags[tag_name]['selected']}
        selected_tags_str = ''
        for tag_name in selected_tags:
            selected_tags_str += f'{tag_name}="'
            tag_values = selected_tags[tag_name]
            for tag_value in tag_values:
                if tag_values[tag_value]:
                    selected_tags_str += f'{tag_value}" '
                    continue
        return selected_tags_str

    def refresh_feature_selection(self):
        if not self.stats_multiselect.get_selected_items():
            self.clear_plot()
            return
        # feature selection triggers the redrawing of plots
        layer = self.iface.activeLayer()
        selected_feats = layer.selectedFeatureIds()
        layer.blockSignals(True)
        layer.removeSelection()
        layer.blockSignals(False)
        layer.selectByIds(selected_feats)

    def remove_type_dep_attrs(self):
        for widget_name in self.type_dep_widget_names:
            if widget_name == 'exclude_no_dmg_ckb':
                if hasattr(self, widget_name):
                    widget = getattr(self, widget_name)
                    for i in reversed(list(range(self.plot_layout.count()))):
                        if self.plot_layout.itemAt(i).widget() == widget:
                            widget.setParent(None)
                            break
            if hasattr(self, widget_name):
                delattr(self, widget_name)

    def set_output_type_and_its_gui(self, new_output_type):
        self.rlzs = None
        self.stats = None
        self.selected_rlzs_or_stats = None
        self.consequences = None
        self.agg_curves = None
        self.damages_aggr = None
        self.aggregate_by = None
        self.dmg_states = None
        self.exposure_metadata = None
        self.was_imt_switched = None
        self.was_poe_switched = None
        self.was_loss_type_switched = None

        # clear type dependent widgets
        # NOTE: typeDepVLayout contains typeDepHLayout1 and typeDepHLayout2,
        #       that will be cleared recursively
        clear_widgets_from_layout(self.typeDepVLayout)
        # NOTE: even after removing widgets from layouts, the viewer dock
        # widget might still keep references to some of its children widgets
        self.remove_type_dep_attrs()
        if hasattr(self, 'plot'):
            self.plot.clear()
            self.plot_canvas.show()
            self.plot_canvas.draw()
            self.table.hide()
        if new_output_type == 'hcurves':
            self.create_imt_selector()
            self.create_stats_multiselect()
            self.stats_multiselect.selection_changed.connect(
                self.refresh_feature_selection)
        elif new_output_type == 'aggcurves':
            self.create_loss_type_selector()
            self.create_rlzs_multiselect()
            self.create_ep_selector()
            self.create_abs_rel_selector()
            # NOTE: tag_names_multiselect is created dynamically afterwards
            self.rlzs_multiselect.selection_changed.connect(
                # lambda: self.draw_agg_curves(new_output_type))
                self.filter_agg_curves)
        elif new_output_type == 'aggcurves-stats':
            self.create_loss_type_selector()
            self.create_stats_multiselect()
            self.create_ep_selector()
            self.create_abs_rel_selector()
            # NOTE: tag_names_multiselect is created dynamically afterwards
            self.stats_multiselect.selection_changed.connect(
                # lambda: self.draw_agg_curves(new_output_type))
                self.filter_agg_curves)
        elif new_output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.create_loss_type_selector()
            self.create_rlz_or_stat_selector()
            self.create_tag_names_multiselect(monovalue=True)
            self.create_exclude_no_dmg_ckb()
        elif new_output_type in ('avg_losses-rlzs_aggr',
                                 'avg_losses-stats_aggr'):
            self.create_loss_type_selector()
            self.create_tag_names_multiselect(monovalue=True)
        elif new_output_type == 'uhs':
            self.create_stats_multiselect()
            self.stats_multiselect.selection_changed.connect(
                self.refresh_feature_selection)
        # NOTE: the window's size is automatically adjusted even without
        # calling self.adjustSize(). If that method is called, it might cause
        # the window to shrink unexpectedly until the focus is moved somewhere
        # else.
        self.output_type = new_output_type

    def load_no_map_output(
            self, calc_id, session, hostname, output_type, engine_version):
        self.calc_id = calc_id
        self.session = session
        self.hostname = hostname
        self.tag_with_all_values = None
        self.change_output_type(output_type)
        self.engine_version = engine_version
        self.setVisible(True)
        self.raise_()
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            oqparam = extract_npz(
                session, hostname, calc_id, 'oqparam',
                message_bar=self.iface.messageBar())
        if output_type in ('aggcurves', 'aggcurves-stats'):
            self.load_agg_curves(
                calc_id, session, hostname, output_type, oqparam)
        elif output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.load_damages_aggr(
                calc_id, session, hostname, output_type, oqparam)
        elif output_type in ('avg_losses-rlzs_aggr',
                             'avg_losses-stats_aggr'):
            self.load_avg_losses_aggr(
                calc_id, session, hostname, output_type, oqparam)
        else:
            raise NotImplementedError(output_type)

    def load_damages_aggr(
            self, calc_id, session, hostname, output_type, oqparam):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            composite_risk_model_attrs = extract_npz(
                session, hostname, calc_id, 'composite_risk_model.attrs',
                message_bar=self.iface.messageBar())
        if composite_risk_model_attrs is None:
            return
        limit_states = composite_risk_model_attrs['limit_states']
        self.consequences = composite_risk_model_attrs['consequences']
        self.dmg_states = numpy.append(['no damage'], limit_states)
        self._get_tags(session, hostname, calc_id, self.iface.messageBar(),
                       with_star=False)

        if self.output_type == 'damages-rlzs_aggr':
            rlzs = self.get_rlzs(calc_id, session, hostname, oqparam)
            if rlzs is None:
                return
            self.rlz_or_stat_cbx.blockSignals(True)
            self.rlz_or_stat_cbx.clear()
            if len(rlzs) == 1:
                self.rlz_or_stat_cbx.addItem('mean', rlzs[0])
            else:
                for rlz in rlzs:
                    self.rlz_or_stat_cbx.addItem(rlz, rlz)
            self.rlz_or_stat_cbx.blockSignals(False)

        self.single_loss_types = composite_risk_model_attrs['loss_types']
        loss_types = self.single_loss_types[:]
        # NOTE: we may want to add total_losses also in this case
        # if 'total_losses' in oqparam:
        #     loss_types.append(oqparam['total_losses'])
        self.loss_type_cbx.blockSignals(True)
        self.loss_type_cbx.clear()
        self.loss_type_cbx.addItems(loss_types)
        self.loss_type_cbx.blockSignals(False)

        if self.output_type == 'damages-stats_aggr':
            stats = self.get_stats(calc_id, session, hostname, oqparam)
            self.rlz_or_stat_cbx.blockSignals(True)
            self.rlz_or_stat_cbx.clear()
            for stat in stats:
                self.rlz_or_stat_cbx.addItem(stat, stat)

        self.tag_names_multiselect.clear()
        tag_names = sorted(self.tags.keys())
        self.tag_names_multiselect.add_unselected_items(tag_names)
        self.clear_tag_values_multiselects(tag_names)

        self.filter_damages_aggr()

    def _build_tags(self):
        tag_names = sorted(self.exposure_metadata['tagnames'])
        self.tags = {}
        for tag_idx, tag_name in enumerate(tag_names):
            tag_values = sorted([
                value for value in self.exposure_metadata[tag_name]
                # if value != '?']) + ['*']
                if value != '?'])
            self.tags[tag_name] = {
                'selected': True if tag_idx == 0 else False,
                'values': {
                    value: True if value_idx == 0 else False
                    for value_idx, value in enumerate(tag_values)
                }
            }

    def clear_tag_values_multiselects(self, tag_names):
        for tag_name in tag_names:
            lbl_name = '%s_values_lbl' % tag_name
            cbx_name = '%s_values_multiselect' % tag_name
            lbl = getattr(self, lbl_name, None)
            cbx = getattr(self, cbx_name, None)
            if lbl is not None:
                delattr(self, lbl_name)
            if cbx is not None:
                delattr(self, cbx_name)

    def _get_tags(self, session, hostname, calc_id, message_bar, with_star):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            tags_npz = extract_npz(
                session, hostname, calc_id, 'asset_tags',
                message_bar=message_bar)
        if tags_npz is None:
            return
        tags_list = []
        for tag_name in tags_npz:
            if tag_name in ['id', 'array', 'extra']:
                continue
            for tag in tags_npz[tag_name]:
                tag = tag.decode('utf8')
                if tag[-1] != '?':
                    tags_list.append(tag)
        self.tags = {}
        for tag in tags_list:
            # tags are in the format 'city=Benicia' (tag_name=tag_value)
            tag_name, tag_value = tag.split('=', 1)
            if tag_name not in self.tags:
                self.tags[tag_name] = {
                    'selected': False,
                    'values': {tag_value: False}}  # False means unselected
            else:
                # False means unselected
                self.tags[tag_name]['values'][tag_value] = False
            if with_star:
                self.tags[tag_name]['values']['*'] = False

    def get_rlzs(self, calc_id, session, hostname, oqparam):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            rlzs_npz = extract_npz(
                session, hostname, calc_id, 'realizations',
                message_bar=self.iface.messageBar())
            if rlzs_npz is None:
                return None
            rlzs = [rlz[1].decode('utf-8')  # branch_path
                    for rlz in rlzs_npz['array']]
            if oqparam['collect_rlzs']:
                rlzs = [rlzs[0]]
            return rlzs

    def get_stats(self, calc_id, session, hostname, oqaram):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            damages_stats_npz = extract_npz(
                session, hostname, calc_id, 'damages-stats',
                message_bar=self.iface.messageBar())
            if damages_stats_npz is None:
                return None
            return [stat for stat in damages_stats_npz if stat != 'extra']

    def load_avg_losses_aggr(
            self, calc_id, session, hostname, output_type, oqparam):
        if self.output_type == 'avg_losses-rlzs_aggr':
            self.rlzs = self.get_rlzs(calc_id, session, hostname, oqparam)
            if self.rlzs is None:
                return
        self._get_tags(session, hostname, calc_id, self.iface.messageBar(),
                       with_star=True)

        self.single_loss_types = get_loss_types(
            session, hostname, calc_id, self.iface.messageBar())
        loss_types = self.single_loss_types[:]
        # NOTE: we may want to add total_losses also in this case
        # if 'total_losses' in oqparam:
        #     loss_types.append(oqparam['total_losses'])
        self.loss_type_cbx.blockSignals(True)
        self.loss_type_cbx.clear()
        self.loss_type_cbx.addItems(loss_types)
        self.loss_type_cbx.blockSignals(False)

        if self.output_type == 'avg_losses-stats_aggr':
            to_extract = 'agg_losses/%s' % loss_types[0]
            with WaitCursorManager(
                    'Extracting...', message_bar=self.iface.messageBar()):
                npz = extract_npz(session, hostname, calc_id, to_extract,
                                  message_bar=self.iface.messageBar())
            # stats might be unavailable in case of a single realization
            if len(npz['stats']) == 0:
                # NOTE: writing 'mean' instead of 'rlz-0' would be equivalent
                self.stats = ['rlz-0']
            else:
                self.stats = npz['stats']

        self.tag_names_multiselect.clear()
        tag_names = sorted(self.tags.keys())
        self.tag_names_multiselect.add_unselected_items(tag_names)
        self.clear_tag_values_multiselects(tag_names)

        self.filter_avg_losses_aggr()

    def get_total_loss_unit(self, total_losses):
        unit = None
        separate_types = total_losses.split('+')
        # NOTE: assuming that the separate types have consistent units
        loss_type_idx = self.loss_type_cbx.findText(separate_types[0])
        unit = self.agg_curves['units'][loss_type_idx]
        return unit

    def load_agg_curves(
            self, calc_id, session, hostname, output_type, oqparam):
        params = {}
        if self.output_type == 'aggcurves':
            params['kind'] = 'rlzs'
        elif self.output_type == 'aggcurves-stats':
            params['kind'] = 'stats'
        else:
            raise NotImplementedError(output_type)
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            composite_risk_model_attrs = extract_npz(
                session, hostname, calc_id, 'composite_risk_model.attrs',
                message_bar=self.iface.messageBar())
        if composite_risk_model_attrs is None:
            return
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.exposure_metadata = extract_npz(
                session, hostname, calc_id, 'exposure_metadata',
                message_bar=self.iface.messageBar())
        if self.exposure_metadata is None:
            return
        self.aggregate_by = None
        if 'aggregate_by' in oqparam and len(oqparam['aggregate_by']):
            self._build_tags()
            self.aggregate_by = oqparam['aggregate_by'][0]
            for tag_name in sorted(self.aggregate_by):
                tag_values = self.tags[tag_name]['values'].keys()
                self.create_tag_values_selector(
                    tag_name,
                    tag_values=tag_values,
                    monovalue=True, preselect_first=True)
                tag_value = [val for val in self.tags[tag_name]['values']
                             if self.tags[tag_name]['values'][val]][0]
                params[tag_name] = tag_value
        self.single_loss_types = composite_risk_model_attrs['loss_types']
        loss_types = self.single_loss_types[:]
        if 'total_losses' in oqparam:
            loss_types.append(oqparam['total_losses'])
        self.loss_type_cbx.blockSignals(True)
        self.loss_type_cbx.clear()
        self.loss_type_cbx.addItems(loss_types)
        self.loss_type_cbx.blockSignals(False)
        params['loss_type'] = self.loss_type_cbx.currentText()
        params['absolute'] = (
            True if self.abs_rel_cbx.currentText() == 'Absolute' else False)
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.agg_curves = extract_npz(
                session, hostname, calc_id, 'agg_curves',
                message_bar=self.iface.messageBar(), params=params)
        self.ep_cbx.blockSignals(True)
        self.ep_cbx.clear()
        self.ep_cbx.addItems(self.agg_curves['ep_field'])
        self.ep_cbx.blockSignals(False)
        if output_type == 'aggcurves':
            self.rlzs = self.agg_curves['kind']
            if oqparam['collect_rlzs']:
                self.rlzs = [self.rlzs[0]]
            self.rlzs_multiselect.blockSignals(True)
            self.rlzs_multiselect.clear()
            self.rlzs_multiselect.add_selected_items(self.rlzs)
            self.rlzs_multiselect.blockSignals(False)
        elif output_type == 'aggcurves-stats':
            self.stats = self.agg_curves['kind']
            self.stats_multiselect.blockSignals(True)
            self.stats_multiselect.clear()
            self.stats_multiselect.add_selected_items(self.stats)
            self.stats_multiselect.blockSignals(False)
        else:
            raise NotImplementedError(
                'Unable to draw outputs of type %s' % output_type)
            return
        self.filter_agg_curves()

    def _get_idxs(self, output_type):
        # aggcurves
        if output_type == 'aggcurves':
            rlzs_or_stats = list(
                self.rlzs_multiselect.get_selected_items())
        elif output_type == 'aggcurves-stats':
            rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            raise NotImplementedError(
                'Unable to get indices for type %s' % output_type)
            return
        rlzs_or_stats_idxs = []
        for stat_idx, stat in enumerate(self.agg_curves['kind']):
            if stat in rlzs_or_stats:
                rlzs_or_stats_idxs.append(stat_idx)
        if self.aggregate_by is not None and len(self.aggregate_by):
            tag_name_idxs = {}
            tag_value_idxs = {}
            if hasattr(self, 'tags'):
                for tag_name in self.tags:
                    if tag_name not in self.aggregate_by:
                        continue
                    tag_name_idx = list(self.aggregate_by).index(tag_name)
                    tag_name_idxs[tag_name] = tag_name_idx
                    tag_value_idxs[tag_name] = []
                    # if not self.tags[tag_name]['selected']:
                    #     continue
                    for tag_value in self.tags[tag_name]['values']:
                        if self.tags[tag_name]['values'][tag_value]:
                            tag_value_idx = list(
                                self.agg_curves[tag_name]).index(tag_value)
                            tag_value_idxs[tag_name].append(tag_value_idx)
            else:
                for tag_name in self.aggregate_by:
                    # FIXME: check if currentIndex is ok
                    tag_value_idx = getattr(
                        self,
                        "%s_values_multiselect" % tag_name).currentIndex()
                    tag_value_idxs[tag_name] = tag_value_idx
        else:
            tag_name_idxs = None
            tag_value_idxs = None
        return rlzs_or_stats_idxs, tag_name_idxs, tag_value_idxs

    def draw_agg_curves(self, output_type):
        if output_type == 'aggcurves':
            rlzs_or_stats = list(
                self.rlzs_multiselect.get_selected_items())
        elif output_type == 'aggcurves-stats':
            rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            raise NotImplementedError(
                'Can not draw outputs of type %s' % output_type)
            return
        abscissa = self.agg_curves['return_period']
        rlzs_or_stats_idxs, tag_name_idxs, tag_value_idxs = \
            self._get_idxs(output_type)
        try:
            ordinates = self.agg_curves['array']
            if not numpy.any(ordinates):
                raise ValueError
        except (KeyError, ValueError):
            msg = 'No data corresponds to the current selection'
            log_msg(msg, level='W', message_bar=self.iface.messageBar(),
                    duration=5)
            self.clear_plot()
            return
        loss_type = self.loss_type_cbx.currentText()
        loss_type_idx = self.loss_type_cbx.currentIndex()
        ep_idx = self.ep_cbx.currentIndex()
        try:
            unit = self.agg_curves['units'][loss_type_idx]
        except IndexError:
            unit = self.get_total_loss_unit(loss_type)
        self.plot.clear()
        # if not ordinates.any():  # too much filtering
        #     self.plot_canvas.draw()
        #     log_msg('No data corresponding to the selected items',
        #             level='W', message_bar=self.iface.messageBar())
        #     return
        marker = dict()
        line_style = dict()
        color_hex = dict()
        for rlz_or_stat_idx, rlz_or_stat in enumerate(rlzs_or_stats):
            marker[rlz_or_stat_idx] = self.markers[
                rlz_or_stat_idx % len(self.markers)]
            if self.bw_chk.isChecked():
                line_styles_whole_cycles = (
                    rlz_or_stat_idx // len(self.line_styles))
                # NOTE: 85 is approximately 256 / 3
                r = g = b = format(
                    (85 * line_styles_whole_cycles) % 256, '02x')
                color_hex_str = "#%s%s%s" % (r, g, b)
                color = QColor(color_hex_str)
                color_hex[rlz_or_stat_idx] = color.darker(120).name()
                # here I am using i in order to cycle through all the
                # line styles, regardless from the feature id
                # (otherwise I might easily repeat styles, that are a
                # small set of 4 items)
                line_style[rlz_or_stat_idx] = self.line_styles[
                    rlz_or_stat_idx % len(self.line_styles)]
            else:
                # here I am using the feature id in order to keep a
                # matching between a curve and the corresponding point
                # in the map
                color_name = self.color_names[
                    rlz_or_stat_idx % len(self.color_names)]
                color = QColor(color_name)
                color_hex[rlz_or_stat_idx] = color.darker(120).name()
                line_style[rlz_or_stat_idx] = "-"  # solid
        # chosen rlz or stat index, all return periods, all ep_fields
        tup = (rlzs_or_stats_idxs, slice(None), ep_idx)
        # add to the tuple the indices of chosen tag values
        if tag_value_idxs is not None:
            value_idxs = tag_value_idxs.values()
            tup += tuple(value_idxs)
        ordinates = self.agg_curves['array'][tup]
        for ys, rlz_or_stat in zip(
                ordinates, rlzs_or_stats):
            rlz_or_stat_idx = rlzs_or_stats.index(rlz_or_stat)
            label = rlz_or_stat
            self.plot.plot(
                abscissa,
                ys,
                # color=color_hex[rlz_or_stat_idx],
                linestyle=line_style[rlz_or_stat_idx],
                marker=marker[rlz_or_stat_idx],
                label=label
            )
        self.plot.set_xscale('log')
        self.plot.set_yscale('linear')
        self.plot.set_xlabel('Return period (years)')
        if self.abs_rel_cbx.currentText() == 'Absolute':
            if loss_type in ['occupants', 'residents']:
                ylabel = 'Loss (%s)' % unit
            elif loss_type == 'area':
                ylabel = 'Area loss (%s)' % unit
            elif loss_type == 'number':
                ylabel = 'Number loss (%s)' % unit
            else:
                ylabel = 'Economic loss (%s)' % unit
        else:
            if loss_type in ['occupants', 'residents']:
                ylabel = 'People loss ratio'
            elif loss_type == 'area':
                ylabel = 'Area loss ratio'
            elif loss_type == 'number':
                ylabel = 'Number loss ratio'
            else:
                ylabel = 'Economic loss ratio'
        self.plot.set_ylabel(ylabel)
        title = 'Loss category: %s' % self.loss_type_cbx.currentText()
        self.plot.set_title(title)
        self.plot.grid(which='both')
        if 1 <= len(rlzs_or_stats) <= 20:
            location = 'upper left'
            self.legend = self.plot.legend(
                loc=location, fancybox=True, shadow=True, fontsize='small')
        self.plot_canvas.draw()

    def draw_damages_aggr(self):
        '''
        Plots the total damage distribution
        '''
        if len(self.damages_aggr['array']) == 0:
            msg = 'No assets satisfy the selected criteria'
            log_msg(msg, level='W', message_bar=self.iface.messageBar())
            self.plot.clear()
            self.plot_canvas.draw()
            return
        rlz = self.rlz_or_stat_cbx.currentIndex()
        # TODO: re-add error bars when stddev will become available again
        # means = self.damages_aggr['array'][rlz]['mean']
        # stddevs = self.damages_aggr['array'][rlz]['stddev']

        # including 'no damage' (FIXME it should be called self.limit_states)
        D = len(self.dmg_states)
        means = self.damages_aggr['array'][rlz][:D]
        if (means < 0).any():
            msg = ('The results displayed include negative damage estimates'
                   ' for one or more damage states. Please check the fragility'
                   ' model for crossing curves.')
            log_msg(msg, level='W', message_bar=self.iface.messageBar())
        dmg_states = self.dmg_states
        if self.exclude_no_dmg_ckb.isChecked():
            # exclude the first element, that is 'no damage'
            means = means[1:]
            # TODO: re-add error bars when stddev will become available again
            # stddevs = stddevs[1:]
            dmg_states = dmg_states[1:]

        indX = numpy.arange(len(dmg_states))  # the x locations for the groups
        # TODO: re-add error bars when stddev will become available again
        # error_config = {'ecolor': '0.3', 'linewidth': '2'}
        bar_width = 0.3
        if self.bw_chk.isChecked():
            color = 'lightgray'
        else:
            color = 'IndianRed'
        self.plot.clear()
        # TODO: re-add error bars when stddev will become available again
        # self.plot.bar(indX, height=means, width=bar_width,
        #               yerr=stddevs, error_kw=error_config, color=color,
        #               linewidth=1.5, alpha=0.6)
        self.plot.bar(indX, height=means, width=bar_width, color=color,
                      linewidth=1.5, alpha=0.6)
        self.plot.set_title('Damage distribution')
        self.plot.set_xlabel('Damage state')
        self.plot.set_ylabel('Number of assets in damage state')
        self.plot.set_xticks(indX+bar_width/2.)
        self.plot.set_xticklabels(dmg_states)
        self.plot.margins(.15, 0)
        self.plot.yaxis.grid()
        self.plot_canvas.draw()
        if self.consequences:
            consequences_array = self.damages_aggr['array'][rlz][D:]
            nrows = 1
            ncols = len(self.consequences)
            self.table.clear()
            self.table.setRowCount(nrows)
            self.table.setColumnCount(ncols)
            # FIXME: perhaps write measurement unit instead of total? If so,
            # should we do the same for avg_losses_rlzs_aggr?
            self.table.setVerticalHeaderLabels(['Total  '])
            self.table.setHorizontalHeaderLabels(self.consequences)
            for col in range(ncols):
                self.table.setItem(
                    0, col, QTableWidgetItem(str(consequences_array[col])))
            # NOTE: vertical headers are not resized properly with respect to
            # contents (they are cut on the right). I couldn't find any proper
            # way to fix it, so I am adding a tail of 2 spaces to each header
            # as a workaround (hack)
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.show()
            # FIXME: the table occupies a lot of useless vertical space

    def _to_2d(self, array):
        # convert 1d array into 2d, unless already 2d
        if len(array.shape) == 1:
            array = array[None, :]
        return array

    def draw_avg_losses_rlzs_aggr(self):
        self.plot_canvas.hide()
        losses_array = self.avg_losses_rlzs_aggr['array']
        losses_array = self._to_2d(losses_array)
        tags = None
        try:
            # NOTE: case with '*'
            tags = [tag.decode('utf8')
                    for tag in self.avg_losses_rlzs_aggr['tags']]
        except KeyError:
            # NOTE: case without '*'
            pass
        nrows, ncols = losses_array.shape
        self.table.clear()
        self.table.setRowCount(nrows)
        self.table.setColumnCount(ncols)
        if self.output_type == 'avg_losses-rlzs_aggr':
            labels = ['Mean'] if len(self.rlzs) == 1 else self.rlzs
            self.table.setHorizontalHeaderLabels(labels)
        else:  # self.output_type == 'avg_losses-stats_aggr'
            self.table.setHorizontalHeaderLabels(self.stats)
        if tags is not None:  # NOTE: case with '*'
            # tags are like
            # array(['taxonomy=Wood',
            #        'taxonomy=Adobe',
            #        'taxonomy=Stone-Masonry',
            #        'taxonomy=Unreinforced-Brick-Masonry',
            #        'taxonomy=Concrete'], dtype='|S35')
            tag_values = [tag.split('=', 1)[1] + '  ' for tag in tags]
            self.table.setVerticalHeaderLabels(tag_values)
        else:  # NOTE: case without '*'
            tag_values = []
            for tag in self.tags:
                if self.tags[tag]['selected']:
                    values = [
                        tag_value for tag_value in self.tags[tag]['values']
                        if self.tags[tag]['values'][tag_value]]
                    tag_values.extend(values)
            if tag_values:
                self.table.setVerticalHeaderLabels([
                    ', '.join(tag_values) + '  '])
            else:
                self.table.setVerticalHeaderLabels(['Total  '])
        for row in range(nrows):
            for col in range(ncols):
                self.table.setItem(
                    row, col, QTableWidgetItem(str(losses_array[row, col])))
        # NOTE: vertical headers are not resized properly with respect to
        # contents (they are cut on the right). I couldn't find any proper way
        # to fix it, so I am adding a tail of 2 spaces to each header as a
        # workaround (hack)
        self.table.resizeColumnsToContents()
        self.table.show()

    def draw(self):
        self.plot.clear()
        gids = dict()
        if (hasattr(self, 'stats_multiselect')
                and self.stats_multiselect is not None):
            selected_rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            selected_rlzs_or_stats = [None]
        selected_features_ids = self.iface.activeLayer().selectedFeatureIds()
        for rlz_or_stat in selected_rlzs_or_stats:
            gids[rlz_or_stat] = selected_features_ids
        count_selected_feats = len(selected_features_ids)
        count_selected_stats = len(selected_rlzs_or_stats)
        count_lines = count_selected_feats * count_selected_stats
        if count_lines == 0:
            self.clear_plot()
            return

        num_plottable_curves = 0
        for rlz_or_stat in selected_rlzs_or_stats:
            for i, (site, curve) in enumerate(
                    self.current_selection[rlz_or_stat].items()):
                # NOTE: it is needed if we need the y-axis to be log scale
                if self.output_type == 'hcurves':
                    if not any(curve['ordinates']):
                        log_msg(
                            'A flat hazard curve with all zero values was'
                            ' found. It will not be displayed in the plot.',
                            level='W', message_bar=self.iface.messageBar())
                        continue
                feature = next(self.iface.activeLayer().getFeatures(
                    QgsFeatureRequest().setFilterFid(site)))

                lon = feature.geometry().asPoint().x()
                lat = feature.geometry().asPoint().y()

                self.line, = self.plot.plot(
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
                num_plottable_curves += 1
        if num_plottable_curves == 0:
            self.clear_plot()
            log_msg(
                'No curves could be plotted.',
                level='W', message_bar=self.iface.messageBar())
            return

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
        poe = self.iface.activeLayer().customProperty('poe', None)

        if investigation_time is not None:
            investigation_time = float(investigation_time)
            if poe is not None:
                poe = float(poe)
                return_period = investigation_time / poe
                title += ' (PoE = %.5f, RP = %.0f years)' % (poe,
                                                             return_period)
            else:
                title += ' (%s years)' % investigation_time
        self.plot.set_title(title)
        self.plot.grid(which='both')
        if 1 <= count_lines <= 20:
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

        if (hasattr(self, 'stats_multiselect')
                and self.stats_multiselect is not None):
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
        for fid in selected:
            if hasattr(self, 'rlzs_or_stats'):
                for rlz_or_stat in self.rlzs_or_stats:
                    self.current_selection[rlz_or_stat] = {}
        if not selected_rlzs_or_stats or not self.current_selection:
            return
        self.current_abscissa = []
        request = QgsFeatureRequest().setFlags(
            QgsFeatureRequest.NoGeometry).setFilterFids(selected)
        for feature in self.iface.activeLayer().getFeatures(request):
            if self.output_type == 'hcurves':
                imt = self.imt_cbx.currentText()
                imls = [field_name.split('_')[2]
                        for field_name in self.field_names
                        if (field_name.split('_')[0]
                            == selected_rlzs_or_stats[0])
                        and field_name.split('_')[1] == imt]
                try:
                    imls = [float(iml) for iml in imls]
                except ValueError:
                    log_msg('Intensity measure levels are not numeric',
                            level='W', message_bar=self.iface.messageBar())
                self.current_abscissa = imls
            elif self.output_type == 'uhs':
                err_msg = ("The selected layer does not contain uniform"
                           " hazard spectra in the expected format.")
                self.field_names = [field.name() for field in feature.fields()]
                # reading from something like
                # [u'rlz-000_PGA', u'rlz-000_SA(0.025)', ...]
                # the first item can be PGA (but PGA can also be missing)
                # and the length of the array of periods must be consistent
                # with the length of or ordinates to plot
                if self.field_names[0].endswith("PGA"):
                    unique_periods = [0.0]  # Use 0.0 for PGA
                else:
                    unique_periods = []  # PGA is not there
                # get the number between parenthesis
                try:
                    periods = [
                        float(name[name.find("(") + 1: name.find(")")])
                        for name in self.field_names
                        if "(" in name]
                    for period in periods:
                        if period not in unique_periods:
                            unique_periods.append(period)
                except ValueError as exc:
                    log_msg(err_msg, level='C',
                            message_bar=self.iface.messageBar(),
                            exception=exc)
                    self.output_type_cbx.setCurrentIndex(-1)
                    return
                self.current_abscissa = unique_periods
                break
            else:
                raise NotImplementedError(self.output_type)

        for i, feature in enumerate(
                self.iface.activeLayer().getFeatures(request)):
            if (self.was_imt_switched
                    or self.was_loss_type_switched
                    or (feature.id() not in
                        self.current_selection[selected_rlzs_or_stats[0]])
                    or self.output_type == 'uhs'):
                self.field_names = [
                    field.name()
                    for field in self.iface.activeLayer().fields()
                    if field.name() != 'fid']
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
                            (i + rlz_or_stat_idx) // len(self.line_styles))
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

    def layer_changed(self):
        self.calc_id = None
        self.clear_plot()

        self.remove_connects()

        if (self.iface.activeLayer() is not None
                and self.iface.activeLayer().type() == QgsMapLayer.VectorLayer
                and self.iface.activeLayer().geometryType()
                == QgsWkbTypes.PointGeometry):
            self.engine_version = self.iface.activeLayer().customProperty(
                'engine_version', None)
            self.iface.activeLayer().selectionChanged.connect(
                self.redraw_current_selection)

            if self.output_type in ['hcurves', 'uhs']:
                self.calc_id = self.iface.activeLayer().customProperty(
                    'calc_id')
                for rlz_or_stat in self.stats_multiselect.get_selected_items():
                    self.current_selection[rlz_or_stat] = {}
                self.stats_multiselect.clear()
                self.field_names = [
                    field.name()
                    for field in self.iface.activeLayer().fields()
                    if field.name() != 'fid']
                if self.output_type == 'hcurves':
                    # fields names are like 'max_PGA_0.005'
                    imts = sorted(set(
                        [field_name.split('_')[1]
                         for field_name in self.field_names]))
                    self.imt_cbx.addItems(imts)
                self.rlzs_or_stats = sorted(set(
                    [field_name.split('_')[0]
                     for field_name in self.field_names]))
                # Select all stats by default
                self.stats_multiselect.add_selected_items(self.rlzs_or_stats)
                self.stats_multiselect.setEnabled(len(self.rlzs_or_stats) > 1)
            else:  # no plots for this layer
                self.current_selection = {}
            self.redraw_current_selection()

    def remove_connects(self):
        try:
            self.iface.activeLayer().selectionChanged.disconnect(
                self.redraw_current_selection)
        except (TypeError, AttributeError):
            # AttributeError may occur if the signal selectionChanged has
            # already been destroyed. In that case, we don't need to disconnect
            # it. TypeError may occur when attempting to disconnect something
            # that was not connected. Also in this case, we don't need to
            # disconnect anything
            pass

    def redraw_current_selection(self):
        selected = self.iface.activeLayer().selectedFeatureIds()
        if len(selected) == 1:
            feat = self.iface.activeLayer().getFeature(selected[0])
            try:
                point = feat.geometry().asPoint()
            except TypeError:
                try:
                    point = feat.geometry().asMultiPoint()[0]
                except TypeError:
                    return
            x, y = point.x(), point.y()
            expression = '$x = %s AND $y = %s' % (x, y)
            request = QgsFeatureRequest().setFilterExpression(expression)
            feats = list(self.iface.activeLayer().getFeatures(request))
            if len(feats) > 1:
                if (hasattr(self, 'select_assets_at_same_site_chk') and
                        self.select_assets_at_same_site_chk.isChecked()):
                    self.iface.activeLayer().selectByExpression(
                        '$x = %s AND $y = %s' % (x, y))
                    return
        self.redraw(selected, [], None)

    def clear_plot(self):
        if hasattr(self, 'plot'):
            self.plot.clear()
            self.plot_canvas.draw()
            self.vertex_marker.hide()

    def clear_imt_cbx(self):
        if hasattr(self, 'imt_cbx') and self.imt_cbx is not None:
            try:
                self.imt_cbx.blockSignals(True)
                self.imt_cbx.clear()
                self.imt_cbx.blockSignals(False)
            except RuntimeError:
                # display a warning if something like this occurs:
                # "wrapped C/C++ object of type QComboBox has been deleted"
                ex_type, ex, tb = sys.exc_info()
                msg = ''.join(traceback.format_exception(ex_type, ex, tb))
                # we log it as a warning, but it should not bother the user,
                # so we are not displaying it in the message bar
                log_msg(msg, level='W')

    def clear_loss_type_cbx(self):
        if hasattr(self, 'loss_type_cbx') and self.loss_type_cbx is not None:
            try:
                self.loss_type_cbx.blockSignals(True)
                self.loss_type_cbx.clear()
                self.loss_type_cbx.blockSignals(False)
            except RuntimeError:
                # display a warning if something like this occurs:
                # "wrapped C/C++ object of type QComboBox has been deleted"
                ex_type, ex, tb = sys.exc_info()
                msg = ''.join(traceback.format_exception(ex_type, ex, tb))
                # we log it as a warning, but it should not bother the user,
                # so we are not displaying it in the message bar
                log_msg(msg, level='W')

    def on_plot_hover(self, event):
        if not self.on_container_hover(event, self.plot):
            if hasattr(self.legend, 'get_lines'):
                self.on_container_hover(event, self.legend)

    def on_container_hover(self, event, container):
        if self.output_type in OQ_EXTRACT_TO_VIEW_TYPES:
            return False
        for line in container.get_lines():
            if line.contains(event)[0]:
                # matplotlib needs a string when exporting to svg, so here we
                # must cast back to long
                fid = int(line.get_gid())
                feature = self.iface.activeLayer().getFeature(fid)
                self.vertex_marker.setCenter(feature.geometry().asPoint())
                self.vertex_marker.show()
                return True
            else:
                self.vertex_marker.hide()
        return False

    def on_multivalue_tag_name_changed(self):
        selected_tag_name = self.multivalue_tag_cbx.currentText()
        for tag_name in self.tags:
            self.tags[tag_name]['selected'] = (tag_name == selected_tag_name)
            cbx = getattr(self, "%s_values_multiselect" % tag_name)
            if tag_name != selected_tag_name:
                cbx.set_idxs_selection([0], checked=True)
        self.filter_agg_curves()

    def on_imt_changed(self):
        self.was_imt_switched = True
        self.redraw_current_selection()

    def on_ep_changed(self):
        self.filter_agg_curves()

    @pyqtSlot(str)
    def on_loss_type_changed(self, loss_type):
        if self.output_type in ('aggcurves', 'aggcurves-stats'):
            self.filter_agg_curves()
        elif self.output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.filter_damages_aggr()
        elif self.output_type in ('avg_losses-rlzs_aggr',
                                  'avg_losses-stats_aggr'):
            self.filter_avg_losses_aggr()
        else:
            self.was_loss_type_switched = True
            self.redraw_current_selection()

    def on_poe_changed(self):
        self.was_poe_switched = True
        self.redraw_current_selection()

    def on_approach_changed(self):
        self.redraw_current_selection()

    def on_recalculate_on_the_fly_chk_toggled(self, checked):
        if checked:
            self.iface.activeLayer().selectionChanged.connect(
                self.redraw_current_selection)
        else:
            self.iface.activeLayer().selectionChanged.disconnect(
                self.redraw_current_selection)

    def on_recalculate_curve_btn_clicked(self):
        self.redraw_current_selection()

    def on_n_simulations_changed(self):
        QSettings().setValue('irmt/n_simulations_per_building',
                             self.n_simulations_sbx.value())

    def on_abs_rel_changed(self):
        self.filter_agg_curves()

    def on_rlz_or_stat_changed(self):
        self.filter_damages_aggr()

    @pyqtSlot(int)
    def on_exclude_no_dmg_ckb_state_changed(self, state):
        self.filter_damages_aggr()

    @pyqtSlot()
    def on_export_data_button_clicked(self):
        filename = None
        if self.output_type == 'hcurves':
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/hazard_curves_%s_%s.csv' % (
                        self.imt_cbx.currentText(), self.calc_id)),
                '*.csv')
        elif self.output_type == 'uhs':
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/uniform_hazard_spectra_%s.csv' % self.calc_id),
                '*.csv')
        elif self.output_type in ('aggcurves', 'aggcurves-stats'):
            loss_type = self.loss_type_cbx.currentText()
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/%s_%s_%s.csv' % (self.output_type,
                                        loss_type,
                                        self.calc_id)),
                '*.csv')
        elif self.output_type in ('damages-rlzs_aggr',
                                  'damages-stats_aggr',
                                  'avg_losses-rlzs_aggr',
                                  'avg_losses-stats_aggr'):
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/%s_%s.csv' % (self.output_type, self.calc_id)),
                '*.csv')
        if filename:
            self.write_export_file(filename)

    def write_export_file(self, filename, empty_is_ok=False):
        # NOTE: param empty_is_ok is to handle a corner case in which recovery
        # curves can not be computed due to an incompatible setting of
        # recover-based damage states. In this case, the plugin correctly
        # gives instructions to the user and the plot area remains empty.

        # The header should be like:
        # Generated DATETIME by OpenQuake Engine vX.Y.Z
        # and OpenQuake Integrated Risk Modelling Toolkit vX.Y.Z
        current_datetime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        csv_headline = "# Generated %s by " % current_datetime
        if self.engine_version:  # engine version is like 'x.y.z'
            csv_headline += (
                "OpenQuake Engine v%s and " % self.engine_version)
        irmt_version = get_irmt_version()  # irmt version is like 'x.y.z'
        csv_headline += (
            "OpenQuake Integrated Risk Modelling Toolkit v%s\r\n"
            % irmt_version)
        with open(filename, 'w', newline='') as csv_file:
            csv_file.write(csv_headline)
            writer = csv.writer(csv_file)
            if self.output_type in ['hcurves', 'uhs']:
                field_names = []
                for field in self.iface.activeLayer().fields():
                    if field.name() == 'fid':
                        continue
                    if self.output_type == 'hcurves':
                        # field names are like 'mean_PGA_0.005'
                        rlz_or_stat, imt, iml = field.name().split('_')
                        # print("stat = %s\nimt = %s\niml = %s" % (
                        #     rlz_or_stat, imt, iml))
                        # print("selected_imt = %s"
                        #       % self.imt_cbx.currentText())
                        if imt != self.imt_cbx.currentText():
                            # print('imt != selected_imt')
                            continue
                    else:  # 'uhs'
                        # field names are like 'mean_PGA'
                        rlz_or_stat, _ = field.name().split('_')
                    if (rlz_or_stat not in
                            self.stats_multiselect.get_selected_items()):
                        # print("selected_rlzs_or_stats = %s" %
                        #       self.stats_multiselect.get_selected_items())
                        # print('rlz_or_stat not in selected_rlzs_or_stats')
                        continue
                    field_names.append(field.name())
                investigation_time = float(
                    self.iface.activeLayer().customProperty(
                        'investigation_time'))
                if self.output_type == 'hcurves':
                    csv_file.write(
                        '# investigation_time = %s\r\n' % investigation_time)
                elif self.output_type == 'uhs':
                    poe = float(self.iface.activeLayer().customProperty('poe'))
                    return_period = investigation_time / poe
                    csv_file.write('# poe = %.5f\r\n' % poe)
                    csv_file.write(
                        '# return_period = %.0f\r\n' % return_period)
                headers = ['lon', 'lat']
                headers.extend(field_names)
                writer.writerow(headers)
                for feature in self.iface.activeLayer().selectedFeatures():
                    values = [feature[field_name]
                              for field_name in field_names]
                    lon = feature.geometry().asPoint().x()
                    lat = feature.geometry().asPoint().y()
                    row = [lon, lat]
                    if values:
                        row.extend(values)
                    writer.writerow(row)
            elif self.output_type in ('aggcurves', 'aggcurves-stats'):
                if self.output_type == 'aggcurves':
                    rlzs = list(self.rlzs_multiselect.get_selected_items())
                else:
                    stats = list(self.stats_multiselect.get_selected_items())
                loss_type = self.loss_type_cbx.currentText()
                ep = self.ep_cbx.currentText()
                ep_idx = self.ep_cbx.currentIndex()
                abs_rel = self.abs_rel_cbx.currentText()
                loss_type_idx = self.loss_type_cbx.currentIndex()
                try:
                    unit = self.agg_curves['units'][loss_type_idx]
                except IndexError:
                    unit = self.get_total_loss_unit(loss_type)
                csv_file.write("# Loss category: %s\r\n" % loss_type)
                csv_file.write("# Exceedance Probability: %s\r\n" % ep)
                csv_file.write("# Absolute or relative: %s\r\n" % abs_rel)
                csv_file.write("# Measurement unit: %s\r\n" % unit)
                if self.aggregate_by is not None and len(self.aggregate_by):
                    csv_file.write(
                        "# Tags: %s\r\n" % (
                            self.get_list_selected_tags_str() or 'None'))
                headers = ['return_period']
                rlzs_or_stats_idxs, tag_name_idxs, tag_value_idxs = \
                    self._get_idxs(self.output_type)
                # FIXME: we should probably produce a zipped file containing N
                # csv files, one per tag value
                has_single_tag_value = None
                if tag_value_idxs:
                    has_single_tag_value = True
                    for tag_name in tag_value_idxs:
                        if len(tag_value_idxs[tag_name]) > 1:
                            has_single_tag_value = False
                            # FIXME: using only the first stat
                            for tval_idx in tag_value_idxs[tag_name]:
                                tval = self.agg_curves[tag_name][tval_idx]
                                headers.append(tval.decode('utf8'))
                            break
                if has_single_tag_value or has_single_tag_value is None:
                    if self.output_type == 'aggcurves':
                        headers.extend(rlzs)
                    else:
                        headers.extend(stats)
                writer.writerow(headers)
                for return_period_idx, return_period in enumerate(
                        self.agg_curves['return_period']):
                    row = [return_period]
                    if has_single_tag_value or has_single_tag_value is None:
                        tup = (rlzs_or_stats_idxs, return_period_idx, ep_idx)
                    else:
                        # FIXME: using only the first stat
                        tup = (return_period_idx, rlzs_or_stats_idxs[0])
                    if tag_value_idxs is not None:
                        tup += tuple(tag_value_idxs.values())
                    values = self.agg_curves['array'][tup]
                    try:
                        row.extend(values)
                    except TypeError:  # it is a single value instead of list
                        row.append(values)
                    writer.writerow(row)
            elif self.output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
                csv_file.write(
                    "# Realization or statistic: %s\r\n" % self.rlz_or_stat_cbx.currentData())
                csv_file.write(
                    "# Loss category: %s\r\n" % self.loss_type_cbx.currentText())
                csv_file.write(
                    "# Tags: %s\r\n" % (
                        self.get_list_selected_tags_str() or 'None'))
                headers = list(self.dmg_states)
                if self.consequences:
                    headers.extend(self.consequences)
                writer.writerow(headers)
                values = self.damages_aggr['array'][self.rlz_or_stat_cbx.currentIndex()]
                writer.writerow(values)
            elif self.output_type in ('avg_losses-rlzs_aggr',
                                      'avg_losses-stats_aggr'):
                csv_file.write(
                    "# Loss category: %s\r\n" % self.loss_type_cbx.currentText())
                csv_file.write(
                    "# Tags: %s\r\n" % (
                        self.get_list_selected_tags_str() or 'None'))
                try:
                    tags = [tag.decode('utf8')
                            for tag in self.avg_losses_rlzs_aggr['tags']]
                    tag = tags[0]
                    # a tag is like 'taxonomy=Wood'
                    tag_name = tag.split('=', 1)[0]
                    headers = [tag_name]
                except KeyError:
                    tags = None
                    headers = []
                if self.output_type == 'avg_losses-rlzs_aggr':
                    headers.extend(self.rlzs)
                else:  # self.output_type == 'avg_losses-stats_aggr':
                    headers.extend(self.stats)
                writer.writerow(headers)
                losses_array = self.avg_losses_rlzs_aggr['array']
                losses_array = self._to_2d(losses_array)
                if tags is not None:
                    for row_idx, row in enumerate(
                            self.avg_losses_rlzs_aggr['array']):
                        tag = tags[row_idx]
                        # a tag is like 'taxonomy=Wood'
                        tag_value = tag.split('=', 1)[1]
                        values = [tag_value]
                        values.extend(losses_array[row_idx])
                        writer.writerow(values)
                else:
                    writer.writerow(losses_array[0])
            else:
                raise NotImplementedError(self.output_type)
        msg = 'Data exported to %s' % filename
        log_msg(msg, level='S', message_bar=self.iface.messageBar())

    @pyqtSlot()
    def on_bw_chk_clicked(self):
        if self.output_type in OQ_TO_LAYER_TYPES:
            self.layer_changed()
        if self.output_type in ('aggcurves', 'aggcurves-stats'):
            # self.draw_agg_curves(self.output_type)
            self.filter_agg_curves()
        elif self.output_type in ('damages-rlzs_aggr', 'damages-stats_aggr'):
            self.filter_damages_aggr()

    @pyqtSlot(int)
    def on_output_type_cbx_currentIndexChanged(self, index):
        otname = self.output_type_cbx.currentText()
        for output_type, output_type_name in list(
                self.output_types_names.items()):
            if output_type_name == otname:
                self.set_output_type_and_its_gui(output_type)
                if output_type not in OQ_EXTRACT_TO_VIEW_TYPES:
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
        prev_index = self.output_type_cbx.currentIndex()
        # get the index of the item that has the given string
        # and set the combobox to that item
        target_index = self.output_type_cbx.findText(
            self.output_types_names[output_type])
        if target_index != -1:
            self.output_type_cbx.setCurrentIndex(target_index)
            if prev_index == target_index:
                # NOTE: if the cbx does not change the selected item, the
                # signal currentIndexChanged is not emitted, but we need to
                # reset the GUI anyway
                self.on_output_type_cbx_currentIndexChanged(target_index)
