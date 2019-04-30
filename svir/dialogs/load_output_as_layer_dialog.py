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
                       )
from qgis.gui import QgsSublayersDialog
from qgis.PyQt.QtCore import (
    pyqtSlot, pyqtSignal, QDir, QSettings, QFileInfo, Qt)
from qgis.PyQt.QtWidgets import (
                                 QDialogButtonBox,
                                 QDialog,
                                 QFileDialog,
                                 QComboBox,
                                 QSpinBox,
                                 QLabel,
                                 QCheckBox,
                                 QHBoxLayout,
                                 QVBoxLayout,
                                 QToolButton,
                                 QGroupBox,
                                 QLineEdit,
                                 )
from qgis.PyQt.QtGui import QColor
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats)
from svir.utilities.shared import (OQ_CSV_TO_LAYER_TYPES,
                                   OQ_COMPLEX_CSV_TO_LAYER_TYPES,
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
                                  )
from svir.tasks.extract_npz_task import TaskCanceled

FORM_CLASS = get_ui_class('ui_load_output_as_layer.ui')


class LoadOutputAsLayerDialog(QDialog, FORM_CLASS):
    """
    Dialog to load an oq-engine output as layer
    """
    init_done = pyqtSignal()
    loading_completed = pyqtSignal()
    loading_exception = pyqtSignal(Exception)

    def __init__(self, iface, viewer_dock,
                 session, hostname, calc_id, output_type=None,
                 path=None, mode=None, zonal_layer_path=None,
                 engine_version=None):
        # sanity check
        if output_type not in OQ_TO_LAYER_TYPES:
            raise NotImplementedError(output_type)
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
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all user options are set
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)

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
        self.init_done.emit()

    def create_file_hlayout(self):
        self.file_hlayout = QHBoxLayout()
        self.file_lbl = QLabel('File to load')
        self.file_browser_tbn = QToolButton()
        self.file_browser_tbn.setText('...')
        self.file_browser_tbn.clicked.connect(self.on_file_browser_tbn_clicked)
        self.path_le = QLineEdit()
        self.path_le.setEnabled(False)
        self.file_hlayout.addWidget(self.file_lbl)
        self.file_hlayout.addWidget(self.file_browser_tbn)
        self.file_hlayout.addWidget(self.path_le)
        self.vlayout.addLayout(self.file_hlayout)

    def create_num_sites_indicator(self):
        self.num_sites_msg = 'Number of sites: %s'
        self.num_sites_lbl = QLabel(self.num_sites_msg % '')
        self.vlayout.addWidget(self.num_sites_lbl)

    def create_file_size_indicator(self):
        self.file_size_msg = 'File size: %s'
        self.file_size_lbl = QLabel(self.file_size_msg % '')
        self.vlayout.addWidget(self.file_size_lbl)

    def create_load_multicol_ckb(self):
        self.load_multicol_ckb = QCheckBox(
            'Load one layer per realization or statistic')
        self.vlayout.addWidget(self.load_multicol_ckb)

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
        self.loss_type_lbl = QLabel('Loss Type')
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.setEnabled(False)
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.vlayout.addWidget(self.loss_type_lbl)
        self.vlayout.addWidget(self.loss_type_cbx)

    def create_eid_selector(self):
        self.eid_lbl = QLabel('Event ID')
        self.eid_sbx = QSpinBox()
        self.eid_sbx.setEnabled(False)
        self.vlayout.addWidget(self.eid_lbl)
        self.vlayout.addWidget(self.eid_sbx)

    def create_dmg_state_selector(self):
        self.dmg_state_lbl = QLabel('Damage state')
        self.dmg_state_cbx = QComboBox()
        self.dmg_state_cbx.setEnabled(False)
        self.dmg_state_cbx.currentIndexChanged['QString'].connect(
            self.on_dmg_state_changed)
        self.vlayout.addWidget(self.dmg_state_lbl)
        self.vlayout.addWidget(self.dmg_state_cbx)

    def create_taxonomy_selector(self):
        self.taxonomy_lbl = QLabel('Taxonomy')
        self.taxonomy_cbx = QComboBox()
        self.taxonomy_cbx.setEnabled(False)
        self.vlayout.addWidget(self.taxonomy_lbl)
        self.vlayout.addWidget(self.taxonomy_cbx)

    def create_style_by_selector(self):
        self.style_by_lbl = QLabel('Style by')
        self.style_by_cbx = QComboBox()
        self.vlayout.addWidget(self.style_by_lbl)
        self.vlayout.addWidget(self.style_by_cbx)

    def create_load_selected_only_ckb(self):
        self.load_selected_only_ckb = QCheckBox("Load only the selected items")
        self.load_selected_only_ckb.setChecked(True)
        self.vlayout.addWidget(self.load_selected_only_ckb)

    def create_show_return_period_ckb(self):
        self.show_return_period_chk = QCheckBox(
            "Show the return time in layer names")
        self.show_return_period_chk.setChecked(False)
        self.vlayout.addWidget(self.show_return_period_chk)

    def create_save_as_shp_ckb(self):
        self.save_as_shp_ckb = QCheckBox("Save the loaded layer as shapefile")
        self.save_as_shp_ckb.setChecked(False)
        self.vlayout.addWidget(self.save_as_shp_ckb)

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

    def on_zonal_layer_gbx_toggled(self, on):
        if on and not self.zonal_layer_cbx.currentText():
            self.ok_button.setEnabled(False)
        else:
            self.set_ok_button()

    def on_output_type_changed(self):
        if self.output_type in OQ_TO_LAYER_TYPES:
            self.create_load_selected_only_ckb()
        elif self.output_type in OQ_COMPLEX_CSV_TO_LAYER_TYPES:
            self.create_save_as_shp_ckb()
        self.set_ok_button()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        path = self.open_file_dialog()
        if path:
            self.populate_out_dep_widgets()
        self.set_ok_button()

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file[self.rlz_or_stat_cbx.currentText()]
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

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select the OQ-Engine output file to import')
        if self.output_type in OQ_CSV_TO_LAYER_TYPES:
            filters = self.tr('CSV files (*.csv)')
        else:
            raise NotImplementedError(self.output_type)
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        path, _ = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if not path:
            return
        selected_dir = QFileInfo(path).dir().path()
        QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
        self.path = path
        self.path_le.setText(self.path)
        return path

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.show_num_sites()

    def get_taxonomies(self):
        raise NotImplementedError()

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = [key for key in sorted(self.npz_file)
                              if key not in ('imtls', 'array')]
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        self.rlz_or_stat_cbx.addItems(self.rlzs_or_stats)

    def populate_loss_type_cbx(self, loss_types):
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(loss_types)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which currently is always true.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz_or_stat_data = self.npz_file[self.rlz_or_stat_cbx.currentText()]
        self.num_sites_lbl.setText(
            self.num_sites_msg % rlz_or_stat_data.shape)

    def set_ok_button(self):
        raise NotImplementedError()

    def build_layer_name(self, *args, **kwargs):
        raise NotImplementedError()

    def get_field_names(self, **kwargs):
        raise NotImplementedError()

    def add_field_to_layer(self, field_name):
        raise NotImplementedError()

    def read_npz_into_layer(self, field_names, **kwargs):
        raise NotImplementedError()

    def load_from_npz(self):
        raise NotImplementedError()

    def get_investigation_time(self):
        if self.output_type in ('hcurves', 'uhs', 'hmaps'):
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
                    loss_type=None, dmg_state=None, gsim=None, imt=None):
        layer_name = self.build_layer_name(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, gsim=gsim, imt=imt)
        field_names = self.get_field_names(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, imt=imt)

        # create layer
        self.layer = QgsVectorLayer(
            "Point?crs=epsg:4326", layer_name, "memory")
        for field_name in field_names:
            if field_name in ['lon', 'lat']:
                continue
            added_field_name = self.add_field_to_layer(field_name)
            if field_name != added_field_name:
                if field_name == self.default_field_name:
                    self.default_field_name = added_field_name
                # replace field_name with the actual added_field_name
                field_name_idx = field_names.index(field_name)
                field_names.remove(field_name)
                field_names.insert(field_name_idx, added_field_name)

        self.read_npz_into_layer(
            field_names, rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, imt=imt)
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
        try:
            if (self.zonal_layer_cbx.currentText()
                    and self.zonal_layer_gbx.isChecked()):
                return
        except AttributeError:
            # the aggregation stuff might not exist for some loaders
            pass
        QgsProject.instance().addMapLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()
        log_msg('Layer %s was created successfully' % layer_name, level='S',
                message_bar=self.iface.messageBar())

    @staticmethod
    def style_maps(layer, style_by, iface, output_type, perils=None,
                   add_null_class=False):
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
        mode = style['mode']

        # in most cases, we override the user-specified setting, and use
        # instead a setting that was required by scientists
        if output_type in OQ_TO_LAYER_TYPES:
            default_qgs_style = QgsStyle().defaultStyle()
            default_color_ramp_names = default_qgs_style.colorRampNames()
            if output_type in ('dmg_by_asset',
                               'losses_by_asset',
                               'avg_losses-stats',):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                mode = QgsGraduatedSymbolRenderer.Jenks
                ramp_type_idx = default_color_ramp_names.index('Reds')
                symbol.setColor(QColor(RAMP_EXTREME_COLORS['Reds']['top']))
                inverted = False
            elif output_type in ('hmaps', 'gmf_data', 'ruptures'):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                if output_type == 'ruptures':
                    mode = QgsGraduatedSymbolRenderer.Pretty
                else:
                    mode = QgsGraduatedSymbolRenderer.EqualInterval
                ramp_type_idx = default_color_ramp_names.index('Spectral')
                inverted = True
                symbol.setColor(QColor(RAMP_EXTREME_COLORS['Reds']['top']))
            elif output_type in ['asset_risk', 'input']:
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                mode = QgsGraduatedSymbolRenderer.EqualInterval
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
            renderer = QgsGraduatedSymbolRenderer.createRenderer(
                layer,
                QgsExpression.quotedColumnRef(style_by),
                min(num_unique_values, style['classes']),
                mode,
                symbol.clone(),
                ramp)
            label_format = renderer.labelFormat()
            # label_format.setTrimTrailingZeroes(True)  # it might be useful
            label_format.setPrecision(2)
            renderer.setLabelFormat(label_format, updateRanges=True)
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
            renderer = QgsCategorizedSymbolRenderer(
                QgsExpression.quotedColumnRef(style_by), categories)
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
                # by default, labels are like:
                # ('"collapse-structural-ASH_DRY_sum" >= 0.0000 AND
                # "collapse-structural-ASH_DRY_sum" <= 2.3949')
                first, second = label.split(" AND ")
                bottom = first.rsplit(" ", 1)[1]
                top = second.rsplit(" ", 1)[1]
                simplified = "%s - %s" % (bottom, top)
                rule.setLabel(simplified)
            root_rule.removeChildAt(0)
            renderer = rule_renderer
        renderer.setUsingSymbolLevels(True)
        symbol_items = [item for item in renderer.legendSymbolItems()]
        for i in range(len(symbol_items)):
            sym = symbol_items[i].symbol().clone()
            key = symbol_items[i].ruleKey()
            for lay in range(sym.symbolLayerCount()):
                sym.symbolLayer(lay).setRenderingPass(i)
            renderer.setLegendSymbolItem(key, sym)
        layer.setRenderer(renderer)
        layer.setOpacity(0.7)
        layer.triggerRepaint()
        iface.setActiveLayer(layer)
        iface.zoomToActiveLayer()
        log_msg('Layer %s was created successfully' % layer.name(), level='S',
                message_bar=iface.messageBar())
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
        renderer = QgsCategorizedSymbolRenderer(
            QgsExpression.quotedColumnRef(style_by), categories)
        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.triggerRepaint()

        # NOTE QGIS3: probably not needed
        # self.iface.layerTreeView().refreshLayerSymbology(layer.id())

        self.iface.mapCanvas().refresh()

    def style_curves(self):
        registry = QgsApplication.symbolLayerRegistry()
        cross = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer(
            {'name': 'cross2', 'color': '0,0,0', 'color_border': '0,0,0',
             'offset': '0,0', 'size': '1.5', 'angle': '0'})
        symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(cross)
        renderer = QgsSingleSymbolRenderer(symbol)
        effect = QgsOuterGlowEffect()
        effect.setSpread(0.5)
        effect.setOpacity(1)
        effect.setColor(QColor(255, 255, 255))
        effect.setBlurLevel(1)
        renderer.paintEffect().appendEffect(effect)
        renderer.paintEffect().setEnabled(True)
        self.layer.setRenderer(renderer)
        self.layer.setOpacity(0.7)
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
                    QgsProject.instance().addMapLayer(zonal_layer)
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
                QgsProject.instance().addMapLayer(zonal_layer)
            else:
                msg = 'Invalid zonal layer'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
                return None
        self.added_zonal_layer = zonal_layer
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
        try:
            self.iface.layerTreeView().currentLayerChanged.disconnect(
                self.on_currentLayerChanged)
        except Exception:
            # it's connected only for some loaders
            pass
        self.hide()
        if self.output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            self.load_from_npz()
            if self.output_type in ('losses_by_asset',
                                    'dmg_by_asset',
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
        try:
            [self.loss_attr_name] = [
                field.name() for field in loss_layer.fields()]
        except ValueError:
            self.loss_attr_name = self.default_field_name
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
            QgsProject.instance().addMapLayer(zonal_layer_plus_sum)
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
        if (hasattr(self, 'npz_file') and self.npz_file is not None
                and self.output_type in OQ_TO_LAYER_TYPES):
            self.npz_file.close()
        super().reject()
