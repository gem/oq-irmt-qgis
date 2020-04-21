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

import os
from qgis.PyQt.QtWidgets import QInputDialog, QDialog
from qgis.core import (
    QgsFeature, QgsGeometry, QgsPointXY, edit, QgsTask, QgsApplication)
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog
from svir.calculations.calculate_utils import add_attribute
from svir.utilities.utils import WaitCursorManager, log_msg, extract_npz
from svir.tasks.extract_npz_task import ExtractNpzTask


class LoadGmfDataAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load gmf_data from an oq-engine output, as layer
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type='gmf_data', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'gmf_data'
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)

        self.setWindowTitle(
            'Load ground motion fields as layer')
        self.create_num_sites_indicator()
        # NOTE: gmpe and gsim are synonyms
        self.create_rlz_or_stat_selector(
            label='Ground Motion Prediction Equation')
        # NOTE: we do not display the selector for realizations, but we can
        # still update and use its contents (e.g. to display the gmpe
        # corresponding to the chosen event)
        self.rlz_or_stat_cbx.setVisible(False)
        self.create_imt_selector()

        log_msg('Extracting number of events. Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.extract_npz_task = ExtractNpzTask(
            'Extract number of events', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, 'num_events', self.get_eid,
            self.on_extract_error)
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def get_eid(self, num_events_npz):
        num_events = num_events_npz['num_events']
        if 'GEM_QGIS_TEST' in os.environ:
            self.eid, ok = 0, True
        else:
            self.eid, ok = QInputDialog.getInt(
                self.drive_engine_dlg,
                "Select an event ID", "range (0 - %s)" % (num_events - 1),
                0, 0, num_events - 1)
        if not ok:
            self.reject()
            return
        log_msg('Extracting ground motion fields.'
                ' Watch progress in QGIS task bar',
                level='I', message_bar=self.iface.messageBar())
        self.extract_npz_task = ExtractNpzTask(
            'Extract ground motion fields', QgsTask.CanCancel, self.session,
            self.hostname, self.calc_id, self.output_type, self.finalize_init,
            self.on_extract_error, params={'event_id': self.eid})
        QgsApplication.taskManager().addTask(self.extract_npz_task)

    def finalize_init(self, gmf_data_npz):
        self.npz_file = gmf_data_npz
        self.populate_rlz_or_stat_cbx()
        self.show_num_sites()
        self.adjustSize()
        self.set_ok_button()
        self.show()
        self.init_done.emit()

    def set_ok_button(self):
        if not len(self.dataset) and 'GEM_QGIS_TEST' in os.environ:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(self.imt_cbx.currentIndex() != -1)

    def show_num_sites(self):
        # NOTE: we are assuming all realizations have the same number of sites,
        #       which is always true for scenario calculations.
        #       If different realizations have a different number of sites, we
        #       need to move this block of code inside on_rlz_or_stat_changed()
        rlz = self.rlz_or_stat_cbx.itemData(
            self.rlz_or_stat_cbx.currentIndex())
        try:
            gmf_data = self.npz_file[rlz]
        except AttributeError:
            self.num_sites_lbl.setText(self.num_sites_msg % 0)
            return
        else:
            self.num_sites_lbl.setText(self.num_sites_msg % gmf_data.shape)

    def populate_rlz_or_stat_cbx(self):
        self.rlzs_or_stats = [key for key in sorted(self.npz_file)
                              if key not in ('imtls', 'array')]
        with WaitCursorManager(
                'Extracting...', message_bar=self.iface.messageBar()):
            self.rlzs_npz = extract_npz(
                self.session, self.hostname, self.calc_id, 'realizations',
                message_bar=self.iface.messageBar(), params=None)
        # rlz[1] is the branch_path field
        self.gsims = [rlz[1].decode('utf8').strip('"')
                      for rlz in self.rlzs_npz['array']]
        self.rlz_or_stat_cbx.clear()
        self.rlz_or_stat_cbx.setEnabled(True)
        for gsim, rlz in zip(self.gsims, self.rlzs_or_stats):
            # storing gsim as text, rlz as hidden data
            self.rlz_or_stat_cbx.addItem(gsim, userData=rlz)

    def on_rlz_or_stat_changed(self):
        rlz = self.rlz_or_stat_cbx.itemData(
            self.rlz_or_stat_cbx.currentIndex())
        gmpe = self.rlz_or_stat_cbx.currentText()
        self.rlz_or_stat_lbl.setText("GMPE: %s" % gmpe)
        self.dataset = self.npz_file[rlz]
        if not len(self.dataset):
            log_msg('No data corresponds to the chosen event and GMPE',
                    level='W', message_bar=self.iface.messageBar())
            if 'GEM_QGIS_TEST' in os.environ:
                self.set_ok_button()
            return
        try:
            imts = list(self.oqparam['hazard_imtls'].keys())
        except KeyError:
            imts = list(self.oqparam['risk_imtls'].keys())
        self.imt_cbx.clear()
        self.imt_cbx.setEnabled(True)
        self.imt_cbx.addItems(imts)
        self.set_ok_button()

    def on_imt_changed(self):
        self.set_ok_button()

    def accept(self):
        if not len(self.dataset) and 'GEM_QGIS_TEST' in os.environ:
            QDialog.accept(self)
        else:
            super().accept()

    def load_from_npz(self):
        for rlz, gsim in zip(self.rlzs_or_stats, self.gsims):
            # NOTE: selecting only 1 event, we have only 1 gsim
            with WaitCursorManager('Creating layer for "%s"...'
                                   % gsim, self.iface.messageBar()):
                self.build_layer(rlz_or_stat=rlz, gsim=gsim)
                self.style_maps(self.layer, self.default_field_name,
                                self.iface, self.output_type)
        if self.npz_file is not None:
            self.npz_file.close()

    def build_layer_name(self, gsim=None, **kwargs):
        self.imt = self.imt_cbx.currentText()
        self.default_field_name = '%s-%s' % (self.imt, self.eid)
        # NOTE: assuming it's a scenario calculation
        layer_name = "scenario_gmfs_%s_eid-%s" % (gsim, self.eid)
        return layer_name

    def get_field_types(self, **kwargs):
        field_types = {name: self.dataset[name].dtype.char
                       for name in self.dataset.dtype.names}
        return field_types

    def add_field_to_layer(self, field_name, field_type):
        # TODO: assuming all attributes are numeric (to be checked!)
        field_name = "%s-%s" % (field_name, self.eid)
        added_field_name = add_attribute(field_name, field_type, self.layer)
        return added_field_name

    def read_npz_into_layer(self, field_types, rlz_or_stat, **kwargs):
        with edit(self.layer):
            feats = []
            fields = self.layer.fields()
            layer_field_names = [field.name() for field in fields]
            dataset_field_names = list(self.get_field_types().keys())
            d2l_field_names = dict(
                list(zip(dataset_field_names[2:], layer_field_names)))
            for row in self.npz_file[rlz_or_stat]:
                # add a feature
                feat = QgsFeature(fields)
                for field_name in dataset_field_names:
                    if field_name in ['lon', 'lat']:
                        continue
                    layer_field_name = d2l_field_names[field_name]
                    value = row[field_name].item()
                    if isinstance(value, bytes):
                        value = value.decode('utf8')
                    feat.setAttribute(layer_field_name, value)
                feat.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row[0], row[1])))
                feats.append(feat)
            added_ok = self.layer.addFeatures(feats)
            if not added_ok:
                msg = 'There was a problem adding features to the layer.'
                log_msg(msg, level='C', message_bar=self.iface.messageBar())
