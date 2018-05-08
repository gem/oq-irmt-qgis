from builtins import zip
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

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, edit
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import (WaitCursorManager,
                                  log_msg,
                                  extract_npz,
                                  )


class LoadGmfDataAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load gmf_data from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='gmf_data', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'gmf_data'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load ground motion fields from NPZ, as layer')
        self.create_load_selected_only_ckb()
        self.create_num_sites_indicator()
        # NOTE: gmpe and gsim are synonyms
        self.create_rlz_or_stat_selector('Ground Motion Prediction Equation')
        self.create_imt_selector()
        self.create_eid_selector()

        self.npz_file = extract_npz(
            session, hostname, calc_id, output_type,
            message_bar=iface.messageBar(), params=None)

        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(self.imt_cbx.currentIndex() != -1)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which is always true for scenario calculations.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz = self.rlz_or_stat_cbx.itemData(
            self.rlz_or_stat_cbx.currentIndex())
        gmf_data = self.npz_file[rlz]
        self.num_sites_lbl.setText(
            self.num_sites_msg % gmf_data.shape)

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = [key for key in sorted(self.npz_file)
                              if key not in ('imtls', 'array')]
        self.rlzs_npz = extract_npz(
            self.session, self.hostname, self.calc_id, 'realizations',
            message_bar=self.iface.messageBar(), params=None)
        self.gsims = self.rlzs_npz['array']['gsims']
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        for gsim, rlz in zip(self.gsims, self.rlzs_or_stats):
            # storing gsim as text, rlz as hidden data
            self.rlz_or_stat_cbx.addItem(gsim, userData=rlz)

    def on_rlz_or_stat_changed(self):
        rlz = self.rlz_or_stat_cbx.itemData(
            self.rlz_or_stat_cbx.currentIndex())
        self.dataset = self.npz_file[rlz]
        imts = self.dataset.dtype.names[2:]
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(imts)
        self.set_ok_button()

    def on_imt_changed(self):
        imt = self.imt_cbx.currentText()
        if imt:
            min_eid = 0
            max_eid = (self.dataset[imt].shape[1] - 1)
            self.eid_sbx.cleanText()
            self.eid_sbx.setEnabled(True)
            self.eid_lbl.setText(
                'Event ID (used for default styling) (range %d-%d)' % (
                    min_eid, max_eid))
            self.eid_sbx.setRange(min_eid, max_eid)
        self.set_ok_button()

    def load_from_npz(self):
        for rlz, gsim in zip(self.rlzs_or_stats, self.gsims):
            if (self.load_selected_only_ckb.isChecked()
                    and gsim != self.rlz_or_stat_cbx.currentText()):
                continue
            with WaitCursorManager('Creating layer for "%s"...'
                                   % gsim, self.iface.messageBar()):
                self.build_layer(rlz_or_stat=rlz, gsim=gsim)
                self.style_maps()
        if self.npz_file is not None:
            self.npz_file.close()

    def build_layer_name(self, gsim=None, **kwargs):
        self.imt = self.imt_cbx.currentText()
        self.eid = self.eid_sbx.value()
        self.default_field_name = '%s-%s' % (self.imt, self.eid)
        # NOTE: assuming it's a scenario calculation
        layer_name = "scenario_gmfs_%s_eid-%s" % (gsim, self.eid)
        return layer_name

    def get_field_names(self, **kwargs):
        # NOTE: we need a list instead of a tuple, because we want to be able
        #       to modify the list afterwards, to keep track of the actual
        #       field names created in the layer, that might be laundered to be
        #       compliant with shapefiles constraints
        field_names = list(self.dataset.dtype.names)
        return field_names

    def add_field_to_layer(self, field_name):
        field_name = "%s-%s" % (field_name, self.eid)
        added_field_name = add_numeric_attribute(field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        with edit(self.layer):
            feats = []
            fields = self.layer.pendingFields()
            layer_field_names = [field.name() for field in fields]
            dataset_field_names = self.get_field_names()
            d2l_field_names = dict(
                list(zip(dataset_field_names[2:], layer_field_names)))
            for row in self.dataset:
                # add a feature
                feat = QgsFeature(fields)
                for field_name in dataset_field_names:
                    if field_name in ['lon', 'lat']:
                        continue
                    layer_field_name = d2l_field_names[field_name]
                    value = float(row[field_name][self.eid])
                    feat.setAttribute(layer_field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row[0], row[1])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
