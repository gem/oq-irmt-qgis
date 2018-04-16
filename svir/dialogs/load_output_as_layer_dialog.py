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

from random import randrange
from qgis.core import (QgsVectorLayer,
                       QgsMapLayerRegistry,
                       QgsStyleV2,
                       QgsSymbolV2,
                       QgsSymbolLayerV2Registry,
                       QgsOuterGlowEffect,
                       QgsSingleSymbolRendererV2,
                       QgsVectorGradientColorRampV2,
                       QgsGraduatedSymbolRendererV2,
                       QgsRendererRangeV2,
                       QgsMapUnitScale,
                       QGis,
                       QgsMapLayer,
                       QgsMarkerSymbolV2,
                       QgsSimpleFillSymbolLayerV2,
                       QgsRendererCategoryV2,
                       QgsCategorizedSymbolRendererV2,
                       )
from qgis.PyQt.QtCore import pyqtSlot, QDir, QSettings, QFileInfo, Qt
from qgis.PyQt.QtGui import (QDialogButtonBox,
                             QDialog,
                             QFileDialog,
                             QColor,
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
from svir.calculations.process_layer import ProcessLayer
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats)
from svir.utilities.shared import (OQ_CSV_TO_LAYER_TYPES,
                                   OQ_COMPLEX_CSV_TO_LAYER_TYPES,
                                   OQ_TO_LAYER_TYPES,
                                   OQ_EXTRACT_TO_LAYER_TYPES,
                                   )
from svir.utilities.utils import (get_ui_class,
                                  get_style,
                                  log_msg,
                                  tr,
                                  get_file_size,
                                  )

FORM_CLASS = get_ui_class('ui_load_output_as_layer.ui')


class LoadOutputAsLayerDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to load an oq-engine output as layer
    """

    def __init__(self, iface, viewer_dock,
                 session, hostname, calc_id, output_type=None,
                 path=None, mode=None, zonal_layer_path=None):
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
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all user options are set
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)

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

    def create_gsim_selector(self):
        self.gsim_lbl = QLabel('GSIM')
        self.gsim_cbx = QComboBox()
        self.gsim_cbx.setEnabled(False)
        self.gsim_cbx.currentIndexChanged['QString'].connect(
            self.on_gsim_changed)
        self.vlayout.addWidget(self.gsim_lbl)
        self.vlayout.addWidget(self.gsim_cbx)

    def create_rlz_or_stat_selector(self):
        self.rlz_or_stat_lbl = QLabel('Realization')
        self.rlz_or_stat_cbx = QComboBox()
        self.rlz_or_stat_cbx.setEnabled(False)
        self.rlz_or_stat_cbx.currentIndexChanged['QString'].connect(
            self.on_rlz_or_stat_changed)
        self.vlayout.addWidget(self.rlz_or_stat_lbl)
        self.vlayout.addWidget(self.rlz_or_stat_cbx)

    def create_imt_selector(self):
        self.imt_lbl = QLabel('Intensity Measure Type')
        self.imt_cbx = QComboBox()
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.currentIndexChanged['QString'].connect(
            self.on_imt_changed)
        self.vlayout.addWidget(self.imt_lbl)
        self.vlayout.addWidget(self.imt_cbx)

    def create_poe_selector(self):
        self.poe_lbl = QLabel('Probability of Exceedance')
        self.poe_cbx = QComboBox()
        self.poe_cbx.setEnabled(False)
        self.poe_cbx.currentIndexChanged['QString'].connect(
            self.on_poe_changed)
        self.vlayout.addWidget(self.poe_lbl)
        self.vlayout.addWidget(self.poe_cbx)

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

    def create_save_as_shp_ckb(self):
        self.save_as_shp_ckb = QCheckBox("Save the loaded layer as shapefile")
        self.save_as_shp_ckb.setChecked(False)
        self.vlayout.addWidget(self.save_as_shp_ckb)

    def create_zonal_layer_selector(self):
        self.zonal_layer_gbx = QGroupBox()
        self.zonal_layer_gbx.setTitle('Aggregate by zone (optional)')
        self.zonal_layer_gbx.setCheckable(True)
        self.zonal_layer_gbx.setChecked(False)
        self.zonal_layer_gbx_v_layout = QVBoxLayout()
        self.zonal_layer_gbx.setLayout(self.zonal_layer_gbx_v_layout)
        self.zonal_layer_cbx = QComboBox()
        self.zonal_layer_cbx.addItem('')
        self.zonal_layer_lbl = QLabel('Zonal layer')
        self.zonal_layer_tbn = QToolButton()
        self.zonal_layer_tbn.setText('...')
        self.zonal_layer_h_layout = QHBoxLayout()
        self.zonal_layer_h_layout.addWidget(self.zonal_layer_cbx)
        self.zonal_layer_h_layout.addWidget(self.zonal_layer_tbn)
        self.zonal_layer_gbx_v_layout.addWidget(self.zonal_layer_lbl)
        self.zonal_layer_gbx_v_layout.addLayout(self.zonal_layer_h_layout)
        self.zone_id_field_lbl = QLabel('Field containing zone ids')
        self.zone_id_field_cbx = QComboBox()
        self.zonal_layer_gbx_v_layout.addWidget(self.zone_id_field_lbl)
        self.zonal_layer_gbx_v_layout.addWidget(self.zone_id_field_cbx)
        self.vlayout.addWidget(self.zonal_layer_gbx)
        self.zonal_layer_tbn.clicked.connect(
            self.on_zonal_layer_tbn_clicked)
        self.zonal_layer_cbx.currentIndexChanged[int].connect(
            self.on_zonal_layer_cbx_currentIndexChanged)

    def pre_populate_zonal_layer_cbx(self):
        for key, layer in \
                QgsMapLayerRegistry.instance().mapLayers().iteritems():
            # populate loss cbx only with layers containing points
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            if layer.geometryType() == QGis.Polygon:
                self.zonal_layer_cbx.addItem(layer.name())
                self.zonal_layer_cbx.setItemData(
                    self.zonal_layer_cbx.count()-1, layer.id())

    def on_zonal_layer_cbx_currentIndexChanged(self, new_index):
        self.zone_id_field_cbx.clear()
        zonal_layer = None
        if not self.zonal_layer_cbx.currentText():
            return
        zonal_layer_id = self.zonal_layer_cbx.itemData(new_index)
        zonal_layer = QgsMapLayerRegistry.instance().mapLayer(zonal_layer_id)
        # if the zonal_layer doesn't have a field containing a unique zone id,
        # the user can choose to add such unique id
        self.zone_id_field_cbx.addItem("Add field with unique zone id")
        for field in zonal_layer.fields():
            # for the zone id accept both numeric or textual fields
            self.zone_id_field_cbx.addItem(field.name())
            # by default, set the selection to the first textual field

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
        path = QFileDialog.getOpenFileName(
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

    def build_layer_name(self, rlz_or_stat, **kwargs):
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
            except KeyError:
                msg = ('investigation_time not found. It is mandatory for %s.'
                       ' Please check if the ouptut was produced by an'
                       ' obsolete version of the OpenQuake Engine'
                       ' Server.') % self.output_type
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
            else:
                return investigation_time
        else:
            # some outputs do not need the investigation time
            return None

    def build_layer(self, rlz_or_stat=None, taxonomy=None, poe=None,
                    loss_type=None, dmg_state=None, gsim=None):
        layer_name = self.build_layer_name(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, gsim=gsim)
        field_names = self.get_field_names(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state)

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
            loss_type=loss_type, dmg_state=dmg_state)
        self.layer.setCustomProperty('output_type', self.output_type)
        investigation_time = self.get_investigation_time()
        if investigation_time is not None:
            self.layer.setCustomProperty('investigation_time',
                                         investigation_time)
        self.layer.setCustomProperty('calc_id', self.calc_id)
        QgsMapLayerRegistry.instance().addMapLayer(self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()

    def _set_symbol_size(self, symbol):
        if self.iface.mapCanvas().mapUnits() == QGis.Degrees:
            point_size = 0.05
        elif self.iface.mapCanvas().mapUnits() == QGis.Meters:
            point_size = 4000
        else:
            # it is not obvious how to choose the point size in the other
            # cases, so we conservatively keep the default sizing
            return
        symbol.symbolLayer(0).setSizeUnit(symbol.MapUnit)
        symbol.symbolLayer(0).setSize(point_size)
        map_unit_scale = QgsMapUnitScale()
        map_unit_scale.maxSizeMMEnabled = True
        map_unit_scale.minSizeMMEnabled = True
        map_unit_scale.minSizeMM = 0.5
        map_unit_scale.maxSizeMM = 10
        symbol.symbolLayer(0).setSizeMapUnitScale(map_unit_scale)

    def style_maps(self, layer=None, style_by=None):
        if layer is None:
            layer = self.layer
        if style_by is None:
            style_by = self.default_field_name
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        # see properties at:
        # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
        symbol.setAlpha(1)  # opacity
        if isinstance(symbol, QgsMarkerSymbolV2):
            # do it only for the layer with points
            self._set_symbol_size(symbol)
            symbol.symbolLayer(0).setOutlineStyle(Qt.PenStyle(Qt.NoPen))

        style = get_style(layer, self.iface.messageBar())

        # this is the default, as specified in the user settings
        ramp = QgsVectorGradientColorRampV2(
            style['color_from'], style['color_to'])
        mode = style['mode']

        # in most cases, we override the user-specified setting, and use
        # instead a setting that was required by scientists
        if self.output_type in OQ_TO_LAYER_TYPES:
            default_qgs_style = QgsStyleV2().defaultStyle()
            default_color_ramp_names = default_qgs_style.colorRampNames()
            if self.output_type in ('dmg_by_asset',
                                    'losses_by_asset',
                                    'avg_losses-stats'):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                # jenks = natural breaks
                mode = QgsGraduatedSymbolRendererV2.Jenks
                ramp_type_idx = default_color_ramp_names.index('Reds')
                inverted = False
            elif self.output_type in ('hmaps', 'gmf_data', 'ruptures'):
                # options are EqualInterval, Quantile, Jenks, StdDev, Pretty
                if self.output_type == 'ruptures':
                    mode = QgsGraduatedSymbolRendererV2.Pretty
                else:
                    mode = QgsGraduatedSymbolRendererV2.EqualInterval
                ramp_type_idx = default_color_ramp_names.index('Spectral')
                inverted = True
            ramp = default_qgs_style.colorRamp(
                default_color_ramp_names[ramp_type_idx])
        graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
            layer,
            style_by,
            style['classes'],
            mode,
            symbol,
            ramp,
            inverted=inverted)
        label_format = graduated_renderer.labelFormat()
        # label_format.setTrimTrailingZeroes(True)  # it might be useful
        label_format.setPrecision(2)
        graduated_renderer.setLabelFormat(label_format, updateRanges=True)
        # add a class for 0 values, unless while styling ruptures
        if self.output_type != 'ruptures':
            VERY_SMALL_VALUE = 1e-20
            graduated_renderer.updateRangeLowerValue(0, VERY_SMALL_VALUE)
            symbol_zeros = QgsSymbolV2.defaultSymbol(layer.geometryType())
            symbol_zeros.setColor(QColor(240, 240, 240))  # very light grey
            if isinstance(symbol, QgsMarkerSymbolV2):
                # do it only for the layer with points
                self._set_symbol_size(symbol_zeros)
                symbol_zeros.symbolLayer(0).setOutlineStyle(
                    Qt.PenStyle(Qt.NoPen))
            zeros_min = 0.0
            zeros_max = VERY_SMALL_VALUE
            range_zeros = QgsRendererRangeV2(
                zeros_min, zeros_max, symbol_zeros,
                " %.2f - %.2f" % (zeros_min, zeros_max), True)
            graduated_renderer.addClassRange(range_zeros)
            graduated_renderer.moveClass(
                len(graduated_renderer.ranges()) - 1, 0)
        layer.setRendererV2(graduated_renderer)
        layer.setLayerTransparency(30)  # percent
        layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(layer)
        self.iface.mapCanvas().refresh()

    def style_categorized(self, layer, style_by):
        # get unique values
        fni = layer.fieldNameIndex(style_by)
        unique_values = layer.dataProvider().uniqueValues(fni)
        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
            # configure a symbol layer
            layer_style = {}
            layer_style['color'] = '%d, %d, %d' % (
                randrange(0, 256), randrange(0, 256), randrange(0, 256))
            layer_style['outline'] = '#000000'
            symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)
            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)
            # create renderer object
            category = QgsRendererCategoryV2(
                unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)
        # create renderer object
        renderer = QgsCategorizedSymbolRendererV2(style_by, categories)
        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRendererV2(renderer)
        layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(layer)
        self.iface.mapCanvas().refresh()

    def style_curves(self):
        registry = QgsSymbolLayerV2Registry.instance()
        cross = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer(
            {'name': 'cross2', 'color': '0,0,0', 'color_border': '0,0,0',
             'offset': '0,0', 'size': '1.5', 'angle': '0'})
        symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
        symbol.deleteSymbolLayer(0)
        symbol.appendSymbolLayer(cross)
        self._set_symbol_size(symbol)
        renderer = QgsSingleSymbolRendererV2(symbol)
        effect = QgsOuterGlowEffect()
        effect.setSpread(0.5)
        effect.setTransparency(0)
        effect.setColor(QColor(255, 255, 255))
        effect.setBlurLevel(1)
        renderer.paintEffect().appendEffect(effect)
        renderer.paintEffect().setEnabled(True)
        self.layer.setRendererV2(renderer)
        self.layer.setLayerTransparency(30)  # percent
        self.layer.triggerRepaint()
        self.iface.legendInterface().refreshLayerSymbology(
            self.layer)
        self.iface.mapCanvas().refresh()

    def open_zonal_layer_dialog(self):
        """
        Open a file dialog to select the zonal layer to be loaded
        :returns: the zonal layer
        """
        text = self.tr('Select zonal layer to import')
        filters = self.tr('Vector shapefiles (*.shp);;SQLite (*.sqlite);;'
                          'All files (*.*)')
        default_dir = QSettings().value('irmt/select_layer_dir',
                                        QDir.homePath())
        file_name, file_type = QFileDialog.getOpenFileNameAndFilter(
            self, text, default_dir, filters)
        if not file_name:
            return None
        selected_dir = QFileInfo(file_name).dir().path()
        QSettings().setValue('irmt/select_layer_dir', selected_dir)
        zonal_layer_plus_stats = self.load_zonal_layer(file_name)
        return zonal_layer_plus_stats

    def load_zonal_layer(self, zonal_layer_path, make_a_copy=False):
        # Load zonal layer
        zonal_layer = QgsVectorLayer(zonal_layer_path, tr('Zonal data'), 'ogr')
        if not zonal_layer.geometryType() == QGis.Polygon:
            msg = 'Zonal layer must contain zone polygons'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return False
        if make_a_copy:
            # Make a copy, where stats will be added
            zonal_layer_plus_stats = ProcessLayer(
                zonal_layer).duplicate_in_memory()
        else:
            zonal_layer_plus_stats = zonal_layer
        # Add zonal layer to registry
        if zonal_layer_plus_stats.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(zonal_layer_plus_stats)
        else:
            msg = 'Invalid zonal layer'
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return None
        return zonal_layer_plus_stats

    def on_zonal_layer_tbn_clicked(self):
        zonal_layer_plus_stats = self.open_zonal_layer_dialog()
        if (zonal_layer_plus_stats and
                zonal_layer_plus_stats.geometryType() == QGis.Polygon):
            self.populate_zonal_layer_cbx(zonal_layer_plus_stats)

    def populate_zonal_layer_cbx(self, zonal_layer_plus_stats):
        cbx = self.zonal_layer_cbx
        cbx.addItem(zonal_layer_plus_stats.name())
        last_index = cbx.count() - 1
        cbx.setItemData(last_index, zonal_layer_plus_stats.id())
        cbx.setCurrentIndex(last_index)

    def show_file_size(self):
        file_size = get_file_size(self.path)
        self.file_size_lbl.setText(self.file_size_msg % file_size)

    def accept(self):
        if self.output_type in OQ_EXTRACT_TO_LAYER_TYPES:
            self.load_from_npz()
            if self.output_type in ('losses_by_asset',
                                    'dmg_by_asset',
                                    'avg_losses-stats'):
                # check if also aggregating by zone or not
                if (not self.zonal_layer_cbx.currentText() or
                        not self.zonal_layer_gbx.isChecked()):
                    super(LoadOutputAsLayerDialog, self).accept()
                    return
                loss_layer = self.layer
                self.iface.legendInterface().setLayerVisible(loss_layer, False)
                zonal_layer_id = self.zonal_layer_cbx.itemData(
                    self.zonal_layer_cbx.currentIndex())
                zonal_layer = QgsMapLayerRegistry.instance().mapLayer(
                    zonal_layer_id)
                # if the two layers have different projections, display an
                # error message and return
                have_same_projection, check_projection_msg = ProcessLayer(
                    loss_layer).has_same_projection_as(zonal_layer)
                if not have_same_projection:
                    log_msg(check_projection_msg, level='C',
                            message_bar=self.iface.messageBar())
                    # TODO: load only loss layer
                    super(LoadOutputAsLayerDialog, self).accept()
                    return
                loss_attr_names = [
                    field.name() for field in loss_layer.fields()]
                zone_id_in_losses_attr_name = None
                # index 0 is for "Add field with unique zone id"
                if self.zone_id_field_cbx.currentIndex() == 0:
                    zone_id_in_zones_attr_name = None
                else:
                    zone_id_in_zones_attr_name = \
                        self.zone_id_field_cbx.currentText()
                # aggregate losses by zone (calculate count of points in the
                # zone, sum and average loss values for the same zone)
                loss_layer_is_vector = True
                try:
                    res = calculate_zonal_stats(loss_layer,
                                                zonal_layer,
                                                loss_attr_names,
                                                loss_layer_is_vector,
                                                zone_id_in_losses_attr_name,
                                                zone_id_in_zones_attr_name,
                                                self.iface,
                                                extra=False)
                except TypeError as exc:
                    log_msg(str(exc), level='C',
                            message_bar=self.iface.messageBar())
                    return
                (loss_layer, zonal_layer, loss_attrs_dict) = res
                # sanity check
                assert len(loss_attrs_dict) == 1, (
                    "Only one attribute should be added to the zonal layer."
                    " %s were added insted" % len(loss_attrs_dict))
                # NOTE: in scenario damage, keys are like
                #       u'structural_no_damage_mean', and not just
                #       u'structural', therefore we can't just use the selected
                #       loss type, but we must use the actual only key in the
                #       dict
                [added_loss_attr] = loss_attrs_dict
                style_by = loss_attrs_dict[added_loss_attr]['sum']
                self.style_maps(layer=zonal_layer, style_by=style_by)
        elif self.output_type in OQ_CSV_TO_LAYER_TYPES:
            self.load_from_csv()
        super(LoadOutputAsLayerDialog, self).accept()

    def reject(self):
        if (hasattr(self, 'npz_file') and self.npz_file is not None
                and self.output_type in OQ_TO_LAYER_TYPES):
            self.npz_file.close()
        super(LoadOutputAsLayerDialog, self).reject()
