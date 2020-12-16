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
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication,
    QgsProject)
from qgis.PyQt.QtCore import Qt
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.utilities.utils import WaitCursorManager, log_msg
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadHazardMapsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load hazard maps from an oq-engine output, as layer
    """
    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='hmaps', path=None, mode=None,
                 engine_version=None, calculation_mode=None):
        assert output_type == 'hmaps'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version, calculation_mode=calculation_mode)

        self.setWindowTitle(
            'Load hazard maps as layer')
        self.create_num_sites_indicator()
        self.create_single_layer_ckb()
        self.create_load_one_layer_per_stat_ckb()
        self.create_rlz_or_stat_selector(all_ckb=True)
        self.create_imt_selector(all_ckb=True)
        self.create_poe_selector(all_ckb=True)
        self.create_show_return_period_ckb()

        self.load_single_layer_ckb.stateChanged[int].connect(
            self.on_load_single_layer_ckb_stateChanged)
        self.load_one_layer_per_stat_ckb.stateChanged[int].connect(
            self.on_load_one_layer_per_stat_ckb_stateChanged)

        log_msg('Extracting hazard maps.'
                ' Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.extract_npz_task = ExtractNpzTask(
            'Extract hazard maps', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def on_load_single_layer_ckb_stateChanged(self, state):
        self.load_one_layer_per_stat_ckb.setDisabled(state)
        self.load_all_rlzs_or_stats_chk.setDisabled(state)
        if state == Qt.Checked:
            self.load_all_rlzs_or_stats_chk.setChecked(True)
        self.cascade_selections(state)

    def on_load_one_layer_per_stat_ckb_stateChanged(self, state):
        self.load_single_layer_ckb.setDisabled(state)
        self.cascade_selections(state)

    def cascade_selections(self, state):
        if state == Qt.Checked:
            self.show_return_period_chk.setChecked(False)
            self.show_return_period_chk.setEnabled(False)
            self.load_all_poes_chk.setChecked(True)
            self.load_all_poes_chk.setEnabled(False)
            self.poe_cbx.setEnabled(True)
            self.poe_lbl.setText(
                'Probability of Exceedance (used for styling)')
            self.load_all_imts_chk.setChecked(True)
            self.load_all_imts_chk.setEnabled(False)
            self.imt_cbx.setEnabled(True)
            self.imt_lbl.setText(
                'Intensity Measure Type (used for styling)')
        else:
            self.show_return_period_chk.setEnabled(True)
            self.load_all_poes_chk.setChecked(False)
            self.load_all_poes_chk.setEnabled(True)
            self.poe_cbx.setEnabled(True)
            self.poe_lbl.setText(
                'Probability of Exceedance')
            self.load_all_imts_chk.setChecked(False)
            self.load_all_imts_chk.setEnabled(True)
            self.imt_cbx.setEnabled(True)
            self.imt_lbl.setText(
                'Intensity Measure Type')

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
        self.imts = {imt: self.dataset[imt].dtype.names
                     for imt in self.dataset.dtype.names}
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(list(self.imts))
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

    def build_layer_name(self, rlz_or_stat=None, **kwargs):
        investigation_time = self.get_investigation_time()
        if self.load_single_layer_ckb.isChecked():
            rlz_or_stat = self.rlz_or_stat_cbx.currentText()
            imt = self.imt_cbx.currentText()
            poe = self.poe_cbx.currentText()
            self.default_field_name = '%s-%s-%s' % (rlz_or_stat, imt, poe)
            return "hmap_%sy" % investigation_time
        elif self.load_one_layer_per_stat_ckb.isChecked():
            imt = self.imt_cbx.currentText()
            poe = self.poe_cbx.currentText()
        else:
            imt = kwargs['imt']
            poe = kwargs['poe']
        self.default_field_name = '%s-%s' % (imt, poe)
        if self.load_one_layer_per_stat_ckb.isChecked():
            layer_name = "hmap_%s_%sy" % (
                rlz_or_stat, investigation_time)
        elif self.show_return_period_chk.isChecked():
            return_period = int(float(investigation_time) / float(poe))
            layer_name = "hmap_%s_%s_%syr" % (
                rlz_or_stat, imt, return_period)
        else:
            layer_name = "hmap_%s_%s_poe-%s_%sy" % (
                rlz_or_stat, imt, poe, investigation_time)
        return layer_name

    def get_field_types(self, **kwargs):
        field_types = {}
        if self.load_single_layer_ckb.isChecked():
            for rlz_or_stat in self.rlzs_or_stats:
                for imt in self.imts:
                    for poe in self.imts[imt]:
                        field_name = "%s-%s-%s" % (rlz_or_stat, imt, poe)
                        field_types[field_name] = 'F'
        elif self.load_one_layer_per_stat_ckb.isChecked():
            for imt in self.imts:
                for poe in self.imts[imt]:
                    field_name = "%s-%s" % (imt, poe)
                    field_types[field_name] = 'F'
        else:
            imt = kwargs['imt']
            poe = kwargs['poe']
            field_name = '%s-%s' % (imt, poe)
            field_types[field_name] = 'F'
        return field_types

    def read_npz_into_layer(self, field_types, **kwargs):
        with edit(self.layer):
            lons = self.npz_file['all']['lon']
            lats = self.npz_file['all']['lat']
            feats = []
            if self.load_single_layer_ckb.isChecked():
                all_data = self.npz_file['all']
                for row_idx, row in enumerate(all_data):
                    # add a feature
                    feat = QgsFeature(self.layer.fields())
                    feat.setGeometry(QgsGeometry.fromPointXY(
                        QgsPointXY(lons[row_idx], lats[row_idx])))
                    for field_name in field_types:
                        # NOTE: example field_name == 'quantile-0.15-PGA-0.01'
                        rlz_or_stat, imt, poe = field_name.rsplit('-', 2)
                        value = row[rlz_or_stat][imt][poe].item()
                        if isinstance(value, bytes):
                            value = value.decode('utf8')
                        feat.setAttribute(field_name, value)
                    feats.append(feat)
            else:
                for row_idx, row in enumerate(self.dataset):
                    # add a feature
                    feat = QgsFeature(self.layer.fields())
                    for field_name in field_types:
                        # NOTE: example field_name == 'PGA-0.01'
                        imt, poe = field_name.split('-')
                        value = row[imt][poe].item()
                        if isinstance(value, bytes):
                            value = value.decode('utf8')
                        feat.setAttribute(field_name, value)
                    feat.setGeometry(QgsGeometry.fromPointXY(
                        QgsPointXY(lons[row_idx], lats[row_idx])))
                    feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())

    def load_from_npz(self):
        ret_per_groups = {}
        poes = set()
        for imt in self.imts:
            for poe in self.imts[imt]:
                poes.add(poe)
        for poe in poes:
            root = QgsProject.instance().layerTreeRoot()
            ret_per_groups[poe] = root.insertGroup(0, 'POE_%s' % poe)
        if self.load_single_layer_ckb.isChecked():
            with WaitCursorManager(
                    'Creating layer...', self.iface.messageBar()):
                self.build_layer()
                style_manager = self.layer.styleManager()
                for field_name in [field.name()
                                   for field in self.layer.fields()]:
                    style_manager.addStyleFromLayer(field_name)
                    style_manager.setCurrentStyle(field_name)
                    self.style_maps(self.layer, field_name,
                                    self.iface, self.output_type,
                                    repaint=False)
                style_manager.setCurrentStyle(self.default_field_name)
                self.layer.triggerRepaint()
                self.iface.setActiveLayer(self.layer)
                self.iface.zoomToActiveLayer()
                # NOTE QGIS3: probably not needed
                # iface.layerTreeView().refreshLayerSymbology(layer.id())
                self.iface.mapCanvas().refresh()
        else:
            for rlz_or_stat in self.rlzs_or_stats:
                if (not self.load_all_rlzs_or_stats_chk.isChecked()
                        and rlz_or_stat != self.rlz_or_stat_cbx.currentText()):
                    continue
                elif self.load_one_layer_per_stat_ckb.isChecked():
                    with WaitCursorManager(
                            'Creating layer for "%s"...' % rlz_or_stat,
                            self.iface.messageBar()):
                        self.build_layer(rlz_or_stat)
                        style_manager = self.layer.styleManager()
                        for field_name in [field.name()
                                           for field in self.layer.fields()]:
                            style_manager.addStyleFromLayer(field_name)
                            style_manager.setCurrentStyle(field_name)
                            self.style_maps(self.layer, field_name,
                                            self.iface, self.output_type,
                                            repaint=False)
                        style_manager.setCurrentStyle(self.default_field_name)
                        self.layer.triggerRepaint()
                        self.iface.setActiveLayer(self.layer)
                        self.iface.zoomToActiveLayer()
                        # NOTE QGIS3: probably not needed
                        # iface.layerTreeView().refreshLayerSymbology(layer.id())
                        self.iface.mapCanvas().refresh()
                else:
                    for imt in self.imts:
                        if (not self.load_all_imts_chk.isChecked()
                                and imt != self.imt_cbx.currentText()):
                            continue
                        for poe in self.imts[imt]:
                            if (not self.load_all_poes_chk.isChecked()
                                    and poe != self.poe_cbx.currentText()):
                                continue
                            with WaitCursorManager(
                                    'Creating layer for "%s, %s, %s"...' % (
                                        rlz_or_stat, imt, poe),
                                    self.iface.messageBar()):
                                self.build_layer(
                                    rlz_or_stat, imt=imt, poe=poe,
                                    add_to_group=ret_per_groups[poe])
                                # NOTE: set sgc_style=True to use SGC settings
                                # for hazard maps styling
                                self.style_maps(self.layer,
                                                self.default_field_name,
                                                self.iface,
                                                self.output_type,
                                                use_sgc_style=False)
