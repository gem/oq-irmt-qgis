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

import gzip
from collections import OrderedDict
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import (
    QgsFeature, QgsGeometry, QgsWkbTypes, edit, QgsTask, QgsApplication,
    QgsProject)
from svir.utilities.utils import log_msg, WaitCursorManager, zoom_to_group
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadRupturesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load ruptures from an oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='ruptures', min_mag=4, path=None,
                 mode=None, engine_version=None, calculation_mode=None):
        assert output_type == 'ruptures'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version, calculation_mode=calculation_mode)
        self.style_by_items = OrderedDict([
            ('Tectonic region type', 'trt'),
            ('Magnitude', 'mag'),
        ])
        self.setWindowTitle('Load ruptures as layer')
        self.create_min_mag_dsb(min_mag)
        self.create_style_by_selector()
        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()
        self.show()

    def accept(self):
        log_msg('Loading output started. Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.hide()
        min_mag = self.min_mag_dsb.value()
        self.extract_npz_task = ExtractNpzTask(
            'Extract ruptures', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'rupture_info',
            self.on_ruptures_extracted,
            self.on_extract_error, params={'min_mag': min_mag})
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def on_ruptures_extracted(self, extracted_npz):
        self.npz_file = extracted_npz
        if 'array' not in self.npz_file:
            log_msg("No ruptures were found above magnitude %s"
                    % self.min_mag_dsb.text(), level='C',
                    message_bar=self.iface.messageBar())
            return
        self.load_from_npz()
        QDialog.accept(self)
        self.loading_completed.emit(self)

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def populate_out_dep_widgets(self):
        self.populate_style_by_cbx()

    def populate_style_by_cbx(self):
        self.style_by_cbx.clear()
        for item in self.style_by_items:
            self.style_by_cbx.addItem(item, self.style_by_items[item])

    def build_layer_name(self, **kwargs):
        investigation_time = self.get_investigation_time()
        geometry_type = kwargs['geometry_type']
        self.layer_name = '%s_ruptures_%sy' % (
            geometry_type, investigation_time)
        return self.layer_name

    def get_field_types(self, **kwargs):
        field_types = {name: self.npz_file['array'][name].dtype.char
                       for name in self.npz_file['array'].dtype.names}
        return field_types

    def load_from_npz(self):
        boundaries = gzip.decompress(self.npz_file['boundaries']).split(b'\n')
        row_wkt_geom_types = {
            row_idx: QgsGeometry.fromWkt(boundary.decode('utf8')).wkbType()
            for row_idx, boundary in enumerate(boundaries)}
        wkt_geom_types = set(row_wkt_geom_types.values())
        if len(wkt_geom_types) > 1:
            root = QgsProject.instance().layerTreeRoot()
            rup_group = root.insertGroup(0, "Earthquake Ruptures")
        else:
            rup_group = None
        for wkt_geom_type in wkt_geom_types:
            if wkt_geom_type == QgsWkbTypes.Point:
                layer_geom_type = "point"
            elif wkt_geom_type == QgsWkbTypes.LineString:
                layer_geom_type = "linestring"
            elif wkt_geom_type == QgsWkbTypes.Polygon:
                layer_geom_type = "polygon"
            elif wkt_geom_type == QgsWkbTypes.MultiPoint:
                layer_geom_type = "multipoint"
            elif wkt_geom_type == QgsWkbTypes.MultiLineString:
                layer_geom_type = "multilinestring"
            elif wkt_geom_type == QgsWkbTypes.MultiPolygon:
                layer_geom_type = "multipolygon"
            else:
                raise ValueError(
                    'Unexpected geometry type: %s' % wkt_geom_type)
            with WaitCursorManager(
                    'Creating layer for "%s" ruptures...' % layer_geom_type,
                    self.iface.messageBar()):
                self.build_layer(boundaries=boundaries,
                                 geometry_type=layer_geom_type,
                                 wkt_geom_type=wkt_geom_type,
                                 row_wkt_geom_types=row_wkt_geom_types,
                                 add_to_group=rup_group)
            style_by = self.style_by_cbx.itemData(
                self.style_by_cbx.currentIndex())
            if style_by == 'mag':
                self.style_maps(self.layer, style_by,
                                self.iface, self.output_type)
            else:  # 'trt'
                self.style_categorized(layer=self.layer, style_by=style_by)
            log_msg('Layer %s was loaded successfully' % self.layer_name,
                    level='S', message_bar=self.iface.messageBar())
        if rup_group:
            zoom_to_group(rup_group)

    def read_npz_into_layer(
            self, field_types, rlz_or_stat, boundaries,
            wkt_geom_type, row_wkt_geom_types, **kwargs):
        with edit(self.layer):
            feats = []
            fields = self.layer.fields()
            field_names = [field.name() for field in fields]
            for row_idx, row in enumerate(self.npz_file['array']):
                if row_wkt_geom_types[row_idx] != wkt_geom_type:
                    continue
                # add a feature
                feat = QgsFeature(fields)
                for field_name in field_names:
                    value = row[field_name].item()
                    if isinstance(value, bytes):
                        value = value.decode('utf8')
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromWkt(
                    boundaries[row_idx].decode('utf8')))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
