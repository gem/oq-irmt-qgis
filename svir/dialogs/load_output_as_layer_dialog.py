# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

import os
import copy
from random import randrange
from osgeo import ogr
from qgis.core import (QgsVectorLayer,
                       QgsProject,
                       QgsStyle,
                       QgsSymbol,
                       QgsOuterGlowEffect,
                       QgsSingleSymbolRenderer,
                       QgsGradientColorRamp,
                       QgsGraduatedSymbolRenderer,
                       QgsRuleBasedRenderer,
                       QgsFillSymbol,
                       QgsWkbTypes,
                       QgsMapLayer,
                       QgsMarkerSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer,
                       QgsApplication,
                       QgsExpression,
                       NULL,
                       QgsSimpleMarkerSymbolLayerBase,
                       Qgis,
                       QgsRectangle,
                       )
from qgis.gui import QgsSublayersDialog
from qgis.PyQt.QtCore import pyqtSignal, QDir, QSettings, QFileInfo, Qt
from qgis.PyQt.QtWidgets import (
                                 QDialogButtonBox,
                                 QDialog,
                                 QDoubleSpinBox,
                                 QFileDialog,
                                 QComboBox,
                                 QSpinBox,
                                 QLabel,
                                 QCheckBox,
                                 QHBoxLayout,
                                 QVBoxLayout,
                                 QToolButton,
                                 QGroupBox,
                                 )
from qgis.PyQt.QtGui import QColor
from svir.calculations.calculate_utils import add_attribute
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats)
from svir.utilities.shared import (OQ_CSV_TO_LAYER_TYPES,
                                   OQ_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_LAYER_TYPES,
                                   RAMP_EXTREME_COLORS,
                                   )
from svir.utilities.utils import (get_ui_class,
                                  get_style,
                                  log_msg,
                                  tr,
                                  get_file_size,
                                  get_irmt_version,
                                  write_metadata_to_layer,
                                  )
from svir.tasks.extract_npz_task import TaskCanceled

FORM_CLASS = get_ui_class('ui_load_output_as_layer.ui')


class LoadOutputAsLayerDialog(QDialog, FORM_CLASS):
    """
    Dialog to load an oq-engine output as layer
    """
    init_done = pyqtSignal(QDialog)
    loading_completed = pyqtSignal(QDialog)
    loading_exception = pyqtSignal(QDialog, Exception)

    def __init__(self, drive_engine_dlg, iface, viewer_dock,
                 session, hostname, calc_id, output_type=None,
                 path=None, mode=None, zonal_layer_path=None,
                 engine_version=None, calculation_mode=None):
        # sanity check
        if output_type not in OQ_TO_LAYER_TYPES:
            raise NotImplementedError(output_type)
        self.drive_engine_dlg = drive_engine_dlg
        self.iface = iface
        self.viewer_dock = viewer_dock
        self.path = path
        self.session = session
        self.hostname = hostname
        self.calc_id = calc_id
        self.output_type = output_type
        self.mode = mode  # if 'testing' it will avoid some user interaction
        self.zonal_layer_path = zonal_layer_path
        self.engine_version = engine_version
        self.calculation_mode = calculation_mode
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all user options are set
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.oqparam = self.drive_engine_dlg.get_oqparam()

    def on_extract_error(self, exception):
        if isinstance(exception, TaskCanceled):
            msg = 'Data extraction canceled'
            log_msg(msg, level='W', message_bar=self.iface.messageBar())
        else:
            log_msg('Unable to complete data extraction', level='C',
                    message_bar=self.iface.messageBar(), exception=exception)
        self.reject()

    def finalize_init(self, extracted_npz):
        self.npz_file = extracted_npz
        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()
        self.show()
        self.init_done.emit(self)

    def create_num_sites_indicator(self):
        self.num_sites_msg = 'Number of sites: %s'
        self.num_sites_lbl = QLabel(self.num_sites_msg % '')
        self.vlayout.addWidget(self.num_sites_lbl)

    def create_file_size_indicator(self):
        self.file_size_msg = 'File size: %s'
        self.file_size_lbl = QLabel(self.file_size_msg % '')
        self.vlayout.addWidget(self.file_size_lbl)

    def create_single_layer_ckb(self):
        self.load_single_layer_ckb = QCheckBox(
            'Load one layer containing all hazard maps')
        self.vlayout.addWidget(self.load_single_layer_ckb)

    def create_load_one_layer_per_stat_ckb(self):
        self.load_one_layer_per_stat_ckb = QCheckBox(
            'Load one layer per realization or statistic')
        self.vlayout.addWidget(self.load_one_layer_per_stat_ckb)

    def create_min_mag_dsb(self, min_mag=4.0):
        self.min_mag_lbl = QLabel()
        self.min_mag_dsb = QDoubleSpinBox(self)
        self.min_mag_dsb.setRange(0, 10)
        self.min_mag_dsb.setDecimals(1)
        self.min_mag_dsb.setSingleStep(0.1)
        self.min_mag_dsb.setValue(min_mag)
        self.vlayout.addWidget(self.min_mag_lbl)
        self.vlayout.addWidget(self.min_mag_dsb)
        # NOTE: if we don't modify the text of the label after adding the
        # widget to the layout, the adjustSize does not work properly, for some
        # unknown reason
        self.min_mag_lbl.setText('Minimum magnitude')

    def create_rlz_or_stat_selector(self, all_ckb=False, label='Realization'):
        self.rlz_or_stat_lbl = QLabel(label)
        self.rlz_or_stat_cbx = QComboBox()
        self.rlz_or_stat_cbx.setEnabled(False)
        self.rlz_or_stat_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_or_stat_changed)
        if all_ckb:
            self.load_all_rlzs_or_stats_chk = QCheckBox(
                'Load all realizations')
            self.load_all_rlzs_or_stats_chk.stateChanged[int].connect(
                self.on_load_all_rlzs_or_stats_chk_stateChanged)
            self.vlayout.addWidget(self.load_all_rlzs_or_stats_chk)
        self.vlayout.addWidget(self.rlz_or_stat_lbl)
        self.vlayout.addWidget(self.rlz_or_stat_cbx)

    def on_load_all_rlzs_or_stats_chk_stateChanged(self, state):
        self.rlz_or_stat_cbx.setEnabled(state == Qt.Unchecked)

    def create_selector(
            self, name, label_text, filter_ckb=False, add_to_layout=None,
            on_text_changed=None):
        if add_to_layout is not None:
            layout = add_to_layout
        else:
            layout = self.vlayout
        setattr(self, "%s_lbl" % name, QLabel(label_text))
        setattr(self, "%s_cbx" % name, QComboBox())
        lbl = getattr(self, "%s_lbl" % name)
        cbx = getattr(self, "%s_cbx" % name)
        cbx.setDisabled(filter_ckb)
        if on_text_changed is not None:
            cbx.currentTextChanged['QString'].connect(on_text_changed)
        if filter_ckb:
            setattr(self, "filter_by_%s_ckb" % name,
                    QCheckBox('Filter by %s' % name))
            filter_ckb = getattr(self, "filter_by_%s_ckb" % name)

            def on_load_all_ckb_changed():
                cbx.setEnabled(filter_ckb.isChecked())

            filter_ckb.stateChanged[int].connect(on_load_all_ckb_changed)
            filter_ckb.setChecked(False)
            layout.addWidget(filter_ckb)
        layout.addWidget(lbl)
        layout.addWidget(cbx)

    def create_imt_selector(self, all_ckb=False):
        self.imt_lbl = QLabel('Intensity Measure Type')
        self.imt_cbx = QComboBox()
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        if all_ckb:
            self.load_all_imts_chk = QCheckBox('Load all IMTs')
            self.load_all_imts_chk.stateChanged[int].connect(
                self.on_load_all_imts_chk_stateChanged)
            self.vlayout.addWidget(self.load_all_imts_chk)
        self.vlayout.addWidget(self.imt_lbl)
        self.vlayout.addWidget(self.imt_cbx)

    def on_load_all_imts_chk_stateChanged(self, state):
        self.imt_cbx.setEnabled(state == Qt.Unchecked)

    def create_poe_selector(self, all_ckb=False):
        self.poe_lbl = QLabel('Probability of Exceedance')
        self.poe_cbx = QComboBox()
        self.poe_cbx.setEnabled(False)
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        if all_ckb:
            self.load_all_poes_chk = QCheckBox('Load all PoEs')
            self.load_all_poes_chk.stateChanged[int].connect(
                self.on_load_all_poes_chk_stateChanged)
            self.vlayout.addWidget(self.load_all_poes_chk)
        self.vlayout.addWidget(self.poe_lbl)
        self.vlayout.addWidget(self.poe_cbx)

    def on_load_all_poes_chk_stateChanged(self, state):
        self.poe_cbx.setEnabled(state == Qt.Unchecked)

    def create_loss_type_selector(self):
        self.loss_type_lbl = QLabel('Loss Category')
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.setEnabled(False)
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.vlayout.addWidget(self.loss_type_lbl)
        self.vlayout.addWidget(self.loss_type_cbx)

    def create_damage_or_consequences_selector(self):
        self.damage_or_consequences_lbl = QLabel('Type')
        self.damage_or_consequences_cbx = QComboBox()
        self.damage_or_consequences_cbx.currentTextChanged['QString'].connect(
            self.on_damage_or_consequences_changed)
        self.vlayout.addWidget(self.damage_or_consequences_lbl)
        self.vlayout.addWidget(self.damage_or_consequences_cbx)

    def create_eid_selector(self):
        self.eid_lbl = QLabel('Event ID')
        self.eid_sbx = QSpinBox()
        self.eid_sbx.setEnabled(False)
        self.vlayout.addWidget(self.eid_lbl)
        self.vlayout.addWidget(self.eid_sbx)

    def create_dmg_state_selector(self):
        self.dmg_state_lbl = QLabel('Damage State')
        self.dmg_state_cbx = QComboBox()
        self.dmg_state_cbx.setEnabled(False)
        self.dmg_state_cbx.currentIndexChanged['QString'].connect(
            self.on_dmg_state_changed)
        self.vlayout.addWidget(self.dmg_state_lbl)
        self.vlayout.addWidget(self.dmg_state_cbx)

    def create_consequence_selector(self):
        self.consequence_lbl = QLabel('Consequence Type')
        self.consequence_cbx = QComboBox()
        self.consequence_cbx.setEnabled(False)
        self.vlayout.addWidget(self.consequence_lbl)
        self.vlayout.addWidget(self.consequence_cbx)

    def create_taxonomy_selector(self):
        self.taxonomy_lbl = QLabel('Taxonomy')
        self.taxonomy_cbx = QComboBox()
        self.taxonomy_cbx.setEnabled(False)
        self.vlayout.addWidget(self.taxonomy_lbl)
        self.vlayout.addWidget(self.taxonomy_cbx)

    def create_style_by_selector(self):
        self.style_by_lbl = QLabel('Style By')
        self.style_by_cbx = QComboBox()
        self.vlayout.addWidget(self.style_by_lbl)
        self.vlayout.addWidget(self.style_by_cbx)

    def create_load_selected_only_ckb(self):
        self.load_selected_only_ckb = QCheckBox("Load only the selected items")
        self.load_selected_only_ckb.setChecked(True)
        self.vlayout.addWidget(self.load_selected_only_ckb)

    def create_show_return_period_ckb(self):
        self.show_return_period_chk = QCheckBox(
            "Show the return period in layer names")
        self.show_return_period_chk.setChecked(False)
        self.vlayout.addWidget(self.show_return_period_chk)

    def create_aggregate_by_site_ckb(self):
        self.aggregate_by_site_ckb = QCheckBox("Aggregate by site")
        self.aggregate_by_site_ckb.setChecked(True)
        self.vlayout.addWidget(self.aggregate_by_site_ckb)

    def create_zonal_layer_selector(self, discard_nonmatching=True):
        self.added_zonal_layer = None
        self.zonal_layer_gbx = QGroupBox()
        self.zonal_layer_gbx.setTitle('Aggregate by zone')
        self.zonal_layer_gbx.setCheckable(True)
        self.zonal_layer_gbx.setChecked(False)
        self.zonal_layer_gbx_v_layout = QVBoxLayout()
        self.zonal_layer_gbx.setLayout(self.zonal_layer_gbx_v_layout)
        self.zonal_layer_cbx = QComboBox()
        self.zonal_layer_cbx.addItem('')
        self.zonal_layer_lbl = QLabel('Zonal layer')
        self.zonal_layer_tbn = QToolButton()
        self.zonal_layer_tbn.setText('...')
        self.discard_nonmatching_chk = QCheckBox(
            'Discard zones with no points')
        self.discard_nonmatching_chk.setChecked(discard_nonmatching)
        self.zonal_layer_h_layout = QHBoxLayout()
        self.zonal_layer_h_layout.addWidget(self.zonal_layer_cbx)
        self.zonal_layer_h_layout.addWidget(self.zonal_layer_tbn)
        self.zonal_layer_gbx_v_layout.addWidget(self.zonal_layer_lbl)
        self.zonal_layer_gbx_v_layout.addLayout(self.zonal_layer_h_layout)
        self.zonal_layer_gbx_v_layout.addWidget(self.discard_nonmatching_chk)
        self.vlayout.addWidget(self.zonal_layer_gbx)
        self.zonal_layer_tbn.clicked.connect(self.open_load_zonal_layer_dialog)
        self.zonal_layer_cbx.currentIndexChanged[int].connect(
            self.on_zonal_layer_cbx_currentIndexChanged)
        self.zonal_layer_gbx.toggled[bool].connect(
            self.on_zonal_layer_gbx_toggled)
        self.iface.layerTreeView().currentLayerChanged.connect(
            self.on_currentLayerChanged)

    def on_currentLayerChanged(self):
        self.pre_populate_zonal_layer_cbx()

    def pre_populate_zonal_layer_cbx(self):
        # populate cbx only with vector layers containing polygons
        self.zonal_layer_cbx.clear()
        for key, layer in QgsProject.instance().mapLayers().items():
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.zonal_layer_cbx.addItem(layer.name())
                self.zonal_layer_cbx.setItemData(
                    self.zonal_layer_cbx.count()-1, layer.id())
        if self.added_zonal_layer is not None:
            self.zonal_layer_cbx.setCurrentIndex(
                self.zonal_layer_cbx.findData(self.added_zonal_layer.id()))
        self.zonal_layer_gbx.setChecked(
            self.zonal_layer_cbx.currentIndex() != -1)

    def on_zonal_layer_cbx_currentIndexChanged(self, new_index):
        self.zonal_layer = None
        if not self.zonal_layer_cbx.currentText():
            if self.zonal_layer_gbx.isChecked():
                self.ok_button.setEnabled(False)
            return
        zonal_layer_id = self.zonal_layer_cbx.itemData(new_index)
        self.zonal_layer = QgsProject.instance().mapLayer(zonal_layer_id)
        self.set_ok_button()

    def on_zonal_layer_gbx_toggled(self, is_checked):
        if is_checked and not self.zonal_layer_cbx.currentText():
            self.ok_button.setEnabled(False)
        else:
            self.set_ok_button()

    def on_output_type_changed(self):
        if self.output_type in OQ_TO_LAYER_TYPES:
            self.create_load_selected_only_ckb()
        self.set_ok_button()

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file[self.rlz_or_stat_cbx.currentData()]
        self.set_ok_button()

    def on_loss_type_changed(self):
        self.set_ok_button()

    def on_imt_changed(self):
        self.set_ok_button()

    def on_poe_changed(self):
        self.set_ok_button()

    def on_eid_changed(self):
        self.set_ok_button()

    def on_dmg_state_changed(self):
        self.set_ok_button()

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.show_num_sites()

    def get_taxonomies(self):
        raise NotImplementedError()

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = [key for key in sorted(self.npz_file)
                              if key not in ('imtls', 'array', 'extra')]
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        if len(self.rlzs_or_stats) == 1:
            self.rlz_or_stat_cbx.addItem('mean', self.rlzs_or_stats[0])
        else:
            for rlz_or_stat in self.rlzs_or_stats:
                self.rlz_or_stat_cbx.addItem(rlz_or_stat, rlz_or_stat)

    def populate_loss_type_cbx(self, loss_types):
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(loss_types)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which currently is always true.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz_or_stat_data = self.npz_file[self.rlz_or_stat_cbx.currentData()]
        self.num_sites_lbl.setText(
            self.num_sites_msg % rlz_or_stat_data.shape)

    def set_ok_button(self):
        raise NotImplementedError()

    def build_layer_name(self, *args, **kwargs):
        raise NotImplementedError()

    def get_field_types(self, **kwargs):
        raise NotImplementedError()

    def read_npz_into_layer(self, field_types, **kwargs):
        raise NotImplementedError()

    def load_from_npz(self):
        raise NotImplementedError()

    def add_field_to_layer(self, field_name, field_type):
        # NOTE: add_attribute use the native qgis editing manager
        added_field_name = add_attribute(
            field_name, field_type, self.layer)
        return added_field_name

    def get_investigation_time(self):
        if self.output_type in ('hcurves', 'uhs', 'hmaps', 'ruptures'):
            try:
                investigation_time = self.npz_file['investigation_time']
            except KeyError as exc:
                msg = ('investigation_time not found. It is mandatory for %s.'
                       ' Please check if the ouptut was produced by an'
                       ' obsolete version of the OpenQuake Engine'
                       ' Server.') % self.output_type
                log_msg(msg, level='C', message_bar=self.iface.messageBar(),
                        exception=exc)
            else:
                # We must cast to 'str' to keep numerical padding
                # after saving the project
                return str(investigation_time)
        else:
            # some outputs do not need the investigation time
            return None

    def build_layer(self, rlz_or_stat=None, taxonomy=None, poe=None,
                    loss_type=None, dmg_state=None, gsim=None, imt=None,
                    consequence=None,
                    boundaries=None, geometry_type='point', wkt_geom_type=None,
                    row_wkt_geom_types=None, add_to_group=None,
                    add_to_map=True, create_spatial_index=True, set_visible=True):
        layer_name = self.build_layer_name(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, gsim=gsim, imt=imt,
            consequence=consequence,
            geometry_type=geometry_type)
        field_types = self.get_field_types(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, imt=imt, consequence=consequence)

        # create layer
        self.layer = QgsVectorLayer(
            "%s?crs=epsg:4326" % geometry_type, layer_name, "memory")
        modified_field_types = copy.copy(field_types)
        for field_name, field_type in field_types.items():
            if field_name in ['lon', 'lat', 'boundary']:
                continue
            added_field_name = self.add_field_to_layer(field_name, field_type)
            if field_name != added_field_name:
                if field_name == self.default_field_name:
                    self.default_field_name = added_field_name
                # replace field_name with the actual added_field_name
                del modified_field_types[field_name]
                modified_field_types[added_field_name] = field_type
        field_types = copy.copy(modified_field_types)

        self.layer = self.read_npz_into_layer(
            field_types, rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, consequence=consequence, imt=imt,
            boundaries=boundaries, geometry_type=geometry_type,
            wkt_geom_type=wkt_geom_type,
            row_wkt_geom_types=row_wkt_geom_types)
        # if we are creating a layer with empty extent, increase the
        # extent by a small delta in order to allow zooming to layer
        if (self.layer.featureCount() > 0
                and self.layer.extent().area() == 0.0):
            delta = 0.1
            ext = self.layer.extent()
            xmax = ext.xMaximum()
            xmin = ext.xMinimum()
            ymax = ext.yMaximum()
            ymin = ext.yMinimum()
            grown_extent = QgsRectangle(
                xmin - delta, ymin - delta, xmax + delta, ymax + delta)
            self.layer.setExtent(grown_extent)
        else:
            self.layer.setCustomProperty('output_type', self.output_type)
        investigation_time = self.get_investigation_time()
        if investigation_time is not None:
            self.layer.setCustomProperty('investigation_time',
                                         investigation_time)
        if self.engine_version is not None:
            self.layer.setCustomProperty('engine_version', self.engine_version)
        irmt_version = get_irmt_version()
        self.layer.setCustomProperty('irmt_version', irmt_version)
        self.layer.setCustomProperty('calc_id', self.calc_id)
        if poe is not None:
            self.layer.setCustomProperty('poe', poe)
        user_params = {'rlz_or_stat': rlz_or_stat,
                       'taxonomy': taxonomy,
                       'poe': poe,
                       'loss_type': loss_type,
                       'dmg_state': dmg_state,
                       'consequence': consequence,
                       'gsim': gsim,
                       'imt': imt}
        write_metadata_to_layer(
            self.drive_engine_dlg, self.output_type, self.layer, user_params)
        # try:
        #     if (self.zonal_layer_cbx.currentText()
        #             and self.zonal_layer_gbx.isChecked()):
        #         return self.layer
        # except AttributeError:
        #     # the aggregation stuff might not exist for some loaders
        #     pass
        if add_to_map:
            if add_to_group:
                tree_node = add_to_group
            else:
                tree_node = QgsProject.instance().layerTreeRoot()
            if self.mode != 'testing':
                # NOTE: the following commented line would cause (unexpectedly)
                #       "QGIS died on signal 11" and double creation of some
                #       layers during integration tests
                QgsProject.instance().addMapLayer(self.layer, False)
            tree_node.insertLayer(0, self.layer)
            self.iface.setActiveLayer(self.layer)
            if add_to_group:
                # NOTE: zooming to group from caller function, to avoid
                #       repeating it once per layer
                pass
            else:
                self.iface.zoomToActiveLayer()
            log_msg('Layer %s was created successfully' % layer_name,
                    level='S', message_bar=self.iface.messageBar())
            if not set_visible:
                layer_node = tree_node.findLayer(self.layer.id())
                if layer_node:
                    layer_node.setItemVisibilityChecked(False)
        if create_spatial_index:
            self.layer.dataProvider().createSpatialIndex()
        return self.layer

    @staticmethod
    def style_maps(layer, style_by, iface, output_type='damages-rlzs',
                   perils=None, add_null_class=False,
                   render_higher_on_top=False, repaint=True,
                   use_sgc_style=False):
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol.setOpacity(1)
        if isinstance(symbol, QgsMarkerSymbol):
            # do it only for the layer with points
            symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))

        style = get_style(layer, iface.messageBar())

        # this is the default, as specified in the user settings
        ramp = QgsGradientColorRamp(
            style['color_from'], style['color_to'])
        style_mode = style['style_mode']

        # in most cases, we override the user-specified setting, and use
        # instead a setting that was required by scientists
        if output_type in OQ_TO_LAYER_TYPES:
            default_qgs_style = QgsStyle().defaultStyle()
            default_color_ramp_names = default_qgs_style.colorRampNames()
            if output_type in ('damages-rlzs',
                               'damages-stats',
                               'avg_losses-rlzs',
                               'avg_losses-stats',):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                if Qgis.QGIS_VERSION_INT < 31000:
                    style_mode = QgsGraduatedSymbolRenderer.Jenks
                else:
                    style_mode = 'Jenks'
                ramp_type_idx = default_color_ramp_names.index('Reds')
                symbol.setColor(QColor(RAMP_EXTREME_COLORS['Reds']['top']))
                inverted = False
            elif (output_type in ('gmf_data', 'ruptures')
                  or (output_type == 'hmaps' and not use_sgc_style)):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                if output_type == 'ruptures':
                    if Qgis.QGIS_VERSION_INT < 31000:
                        style_mode = QgsGraduatedSymbolRenderer.Pretty
                    else:
                        style_mode = 'Pretty'
                else:
                    if Qgis.QGIS_VERSION_INT < 31000:
                        style_mode = QgsGraduatedSymbolRenderer.EqualInterval
                    else:
                        style_mode = 'EqualInterval'
                ramp_type_idx = default_color_ramp_names.index('Spectral')
                inverted = True
                symbol.setColor(QColor(RAMP_EXTREME_COLORS['Reds']['top']))
            elif output_type == 'hmaps' and use_sgc_style:
                # FIXME: for SGC they were using size 10000 map units

                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                if Qgis.QGIS_VERSION_INT < 31000:
                    style_mode = QgsGraduatedSymbolRenderer.Pretty
                else:
                    style_mode = 'Pretty'
                try:
                    ramp_type_idx = default_color_ramp_names.index(
                        'SGC_Green2Red_Hmap_Color_Ramp')
                except ValueError:
                    raise ValueError(
                            'Color ramp SGC_Green2Red_Hmap_Color_Ramp was '
                            'not found. Please import it from '
                            'Settings -> Style Manager, loading '
                            'svir/resources/sgc_green2red_hmap_color_ramp.xml')
                inverted = False
                registry = QgsApplication.symbolLayerRegistry()
                symbol_props = {
                    'name': 'square',
                    'color': '0,0,0',
                    'color_border': '0,0,0',
                    'offset': '0,0',
                    'size': '1.5',  # FIXME
                    'angle': '0',
                }
                square = registry.symbolLayerMetadata(
                    "SimpleMarker").createSymbolLayer(symbol_props)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType()).clone()
                symbol.deleteSymbolLayer(0)
                symbol.appendSymbolLayer(square)
                symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
            elif output_type in ['asset_risk', 'input']:
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                if Qgis.QGIS_VERSION_INT < 31000:
                    style_mode = QgsGraduatedSymbolRenderer.EqualInterval
                else:
                    style_mode = 'EqualInterval'
                # exposure_strings = ['number', 'occupants', 'value']
                # setting exposure colors by default
                colors = {'single': RAMP_EXTREME_COLORS['Blues']['top'],
                          'ramp_name': 'Blues'}
                inverted = False
                if output_type == 'asset_risk':
                    damage_strings = perils
                    for damage_string in damage_strings:
                        if damage_string in style_by:
                            colors = {'single': RAMP_EXTREME_COLORS[
                                          'Spectral']['top'],
                                      'ramp_name': 'Spectral'}
                            inverted = True
                            break
                else:  # 'input'
                    colors = {'single': RAMP_EXTREME_COLORS['Greens']['top'],
                              'ramp_name': 'Greens'}
                    symbol.symbolLayer(0).setShape(
                        QgsSimpleMarkerSymbolLayerBase.Square)
                single_color = colors['single']
                ramp_name = colors['ramp_name']
                ramp_type_idx = default_color_ramp_names.index(ramp_name)
                symbol.setColor(QColor(single_color))
            else:
                raise NotImplementedError(
                    'Undefined color ramp for output type %s' % output_type)
            ramp = default_qgs_style.colorRamp(
                default_color_ramp_names[ramp_type_idx])
            if inverted:
                ramp.invert()
        # get unique values
        fni = layer.fields().indexOf(style_by)
        unique_values = layer.dataProvider().uniqueValues(fni)
        num_unique_values = len(unique_values - {NULL})
        if num_unique_values > 2:
            if Qgis.QGIS_VERSION_INT < 31000:
                renderer = QgsGraduatedSymbolRenderer.createRenderer(
                    layer,
                    style_by,
                    min(num_unique_values, style['classes']),
                    style_mode,
                    symbol.clone(),
                    ramp)
            else:
                renderer = QgsGraduatedSymbolRenderer(
                    style_by, [])
                # NOTE: the following returns an instance of one of the
                #       subclasses of QgsClassificationMethod
                classification_method = \
                    QgsApplication.classificationMethodRegistry().method(
                        style_mode)
                renderer.setClassificationMethod(classification_method)
                renderer.updateColorRamp(ramp)
                renderer.updateSymbols(symbol.clone())
                renderer.updateClasses(
                    layer, min(num_unique_values, style['classes']))
            if not use_sgc_style:
                if Qgis.QGIS_VERSION_INT < 31000:
                    label_format = renderer.labelFormat()
                    # NOTE: the following line might be useful
                    # label_format.setTrimTrailingZeroes(True)
                    label_format.setPrecision(2)
                    renderer.setLabelFormat(label_format, updateRanges=True)
                else:
                    renderer.classificationMethod().setLabelPrecision(2)
                    renderer.calculateLabelPrecision()
        elif num_unique_values == 2:
            categories = []
            for unique_value in unique_values:
                symbol = symbol.clone()
                try:
                    symbol.setColor(QColor(RAMP_EXTREME_COLORS[ramp_name][
                        'bottom' if unique_value == min(unique_values)
                        else 'top']))
                except Exception:
                    symbol.setColor(QColor(
                        style['color_from']
                        if unique_value == min(unique_values)
                        else style['color_to']))
                category = QgsRendererCategory(
                    unique_value, symbol, str(unique_value))
                # entry for the list of category items
                categories.append(category)
            renderer = QgsCategorizedSymbolRenderer(style_by, categories)
        else:
            renderer = QgsSingleSymbolRenderer(symbol.clone())
        if add_null_class and NULL in unique_values:
            # add a class for NULL values
            rule_renderer = QgsRuleBasedRenderer(symbol.clone())
            root_rule = rule_renderer.rootRule()
            not_null_rule = root_rule.children()[0].clone()
            # strip parentheses from stringified color HSL
            not_null_rule.setFilterExpression(
                '%s IS NOT NULL' % QgsExpression.quotedColumnRef(style_by))
            not_null_rule.setLabel('%s:' % style_by)
            root_rule.appendChild(not_null_rule)
            null_rule = root_rule.children()[0].clone()
            null_rule.setSymbol(QgsFillSymbol.createSimple(
                {'color': '160,160,160', 'style': 'diagonal_x'}))
            null_rule.setFilterExpression(
                '%s IS NULL' % QgsExpression.quotedColumnRef(style_by))
            null_rule.setLabel(tr('No points'))
            root_rule.appendChild(null_rule)
            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                # create value ranges
                rule_renderer.refineRuleRanges(not_null_rule, renderer)
                # remove default rule
            elif isinstance(renderer, QgsCategorizedSymbolRenderer):
                rule_renderer.refineRuleCategoris(not_null_rule, renderer)
            for rule in rule_renderer.rootRule().children()[1].children():
                label = rule.label()
                # NOTE: in old QGIS versions,
                # by default, labels were like:
                # ('"collapse-structural-ASH_DRY_sum" >= 0.0000 AND
                # "collapse-structural-ASH_DRY_sum" <= 2.3949')
                # whereas in newer versions they are like '0 - 0.02'
                # and we want to convert the old format in the new one if
                # needed
                if 'AND' in label:
                    first, second = label.split(" AND ")
                    bottom = first.rsplit(" ", 1)[1]
                    top = second.rsplit(" ", 1)[1]
                    simplified = "%s - %s" % (bottom, top)
                    rule.setLabel(simplified)
            root_rule.removeChildAt(0)
            renderer = rule_renderer
        if render_higher_on_top:
            renderer.setUsingSymbolLevels(True)
            symbol_items = [item for item in renderer.legendSymbolItems()]
            for i in range(len(symbol_items)):
                sym = symbol_items[i].symbol().clone()
                key = symbol_items[i].ruleKey()
                for lay in range(sym.symbolLayerCount()):
                    sym.symbolLayer(lay).setRenderingPass(i)
                renderer.setLegendSymbolItem(key, sym)
        layer.setRenderer(renderer)
        if not use_sgc_style:
            layer.setOpacity(0.7)
        if repaint:
            layer.triggerRepaint()
            iface.setActiveLayer(layer)
            iface.zoomToActiveLayer()
            # NOTE QGIS3: probably not needed
            # iface.layerTreeView().refreshLayerSymbology(layer.id())
            iface.mapCanvas().refresh()

    def style_categorized(self, layer=None, style_by=None):
        if layer is None:
            layer = self.layer
        if style_by is None:
            style_by = self.default_field_name
        # get unique values
        fni = layer.fields().indexOf(style_by)
        unique_values = layer.dataProvider().uniqueValues(fni)
        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            # configure a symbol layer
            layer_style = {}
            layer_style['color'] = '%d, %d, %d' % (
                randrange(0, 256), randrange(0, 256), randrange(0, 256))
            layer_style['outline'] = '#000000'
            symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)
            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)
            # create renderer object
            category = QgsRendererCategory(
                unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)
        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(style_by, categories)
        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.triggerRepaint()

        # NOTE QGIS3: probably not needed
        # self.iface.layerTreeView().refreshLayerSymbology(layer.id())

        self.iface.mapCanvas().refresh()

    def style_curves(self):
        registry = QgsApplication.symbolLayerRegistry()
        symbol_props = {
            'name': 'cross2',
            'color': '0,0,0',
            'color_border': '0,0,0',
            'offset': '0,0',
            'size': '1.5',
            'angle': '0',
        }
        opacity = 0.7
        cross = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer(
            symbol_props)
        # NOTE: Cross symbols rendered for OQ-Engine disaggregation outputs are
        # opaque, wider and thicker than those used for other outputs (e.g.
        # hcurves)
        if self.output_type == 'disagg-rlzs':
            cross.setSize(3)
            cross.setStrokeWidth(0.5)
            opacity = 1
        symbol = QgsSymbol.defaultSymbol(self.layer.geometryType()).clone()
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(cross)
        renderer = QgsSingleSymbolRenderer(symbol)
        effect = QgsOuterGlowEffect()
        effect.setSpread(0.5)
        effect.setOpacity(opacity)
        effect.setColor(QColor(255, 255, 255))
        effect.setBlurLevel(1)

        renderer.paintEffect().appendEffect(effect)
        renderer.paintEffect().setEnabled(True)

        self.layer.setRenderer(renderer)
        self.layer.setOpacity(opacity)
        self.layer.triggerRepaint()

        # NOTE QGIS3: probably not needed
        # self.iface.layerTreeView().refreshLayerSymbology(self.layer.id())

        self.iface.mapCanvas().refresh()

    def open_load_zonal_layer_dialog(self):
        """
        Open a file dialog to select the zonal layer to be loaded
        :returns: the zonal layer
        """
        text = self.tr('Select zonal layer to import')
        filters = self.tr('All files (*.*);;'
                          'GeoPackages (*.gpkg);;'
                          'Vector shapefiles (*.shp);;'
                          'SQLite (*.sqlite);;'
                          )
        default_dir = QSettings().value('irmt/select_layer_dir',
                                        QDir.homePath())
        file_name, _ = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if not file_name:
            return None
        selected_dir = QFileInfo(file_name).dir().path()
        QSettings().setValue('irmt/select_layer_dir', selected_dir)
        zonal_layer = self.load_zonal_layer(file_name)
        return zonal_layer

    def load_zonal_layer(self, zonal_layer_path):
        self.added_zonal_layer = zonal_layer = None
        zonal_layer_basename, zonal_layer_ext = os.path.splitext(
            os.path.basename(zonal_layer_path))
        if zonal_layer_ext == '.gpkg':
            dlg = QgsSublayersDialog(
                QgsSublayersDialog.Ogr, 'Select zonal layer')
            conn = ogr.Open(zonal_layer_path)
            layer_defs = []
            for idx, c in enumerate(conn):
                ld = QgsSublayersDialog.LayerDefinition()
                ld.layerId = idx
                ld.layerName = c.GetDescription()
                ld.count = c.GetFeatureCount()
                ld.type = ogr.GeometryTypeToName(c.GetGeomType())
                layer_defs.append(ld)
            dlg.populateLayerTable(layer_defs)
            dlg.exec_()
            if not dlg.selection():
                return None
            for sel in dlg.selection():
                # NOTE: the last one will be chosen as zonal layer
                zonal_layer = QgsVectorLayer(
                    zonal_layer_path + "|layername=" + sel.layerName,
                    sel.layerName, 'ogr')
                if zonal_layer.isValid():
                    root = QgsProject.instance().layerTreeRoot()
                    QgsProject.instance().addMapLayer(zonal_layer, False)
                    root.insertLayer(0, zonal_layer)
                else:
                    msg = 'Invalid layer'
                    log_msg(msg, level='C',
                            message_bar=self.iface.messageBar())
                    return None
        else:
            zonal_layer = QgsVectorLayer(
                zonal_layer_path, zonal_layer_basename, 'ogr')
        if not zonal_layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            msg = 'Zonal layer must contain zone polygons'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        if zonal_layer_ext != '.gpkg':
            # Add zonal layer to registry
            if zonal_layer.isValid():
                root = QgsProject.instance().layerTreeRoot()
                QgsProject.instance().addMapLayer(zonal_layer, False)
                root.insertLayer(0, zonal_layer)
            else:
                msg = 'Invalid zonal layer'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
                return None
        self.added_zonal_layer = zonal_layer
        self.pre_populate_zonal_layer_cbx()
        return zonal_layer

    def populate_zonal_layer_cbx(self, zonal_layer):
        cbx = self.zonal_layer_cbx
        cbx.addItem(zonal_layer.name())
        last_index = cbx.count() - 1
        cbx.setItemData(last_index, zonal_layer.id())
        cbx.setCurrentIndex(last_index)

    def show_file_size(self):
        file_size = get_file_size(self.path)
        self.file_size_lbl.setText(self.file_size_msg % file_size)

    def accept(self):
        log_msg('Loading output started. Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        try:
            self.iface.layerTreeView().currentLayerChanged.disconnect(
                self.on_currentLayerChanged)
        except Exception:
            # it's connected only for some loaders
            pass
        self.hide()
        if self.output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            self.load_from_npz()
            if self.output_type in ('damages-rlzs',
                                    'damages-stats',
                                    'avg_losses-rlzs',
                                    'avg_losses-stats'):
                # check if also aggregating by zone or not
                if (not self.zonal_layer_cbx.currentText() or
                        not self.zonal_layer_gbx.isChecked()):
                    super().accept()
                    return
                self.aggregate_by_zone()
            else:
                super().accept()
        elif self.output_type in OQ_CSV_TO_LAYER_TYPES:
            self.load_from_csv()
            super().accept()

    def aggregate_by_zone(self):
        loss_layer = self.layer
        zonal_layer_id = self.zonal_layer_cbx.itemData(
            self.zonal_layer_cbx.currentIndex())
        zonal_layer = QgsProject.instance().mapLayer(
            zonal_layer_id)
        QgsProject.instance().layerTreeRoot().findLayer(
            zonal_layer.id()).setItemVisibilityChecked(False)
        # if the two layers have different projections, display a
        # warning, but try proceeding anyway
        have_same_projection, check_projection_msg = ProcessLayer(
            loss_layer).has_same_projection_as(zonal_layer)
        if not have_same_projection:
            log_msg(check_projection_msg, level='W',
                    message_bar=self.iface.messageBar())
        loss_layer_fieldnames = [field.name() for field in loss_layer.fields()]
        if len(loss_layer_fieldnames) == 1:
            self.loss_attr_name = loss_layer_fieldnames[0]
        elif self.default_field_name in loss_layer_fieldnames:
            self.loss_attr_name = self.default_field_name
        else:
            msg = (f'Field {self.default_field_name} to be used for the'
                   f' aggregation was not found')
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return
        zonal_layer_plus_sum_name = "%s: %s_sum" % (
            zonal_layer.name(), self.loss_attr_name)
        discard_nonmatching = self.discard_nonmatching_chk.isChecked()
        try:
            calculate_zonal_stats(
                self.on_calculate_zonal_stats_completed,
                zonal_layer, loss_layer, [self.loss_attr_name],
                zonal_layer_plus_sum_name,
                discard_nonmatching=discard_nonmatching,
                predicates=('intersects',), summaries=('sum',))
        except Exception as exc:
            log_msg(str(exc), level='C',
                    message_bar=self.iface.messageBar(),
                    exception=exc)

    def on_calculate_zonal_stats_completed(self, zonal_layer_plus_sum):
        if zonal_layer_plus_sum is None:
            msg = 'The calculation of zonal statistics was not completed'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        # Add zonal layer to registry
        if zonal_layer_plus_sum.isValid():
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(zonal_layer_plus_sum, False)
            root.insertLayer(0, zonal_layer_plus_sum)
        else:
            msg = 'The layer aggregating data by zone is invalid.'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        # NOTE: in scenario damage, keys are like
        #       u'structural_no_damage_mean', and not just
        #       u'structural', therefore we can't just use the selected
        #       loss type, but we must use the actual only key in the
        #       dict
        added_loss_attr = "%s_sum" % self.loss_attr_name
        style_by = added_loss_attr
        try:
            perils = self.perils
        except AttributeError:
            perils = None
        self.style_maps(zonal_layer_plus_sum, style_by,
                        self.iface, self.output_type,
                        perils=perils,
                        add_null_class=True)
        super().accept()

    def reject(self):
        try:
            self.iface.layerTreeView().currentLayerChanged.disconnect(
                self.on_currentLayerChanged)
        except Exception:
            # it's connected only for some loaders
            pass
        super().reject()
