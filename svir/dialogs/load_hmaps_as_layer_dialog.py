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
from svir.utilities.utils import (WaitCursorManager,
                                  LayerEditingManager,
                                  log_msg,
                                  )
from svir.utilities.shared import DEBUG


class LoadHazardMapsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load hazard maps from an oq-engine output, as layer
    """

    def __init__(self, iface, output_type='hmaps', path=None, mode=None):
        assert(output_type == 'hmaps')
        LoadOutputAsLayerDialog.__init__(self, iface, output_type, path, mode)
        self.file_browser_tbn.setEnabled(False)
        self.setWindowTitle(
            'Load hazard maps from NPZ, as layer')
        self.create_load_selected_only_ckb()
        self.create_rlz_selector()
        self.create_imt_selector()
        self.create_poe_selector()
        if self.path:
            self.npz_file = numpy.load(self.path, 'r')
            self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(
            bool(self.path) and self.poe_cbx.currentIndex() != -1)

    def on_rlz_changed(self):
        self.dataset = self.npz_file[self.rlz_cbx.currentText()]
        self.imts = {}
        for name in self.dataset.dtype.names[2:]:
            imt, poe = name.split('-')
            if imt not in self.imts:
                self.imts[imt] = [poe]
            else:
                self.imts[imt].append(poe)
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(self.imts.keys())
        self.set_ok_button()

    def on_imt_changed(self):
        imt = self.imt_cbx.currentText()
        self.poe_cbx.clear()
        self.poe_cbx.setEnabled(True)
        self.poe_cbx.addItems(self.imts[imt])
        self.set_ok_button()

    def populate_rlz_cbx(self):
        self.rlzs = [key for key in self.npz_file.keys()
                     if key.startswith('rlz')]
        self.rlz_cbx.clear()
        self.rlz_cbx.setEnabled(True)
        self.rlz_cbx.addItems(self.rlzs)

    def build_layer_name(self):
        rlz = self.rlz_cbx.currentText()
        # build layer name
        self.imt = self.imt_cbx.currentText()
        self.poe = self.poe_cbx.currentText()
        self.default_field_name = '%s-%s' % (self.imt, self.poe)
        layer_name = "hazard_map_%s" % rlz
        return layer_name

    def get_field_names(self):
        # get field names
        field_names = list(self.dataset.dtype.names)
        return field_names

    def add_field_to_layer(self, field_name):
        # NOTE: add_numeric_attribute uses LayerEditingManager
        added_field_name = add_numeric_attribute(
            field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names):
        with LayerEditingManager(self.layer, 'Reading npz', DEBUG):
            feats = []
            for row in self.dataset:
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    # NOTE: without casting to float, it produces a
                    #       null because it does not recognize the
                    #       numpy type
                    value = float(row[field_name_idx])
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPoint(
                    QgsPoint(row[0], row[1])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats, makeSelected=False)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_npz(self):
        for rlz in self.rlzs:
            if (self.load_selected_only_ckb.isChecked()
                    and rlz != self.rlz_cbx.currentText()):
                continue
            with WaitCursorManager('Creating layer for '
                                   ' realization "%s"...' % rlz,
                                   self.iface):
                self.build_layer(rlz)
                self.style_maps()
        if self.npz_file is not None:
            self.npz_file.close()
