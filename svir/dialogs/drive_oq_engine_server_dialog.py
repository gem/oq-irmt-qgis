# -*- coding: utf-8 -*-
#/***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2016 by GEM Foundation
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
import json
import tempfile
import zipfile
from qgis.gui import QgsMessageBar
# from qgis.core import (QgsVectorLayer,
#                        QgsFeature,
#                        QgsPoint,
#                        QgsGeometry,
#                        QgsMapLayerRegistry,
#                        QgsSymbolV2,
#                        QgsVectorGradientColorRampV2,
#                        QgsGraduatedSymbolRendererV2,
#                        QgsRendererRangeV2,
#                        )
from PyQt4.QtCore import pyqtSlot, QDir, Qt, QObject, SIGNAL, QTimer

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QTableWidgetItem,
                         QAbstractItemView,
                         QPushButton,
                         QFileDialog,
                         # QColor,
                         )
# from openquake.baselib import hdf5
from svir.third_party.requests import Session
from svir.ui.ui_drive_engine_server import Ui_DriveEngineServerDialog
# from svir.utilities.shared import DEBUG
from svir.utilities.utils import (WaitCursorManager,
                                  get_engine_credentials,
                                  engine_login,
                                  log_msg,
                                  tr,
                                  ask_for_download_destination_folder,
                                  )
from svir.dialogs.load_hdf5_as_layer_dialog import LoadHdf5AsLayerDialog
from svir.dialogs.load_geojson_as_layer_dialog import LoadGeoJsonAsLayerDialog
# from svir.calculations.calculate_utils import add_numeric_attribute


class DriveOqEngineServerDialog(QDialog):
    """
    FIXME
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_DriveEngineServerDialog()
        self.ui.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        # self.ok_button.setDisabled(True)
        # self.ui.open_hdfview_btn.setDisabled(True)

        # keep track of the log lines acquired for each calculation
        self.calc_log_line = {}
        self.session = None
        self.hostname = None
        self.login()
        self.refresh_calc_list()
        self.timer = QTimer()
        QObject.connect(
            self.timer, SIGNAL('timeout()'), self.refresh_calc_list)
        self.timer.start(4000)  # refresh calc list time in milliseconds
        self.finished.connect(self.stop_timer)

    def login(self):
        self.session = Session()
        self.hostname, username, password = get_engine_credentials(self.iface)
        with WaitCursorManager('Logging in...', self.iface):
            engine_login(self.hostname, username, password, self.session)

    def refresh_calc_list(self):
        calc_list_url = "%s/v1/calc/list?relevant=true" % self.hostname
        # with WaitCursorManager('Getting list of calculations...', self.iface):
        with WaitCursorManager():
            resp = self.session.get(calc_list_url, timeout=10)
            calc_list = json.loads(resp.text)
        if not calc_list:
            # empty list
            while self.ui.calc_list_tbl.rowCount() > 0:
                self.ui.calc_list_tbl.removeRow(0)
            return
        exclude = ['url', 'is_running']
        selected_keys = [key for key in sorted(calc_list[0].keys())
                         if key not in exclude]
        actions = [
            {'label': 'Console', 'bg_color': 'blue', 'txt_color': 'white'},
            {'label': 'Remove', 'bg_color': 'red', 'txt_color': 'white'},
            {'label': 'Outputs', 'bg_color': 'blue', 'txt_color': 'white'},
            {'label': 'Run Risk', 'bg_color': 'white', 'txt_color': 'black'}
        ]
        self.ui.calc_list_tbl.setRowCount(len(calc_list))
        self.ui.calc_list_tbl.setColumnCount(
            len(selected_keys) + len(actions))
        self.ui.calc_list_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for row, calc in enumerate(calc_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                value = calc_list[row][key]
                item.setData(Qt.DisplayRole, value)
                # set default colors
                row_bg_color = Qt.white
                row_txt_color = Qt.black
                if calc['status'] == 'failed':
                    row_bg_color = Qt.red
                    row_txt_color = Qt.white
                elif calc['status'] == 'complete':
                    row_bg_color = Qt.green
                    row_txt_color = Qt.white
                item.setBackgroundColor(row_bg_color)
                item.setTextColor(row_txt_color)
                self.ui.calc_list_tbl.setItem(row, col, item)
            for col, action in enumerate(actions, len(selected_keys)):
                button = QPushButton()
                button.setText(action['label'])
                style = 'background-color: %s; color: %s' % (
                    action['bg_color'], action['txt_color'])
                button.setStyleSheet(style)
                QObject.connect(
                    button, SIGNAL("clicked()"),
                    lambda calc_id=calc['id'], action=action['label']: (
                        self.on_calc_action_btn_clicked(calc_id, action)))
                self.ui.calc_list_tbl.setCellWidget(row, col, button)
        col_names = [key.capitalize() for key in selected_keys]
        empty_col_names = ['' for action in actions]
        headers = col_names + empty_col_names
        self.ui.calc_list_tbl.setHorizontalHeaderLabels(headers)
        self.ui.calc_list_tbl.resizeColumnsToContents()
        self.ui.calc_list_tbl.resizeRowsToContents()

    def on_calc_action_btn_clicked(self, calc_id, action):
        if action == 'Console':
            calc_log = self.get_calc_log(calc_id)
            log_msg(calc_log, tag='Calculation %s' % calc_id)
        elif action == 'Remove':
            self.remove_calc(calc_id)
        elif action == 'Outputs':
            output_list = self.get_output_list(calc_id)
            self.show_output_list(output_list)
        elif action == 'Run Risk':
            self.run_risk(calc_id)
        else:
            raise NotImplementedError(action)

    def get_calc_log(self, calc_id):
        if calc_id not in self.calc_log_line:
            self.calc_log_line[calc_id] = 0
        start = self.calc_log_line[calc_id]
        stop = ''  # get until the end
        calc_log_url = "%s/v1/calc/%s/log/%s:%s" % (
            self.hostname, calc_id, start, stop)
        with WaitCursorManager('Getting list of outputs...', self.iface):
            resp = self.session.get(calc_log_url, timeout=10)
            calc_log = json.loads(resp.text)
            self.calc_log_line[calc_id] = start + len(calc_log)
            return '\n'.join([','.join(row) for row in calc_log])

    def remove_calc(self, calc_id):
        calc_remove_url = "%s/v1/calc/%s/remove" % (self.hostname, calc_id)
        with WaitCursorManager('Removing calculation...', self.iface):
            resp = self.session.post(calc_remove_url, timeout=10)
        if resp.ok:
            self.iface.messageBar().pushMessage(
                tr("Info"),
                'Calculation %s successfully removed' % calc_id,
                level=QgsMessageBar.INFO,
                duration=8)
            self.refresh_calc_list()
        else:
            self.iface.messageBar().pushMessage(
                tr("Error"),
                'Unable to remove calculation %s' % calc_id,
                level=QgsMessageBar.CRITICAL)
        return

    def run_risk(self, calc_id):
        text = self.tr('Select the files needed to run the calculation')
        file_names = QFileDialog.getOpenFileNames(self, text, QDir.homePath())
        if not file_names:
            return
        _, zipped_file_name = tempfile.mkstemp()
        with zipfile.ZipFile(zipped_file_name, 'w') as zipped_file:
            for file_name in file_names:
                zipped_file.write(file_name)
        run_risk_url = "%s/v1/calc/run" % self.hostname
        with WaitCursorManager('Starting risk calculation...', self.iface):
            data = {'hazard_job_id': calc_id}
            files = {'archive': open(zipped_file_name, 'rb')}
            resp = self.session.post(
                run_risk_url, files=files, data=data, timeout=20)
        if resp.ok:
            self.refresh_calc_list()
        else:
            self.iface.messageBar().pushMessage(
                tr("Error"),
                resp.text,
                level=QgsMessageBar.CRITICAL)

    def get_output_list(self, calc_id):
        output_list_url = "%s/v1/calc/%s/results" % (self.hostname, calc_id)
        with WaitCursorManager('Getting list of outputs...', self.iface):
            resp = self.session.get(output_list_url, timeout=10)
        if resp.ok:
            output_list = json.loads(resp.text)
            return output_list
        else:
            return []

    def show_output_list(self, output_list):
        if not output_list:
            self.ui.output_list_tbl.setRowCount(0)
            self.ui.output_list_tbl.setColumnCount(0)
            return
        exclude = ['url', 'outtypes']
        selected_keys = [key for key in sorted(output_list[0].keys())
                         if key not in exclude]
        max_actions = 0
        has_hmaps = False
        for row in output_list:
            if row['type'] == 'hmaps':
                has_hmaps = True
            num_actions = len(row['outtypes'])
            if num_actions > max_actions:
                max_actions = num_actions
        if has_hmaps:
            max_actions += 1
        self.ui.output_list_tbl.setRowCount(len(output_list))
        self.ui.output_list_tbl.setColumnCount(
            len(selected_keys) + max_actions)
        self.ui.output_list_tbl.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        for row, output in enumerate(output_list):
            for col, key in enumerate(selected_keys):
                item = QTableWidgetItem()
                value = output_list[row][key]
                item.setData(Qt.DisplayRole, value)
                self.ui.output_list_tbl.setItem(row, col, item)
            outtypes = output_list[row]['outtypes']
            for col, outtype in enumerate(outtypes, len(selected_keys)):
                action = 'Download'
                button = QPushButton()
                self.connect_button_to_action(button, action, output, outtype)
                self.ui.output_list_tbl.setCellWidget(row, col, button)
            if output['type'] in ['hmaps', 'hcurves']:
                action = 'Load as layer'
                button = QPushButton()
                self.connect_button_to_action(button, action, output, outtype)
                self.ui.output_list_tbl.setCellWidget(row, col + 1, button)
        col_names = [key.capitalize() for key in selected_keys]
        empty_col_names = ['' for outtype in range(max_actions)]
        headers = col_names + empty_col_names
        self.ui.output_list_tbl.setHorizontalHeaderLabels(headers)
        self.ui.output_list_tbl.resizeColumnsToContents()
        self.ui.output_list_tbl.resizeRowsToContents()

    def connect_button_to_action(self, button, action, output, outtype):
        if action != 'Load as layer':
            button.setText("%s %s" % (action, outtype))
        else:
            # otherwise it would look ugly, e.g. 'Load as layer hdf5'
            button.setText(action)
        QObject.connect(
            button, SIGNAL("clicked()"),
            lambda output=output, action=action, outtype=outtype: self.on_output_action_btn_clicked(output, action, outtype)
        )

    def on_output_action_btn_clicked(self, output, action, outtype):
        output_id = output['id']
        output_type = output['type']
        if action == 'Load as layer':
            dest_folder = tempfile.gettempdir()
            if outtype == 'hdf5':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                dlg = LoadHdf5AsLayerDialog(self.iface, filepath, output_type)
                dlg.exec_()
            elif outtype == 'geojson':
                filepath = self.download_output(
                    output_id, outtype, dest_folder)
                dlg = LoadGeoJsonAsLayerDialog(self.iface, filepath)
                dlg.exec_()
            else:
                raise NotImplementedError("%s %s" % (action, outtype))
        elif action == 'Download':
            filepath = self.download_output(output_id, outtype)
            if not filepath:
                return
            self.iface.messageBar().pushMessage(
                tr("Info"),
                'Calculation %s was saved as %s' % (output_id, filepath),
                level=QgsMessageBar.INFO)
            if outtype == 'hdf5':
                # FIXME make system independent
                os.system("hdfview %s" % filepath)
        else:
            raise NotImplementedError(action)

    def download_output(self, output_id, outtype, dest_folder=None):
        if not dest_folder:
            dest_folder = ask_for_download_destination_folder(self)
            if not dest_folder:
                return
        output_download_url = (
            "%s/v1/calc/result/%s?export_type=%s&dload=true" % (self.hostname,
                                                                output_id,
                                                                outtype))
        with WaitCursorManager('Downloading output...', self.iface):
            resp = self.session.get(output_download_url, timeout=10)
            filename = resp.headers['content-disposition'].split(
                'filename=')[1]
            filepath = os.path.join(dest_folder, filename)
            open(filepath, "wb").write(resp.content)
        return filepath

    @pyqtSlot()
    def on_reload_calcs_btn_clicked(self):
        self.refresh_calc_list()

    def stop_timer(self):
        self.timer.stop()

    # @pyqtSlot(str)
    # def on_hdf5_path_le_textChanged(self):
    #     self.ui.open_hdfview_btn.setDisabled(
    #         self.ui.hdf5_path_le.text() == '')

    # @pyqtSlot()
    # def on_open_hdfview_btn_clicked(self):
    #     file_path = self.ui.hdf5_path_le.text()
    #     if file_path:
    #         to_run = "hdfview " + file_path
    #         # FIXME make system independent
    #         os.system(to_run)

    # @pyqtSlot()
    # def on_file_browser_tbn_clicked(self):
    #     self.hdf5_path = self.open_file_dialog()

    # @pyqtSlot(str)
    # def on_rlz_cbx_currentIndexChanged(self):
    #     self.dataset = self.hmaps.get(self.ui.rlz_cbx.currentText())
    #     self.imts = {}
    #     for name in self.dataset.dtype.names[2:]:
    #         imt, poe = name.split('~')
    #         if imt not in self.imts:
    #             self.imts[imt] = [poe]
    #         else:
    #             self.imts[imt].append(poe)
    #     self.ui.imt_cbx.clear()
    #     self.ui.imt_cbx.setEnabled(True)
    #     self.ui.imt_cbx.addItems(self.imts.keys())

    # @pyqtSlot(str)
    # def on_imt_cbx_currentIndexChanged(self):
    #     imt = self.ui.imt_cbx.currentText()
    #     self.ui.poe_cbx.clear()
    #     self.ui.poe_cbx.setEnabled(True)
    #     self.ui.poe_cbx.addItems(self.imts[imt])

    # @pyqtSlot(str)
    # def on_poe_cbx_currentIndexChanged(self):
    #     self.set_ok_button()

    # def open_file_dialog(self):
    #     """
    #     Open a file dialog to select the data file to be loaded
    #     """
    #     text = self.tr('Select oq-engine output to import')
    #     filters = self.tr('HDF5 files (*.hdf5)')
    #     hdf5_path = QFileDialog.getOpenFileName(
    #         self, text, QDir.homePath(), filters)
    #     if hdf5_path:
    #         self.hdf5_path = hdf5_path
    #         self.ui.hdf5_path_le.setText(self.hdf5_path)
    #         self.populate_rlz_cbx()

    # def populate_rlz_cbx(self):
    #     # FIXME: will the file be closed correctly?
    #     # with hdf5.File(self.hdf5_path, 'r') as hf:
    #     self.hfile = hdf5.File(self.hdf5_path, 'r')
    #     self.hmaps = self.hfile.get('hmaps')
    #     self.rlzs = self.hmaps.keys()
    #     self.ui.rlz_cbx.clear()
    #     self.ui.rlz_cbx.setEnabled(True)
    #     self.ui.rlz_cbx.addItems(self.rlzs)

    # def set_ok_button(self):
    #     self.ok_button.setEnabled(self.ui.poe_cbx.currentIndex != -1)

    # def build_layer(self):
    #     rlz = self.ui.rlz_cbx.currentText()
    #     imt = self.ui.imt_cbx.currentText()
    #     poe = self.ui.poe_cbx.currentText()
    #     self.field_name = '%s~%s' % (imt, poe)
    #     array = self.dataset.value[['lon', 'lat', self.field_name]]

    #     layer_name = "%s_%s_%s" % (rlz, imt, poe)
    #     # create layer
    #     self.layer = QgsVectorLayer(
    #         "Point?crs=epsg:4326", layer_name, "memory")
    #     # NOTE: if we use shapefiles, we need to make sure ~ is fine,
    #     #       otherwise we have to replace it with something like _
    #     # NOTE: add_numeric_attribute uses LayerEditingManager
    #     add_numeric_attribute(self.field_name, self.layer)
    #     pr = self.layer.dataProvider()
    #     with LayerEditingManager(self.layer, 'Reading hdf5', DEBUG):
    #         feats = []
    #         for row in array:
    #             # add a feature
    #             feat = QgsFeature(self.layer.pendingFields())
    #             lon, lat, value = row
    #             # NOTE: without casting to float, it produces a null
    #             #       because it does not recognize the numpy type
    #             feat.setAttribute(self.field_name, float(value))
    #             feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(lon, lat)))
    #             feats.append(feat)
    #         (res, outFeats) = pr.addFeatures(feats)
    #     # add self.layer to the legend
    #     QgsMapLayerRegistry.instance().addMapLayer(self.layer)
    #     self.iface.setActiveLayer(self.layer)
    #     self.iface.zoomToActiveLayer()

    # def style_layer(self):
    #     color1 = QColor("#FFEBEB")
    #     color2 = QColor("red")
    #     classes_count = 10
    #     ramp = QgsVectorGradientColorRampV2(color1, color2)
    #     symbol = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
    #     # see properties at:
    #     # https://qgis.org/api/qgsmarkersymbollayerv2_8cpp_source.html#l01073
    #     symbol = symbol.createSimple({'outline_width': '0.000001'})
    #     symbol.setAlpha(1)  # opacity
    #     graduated_renderer = QgsGraduatedSymbolRendererV2.createRenderer(
    #         self.layer,
    #         self.field_name,
    #         classes_count,
    #         # QgsGraduatedSymbolRendererV2.Quantile,
    #         QgsGraduatedSymbolRendererV2.EqualInterval,
    #         symbol,
    #         ramp)
    #     graduated_renderer.updateRangeLowerValue(0, 0.0)
    #     symbol_zeros = QgsSymbolV2.defaultSymbol(self.layer.geometryType())
    #     symbol_zeros = symbol.createSimple({'outline_width': '0.000001'})
    #     symbol_zeros.setColor(QColor(222, 255, 222))
    #     zeros_min = 0.0
    #     zeros_max = 0.0
    #     range_zeros = QgsRendererRangeV2(
    #         zeros_min, zeros_max, symbol_zeros,
    #         " %.4f - %.4f" % (zeros_min, zeros_max), True)
    #     graduated_renderer.addClassRange(range_zeros)
    #     graduated_renderer.moveClass(classes_count, 0)
    #     self.layer.setRendererV2(graduated_renderer)
    #     self.layer.setLayerTransparency(30)  # percent
    #     self.layer.triggerRepaint()
    #     self.iface.legendInterface().refreshLayerSymbology(
    #         self.layer)
    #     self.iface.mapCanvas().refresh()

#     def accept(self):
#         with WaitCursorManager('Creating layer...', self.iface):
#             self.build_layer()
#         self.hfile.close()
#         self.style_layer()
#         self.close()

    #
