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

from qgis.core import QgsFeature, QgsGeometry, QgsPoint, edit
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import (WaitCursorManager,
                                  log_msg,
                                  extract_npz,
                                  )


class LoadHazardMapsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load hazard maps from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='hmaps', path=None, mode=None):
        assert output_type == 'hmaps'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type, path, mode)

        # FIXME: add layout only for output types that load from file
        self.remove_file_hlayout()

        self.setWindowTitle(
            'Load hazard maps as layer')
        self.create_load_selected_only_ckb()
        self.create_num_sites_indicator()
        self.create_rlz_or_stat_selector()
        self.create_imt_selector()
        self.create_poe_selector()
        self.npz_file = extract_npz(
            session, hostname, calc_id, output_type,
            message_bar=iface.messageBar(), params=None)
        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(self.poe_cbx.currentIndex() != -1)

    def populate_rlz_or_stat_cbx(self):
        # excluding lon, lat (in old calculations, we might also find 'vs30',
        # that has to be discarded too)
        self.rlzs_or_stats = [
            rlz_or_stat
            for rlz_or_stat in self.npz_file['all'].dtype.names[2:]
            if rlz_or_stat != 'vs30']
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        self.rlz_or_stat_cbx.addItems(self.rlzs_or_stats)

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file['all'][self.rlz_or_stat_cbx.currentText()]
        self.imts = {}
        imts_poes = self.dataset.dtype.names
        for imt_poe in imts_poes:
            imt, poe = imt_poe.split('-')
            if imt not in self.imts:
                self.imts[imt] = [poe]
            else:
                self.imts[imt].append(poe)
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(self.imts.keys())
        self.set_ok_button()

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which currently is always true.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz_or_stat_data = self.npz_file['all'][
            self.rlz_or_stat_cbx.currentText()]
        self.num_sites_lbl.setText(
            self.num_sites_msg % rlz_or_stat_data.shape)

    def on_imt_changed(self):
        self.imt = self.imt_cbx.currentText()
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        if self.imt:
            self.poe_cbx.addItems(self.imts[self.imt])
        self.set_ok_button()

    def build_layer_name(self, rlz_or_stat, **kwargs):
        imt = self.imt_cbx.currentText()
        poe = self.poe_cbx.currentText()
        self.default_field_name = '%s-%s' % (imt, poe)
        investigation_time = self.get_investigation_time()
        layer_name = "hazard_map_%s_%sy" % (rlz_or_stat, investigation_time)
        return layer_name

    def get_field_names(self, **kwargs):
        if self.load_selected_only_ckb.isChecked():
            field_names = [self.default_field_name]
        else:  # load everything
            # field names will be like "imt-poe"
            # self.dataset contains data for the chosen rlz or stat
            field_names = self.dataset.dtype.names
        return field_names

    def add_field_to_layer(self, field_name):
        try:
            # NOTE: add_numeric_attribute uses the native qgis editing manager
            added_field_name = add_numeric_attribute(field_name, self.layer)
        except TypeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar())
            return
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            lons = self.npz_file['all']['lon']
            lats = self.npz_file['all']['lat']
            feats = []
            for row_idx, row in enumerate(self.dataset):
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                for field_name in field_names:
                    # NOTE: without casting to float, it produces a
                    #       null because it does not recognize the
                    #       numpy type
                    value = float(row[field_name])
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
            with WaitCursorManager('Creating layer for "%s"...' % rlz_or_stat,
                                   self.iface.messageBar()):
                self.build_layer(rlz_or_stat)
                self.style_maps()
        if self.npz_file is not None:
            self.npz_file.close()
