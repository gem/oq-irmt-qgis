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
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.utilities.utils import log_msg, WaitCursorManager
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadHazardCurvesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load hazard curves from an oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='hcurves', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'hcurves'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load hazard curves as layer')
        self.create_num_sites_indicator()
        self.create_rlz_or_stat_selector(all_ckb=True)
        self.create_imt_selector(all_ckb=True)
        self.load_all_rlzs_or_stats_chk.setChecked(True)
        self.load_all_imts_chk.setChecked(True)

        log_msg('Extracting hazard curves.'
                ' Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.extract_npz_task = ExtractNpzTask(
            'Extract hazard curves', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def populate_dataset(self):
        self.dataset = self.extracted_dict['all']

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = self.extracted_dict['all'].dtype.names[2:]
        for rlz_or_stat in self.rlzs_or_stats:
            self.rlz_or_stat_cbx.addItem(rlz_or_stat)

    def on_rlz_or_stat_changed(self):
        rlz_or_stat = self.rlz_or_stat_cbx.currentText()
        dataset = self.extracted_dict['all'][rlz_or_stat]
        self.imts = [imt for imt in dataset.dtype.names]
        self.imt_cbx.clear()
        for imt in self.imts:
            self.imt_cbx.addItem(imt)

    def on_imt_changed(self):
        self.set_ok_button()

    def show_num_sites(self):
        self.num_sites_lbl.setText(
            self.num_sites_msg % self.dataset.shape)

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.populate_dataset()
        self.show_num_sites()

    def build_layer_name(self, **kwargs):
        investigation_time = self.get_investigation_time()
        layer_name = "hcurves_%sy" % investigation_time
        return layer_name

    def get_field_types(self, **kwargs):
        field_types = {}
        for rlz_or_stat in self.rlzs_or_stats:
            if (not self.load_all_rlzs_or_stats_chk.isChecked()
                    and rlz_or_stat != self.rlz_or_stat_cbx.currentText()):
                continue
            for imt in self.dataset[rlz_or_stat].dtype.names:
                if (not self.load_all_imts_chk.isChecked()
                        and imt != self.imt_cbx.currentText()):
                    continue
                for iml in self.dataset[rlz_or_stat][imt].dtype.names:
                    field_name = "%s_%s_%s" % (rlz_or_stat, imt, iml)
                    # NOTE: assuming that all fields are numeric
                    field_types[field_name] = 'F'
        return field_types

    def on_iml_changed(self):
        self.set_ok_button()

    def read_extracted_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            lons = self.extracted_dict['all']['lon']
            lats = self.extracted_dict['all']['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                feat = QgsFeature(self.layer.fields())
                for field_name_idx, field_name in enumerate(field_names):
                    rlz_or_stat, imt, iml = field_name.split('_')
                    poe = row[rlz_or_stat][imt][iml]
                    feat.setAttribute(field_name, float(poe))
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(lons[row_idx], lats[row_idx])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_extracted_dict(self):
        with WaitCursorManager('Creating layer...', self.iface.messageBar()):
            self.build_layer()
            self.style_curves()
