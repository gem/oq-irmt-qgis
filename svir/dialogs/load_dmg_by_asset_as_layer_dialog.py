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
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication,
    QgsVectorLayer, QgsProject)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.utilities.utils import (WaitCursorManager,
                                  log_msg,
                                  get_loss_types,
                                  get_irmt_version,
                                  write_metadata_to_layer,
                                  )
from svir.calculations.calculate_utils import add_attribute
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadDmgByAssetAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load dmg_by_asset from an oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='dmg_by_asset',
                 path=None, mode=None, zonal_layer_path=None,
                 engine_version=None):
        assert output_type == 'dmg_by_asset'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            zonal_layer_path=zonal_layer_path, engine_version=engine_version)

        self.setWindowTitle('Load scenario damage by asset as layer')
        self.create_load_selected_only_ckb()
        self.create_num_sites_indicator()
        self.create_rlz_or_stat_selector()
        self.create_taxonomy_selector()
        self.create_loss_type_selector()
        self.create_dmg_state_selector()
        self.create_aggregate_by_site_ckb()
        self.create_zonal_layer_selector()

        self.aggregate_by_site_ckb.toggled[bool].connect(
            self.on_aggregate_by_site_ckb_toggled)
        self.zonal_layer_gbx.toggled[bool].connect(
            self.on_zonal_layer_gbx_toggled)

        self.extract_npz_task = ExtractNpzTask(
            'Extract damage by asset', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def finalize_init(self, extracted_npz):
        self.npz_file = extracted_npz

        # NOTE: still running this synchronously, because it's small stuff
        with WaitCursorManager('Loading loss types...',
                               self.iface.messageBar()):
            self.loss_types = get_loss_types(
                self.session, self.hostname, self.calc_id,
                self.iface.messageBar())

        self.populate_out_dep_widgets()

        if self.zonal_layer_path:
            zonal_layer = self.load_zonal_layer(self.zonal_layer_path)
            self.populate_zonal_layer_cbx(zonal_layer)
        else:
            self.pre_populate_zonal_layer_cbx()
        self.adjustSize()
        self.set_ok_button()
        self.show()
        self.init_done.emit()

    def set_ok_button(self):
        self.ok_button.setEnabled(self.dmg_state_cbx.currentIndex() != -1
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
        self.dataset = self.npz_file[self.rlz_or_stat_cbx.currentText()]
        self.taxonomies = numpy.unique(self.dataset['taxonomy']).tolist()
        self.taxonomies = [taxonomy.decode('utf8')
                           for taxonomy in self.taxonomies]
        self.populate_taxonomy_cbx(self.taxonomies)
        self.set_ok_button()

    def populate_out_dep_widgets(self):
        self.populate_rlz_or_stat_cbx()
        self.populate_loss_type_cbx(self.loss_types)
        self.show_num_sites()

    def populate_taxonomy_cbx(self, taxonomies):
        self.taxonomies.insert(0, 'All')
        self.taxonomy_cbx.clear()
        self.taxonomy_cbx.addItems(taxonomies)
        self.taxonomy_cbx.setEnabled(True)

    def on_loss_type_changed(self):
        names = self.dataset[self.loss_type_cbx.currentText()].dtype.names
        self.dmg_states = []
        for dmg_state_plus_stat in names:
            # each name looks like: no_damage_mean
            dmg_state, _ = dmg_state_plus_stat.rsplit('_', 1)
            if dmg_state not in self.dmg_states:
                self.dmg_states.append(dmg_state)
        self.populate_dmg_state_cbx()

    def populate_dmg_state_cbx(self):
        self.dmg_state_cbx.clear()
        self.dmg_state_cbx.setEnabled(True)
        self.dmg_state_cbx.addItems(self.dmg_states)

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        taxonomy = kwargs['taxonomy']
        loss_type = kwargs['loss_type']
        dmg_state = kwargs['dmg_state']
        if (self.aggregate_by_site_ckb.isChecked() or
                self.zonal_layer_gbx.isChecked()):
            layer_name = "dmg_by_asset_%s_%s_%s_%s" % (
                rlz_or_stat, taxonomy, loss_type, dmg_state)
        else:  # recovery modeling
            layer_name = "dmg_by_asset_%s_%s" % (rlz_or_stat, loss_type)
        return layer_name

    def get_field_types(self, **kwargs):
        loss_type = kwargs['loss_type']
        dmg_state = kwargs['dmg_state']
        if self.aggregate_by_site_ckb.isChecked():
            ltds = "%s_%s_mean" % (loss_type, dmg_state)
            field_names = ['lon', 'lat', ltds]
            self.default_field_name = ltds
        else:
            field_names = list(self.dataset.dtype.names)
            for lt in self.loss_types:
                field_names.remove(lt)
            field_names.extend([
                '%s_%s' % (loss_type, name)
                for name in self.dataset[loss_type].dtype.names])
        if self.zonal_layer_gbx.isChecked():
            self.default_field_name = "%s_%s_mean" % (
                self.loss_type_cbx.currentText(),
                self.dmg_state_cbx.currentText())
        if self.aggregate_by_site_ckb.isChecked():
            field_types = {field_name: 'F' for field_name in field_names}
        else:
            field_types = {}
            for field_name in field_names:
                try:
                    field_types[field_name] = self.dataset.dtype[
                        field_name].kind
                except KeyError:
                    field_types[field_name] = 'F'
        return field_types

    def read_npz_into_layer(self, field_types, **kwargs):
        if self.aggregate_by_site_ckb.isChecked():
            self.read_npz_into_layer_aggr_by_site(list(field_types), **kwargs)
        else:
            # do not aggregate by site, then aggregate by zone afterwards if
            # required
            self.read_npz_into_layer_no_aggr(field_types, **kwargs)

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
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    elif field_name in data.dtype.names:
                        value = row[field_name]
                        try:
                            value = float(value)
                        except ValueError:
                            value = str(value, encoding='utf8').strip('"')
                    else:
                        value = float(
                            row[loss_type][field_name[len(loss_type)+1:]])
                    feat.setAttribute(field_names[field_name_idx], value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row['lon'], row['lat'])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def read_npz_into_layer_aggr_by_site(self, field_names, **kwargs):
        rlz_or_stat = kwargs['rlz_or_stat']
        loss_type = kwargs['loss_type']
        taxonomy = kwargs['taxonomy']
        dmg_state = kwargs['dmg_state']
        with edit(self.layer):
            feats = []
            grouped_by_site = self.group_by_site(
                self.npz_file, rlz_or_stat, loss_type, dmg_state, taxonomy)
            for row in grouped_by_site:
                # add a feature
                feat = QgsFeature(self.layer.fields())
                for field_name_idx, field_name in enumerate(field_names):
                    if field_name in ['lon', 'lat']:
                        continue
                    value = float(row[field_name_idx])
                    feat.setAttribute(field_names[field_name_idx], value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row['lon'], row['lat'])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def group_by_site(self, npz, rlz_or_stat, loss_type, dmg_state,
                      taxonomy='All'):
        F32 = numpy.float32
        dmg_by_site = collections.defaultdict(float)  # lon, lat -> dmg
        for rec in npz[rlz_or_stat]:
            if taxonomy == 'All' or taxonomy.encode('utf8') == rec['taxonomy']:
                value = rec[loss_type]['%s_mean' % dmg_state]
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
                    and rlz_or_stat != self.rlz_or_stat_cbx.currentText()):
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
                        for dmg_state in self.dmg_states:
                            if (self.load_selected_only_ckb.isChecked() and
                                    dmg_state != self.dmg_state_cbx.currentText()):  # NOQA
                                continue
                            with WaitCursorManager(
                                    'Creating layer for "%s",'
                                    ' taxonomy "%s", loss type "%s" and'
                                    ' damage state "%s"...' % (
                                    rlz_or_stat, taxonomy, loss_type,
                                    dmg_state), self.iface.messageBar()):
                                self.build_layer(
                                    rlz_or_stat, taxonomy=taxonomy,
                                    loss_type=loss_type, dmg_state=dmg_state)
                                self.style_maps(self.layer,
                                                self.default_field_name,
                                                self.iface, self.output_type)
            elif self.zonal_layer_gbx.isChecked():
                taxonomy = self.taxonomy_cbx.currentText()
                loss_type = self.loss_type_cbx.currentText()
                dmg_state = self.dmg_state_cbx.currentText()
                with WaitCursorManager(
                    'Creating layer for "%s", taxonomy "%s", loss type "%s"'
                    ' and damage state "%s"...' % (
                        rlz_or_stat, taxonomy, loss_type, dmg_state)):
                    self.build_layer(
                        rlz_or_stat, taxonomy=taxonomy, loss_type=loss_type,
                        dmg_state=dmg_state)
            else:  # recovery modeling
                for loss_type in self.loss_types:
                    if (self.load_selected_only_ckb.isChecked()
                            and loss_type != self.loss_type_cbx.currentText()):
                        continue
                    with WaitCursorManager(
                        'Creating layer for "%s" and loss_type "%s"' % (
                            rlz_or_stat, loss_type), self.iface.messageBar()):
                        self.build_layer(rlz_or_stat, loss_type=loss_type)
                        self.style_curves()
        if self.npz_file is not None:
            self.npz_file.close()

    def add_field_to_layer(self, field_name, field_type):
        # NOTE: add_attribute use the native qgis editing manager
        added_field_name = add_attribute(
            field_name, field_type, self.layer)
        return added_field_name

    def build_layer(self, rlz_or_stat=None, taxonomy=None, poe=None,
                    loss_type=None, dmg_state=None, gsim=None, imt=None,
                    boundaries=None, geometry_type='Point'):
        layer_name = self.build_layer_name(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, gsim=gsim, imt=imt)
        field_types = self.get_field_types(
            rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, imt=imt)
        field_names = field_types.keys()

        # create layer
        self.layer = QgsVectorLayer(
            "%s?crs=epsg:4326" % geometry_type, layer_name, "memory")
        for field_name, field_type in field_types.items():
            if field_name in ['lon', 'lat', 'boundary']:
                continue
            added_field_name = self.add_field_to_layer(field_name, field_type)
            if field_name != added_field_name:
                if field_name == self.default_field_name:
                    self.default_field_name = added_field_name
                # replace field_name with the actual added_field_name
                field_name_idx = field_names.index(field_name)
                field_names.remove(field_name)
                field_names.insert(field_name_idx, added_field_name)

        self.read_npz_into_layer(
            field_types, rlz_or_stat=rlz_or_stat, taxonomy=taxonomy, poe=poe,
            loss_type=loss_type, dmg_state=dmg_state, imt=imt,
            boundaries=boundaries)
        if (self.output_type == 'dmg_by_asset' and
                not self.aggregate_by_site_ckb.isChecked()):
            self.layer.setCustomProperty('output_type', 'recovery_curves')
        else:
            self.layer.setCustomProperty('output_type', self.output_type)
        investigation_time = self.get_investigation_time()
        if investigation_time is not None:
            self.layer.setCustomProperty('investigation_time',
                                         investigation_time)
        if self.engine_version is not None:
            self.layer.setCustomProperty('engine_version', self.engine_version)
        irmt_version = get_irmt_version()
        self.layer.setCustomProperty('irmt_version', irmt_version)
        self.layer.setCustomProperty('calc_id', self.calc_id)
        if poe is not None:
            self.layer.setCustomProperty('poe', poe)
        user_params = {'rlz_or_stat': rlz_or_stat,
                       'taxonomy': taxonomy,
                       'poe': poe,
                       'loss_type': loss_type,
                       'dmg_state': dmg_state,
                       'gsim': gsim,
                       'imt': imt}
        write_metadata_to_layer(
            self.drive_engine_dlg, self.output_type, self.layer, user_params)
        try:
            if (self.zonal_layer_cbx.currentText()
                    and self.zonal_layer_gbx.isChecked()):
                return
        except AttributeError:
            # the aggregation stuff might not exist for some loaders
            pass
        root = QgsProject.instance().layerTreeRoot()
        QgsProject.instance().addMapLayer(self.layer, False)
        root.insertLayer(0, self.layer)
        self.iface.setActiveLayer(self.layer)
        self.iface.zoomToActiveLayer()
        log_msg('Layer %s was created successfully' % layer_name, level='S',
                message_bar=self.iface.messageBar())
