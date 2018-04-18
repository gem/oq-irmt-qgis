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
import collections
from qgis.core import QgsFeature, QgsGeometry, QgsPoint
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_numeric_attribute
from svir.utilities.utils import (WaitCursorManager,
                                  LayerEditingManager,
                                  log_msg,
                                  extract_npz,
                                  get_loss_types,
                                  )
from svir.utilities.shared import DEBUG


class LoadLossesByAssetAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load losses by asset or average asset losses from an
    oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type=None,
                 path=None, mode=None, zonal_layer_path=None):
        assert output_type in ('losses_by_asset', 'avg_losses-stats')
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type, path, mode, zonal_layer_path)

        if self.output_type == 'losses_by_asset':
            self.setWindowTitle(
                'Load losses by asset, aggregated by location, as layer')
        elif self.output_type == 'avg_losses-stats':
            self.setWindowTitle(
                'Load average asset losses (statistics),'
                ' aggregated by location, as layer')
        else:
            raise NotImplementedError(output_type)
        self.create_load_selected_only_ckb()
        self.create_num_sites_indicator()
        self.create_rlz_or_stat_selector()
        self.create_taxonomy_selector()
        self.create_loss_type_selector()
        self.create_zonal_layer_selector()

        # NOTE: it's correct to use 'losses_by_asset' instead of output_type,
        #       both in case of losses_by_asset and in case of avg_losses-stats
        self.npz_file = extract_npz(
            session, hostname, calc_id, 'losses_by_asset',
            message_bar=iface.messageBar(), params=None)

        self.loss_types = get_loss_types(
            session, hostname, calc_id, self.iface.messageBar())

        self.populate_out_dep_widgets()
        if self.zonal_layer_path:
            # NOTE: it happens while running tests. We need to avoid
            #       overwriting the original layer, so we make a copy of it.
            zonal_layer_plus_stats = self.load_zonal_layer(
                self.zonal_layer_path, make_a_copy=True)
            self.populate_zonal_layer_cbx(zonal_layer_plus_stats)
        else:
            self.pre_populate_zonal_layer_cbx()
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file[self.rlz_or_stat_cbx.currentText()]
        self.taxonomies = numpy.unique(self.dataset['taxonomy']).tolist()
        self.populate_taxonomy_cbx(self.taxonomies)
        self.set_ok_button()

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.populate_loss_type_cbx(self.loss_types)
        self.show_num_sites()

    def populate_taxonomy_cbx(self, taxonomies):
        taxonomies.insert(0, 'All')
        self.taxonomy_cbx.clear()
        self.taxonomy_cbx.addItems(taxonomies)
        self.taxonomy_cbx.setEnabled(True)

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        taxonomy = kwargs['taxonomy']
        loss_type = kwargs['loss_type']
        if self.output_type == 'losses_by_asset':
            layer_name = "losses_by_asset_%s_%s_%s" % (
                rlz_or_stat, taxonomy, loss_type)
        elif self.output_type == 'avg_losses-stats':
            layer_name = "avg_losses-stats_%s_%s_%s" % (
                rlz_or_stat, taxonomy, loss_type)
        else:
            raise NotImplementedError(self.output_type)
        return layer_name

    def get_field_names(self, **kwargs):
        loss_type = kwargs['loss_type']
        field_names = ['lon', 'lat', loss_type]
        self.default_field_name = loss_type
        return field_names

    def add_field_to_layer(self, field_name):
        # NOTE: add_numeric_attribute uses LayerEditingManager
        added_field_name = add_numeric_attribute(
            field_name, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_names, **kwargs):
        rlz_or_stat = kwargs['rlz_or_stat']
        loss_type = kwargs['loss_type']
        taxonomy = kwargs['taxonomy']
        with LayerEditingManager(self.layer, 'Reading npz', DEBUG):
            feats = []
            grouped_by_site = self.group_by_site(
                self.npz_file, rlz_or_stat, loss_type, taxonomy)
            for row in grouped_by_site:
                # add a feature
                feat = QgsFeature(self.layer.pendingFields())
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    value = float(row[field_name_idx])
                    feat.setAttribute(field_names[field_name_idx], value)
                feat.setGeometry(QgsGeometry.fromPoint(
                    QgsPoint(row['lon'], row['lat'])))
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
            for taxonomy in self.taxonomies:
                if (self.load_selected_only_ckb.isChecked()
                        and taxonomy != self.taxonomy_cbx.currentText()):
                    continue
                for loss_type in self.loss_types:
                    if (self.load_selected_only_ckb.isChecked()
                            and loss_type != self.loss_type_cbx.currentText()):
                        continue
                    with WaitCursorManager(
                            'Creating layer for "%s", '
                            ' taxonomy "%s" and loss type "%s"...' % (
                            rlz_or_stat, taxonomy, loss_type),
                            self.iface.messageBar()):
                        self.build_layer(rlz_or_stat, taxonomy=taxonomy,
                                         loss_type=loss_type)
                        self.style_maps()
        if self.npz_file is not None:
            self.npz_file.close()

    def group_by_site(self, npz, rlz_or_stat, loss_type, taxonomy='All'):
        # example:
        # npz = numpy.load(npzfname)
        # print(group_by_site(npz, 'rlz-000', 'structural_ins', '"tax1"'))
        F32 = numpy.float32
        loss_by_site = collections.defaultdict(float)  # lon, lat -> loss
        for rec in npz[rlz_or_stat]:
            if taxonomy == 'All' or taxonomy == rec['taxonomy']:
                loss_by_site[rec['lon'], rec['lat']] += rec[loss_type]
        data = numpy.zeros(len(loss_by_site),
                           [('lon', F32), ('lat', F32), (loss_type, F32)])
        for i, (lon, lat) in enumerate(sorted(loss_by_site)):
            data[i] = (lon, lat, loss_by_site[lon, lat])
        return data
