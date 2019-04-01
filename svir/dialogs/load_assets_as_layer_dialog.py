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

from qgis.core import (
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication,
    QgsProject,)
# from qgis.PyQt.QtCore import Qt
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.calculations.aggregate_loss_by_zone import (
    calculate_zonal_stats)
from svir.calculations.process_layer import ProcessLayer
from svir.utilities.utils import WaitCursorManager, log_msg, extract_npz
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadAssetsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load assets from an oq-engine output, as layer
    """
    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='assets', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'assets'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load assets as layer')
        with WaitCursorManager(
                "Reading tag collection...", self.iface.messageBar()):
            tag_collection = extract_npz(
                session, hostname, calc_id, output_type,
                self.iface.messageBar())
            self.tag_names = sorted(tag_collection['tagnames'])
            for tag_name in self.tag_names:
                self.create_selector(tag_name, tag_name, filter_ckb=True)
                cbx = getattr(self, "%s_cbx" % tag_name)
                cbx.addItems(sorted(tag_collection[tag_name]))
        self.create_zonal_layer_selector()
        if self.zonal_layer_path:
            zonal_layer = self.load_zonal_layer(self.zonal_layer_path)
            self.populate_zonal_layer_cbx(zonal_layer)
        else:
            self.pre_populate_zonal_layer_cbx()
        self.adjustSize()
        self.set_ok_button()
        self.show()
        self.init_done.emit()

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        self.default_field_name = 'number'  # FIXME: let the user choose one
        layer_name = "assets"
        return layer_name

    def get_field_names(self, **kwargs):
        field_names = [name for name in self.dataset.dtype.names
                       if name not in self.tag_names and
                       name not in ['lon', 'lat']]
        return field_names

    def add_field_to_layer(self, field_name):
        try:
            # NOTE: add_numeric_attribute uses the native qgis editing manager
            added_field_name = add_numeric_attribute(field_name, self.layer)
        except TypeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            return
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            lons = self.dataset['lon']
            lats = self.dataset['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name in field_names:
                    value = float(row[field_name])
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(lons[row_idx], lats[row_idx])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def accept(self):
        self.hide()
        extract_params = self.get_extract_params()
        self.download_assets(extract_params)

    def get_extract_params(self):
        params = {}
        for tag_name in self.tag_names:
            filter_ckb = getattr(self, "filter_by_%s_ckb" % tag_name)
            if filter_ckb.isChecked():
                cbx = getattr(self, "%s_cbx" % tag_name)
                params[tag_name] = cbx.currentText()
        return params

    def download_assets(self, extract_params):
        self.extract_npz_task = ExtractNpzTask(
            'Extract assets', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'assets',
            self.on_assets_downloaded, self.on_extract_error,
            params=extract_params)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def on_assets_downloaded(self, extracted_npz):
        self.npz_file = extracted_npz
        self.dataset = self.npz_file['array']
        with WaitCursorManager('Creating layer...', self.iface.messageBar()):
            self.build_layer()
            self.style_maps()
        if (self.zonal_layer_cbx.currentText()
                and self.zonal_layer_gbx.isChecked()):
            self.aggregate_by_zone()

    def aggregate_by_zone(self):
        loss_layer = self.layer
        QgsProject.instance().layerTreeRoot().findLayer(
            loss_layer.id()).setItemVisibilityChecked(False)
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
        # [self.loss_attr_name] = [
        #     field.name() for field in loss_layer.fields()]
        self.loss_attr_name = self.default_field_name
        zonal_layer_plus_sum_name = "%s_sum" % zonal_layer.name()
        try:
            calculate_zonal_stats(
                self.on_calculate_zonal_stats_completed,
                zonal_layer, loss_layer, (self.loss_attr_name,),
                zonal_layer_plus_sum_name)
        except Exception as exc:
            log_msg(str(exc), level='C',
                    message_bar=self.iface.messageBar(),
                    exception=exc)

