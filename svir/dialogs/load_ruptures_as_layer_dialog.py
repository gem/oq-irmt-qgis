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

from collections import OrderedDict
from qgis.core import (
    QgsFeature, QgsGeometry, edit, QgsTask, QgsApplication)
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import log_msg, WaitCursorManager
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadRupturesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load ruptures from an oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='ruptures', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'ruptures'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)
        self.style_by_items = OrderedDict([
            ('Tectonic region type', 'trt'),
            ('Magnitude', 'mag'),
        ])
        self.setWindowTitle('Load ruptures as layer')
        # self.create_save_as_gpkg_ckb()
        self.create_style_by_selector()

        self.extract_npz_task = ExtractNpzTask(
            'Extract ruptures', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'rupture_info', self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

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
        self.layer_name = 'ruptures_%sy' % investigation_time
        return self.layer_name

    def get_field_names(self, **kwargs):
        field_names = list(self.npz_file['array'].dtype.names)
        return field_names

    def load_from_npz(self):
        with WaitCursorManager(
                'Creating layer for ruptures...', self.iface.messageBar()):
            self.build_layer()
        style_by = self.style_by_cbx.itemData(self.style_by_cbx.currentIndex())
        if style_by == 'mag':
            self.style_maps(self.layer, style_by,
                            self.iface, self.output_type)
        else:  # 'trt'
            self.style_categorized(layer=self.layer, style_by=style_by)
        log_msg('Layer %s was loaded successfully' % self.layer_name,
                level='S', message_bar=self.iface.messageBar())

    def add_field_to_layer(self, field_name):
        added_field_name = add_numeric_attribute(field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, rlz_or_stat, **kwargs):
        with edit(self.layer):
            feats = []
            fields = self.layer.fields()
            layer_field_names = [field.name() for field in fields]
            dataset_field_names = self.get_field_names()
            # FIXME
            d2l_field_names = dict(
                list(zip(dataset_field_names[:-1], layer_field_names)))
            for row in self.npz_file['array']:
                # add a feature
                feat = QgsFeature(fields)
                for field_name in dataset_field_names:
                    if field_name in ['boundary']:
                        continue
                    layer_field_name = d2l_field_names[field_name]
                    try:
                        value = float(row[field_name])
                    except ValueError:
                        try:
                            value = row[field_name].decode('utf8')
                        except AttributeError:
                            value = row[field_name]
                    feat.setAttribute(layer_field_name, value)
                feat.setGeometry(QgsGeometry.fromWkt(
                    row['boundary'].decode('utf8')))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
