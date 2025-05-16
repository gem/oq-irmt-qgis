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
from qgis.core import (
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.utilities.utils import WaitCursorManager, log_msg, get_attrs
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadDamagesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load damages-rlzs or damages-stats from an
    oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='damages-rlzs',
                 path=None, mode=None, zonal_layer_path=None,
                 engine_version=None, calculation_mode=None):
        assert output_type in ('damages-rlzs', 'damages-stats')
        super().__init__(
            drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            zonal_layer_path=zonal_layer_path, engine_version=engine_version,
            calculation_mode=calculation_mode)

        self.setWindowTitle(
            'Load scenario damages/consequences by asset as layer')
        self.create_load_selected_only_ckb()
        self.create_num_sites_indicator()
        self.create_rlz_or_stat_selector()
        self.create_taxonomy_selector()

        attrs = get_attrs(self.session, self.hostname, self.calc_id,
                          self.iface.messageBar())
        self.limit_states = attrs['limit_states']
        self.loss_types = attrs['loss_types']
        self.dmg_states = ['no_damage'] + self.limit_states
        self.consequences = attrs['consequences']

        self.create_loss_type_selector()
        self.create_damage_or_consequences_selector()  # damages or consequences
        self.create_dmg_state_selector()
        self.create_consequence_selector()
        self.create_aggregate_by_site_ckb()
        self.create_zonal_layer_selector()

        self.aggregate_by_site_ckb.toggled[bool].connect(
            self.on_aggregate_by_site_ckb_toggled)
        self.zonal_layer_gbx.toggled[bool].connect(
            self.on_zonal_layer_gbx_toggled)

        log_msg('Extracting output data. Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.extract_npz_task = ExtractNpzTask(
            'Extract damage by asset', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def finalize_init(self, extracted_npz):
        self.npz_file = extracted_npz
        self.populate_out_dep_widgets()
        if self.zonal_layer_path:
            zonal_layer = self.load_zonal_layer(self.zonal_layer_path)
            self.populate_zonal_layer_cbx(zonal_layer)
        else:
            self.pre_populate_zonal_layer_cbx()
        self.adjustSize()
        self.set_ok_button()
        self.show()
        self.init_done.emit(self)

    def set_ok_button(self):
        if not hasattr(self, 'damage_or_consequences'):
            self.ok_button.setEnabled(False)
            return
        if self.damage_or_consequences == 'Damage':
            self.ok_button.setEnabled(self.dmg_state_cbx.currentIndex() != -1
                                      and self.loss_type_cbx.currentIndex() != -1)
        else:  # 'Consequences'
            self.ok_button.setEnabled(self.consequence_cbx.currentIndex() != -1
                                      and self.loss_type_cbx.currentIndex() != -1)

    def on_aggregate_by_site_ckb_toggled(self, on):
        if on:
            self.zonal_layer_gbx.setChecked(False)
            self.load_selected_only_ckb.setEnabled(True)

    def on_zonal_layer_gbx_toggled(self, on):
        if on:
            self.aggregate_by_site_ckb.setChecked(False)
            self.load_selected_only_ckb.setEnabled(False)
        else:
            self.load_selected_only_ckb.setEnabled(True)

    def on_rlz_or_stat_changed(self):
        self.dataset = self.npz_file[self.rlz_or_stat_cbx.currentData()]
        self.taxonomies = numpy.unique(self.dataset['taxonomy']).tolist()
        self.taxonomies = [taxonomy.decode('utf8')
                           for taxonomy in self.taxonomies]
        self.populate_taxonomy_cbx(self.taxonomies)
        self.set_ok_button()

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.populate_loss_type_cbx(self.loss_types)
        self.populate_damage_or_consequences_cbx()
        self.populate_dmg_state_cbx()
        self.populate_consequence_cbx()
        self.show_num_sites()

    def populate_damage_or_consequences_cbx(self):
        items = ['Damage']
        if self.consequences:
            items.append('Consequences')
        self.damage_or_consequences_cbx.addItems(items)

    def on_damage_or_consequences_changed(self, text):
        self.damage_or_consequences = text
        if self.damage_or_consequences == 'Damage':
            self.consequence_lbl.hide()
            self.consequence_cbx.hide()
            self.dmg_state_lbl.show()
            self.dmg_state_cbx.show()
        else:
            self.dmg_state_lbl.hide()
            self.dmg_state_cbx.hide()
            self.consequence_lbl.show()
            self.consequence_cbx.show()

    def populate_taxonomy_cbx(self, taxonomies):
        self.taxonomies.insert(0, 'All')
        self.taxonomy_cbx.clear()
        self.taxonomy_cbx.addItems(taxonomies)
        self.taxonomy_cbx.setEnabled(True)

    def populate_dmg_state_cbx(self):
        self.dmg_state_cbx.clear()
        self.dmg_state_cbx.setEnabled(True)
        self.dmg_state_cbx.addItems(self.dmg_states)

    def populate_consequence_cbx(self):
        self.consequence_cbx.clear()
        self.consequence_cbx.setEnabled(True)
        self.consequence_cbx.addItems(self.consequences)

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        taxonomy = kwargs['taxonomy']
        loss_type = kwargs['loss_type']
        dmg_state = kwargs['dmg_state']
        consequence = kwargs['consequence']
        rlzs_or_stats = 'rlzs' if self.output_type == 'damages-rlzs' else 'stats'
        layer_name = f'damages-{rlzs_or_stats}_{rlz_or_stat}_'
        if (self.aggregate_by_site_ckb.isChecked() or
                self.zonal_layer_gbx.isChecked()):
            if self.damage_or_consequences == 'Damage':
                layer_name += f'{taxonomy}_{loss_type}_{dmg_state}'
            else:
                layer_name += f'{taxonomy}_{loss_type}_{consequence}'
        else:  # also needed for recovery modeling
            layer_name += loss_type
        return layer_name

    def get_field_types(self, **kwargs):
        loss_type = kwargs['loss_type']
        dmg_state = kwargs['dmg_state']
        consequence = kwargs['consequence']
        if self.aggregate_by_site_ckb.isChecked():
            if self.damage_or_consequences == 'Damage':
                ltds = "%s_%s_mean" % (loss_type, dmg_state)
            else:  # 'Consequences'
                ltds = "%s_%s_mean" % (loss_type, consequence)
            field_names = ['lon', 'lat', ltds]
            self.default_field_name = ltds
        else:
            field_names = list(self.dataset.dtype.names)
        if self.zonal_layer_gbx.isChecked():
            if self.damage_or_consequences == 'Damage':
                self.default_field_name = "%s-%s" % (
                    self.loss_type_cbx.currentText(),
                    self.dmg_state_cbx.currentText())
            else:  # 'Consequences'
                self.default_field_name = "%s-%s" % (
                    self.loss_type_cbx.currentText(),
                    self.consequence_cbx.currentText())
        if self.aggregate_by_site_ckb.isChecked():
            field_types = {field_name: 'F' for field_name in field_names}
        else:
            field_types = {}
            for field_name in field_names:
                try:
                    field_types[field_name] = self.dataset.dtype[field_name].kind
                except KeyError:
                    field_types[field_name] = 'F'
        return field_types

    def read_npz_into_layer(self, field_types, **kwargs):
        if self.aggregate_by_site_ckb.isChecked():
            self.layer = self.read_npz_into_layer_aggr_by_site(
                field_types, **kwargs)
        else:
            # do not aggregate by site, then aggregate by zone afterwards if
            # required
            self.layer = self.read_npz_into_layer_no_aggr(
                field_types, **kwargs)
        return self.layer

    def read_npz_into_layer_no_aggr(self, field_types, **kwargs):
        field_names = list(field_types)
        rlz_or_stat = kwargs['rlz_or_stat']
        loss_type = kwargs['loss_type']
        with edit(self.layer):
            feats = []
            data = self.npz_file[rlz_or_stat]
            for row in data:
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name in field_names:
                    if field_name in ['lon', 'lat']:
                        continue
                    elif field_name in data.dtype.names:
                        value = row[field_name].item()
                        if isinstance(value, bytes):
                            value = value.decode('utf8').strip('"')
                    else:
                        value = row[loss_type][
                            field_name[len(loss_type)+1:]].item()
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row['lon'], row['lat'])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
        return self.layer

    def read_npz_into_layer_aggr_by_site(self, field_types, **kwargs):
        field_names = list(field_types)
        rlz_or_stat = kwargs['rlz_or_stat']
        loss_type = kwargs['loss_type']
        taxonomy = kwargs['taxonomy']
        dmg_state = kwargs['dmg_state']
        consequence = kwargs['consequence']
        with edit(self.layer):
            feats = []
            grouped_by_site = self.group_by_site(
                self.npz_file, rlz_or_stat, loss_type, dmg_state, consequence, taxonomy)
            for row in grouped_by_site:
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    value = row[field_name_idx].item()
                    if isinstance(value, bytes):
                        value = value.decode('utf8')
                    feat.setAttribute(field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row['lon'], row['lat'])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
        return self.layer

    def group_by_site(self, npz, rlz_or_stat, loss_type, dmg_state, consequence,
                      taxonomy='All'):
        F32 = numpy.float32
        dmg_by_site = collections.defaultdict(float)  # lon, lat -> dmg
        for rec in npz[rlz_or_stat]:
            if taxonomy == 'All' or taxonomy.encode('utf8') == rec['taxonomy']:
                if self.damage_or_consequences == 'Damage':
                    value = rec[f'{loss_type}-{dmg_state}']
                else:
                    value = rec[f'{loss_type}-{consequence}']
                dmg_by_site[rec['lon'], rec['lat']] += value
        data = numpy.zeros(
            len(dmg_by_site),
            [('lon', F32), ('lat', F32), (loss_type, F32)])
        for i, (lon, lat) in enumerate(sorted(dmg_by_site)):
            data[i] = (lon, lat, dmg_by_site[lon, lat])
        return data

    def load_from_npz(self):
        for rlz_or_stat in self.rlzs_or_stats:
            if (self.load_selected_only_ckb.isChecked()
                    and rlz_or_stat != self.rlz_or_stat_cbx.currentData()):
                continue
            if self.aggregate_by_site_ckb.isChecked():
                for taxonomy in self.taxonomies:
                    if (self.load_selected_only_ckb.isChecked()
                            and taxonomy != self.taxonomy_cbx.currentText()):
                        continue
                    for loss_type in self.loss_types:
                        if (self.load_selected_only_ckb.isChecked() and
                                loss_type != self.loss_type_cbx.currentText()):
                            continue
                        if self.damage_or_consequences == 'Damage':
                            for dmg_state in self.dmg_states:
                                if (self.load_selected_only_ckb.isChecked() and
                                        dmg_state != self.dmg_state_cbx.currentText()):  # NOQA
                                    continue
                                with WaitCursorManager(
                                        'Creating layer for "%s",'
                                        ' taxonomy "%s", loss type "%s" and'
                                        ' damage state "%s"...' % (
                                            rlz_or_stat, taxonomy, loss_type,
                                            dmg_state),
                                        self.iface.messageBar()):
                                    self.layer = self.build_layer(
                                        rlz_or_stat, taxonomy=taxonomy,
                                        loss_type=loss_type,
                                        dmg_state=dmg_state)
                                    self.style_maps(
                                        self.layer, self.default_field_name,
                                        self.iface, self.output_type)
                        else:  # 'Consequences'
                            for consequence in self.consequences:
                                if (self.load_selected_only_ckb.isChecked() and
                                        consequence != self.consequence_cbx.currentText()):  # NOQA
                                    continue
                                with WaitCursorManager(
                                        'Creating layer for "%s",'
                                        ' taxonomy "%s", loss type "%s" and'
                                        ' consequence "%s"...' % (
                                            rlz_or_stat, taxonomy, loss_type,
                                            consequence),
                                        self.iface.messageBar()):
                                    self.layer = self.build_layer(
                                        rlz_or_stat, taxonomy=taxonomy,
                                        loss_type=loss_type,
                                        consequence=consequence)
                                    self.style_maps(
                                        self.layer, self.default_field_name,
                                        self.iface, self.output_type)
            elif self.zonal_layer_gbx.isChecked():
                taxonomy = self.taxonomy_cbx.currentText()
                loss_type = self.loss_type_cbx.currentText()
                dmg_state = self.dmg_state_cbx.currentText()
                consequence = self.consequence_cbx.currentText()

                if self.damage_or_consequences == 'Damage':
                    with WaitCursorManager(
                        'Creating layer for "%s", taxonomy "%s", loss type "%s"'
                        ' and damage state "%s"...' % (
                            rlz_or_stat, taxonomy, loss_type, dmg_state)):
                        self.layer = self.build_layer(
                            rlz_or_stat, taxonomy=taxonomy, loss_type=loss_type,
                            dmg_state=dmg_state, set_visible=False)
                else:  # 'Consequences'
                    with WaitCursorManager(
                        'Creating layer for "%s", taxonomy "%s", loss type "%s"'
                        ' and consequence "%s"...' % (
                            rlz_or_stat, taxonomy, loss_type, consequence)):
                        self.layer = self.build_layer(
                            rlz_or_stat, taxonomy=taxonomy, loss_type=loss_type,
                            consequence=consequence, set_visible=False)
                self.style_maps(self.layer, self.default_field_name,
                                self.iface, self.output_type)

            else:  # also needed for recovery modeling
                for loss_type in self.loss_types:
                    if (self.load_selected_only_ckb.isChecked()
                            and loss_type != self.loss_type_cbx.currentText()):
                        continue
                    with WaitCursorManager(
                        'Creating layer for "%s" and loss_type "%s"' % (
                            rlz_or_stat, loss_type), self.iface.messageBar()):
                        self.layer = self.build_layer(
                            rlz_or_stat, loss_type=loss_type)
                        self.style_curves()
