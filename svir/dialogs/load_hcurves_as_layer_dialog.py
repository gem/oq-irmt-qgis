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


class LoadHazardCurvesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load hazard curves from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='hcurves', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'hcurves'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load hazard curves as layer')
        self.create_num_sites_indicator()

        self.extract_npz_task = ExtractNpzTask(
            'Extract hazard curves', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def populate_dataset(self):
        self.rlzs_or_stats = self.npz_file['all'].dtype.names[2:]
        self.dataset = self.npz_file['all']

    def show_num_sites(self):
        self.num_sites_lbl.setText(
            self.num_sites_msg % self.dataset.shape)

    def populate_out_dep_widgets(self):
        self.populate_dataset()
        self.show_num_sites()

    def build_layer_name(self, **kwargs):
        investigation_time = self.get_investigation_time()
        layer_name = "hazard_curves_%sy" % investigation_time
        return layer_name

    def get_field_names(self, **kwargs):
        field_names = []
        for rlz_or_stat in self.rlzs_or_stats:
            for imt in self.dataset[rlz_or_stat].dtype.names:
                for iml in self.dataset[rlz_or_stat][imt].dtype.names:
                    field_name = "%s_%s_%s" % (rlz_or_stat, imt, iml)
                    field_names.append(field_name)
        return field_names

    def add_field_to_layer(self, field_name):
        added_field_name = add_numeric_attribute(field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            lons = self.npz_file['all']['lon']
            lats = self.npz_file['all']['lat']
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

    def load_from_npz(self):
        with WaitCursorManager('Creating layer...', self.iface.messageBar()):
            self.build_layer()
            self.style_curves()
        if self.npz_file is not None:
            self.npz_file.close()
