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
from datetime import datetime
from collections import OrderedDict

from qgis.PyQt.QtCore import pyqtSlot, QSettings  # , Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
                                 QLabel,
                                 QComboBox,
                                 QSizePolicy,
                                 QSpinBox,
                                 QPushButton,
                                 QCheckBox,
                                 QDockWidget,
                                 QFileDialog,
                                 QAbstractItemView,
                                 QTableWidget,
                                 QTableWidgetItem,
                                 QHBoxLayout,
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
                                  warn_missing_package,
                                  extract_npz,
                                  get_loss_types,
                                  get_irmt_version,
                                  WaitCursorManager,
                                  )
from svir.recovery_modeling.recovery_modeling import (
    RecoveryModeling, fill_fields_multiselect)
from svir.ui.multi_select_combo_box import MultiSelectComboBox

from svir import IS_SCIPY_INSTALLED, IS_MATPLOTLIB_INSTALLED

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

        self.calc_id = None

        self.engine_version = None

        # self.current_selection[None] is for recovery curves
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
            ('agg_curves-rlzs', 'Aggregate loss curves (realizations)'),
            ('agg_curves-stats', 'Aggregate loss curves (statistics)'),
            ('dmg_by_asset_aggr', 'Damage distribution'),
            ('losses_by_asset_aggr', 'Loss distribution'),
            ('avg_losses-stats_aggr', 'Average assets losses (statistics)'),
        ])

        if QSettings().value('/irmt/experimental_enabled', False, type=bool):
            self.output_types_names.update(
                {'recovery_curves': 'Recovery Curves'})
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
        self.loss_type_lbl = QLabel('Loss Type')
        self.loss_type_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.typeDepHLayout2.addWidget(self.loss_type_lbl)
        self.typeDepHLayout2.addWidget(self.loss_type_cbx)

    def create_tag_selector(
            self, tag_name, tag_values=None, on_currentIndexChanged=None,
            mono=False):
        setattr(self, "%s_lbl" % tag_name, QLabel(tag_name))
        setattr(self, "%s_values_multiselect" % tag_name,
                MultiSelectComboBox(self))
        lbl = getattr(self, "%s_lbl" % tag_name)
        cbx = getattr(self, "%s_values_multiselect" % tag_name)
        if tag_values is not None:
            cbx.addItems(tag_values)
        self.typeDepVLayout.addWidget(lbl)
        self.typeDepVLayout.addWidget(cbx)
        if on_currentIndexChanged is not None:
            cbx.item_was_clicked.connect(on_currentIndexChanged)

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

    def create_rlz_selector(self):
        self.rlz_lbl = QLabel('Realization')
        self.rlz_lbl.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.rlz_cbx = QComboBox()
        self.rlz_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_changed)
        self.typeDepHLayout1.addWidget(self.rlz_lbl)
        self.typeDepHLayout1.addWidget(self.rlz_cbx)

    def create_exclude_no_dmg_ckb(self):
        self.exclude_no_dmg_ckb = QCheckBox('Exclude "no damage"')
        self.exclude_no_dmg_ckb.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.exclude_no_dmg_ckb.setChecked(True)
        self.exclude_no_dmg_ckb.stateChanged[int].connect(
            self.on_exclude_no_dmg_ckb_state_changed)
        self.plot_layout.insertWidget(0, self.exclude_no_dmg_ckb)

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

    def create_select_assets_at_same_site_chk(self):
        self.select_assets_at_same_site_chk = QCheckBox(
            'Select all assets at the same site')
        self.select_assets_at_same_site_chk.setChecked(True)
        self.typeDepVLayout.addWidget(self.select_assets_at_same_site_chk)

    def create_recalculate_on_the_fly_chk(self):
        self.recalculate_on_the_fly_chk = QCheckBox('Recalculate on-the-fly')
        self.recalculate_on_the_fly_chk.setChecked(True)
        self.typeDepVLayout.addWidget(self.recalculate_on_the_fly_chk)
        self.recalculate_on_the_fly_chk.toggled.connect(
            self.on_recalculate_on_the_fly_chk_toggled)

    def create_recalculate_curve_btn(self):
        self.recalculate_curve_btn = QPushButton('Calculate recovery curve')
        self.typeDepVLayout.addWidget(self.recalculate_curve_btn)
        self.recalculate_curve_btn.clicked.connect(
            self.on_recalculate_curve_btn_clicked)

    def create_fields_multiselect(self):
        self.fields_lbl = QLabel(
            'Fields containing loss-based damage state probabilities')
        self.fields_multiselect = MultiSelectComboBox(self)
        self.typeDepVLayout.addWidget(self.fields_lbl)
        self.typeDepVLayout.addWidget(self.fields_multiselect)
        fill_fields_multiselect(
            self.fields_multiselect, self.iface.activeLayer())

    def create_rlzs_multiselect(self):
        self.rlzs_lbl = QLabel('Realizations')
        self.rlzs_multiselect = MultiSelectComboBox(self)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.rlzs_lbl)
        hlayout.addWidget(self.rlzs_multiselect)
        self.typeDepVLayout.addLayout(hlayout)

    def create_stats_multiselect(self):
        self.stats_lbl = QLabel('Statistics')
        self.stats_multiselect = MultiSelectComboBox(self)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.stats_lbl)
        hlayout.addWidget(self.stats_multiselect)
        self.typeDepVLayout.addLayout(hlayout)

    def create_tag_names_multiselect(self):
        self.tag_names_lbl = QLabel('Tag names')
        self.tag_names_multiselect = MultiSelectComboBox(self)
        self.typeDepVLayout.addWidget(self.tag_names_lbl)
        self.typeDepVLayout.addWidget(self.tag_names_multiselect)
        self.tag_names_multiselect.item_was_clicked.connect(
            self.toggle_tag_values_multiselect)
        self.tag_names_multiselect.selection_changed.connect(
            self.update_selected_tag_names)

    def toggle_tag_values_multiselect(
            self, tag_name, tag_name_is_checked, mono=False):  # FIXME
        lbl = getattr(self, "%s_values_lbl" % tag_name, None)
        cbx = getattr(self, "%s_values_multiselect" % tag_name, None)
        # NOTE: removing widgets anyway, then re-adding them if needed
        if lbl is not None:
            lbl.setParent(None)
        if cbx is not None:
            cbx.setParent(None)
        if tag_name_is_checked:
            setattr(self, "%s_values_lbl" % tag_name,
                    QLabel('%s values' % tag_name))
            setattr(self, "%s_values_multiselect" % tag_name,
                    MultiSelectComboBox(self, mono=mono))
            self.typeDepVLayout.addWidget(
                getattr(self, "%s_values_lbl" % tag_name))
            self.typeDepVLayout.addWidget(
                getattr(self, "%s_values_multiselect" % tag_name))
            if mono:
                getattr(self, "%s_values_multiselect"
                        % tag_name).currentIndexChanged.connect(
                            lambda idx: self.update_selected_tag_values(
                                tag_name))
            else:
                getattr(self, "%s_values_multiselect"
                        % tag_name).selection_changed.connect(
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

    def filter_dmg_by_asset_aggr(self):
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
            self.dmg_by_asset_aggr = extract_npz(
                self.session, self.hostname, self.calc_id, output_type,
                message_bar=self.iface.messageBar(), params=params)
        if (self.dmg_by_asset_aggr is None
                or 'array' not in self.dmg_by_asset_aggr):
            msg = 'No data corresponds to the current selection'
            log_msg(msg, level='W', message_bar=self.iface.messageBar(),
                    duration=5)
            self.plot.clear()
            return
        self.draw_dmg_by_asset_aggr()

    def filter_agg_curves(self):
        # params = {}
        # # NOTE: self.tags is structured like:
        # # {'taxonomy': {
        # #     'selected': True,
        # #     'values': {
        # #         'Wood': False,
        # #         'Adobe': False,
        # #         'Stone-Masonry': False,
        # #         'Unreinforced-Brick-Masonry': False,
        # #         'Concrete': True
        # #     }
        # #  },
        # #  'NAME_1': {
        # #      'selected': False,
        # #      'values': {
        # #          'Mid-Western': False,
        # #          'Far-Western': False,
        # #          'West': False,
        # #          'East': False,
        # #          'Central': False
        # #      }
        # #  },
        # # }
        # for tag_name in self.tags:
        #     if self.tags[tag_name]['selected']:
        #         for value in self.tags[tag_name]['values']:
        #             if self.tags[tag_name]['values'][value]:
        #                 if tag_name in params:
        #                     params[tag_name].append(value)
        #                 else:
        #                     params[tag_name] = [value]
        # to_extract = self.output_type
        # with WaitCursorManager(
        #         'Extracting...', message_bar=self.iface.messageBar()):
        #     self.agg_curves = extract_npz(
        #         self.session, self.hostname, self.calc_id, to_extract,
        #         message_bar=self.iface.messageBar(), params=params)
        self.draw_agg_curves(self.output_type)

    def filter_losses_by_asset_aggr(self):
        params = {}
        for tag_name in self.tags:
            if self.tags[tag_name]['selected']:
                for value in self.tags[tag_name]['values']:
                    if self.tags[tag_name]['values'][value]:
                        if tag_name in params:
                            params[tag_name].append(value)
                        else:
                            params[tag_name] = [value]
        to_extract = 'agg_losses/%s' % self.loss_type_cbx.currentText()
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.losses_by_asset_aggr = extract_npz(
                self.session, self.hostname, self.calc_id, to_extract,
                message_bar=self.iface.messageBar(), params=params)
        if (self.losses_by_asset_aggr is None
                or 'array' not in self.losses_by_asset_aggr):
            msg = 'No data corresponds to the current selection'
            log_msg(msg, level='W', message_bar=self.iface.messageBar(),
                    duration=5)
            self.plot.clear()
            return
        self.draw_losses_by_asset_aggr()

    def update_selected_tag_names(self):
        for tag_name in self.tag_names_multiselect.get_selected_items():
            self.tags[tag_name]['selected'] = True
        for tag_name in self.tag_names_multiselect.get_unselected_items():
            self.tags[tag_name]['selected'] = False
            # deselect all tag values for tags that are unselected
            # for value in self.tags[tag_name]['values']:
            #     self.tags[tag_name]['values'][value] = False
            #     if self.tag_with_all_values == tag_name:
            #         self.tag_with_all_values = None
        if self.output_type == 'dmg_by_asset_aggr':
            self.filter_dmg_by_asset_aggr()
        elif self.output_type in ('losses_by_asset_aggr',
                                  'avg_losses-stats_aggr'):
            self.filter_losses_by_asset_aggr()
        elif self.output_type in ['agg_curves-rlzs', 'agg_curves-stats']:
            self.filter_agg_curves()

    def update_selected_tag_values(self, tag_name):
        cbx = getattr(self, "%s_values_multiselect" % tag_name)
        for tag_value in cbx.get_selected_items():
            self.tags[tag_name]['values'][tag_value] = True
        for tag_value in cbx.get_unselected_items():
            self.tags[tag_name]['values'][tag_value] = False
        if self.output_type == 'dmg_by_asset_aggr':
            self.filter_dmg_by_asset_aggr()
        elif self.output_type in ('losses_by_asset_aggr',
                                  'avg_losses-stats_aggr',
                                  'agg_curves-rlzs',
                                  'agg_curves-stats'):
            if "*" in cbx.get_selected_items():
                self.tag_with_all_values = tag_name
            elif (self.tag_with_all_values == tag_name and
                    "*" in cbx.get_unselected_items()):
                self.tag_with_all_values = None
            if self.output_type in ('losses_by_asset_aggr',
                                    'avg_losses-stats_aggr'):
                self.filter_losses_by_asset_aggr()
            elif self.output_type in ['agg_curves-rlzs', 'agg_curves-stats']:
                self.filter_agg_curves()

    def get_list_selected_tags_str(self):
        selected_tags_str = ''
        for tag_name in self.tags:
            if self.tags[tag_name]['selected']:
                for tag_value in self.tags[tag_name]['values']:
                    if self.tags[tag_name]['values'][tag_value]:
                        selected_tags_str += '%s="%s" ' % (tag_name, tag_value)
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

    def set_output_type_and_its_gui(self, new_output_type):
        # clear type dependent widgets
        # NOTE: typeDepVLayout contains typeDepHLayout1 and typeDepHLayout2,
        #       that will be cleared recursively
        clear_widgets_from_layout(self.typeDepVLayout)
        clear_widgets_from_layout(self.table_layout)
        if hasattr(self, 'plot'):
            self.plot.clear()
            self.plot_canvas.show()
            self.plot_canvas.draw()
        if hasattr(self, 'exclude_no_dmg_ckb'):
            self.exclude_no_dmg_ckb.setParent(None)

        if new_output_type == 'hcurves':
            self.create_imt_selector()
            self.create_stats_multiselect()
            self.stats_multiselect.selection_changed.connect(
                self.refresh_feature_selection)
        elif new_output_type == 'agg_curves-rlzs':
            self.create_loss_type_selector()
            self.create_rlzs_multiselect()
            self.rlzs_multiselect.selection_changed.connect(
                lambda: self.draw_agg_curves(new_output_type))
        elif new_output_type == 'agg_curves-stats':
            self.create_loss_type_selector()
            self.create_stats_multiselect()
            # NOTE: tag_names_multiselect is created dynamically afterwards
            self.stats_multiselect.selection_changed.connect(
                # lambda: self.draw_agg_curves(new_output_type))
                self.filter_agg_curves)
        elif new_output_type == 'dmg_by_asset_aggr':
            self.create_loss_type_selector()
            self.create_rlz_selector()
            self.create_tag_names_multiselect()
            self.create_exclude_no_dmg_ckb()
        elif new_output_type in ('losses_by_asset_aggr',
                                 'avg_losses-stats_aggr'):
            self.create_loss_type_selector()
            self.create_tag_names_multiselect()
        elif new_output_type == 'uhs':
            self.create_stats_multiselect()
            self.stats_multiselect.selection_changed.connect(
                self.refresh_feature_selection)
        elif new_output_type == 'recovery_curves':
            if not IS_SCIPY_INSTALLED:
                warn_missing_package('scipy', self.iface.messageBar())
                self.output_type = None
                return
            self.create_approach_selector()
            self.create_n_simulations_spinbox()
            self.create_fields_multiselect()
            self.create_select_assets_at_same_site_chk()
            self.create_recalculate_on_the_fly_chk()
            self.create_recalculate_curve_btn()
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
        if output_type in ['agg_curves-rlzs', 'agg_curves-stats']:
            self.load_agg_curves(calc_id, session, hostname, output_type)
        elif output_type == 'dmg_by_asset_aggr':
            self.load_dmg_by_asset_aggr(
                calc_id, session, hostname, output_type)
        elif output_type in ('losses_by_asset_aggr',
                             'avg_losses-stats_aggr'):
            self.load_losses_by_asset_aggr(
                calc_id, session, hostname, output_type)
        else:
            raise NotImplementedError(output_type)

    def load_dmg_by_asset_aggr(self, calc_id, session, hostname, output_type):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            composite_risk_model_attrs = extract_npz(
                session, hostname, calc_id, 'composite_risk_model.attrs',
                message_bar=self.iface.messageBar())
        if composite_risk_model_attrs is None:
            return
        limit_states = composite_risk_model_attrs['limit_states']
        self.dmg_states = numpy.append(['no damage'], limit_states)
        self._get_tags(session, hostname, calc_id, self.iface.messageBar(),
                       with_star=False)

        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            rlzs_npz = extract_npz(
                session, hostname, calc_id, 'realizations',
                message_bar=self.iface.messageBar())
        if rlzs_npz is None:
            return
        # rlz[1] is the branch-path field
        rlzs = [rlz[1].decode('utf8').strip('"') for rlz in rlzs_npz['array']]
        self.rlz_cbx.blockSignals(True)
        self.rlz_cbx.clear()
        self.rlz_cbx.addItems(rlzs)
        self.rlz_cbx.blockSignals(False)

        loss_types = composite_risk_model_attrs['loss_types']
        self.loss_type_cbx.blockSignals(True)
        self.loss_type_cbx.clear()
        self.loss_type_cbx.addItems(loss_types)
        self.loss_type_cbx.blockSignals(False)

        self.tag_names_multiselect.clear()
        tag_names = sorted(self.tags.keys())
        self.tag_names_multiselect.add_unselected_items(tag_names)
        self.clear_tag_values_multiselects(tag_names)

        self.filter_dmg_by_asset_aggr()

    def _build_tags(self):
        # NOTE: shape_descr is like:
        # array([b'return_periods', b'stats', b'loss_types', b'NAME_1'],
        # dtype='|S14')
        tag_names = [str(tag_name, encoding='utf8')
                     for tag_name in self.agg_curves['shape_descr'][3:]]
        self.tags = {}
        for tag_idx, tag_name in enumerate(tag_names):
            self.tags[tag_name] = {
                'selected': True if tag_idx == 0 else False,
                'values': {
                    value.decode('utf8'): True if value_idx == 0 else False
                    for value_idx, value in enumerate(
                        self.agg_curves[tag_name])}}

    def clear_tag_values_multiselects(self, tag_names):
        for tag_name in tag_names:
            lbl_name = '%s_values_lbl' % tag_name
            cbx_name = '%s_values_multiselect' % tag_name
            lbl = getattr(self, lbl_name, None)
            cbx = getattr(self, cbx_name, None)
            if lbl is not None:
                delattr(self, lbl_name)
                lbl.setParent(None)
            if cbx is not None:
                delattr(self, cbx_name)
                cbx.setParent(None)

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
            # if tag_name in ['id', 'array']:
            if tag_name == 'array':
                continue
            for tag in tags_npz[tag_name]:
                tag = tag.decode('utf8')
                if tag[-1] != '?':
                    tags_list.append(tag)
        self.tags = {}
        for tag in tags_list:
            # tags are in the format 'city=Benicia' (tag_name=tag_value)
            tag_name, tag_value = tag.split('=')
            if tag_name not in self.tags:
                self.tags[tag_name] = {
                    'selected': False,
                    'values': {tag_value: False}}  # False means unselected
            else:
                # False means unselected
                self.tags[tag_name]['values'][tag_value] = False
            if with_star:
                self.tags[tag_name]['values']['*'] = False

    def load_losses_by_asset_aggr(
            self, calc_id, session, hostname, output_type):
        if self.output_type == 'losses_by_asset_aggr':
            with WaitCursorManager(
                    'Extracting...', message_bar=self.iface.messageBar()):
                rlzs_npz = extract_npz(
                    session, hostname, calc_id, 'realizations',
                    message_bar=self.iface.messageBar())
            if rlzs_npz is None:
                return
            self.rlzs = [rlz[1].decode('utf-8')  # branch_path
                         for rlz in rlzs_npz['array']]
        self._get_tags(session, hostname, calc_id, self.iface.messageBar(),
                       with_star=True)

        loss_types = get_loss_types(
            session, hostname, calc_id, self.iface.messageBar())
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
                self.stats = [str(stat, 'utf8') for stat in npz['stats']]

        self.tag_names_multiselect.clear()
        tag_names = sorted(self.tags.keys())
        self.tag_names_multiselect.add_unselected_items(tag_names)
        self.clear_tag_values_multiselects(tag_names)

        self.filter_losses_by_asset_aggr()

    def load_agg_curves(self, calc_id, session, hostname, output_type):
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.agg_curves = extract_npz(
                session, hostname, calc_id, output_type,
                message_bar=self.iface.messageBar())
        loss_types = [loss_type.decode('utf8')
                      for loss_type in self.agg_curves['loss_types']]
        self.loss_type_cbx.blockSignals(True)
        self.loss_type_cbx.clear()
        self.loss_type_cbx.addItems(loss_types)
        self.loss_type_cbx.blockSignals(False)
        if output_type == 'agg_curves-stats':
            self.stats = [stat.decode('utf8')
                          for stat in self.agg_curves['stats']]
            self.stats_multiselect.blockSignals(True)
            self.stats_multiselect.clear()
            self.stats_multiselect.add_selected_items(self.stats)
            self.stats_multiselect.blockSignals(False)
        elif output_type == 'agg_curves-rlzs':
            rlzs = ["Rlz %s" % rlz
                    for rlz in range(self.agg_curves['array'].shape[1])]
            self.rlzs_multiselect.blockSignals(True)
            self.rlzs_multiselect.clear()
            self.rlzs_multiselect.add_selected_items(rlzs)
            self.rlzs_multiselect.blockSignals(False)
        else:
            raise NotImplementedError(
                'Unable to draw outputs of type %s' % output_type)
            return
        if ('aggregate_by' in self.agg_curves
                and len(self.agg_curves['aggregate_by']) > 0):
            self.create_tag_names_multiselect()
            self._build_tags()
            self.update_selected_tag_names()
            self.tag_names_multiselect.clear()
            for tag_name in self.tags:
                if self.tags[tag_name]['selected']:
                    self.tag_names_multiselect.add_selected_items([tag_name])
                else:
                    self.tag_names_multiselect.add_unselected_items([tag_name])
        self.filter_agg_curves()

    def _get_idxs(self):
        if self.output_type == 'agg_curves-rlzs':
            rlzs_or_stats = list(
                self.rlzs_multiselect.get_selected_items())
        else:  # agg_curves-stats
            rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        loss_type_idx = self.loss_type_cbx.currentIndex()
        rlzs_or_stats_idxs = []
        if self.output_type == 'agg_curves-rlzs':
            for rlz_idx in range(self.agg_curves['array'].shape[1]):
                if "Rlz %s" % rlz_idx in rlzs_or_stats:
                    rlzs_or_stats_idxs.append(rlz_idx)
        else:  # agg_curves-stats
            for stat_idx, stat in enumerate(self.agg_curves['stats']):
                if stat.decode('utf8') in rlzs_or_stats:
                    rlzs_or_stats_idxs.append(stat_idx)
        if ('aggregate_by' in self.agg_curves
                and len(self.agg_curves['aggregate_by']) > 0):
            tag_name_idxs = {}
            tag_value_idxs = {}
            if hasattr(self, 'tags'):
                for tag_name in self.tags:
                    tag_name_idx = list(self.agg_curves['aggregate_by']).index(
                        tag_name.encode('utf8'))
                    tag_name_idxs[tag_name] = tag_name_idx
                    tag_value_idxs[tag_name] = []
                    # if not self.tags[tag_name]['selected']:
                    #     continue
                    for tag_value in self.tags[tag_name]['values']:
                        if self.tags[tag_name]['values'][tag_value]:
                            # (if it is selected)
                            tag_value_idx = list(
                                self.agg_curves[tag_name]).index(
                                    tag_value.encode('utf8'))
                            tag_value_idxs[tag_name].append(tag_value_idx)
            else:
                for tag in self.agg_curves['aggregate_by']:
                    tag_name = tag.decode('utf8')
                    # FIXME: check if currentIndex is ok
                    tag_value_idx = getattr(
                        self,
                        "%s_values_multiselect" % tag_name).currentIndex()
                    tag_value_idxs[tag_name] = tag_value_idx
        else:
            tag_name_idxs = None
            tag_value_idxs = None
        return rlzs_or_stats_idxs, loss_type_idx, tag_name_idxs, tag_value_idxs

    def draw_agg_curves(self, output_type):
        if output_type == 'agg_curves-rlzs':
            if self.rlzs_multiselect is None:
                rlzs_or_stats = []
            else:
                rlzs_or_stats = list(
                    self.rlzs_multiselect.get_selected_items())
        elif output_type == 'agg_curves-stats':
            rlzs_or_stats = list(
                self.stats_multiselect.get_selected_items())
        else:
            raise NotImplementedError(
                'Can not draw outputs of type %s' % output_type)
            return
        loss_type = self.loss_type_cbx.currentText()
        loss_type_idx = self.loss_type_cbx.currentIndex()
        abscissa = self.agg_curves['return_periods']
        if output_type in ['agg_curves-rlzs', 'agg_curves-stats']:
            (rlzs_or_stats_idxs, loss_type_idx, tag_name_idxs,
             tag_value_idxs) = self._get_idxs()
            ordinates = self.agg_curves['array']
            unit = self.agg_curves['units'][loss_type_idx]
        self.plot.clear()
        if not ordinates.any():  # too much filtering
            self.plot_canvas.draw()
            return
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
        if output_type == 'agg_curves-rlzs':
            tup = (slice(None), rlzs_or_stats_idxs, loss_type_idx)
            if tag_value_idxs is not None:
                value_idxs = tag_value_idxs.values()
                tup += tuple(value_idxs)
            ordinates = self.agg_curves['array'][tup]
            for ys, rlz_or_stat in zip(
                    ordinates.T, rlzs_or_stats):
                rlz_or_stat_idx = rlzs_or_stats.index(rlz_or_stat)
                self.plot.plot(
                    abscissa,
                    ys,
                    # color=color_hex[rlz_or_stat_idx],
                    linestyle=line_style[rlz_or_stat_idx],
                    marker=marker[rlz_or_stat_idx],
                    label="Rlz_%s" % rlz_or_stat_idx
                )
        elif output_type == 'agg_curves-stats':
            if tag_value_idxs is None:
                tup = (slice(None), rlzs_or_stats_idxs, loss_type_idx)
                ordinates = self.agg_curves['array'][tup]
                for ys, rlz_or_stat in zip(
                        ordinates.T, rlzs_or_stats):
                    rlz_or_stat_idx = rlzs_or_stats.index(rlz_or_stat)
                    self.plot.plot(
                        abscissa,
                        ys,
                        # color=color_hex[rlz_or_stat_idx],
                        linestyle=line_style[rlz_or_stat_idx],
                        marker=marker[rlz_or_stat_idx],
                        label=rlz_or_stat,
                    )
            else:
                for tag_name in tag_value_idxs:
                    if not self.tags[tag_name]['selected']:
                        continue
                    for value_idx in tag_value_idxs[tag_name]:
                        tag_value = self.agg_curves[
                            tag_name][value_idx].decode('utf8')
                        tup = (slice(None), rlzs_or_stats_idxs, loss_type_idx)
                        tag_name_idx = tag_name_idxs[tag_name]
                        for t_name in tag_name_idxs:
                            if tag_name_idxs[t_name] == tag_name_idx:
                                tup += (value_idx,)
                            else:
                                tup += (tag_value_idxs[t_name],)
                        try:
                            curr_ordinates = ordinates[tup]
                        except IndexError:
                            log_msg('For each unselected tag, one and only one'
                                    ' value must be selected.', level='C',
                                    message_bar=self.iface.messageBar())
                            self.plot_canvas.draw()
                            return
                        for ys, rlz_or_stat in zip(
                                curr_ordinates.T, rlzs_or_stats):
                            rlz_or_stat_idx = rlzs_or_stats.index(rlz_or_stat)
                            self.plot.plot(
                                abscissa,
                                ys,
                                # color=color_hex[rlz_or_stat_idx],
                                linestyle=line_style[rlz_or_stat_idx],
                                marker=marker[rlz_or_stat_idx],
                                # label=rlz_or_stat,
                                label="%s (%s)" % (tag_value, rlz_or_stat)
                            )
        self.plot.set_xscale('log')
        self.plot.set_yscale('linear')
        self.plot.set_xlabel('Return period (years)')
        self.plot.set_ylabel('Loss (%s)' % unit.decode('utf8'))
        title = 'Loss type: %s' % loss_type
        self.plot.set_title(title)
        self.plot.grid(which='both')
        if 1 <= len(rlzs_or_stats) <= 20:
            location = 'upper left'
            self.legend = self.plot.legend(
                loc=location, fancybox=True, shadow=True, fontsize='small')
        self.plot_canvas.draw()

    def draw_dmg_by_asset_aggr(self):
        '''
        Plots the total damage distribution
        '''
        if len(self.dmg_by_asset_aggr['array']) == 0:
            msg = 'No assets satisfy the selected criteria'
            log_msg(msg, level='W', message_bar=self.iface.messageBar())
            self.plot.clear()
            self.plot_canvas.draw()
            return
        rlz = self.rlz_cbx.currentIndex()
        # TODO: re-add error bars when stddev will become available again
        # means = self.dmg_by_asset_aggr['array'][rlz]['mean']
        # stddevs = self.dmg_by_asset_aggr['array'][rlz]['stddev']
        means = self.dmg_by_asset_aggr['array'][rlz]
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

    def _to_2d(self, array):
        # convert 1d array into 2d, unless already 2d
        if len(array.shape) == 1:
            array = array[None, :]
        return array

    def draw_losses_by_asset_aggr(self):
        self.plot_canvas.hide()
        clear_widgets_from_layout(self.table_layout)
        losses_array = self.losses_by_asset_aggr['array']
        losses_array = self._to_2d(losses_array)
        tags = None
        try:
            tags = [tag.decode('utf8')
                    for tag in self.losses_by_asset_aggr['tags']]
        except KeyError:
            pass
        nrows, ncols = losses_array.shape
        table = QTableWidget(nrows, ncols)
        table.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        if self.output_type == 'losses_by_asset_aggr':
            table.setHorizontalHeaderLabels(self.rlzs)
        else:  # self.output_type == 'avg_losses-stats_aggr'
            table.setHorizontalHeaderLabels(self.stats)
        if tags is not None:
            # tags are like
            # array(['taxonomy=Wood',
            #        'taxonomy=Adobe',
            #        'taxonomy=Stone-Masonry',
            #        'taxonomy=Unreinforced-Brick-Masonry',
            #        'taxonomy=Concrete'], dtype='|S35')
            tag_values = [tag.split('=')[1] for tag in tags]
            table.setVerticalHeaderLabels(tag_values)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for row in range(nrows):
            for col in range(ncols):
                table.setItem(
                    row, col, QTableWidgetItem(str(losses_array[row, col])))
        table.resizeColumnsToContents()
        self.table_layout.addWidget(table)

    def draw(self):
        self.plot.clear()
        gids = dict()
        if self.stats_multiselect is not None:
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

        for rlz_or_stat in selected_rlzs_or_stats:
            for i, (site, curve) in enumerate(
                    self.current_selection[rlz_or_stat].items()):
                # NOTE: we associated the same cumulative curve to all the
                # selected points (ugly), and here we need to get only one
                if self.output_type == 'recovery_curves' and i > 0:
                    break
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
                if self.output_type == 'recovery_curves':
                    self.create_annot()
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
        elif self.output_type == 'recovery_curves':
            self.plot.set_xscale('linear')
            self.plot.set_yscale('linear')
            self.plot.set_xlabel('Time [days]')
            self.plot.set_ylabel('Normalized recovery level [%]')
            self.plot.set_ylim((0.0, 105.0))
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
            else:  # recovery curves
                try:
                    del self.current_selection[None][fid]
                except KeyError:
                    pass
        for fid in selected:
            if hasattr(self, 'rlzs_or_stats'):
                for rlz_or_stat in self.rlzs_or_stats:
                    self.current_selection[rlz_or_stat] = {}
            else:  # recovery curves
                self.current_selection[None] = {}
        if self.output_type == 'recovery_curves':
            if len(selected) > 0:
                self.redraw_recovery_curve(selected)
            return
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

    def redraw_recovery_curve(self, selected):
        request = QgsFeatureRequest().setFlags(
            QgsFeatureRequest.NoGeometry).setFilterFids(selected)
        features = list(self.iface.activeLayer().getFeatures(request))
        approach = self.approach_cbx.currentText()
        recovery = RecoveryModeling(features, approach, self.iface)
        integrate_svi = False
        probs_field_names = self.fields_multiselect.get_selected_items()
        zonal_dmg_by_asset_probs, zonal_asset_refs = \
            recovery.collect_zonal_data(probs_field_names, integrate_svi)
        n_simulations = self.n_simulations_sbx.value()
        recovery_function = \
            recovery.generate_community_level_recovery_curve(
                'ALL', zonal_dmg_by_asset_probs, zonal_asset_refs,
                n_simulations=n_simulations)
        self.current_abscissa = list(range(len(recovery_function)))
        color = QColor('black')
        color_hex = color.name()
        # NOTE: differently with respect to the other approaches, we are
        # associating only a single feature with the cumulative recovery curve.
        # It might be a little ugly, but otherwise it would be inefficient.
        if len(features) > 0:
            self.current_selection[None] = {}
            self.current_selection[None][features[0].id()] = {
                'abscissa': self.current_abscissa,
                'ordinates': [value * 100 for value in recovery_function],
                'color': color_hex,
                'line_style': "-",  # solid
                'marker': "None",
            }
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
            elif self.output_type == 'recovery_curves':
                fill_fields_multiselect(
                    self.fields_multiselect, self.iface.activeLayer())
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
            point = feat.geometry().asPoint()
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
        if self.imt_cbx is not None:
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
        if self.loss_type_cbx is not None:
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
        if self.output_type == 'recovery_curves':
            vis = self.annot.get_visible()
            if event.inaxes == self.plot:
                if not hasattr(self, 'line'):
                    return
                cont, ind = self.line.contains(event)
                if cont:
                    self.update_annot(ind)
                    self.annot.set_visible(True)
                    self.plot_figure.canvas.draw_idle()
                else:
                    if vis:
                        self.annot.set_visible(False)
                        self.plot_figure.canvas.draw_idle()

    def on_container_hover(self, event, container):
        if self.output_type in (
                OQ_EXTRACT_TO_VIEW_TYPES | set(['recovery_curves'])):
            # NOTE: recovery curves correspond to many points in the map, but
            # only one id can be retrieved from the line. Highlighting only one
            # of the points might be misleading, so it's probably better to
            # avoid highlighting anything at all in such case.
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

    def on_imt_changed(self):
        self.was_imt_switched = True
        self.redraw_current_selection()

    @pyqtSlot(str)
    def on_loss_type_changed(self, loss_type):
        if self.output_type == 'agg_curves-rlzs':
            self.filter_agg_curves()
            # self.draw_agg_curves(self.output_type)
        elif self.output_type == 'agg_curves-stats':
            self.filter_agg_curves()
        elif self.output_type == 'dmg_by_asset_aggr':
            self.filter_dmg_by_asset_aggr()
        elif self.output_type in ('losses_by_asset_aggr',
                                  'avg_losses-stats_aggr'):
            self.filter_losses_by_asset_aggr()
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

    def on_rlz_changed(self):
        self.filter_dmg_by_asset_aggr()

    @pyqtSlot(int)
    def on_exclude_no_dmg_ckb_state_changed(self, state):
        self.filter_dmg_by_asset_aggr()

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
        elif self.output_type in ['agg_curves-rlzs', 'agg_curves-stats']:
            loss_type = self.loss_type_cbx.currentText()
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/%s_%s_%s.csv' % (self.output_type,
                                        loss_type,
                                        self.calc_id)),
                '*.csv')
        elif self.output_type in ('dmg_by_asset_aggr',
                                  'losses_by_asset_aggr',
                                  'avg_losses-stats_aggr'):
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/%s_%s.csv' % (self.output_type, self.calc_id)),
                '*.csv')
        elif self.output_type == 'recovery_curves':
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.tr('Export data'),
                os.path.expanduser(
                    '~/recovery_curves_%s.csv' %
                    self.approach_cbx.currentText()),
                '*.csv')
        if filename:
            self.write_export_file(filename)

    def write_export_file(self, filename):
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
        if self.output_type == 'recovery_curves':
            approach = self.approach_cbx.currentText()
            n_simulations = self.n_simulations_sbx.value()
            asset_ids = [
                feat['id']
                for feat in self.iface.activeLayer().selectedFeatures()]
            csv_headline += "# Recovery time approach: %s\r\n" % approach
            csv_headline += "# Number of simulations: %s\r\n" % n_simulations
            csv_headline += "# Asset ids: %s\r\n" % ", ".join(asset_ids)
        with open(filename, 'w', newline='') as csv_file:
            csv_file.write(csv_headline)
            writer = csv.writer(csv_file)
            if self.output_type == 'recovery_curves':
                headers = ['lon', 'lat']
                headers.extend(self.current_abscissa)
                writer.writerow(headers)
                # NOTE: taking the first element, because they are all the
                # same
                feature = self.iface.activeLayer().selectedFeatures()[0]
                lon = feature.geometry().asPoint().x()
                lat = feature.geometry().asPoint().y()
                values = list(self.current_selection[None].values())[0]
                row = [lon, lat]
                if values:
                    row.extend(values['ordinates'])
                writer.writerow(row)
            elif self.output_type in ['hcurves', 'uhs']:
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
            elif self.output_type == 'agg_curves-rlzs':
                (rlzs_idxs, loss_type_idx, tag_name_idxs,
                    tag_value_idxs) = self._get_idxs()
                if tag_name_idxs is not None:
                    tag_values = {}
                    for tag_name in tag_value_idxs:
                        tag_values[tag_name] = self.agg_curves[tag_name][
                            tag_value_idxs[tag_name]]
                    tag_values_list = [
                        "%s=%s" % (tname, tag_values[tname].decode('utf8'))
                        for tname in tag_values]
                    csv_file.write(
                        "# Tags: %s\r\n" % ", ".join(tag_values_list))
                rlzs = list(self.rlzs_multiselect.get_selected_items())
                headers = ['return_period']
                headers.extend(rlzs)
                writer.writerow(headers)
                # loss_type_idx = self.loss_type_cbx.currentIndex()
                for i, return_period in enumerate(
                        self.agg_curves['return_periods']):
                    tup = (slice(None), rlzs_idxs, loss_type_idx)
                    if tag_value_idxs is not None:
                        tup += tuple(tag_value_idxs.values())
                    values = self.agg_curves['array'][tup]
                    row = [return_period]
                    row.extend([value for value in values[i]])
                    writer.writerow(row)
            elif self.output_type == 'agg_curves-stats':
                stats = list(self.stats_multiselect.get_selected_items())
                loss_type = self.loss_type_cbx.currentText()
                loss_type_idx = self.loss_type_cbx.currentIndex()
                csv_file.write(
                    "# Loss type: %s\r\n" % loss_type)
                if ('aggregate_by' in self.agg_curves
                        and len(self.agg_curves['aggregate_by']) > 0):
                    csv_file.write(
                        "# Tags: %s\r\n" % (
                            self.get_list_selected_tags_str() or 'None'))
                headers = ['return_period']
                (rlzs_or_stats_idxs, loss_type_idx, tag_name_idxs,
                    tag_value_idxs) = self._get_idxs()
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
                    headers.extend(stats)
                writer.writerow(headers)
                for return_period_idx, return_period in enumerate(
                        self.agg_curves['return_periods']):
                    row = [return_period]
                    if has_single_tag_value or has_single_tag_value is None:
                        tup = (return_period_idx, rlzs_or_stats_idxs,
                               loss_type_idx)
                    else:
                        # FIXME: using only the first stat
                        tup = (return_period_idx, rlzs_or_stats_idxs[0],
                               loss_type_idx)
                    if tag_value_idxs is not None:
                        tup += tuple(tag_value_idxs.values())
                    values = self.agg_curves['array'][tup]
                    try:
                        row.extend(values)
                    except TypeError:  # it is a single value instead of list
                        row.append(values)
                    writer.writerow(row)
            elif self.output_type == 'dmg_by_asset_aggr':
                csv_file.write(
                    "# Realization: %s\r\n" % self.rlz_cbx.currentText())
                csv_file.write(
                    "# Loss type: %s\r\n" % self.loss_type_cbx.currentText())
                csv_file.write(
                    "# Tags: %s\r\n" % (
                        self.get_list_selected_tags_str() or 'None'))
                headers = self.dmg_states
                writer.writerow(headers)
                values = self.dmg_by_asset_aggr[
                    'array'][self.rlz_cbx.currentIndex()]
                writer.writerow(values)
            elif self.output_type in ('losses_by_asset_aggr',
                                      'avg_losses-stats_aggr'):
                csv_file.write(
                    "# Loss type: %s\r\n" % self.loss_type_cbx.currentText())
                csv_file.write(
                    "# Tags: %s\r\n" % (
                        self.get_list_selected_tags_str() or 'None'))
                try:
                    tags = [tag.decode('utf8')
                            for tag in self.losses_by_asset_aggr['tags']]
                    tag = tags[0]
                    # a tag is like 'taxonomy=Wood'
                    tag_name = tag.split('=')[0]
                    headers = [tag_name]
                except KeyError:
                    tags = None
                    headers = []
                if self.output_type == 'losses_by_asset_aggr':
                    headers.extend(self.rlzs)
                else:  # self.output_type == 'avg_losses-stats_aggr':
                    headers.extend(self.stats)
                writer.writerow(headers)
                losses_array = self.losses_by_asset_aggr['array']
                losses_array = self._to_2d(losses_array)
                if tags is not None:
                    for row_idx, row in enumerate(
                            self.losses_by_asset_aggr['array']):
                        tag = tags[row_idx]
                        # a tag is like 'taxonomy=Wood'
                        tag_value = tag.split('=')[1]
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
        if self.output_type in OQ_TO_LAYER_TYPES | set('recovery_curves'):
            self.layer_changed()
        if self.output_type == 'agg_curves-rlzs':
            self.draw_agg_curves(self.output_type)
        elif self.output_type == 'agg_curves-stats':
            # self.draw_agg_curves(self.output_type)
            self.filter_agg_curves()
        elif self.output_type == 'dmg_by_asset_aggr':
            self.filter_dmg_by_asset_aggr()

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
