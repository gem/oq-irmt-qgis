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

import csv
import tempfile
from PyQt4.QtCore import pyqtSlot
from svir.utilities.utils import import_layer_from_csv, log_msg
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadDmgByAssetAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load dmg_by_asset from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, output_type='dmg_by_asset',
                 path=None, mode=None):
        assert output_type == 'dmg_by_asset'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, output_type, path, mode)
        self.create_dmg_state_selector()
        self.create_loss_type_selector()
        self.create_save_as_shp_ckb()
        self.setWindowTitle('Load scenario damage by asset from CSV, as layer')
        self.adjustSize()
        self.set_ok_button()
        if self.path:
            self.read_loss_types_and_dmg_states_from_csv_header()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        if self.open_file_dialog():
            # read the header of the csv, so we can select from its fields
            self.read_loss_types_and_dmg_states_from_csv_header()

    def set_ok_button(self):
        self.ok_button.setEnabled(
            bool(self.path)
            and self.dmg_state_cbx.currentIndex() != -1
            and self.loss_type_cbx.currentIndex() != -1)

    def load_from_csv(self):
        if self.mode == 'testing':
            dest_shp = tempfile.mkstemp(suffix='.shp')[1]
        else:
            dest_shp = None  # the destination file will be selected via GUI
        self.layer = import_layer_from_csv(
            self, self.path_le.text(), self.output_type, self.iface,
            save_as_shp=self.save_as_shp_ckb.isChecked(), dest_shp=dest_shp)
        dmg_state = self.dmg_state_cbx.currentText()
        loss_type = self.loss_type_cbx.currentText()
        field_idx = None
        for idx, name in enumerate(self.csv_header):
            if dmg_state in name and loss_type in name and 'mean' in name:
                field_idx = idx
                break
        if field_idx is None:
            msg = ('Unable to style the layer, because the header of the csv'
                   ' file does not contain any field corresponding to the'
                   ' chosen damage state and loss type.')
            log_msg(msg, level='C', message_bar=self.iface.messageBar())
            return
        self.default_field_name = self.layer.fields()[field_idx].name()
        self.style_maps()

    def read_loss_types_and_dmg_states_from_csv_header(self):
        with open(self.path, "rb") as source:
            reader = csv.reader(source)
            self.csv_header = reader.next()
            # the header looks like:
            # asset_ref,taxonomy,lon,lat,structural~no_damage_mean,
            #    structural~no_damage_stdv,structural~slight_mean,
            #    structural~slight_stdv,...
            # we will ignore: asset_ref, taxonomy, lon, lat
            names = self.csv_header[4:]
            loss_types = []
            dmg_states = []
            for name in names:
                # each name looks like: structural~no_damage_mean
                loss_type, dmg_state_plus_stat = name.split('~')
                # dmg_state_plus_stat looks like: no_damage_mean
                dmg_state, _ = dmg_state_plus_stat.rsplit('_', 1)
                if loss_type not in loss_types:
                    loss_types.append(loss_type)
                if dmg_state not in dmg_states:
                    dmg_states.append(dmg_state)
            self.populate_loss_type_cbx(loss_types)
            self.populate_dmg_state_cbx(dmg_states)

    # def populate_taxonomies(self):
    #     # TODO: change as soon as npz risk outputs are available
    #     if self.output_type == 'dmg_by_asset':
    #         self.taxonomies.insert(0, 'Sum')
    #         self.taxonomy_cbx.clear()
    #         self.taxonomy_cbx.addItems(self.taxonomies)
    #         self.taxonomy_cbx.setEnabled(True)

    # def populate_dmg_states(self):
    #     # TODO: change as soon as npz risk outputs are available
    #     if self.output_type == 'dmg_by_asset':
    #         self.dmg_states = ['no damage']
    #         self.dmg_states.extend(self.npz_file['oqparam'].limit_states)
    #         self.dmg_state_cbx.clear()
    #         self.dmg_state_cbx.setEnabled(True)
    #         self.dmg_state_cbx.addItems(self.dmg_states)
