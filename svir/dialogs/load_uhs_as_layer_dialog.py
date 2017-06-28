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

import numpy
from qgis.core import QgsFeature, QgsGeometry, QgsPoint
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import (LayerEditingManager,
                                  log_msg,
                                  WaitCursorManager,
                                  )
from svir.utilities.shared import DEBUG


class LoadUhsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load uniform hazard spectra from an oq-engine output,
    as layer
    """

    def __init__(self, iface, viewer_dock, output_type='uhs',
                 path=None, mode=None):
        assert output_type == 'uhs'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, output_type, path, mode)
        self.setWindowTitle(
            'Load uniform hazard spectra from NPZ, as layer')
        self.create_load_selected_only_ckb()
        self.create_rlz_or_stat_selector()
        self.create_poe_selector()
        if self.path:
            self.npz_file = numpy.load(self.path, 'r')
            self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(
            bool(self.path) and self.poe_cbx.currentIndex() != -1)

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = [
            key for key in sorted(self.npz_file['all'].dtype.names)
            if key not in ('lon', 'lat')]
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        self.rlz_or_stat_cbx.addItems(self.rlzs_or_stats)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which currently is always true.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz_or_stat_data = self.npz_file['all'][
            self.rlz_or_stat_cbx.currentText()]
        self.rlz_or_stat_num_sites_lbl.setText(
            self.num_sites_msg % rlz_or_stat_data.shape)

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file['all'][self.rlz_or_stat_cbx.currentText()]
        self.poes = self.dataset.dtype.names
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.poes)
        self.set_ok_button()

    def build_layer_name(self, rlz_or_stat, **kwargs):
        poe = kwargs['poe']
        investigation_time = self.get_investigation_time()
        layer_name = "uhs_%s_poe-%s_%sy" % (rlz_or_stat, poe,
                                            investigation_time)
        return layer_name

    def get_field_names(self, **kwargs):
        poe = kwargs['poe']
        field_names = self.dataset[poe].dtype.names
        return field_names

    def add_field_to_layer(self, field_name):
        # NOTE: add_numeric_attribute uses LayerEditingManager
        added_field_name = add_numeric_attribute(
            field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        poe = kwargs['poe']
        with LayerEditingManager(self.layer, 'Reading npz', DEBUG):
            lons = self.npz_file['all']['lon']
            lats = self.npz_file['all']['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                for field_name_idx, field_name in enumerate(field_names):
                    value = float(row[poe][field_name_idx])
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPoint(
                    QgsPoint(lons[row_idx], lats[row_idx])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats, makeSelected=False)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_npz(self):
        for rlz_or_stat in self.rlzs_or_stats:
            if (self.load_selected_only_ckb.isChecked()
                    and rlz_or_stat != self.rlz_or_stat_cbx.currentText()):
                continue
            for poe in self.poes:
                if (self.load_selected_only_ckb.isChecked()
                        and poe != self.poe_cbx.currentText()):
                    continue
                with WaitCursorManager(
                        'Creating layer for "%s" '
                        ' and poe "%s"...' % (rlz_or_stat, poe), self.iface):
                    self.build_layer(rlz_or_stat, poe=poe)
                    self.style_curves()
