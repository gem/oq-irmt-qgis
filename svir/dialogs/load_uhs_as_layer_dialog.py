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
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import log_msg, WaitCursorManager
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadUhsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load uniform hazard spectra from an oq-engine output,
    as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='uhs', path=None, mode=None, engine_version=None):
        assert output_type == 'uhs'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load uniform hazard spectra as layer')
        self.create_num_sites_indicator()
        self.create_load_selected_only_ckb()
        self.create_poe_selector()

        self.extract_npz_task = ExtractNpzTask(
            'Extract uniform hazard spectra', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.poe_cbx.currentIndex() != -1)

    def populate_dataset(self):
        self.rlzs_or_stats = [
            key for key in sorted(self.npz_file['all'].dtype.names)
            if key not in ('lon', 'lat')]
        self.dataset = self.npz_file['all']
        self.poes = self.dataset[self.rlzs_or_stats[0]].dtype.names
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.poes)
        self.set_ok_button()

    def show_num_sites(self):
        self.num_sites_lbl.setText(
            self.num_sites_msg % self.dataset.shape)

    def populate_out_dep_widgets(self):
        self.populate_dataset()
        self.show_num_sites()

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file['all'][self.rlz_or_stat_cbx.currentText()]
        self.poes = self.dataset.dtype.names
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.poes)
        self.set_ok_button()

    def build_layer_name(self, **kwargs):
        poe = kwargs['poe']
        investigation_time = self.get_investigation_time()
        layer_name = "uhs_poe-%s_%sy" % (poe, investigation_time)
        return layer_name

    def get_field_names(self, **kwargs):
        poe = kwargs['poe']
        field_names = []
        for rlz_or_stat in self.rlzs_or_stats:
            field_names.extend([
                "%s_%s" % (rlz_or_stat, imt)
                for imt in self.dataset[rlz_or_stat][poe].dtype.names])
        return field_names

    def add_field_to_layer(self, field_name):
        # NOTE: add_numeric_attribute uses the native qgis editing manager
        added_field_name = add_numeric_attribute(
            field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        poe = kwargs['poe']
        with edit(self.layer):
            lons = self.npz_file['all']['lon']
            lats = self.npz_file['all']['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name_idx, field_name in enumerate(field_names):
                    rlz_or_stat, imt = field_name.split('_')
                    iml = row[rlz_or_stat][poe][imt]
                    feat.setAttribute(field_name, float(iml))
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(lons[row_idx], lats[row_idx])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_npz(self):
        for poe in self.poes:
            if (self.load_selected_only_ckb.isChecked()
                    and poe != self.poe_cbx.currentText()):
                continue
            with WaitCursorManager(
                    'Creating layer for poe "%s"...'
                    % poe, self.iface.messageBar()):
                self.build_layer(poe=poe)
                self.style_curves()
