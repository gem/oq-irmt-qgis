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
import tempfile
from collections import OrderedDict
from svir.utilities.utils import (import_layer_from_csv,
                                  get_params_from_comment_line,
                                  log_msg,
                                  )
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadRupturesAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load ruptures from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='ruptures', path=None, mode=None,
                 engine_version=None):
        assert output_type == 'ruptures'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)
        self.style_by_items = OrderedDict([
            ('Tectonic region type', 'trt'),
            ('Magnitude', 'mag'),
        ])
        self.create_file_hlayout()
        self.create_file_size_indicator()
        self.create_save_as_shp_ckb()
        self.create_style_by_selector()
        self.populate_out_dep_widgets()
        self.setWindowTitle('Load ruptures from CSV, as layer')
        self.adjustSize()
        self.set_ok_button()
        self.file_browser_tbn.setEnabled(True)
        if self.path:
            self.path_le.setText(self.path)

    def set_ok_button(self):
        self.ok_button.setEnabled(bool(self.path))

    def populate_out_dep_widgets(self):
        self.show_file_size()
        self.populate_style_by_cbx()

    def populate_style_by_cbx(self):
        self.style_by_cbx.clear()
        for item in self.style_by_items:
            self.style_by_cbx.addItem(item, self.style_by_items[item])

    def load_from_csv(self):
        if self.mode == 'testing':
            dest_shp = tempfile.mkstemp(suffix='.shp')[1]
        else:
            dest_shp = None  # the destination file will be selected via GUI
        csv_path = self.path_le.text()
        # extract the investigation_time from the heading commented line
        with open(csv_path, 'r') as f:
            comment_line = f.readline()
            try:
                params_dict = get_params_from_comment_line(comment_line)
            except LookupError as exc:
                log_msg(exc.message, level='C',
                        message_bar=self.iface.messageBar())
                return
            try:
                investigation_time = params_dict['investigation_time']
            except KeyError:
                log_msg('Investigation time not found', level='C',
                        message_bar=self.iface.messageBar())
                return
        # extract the name of the csv file and remove the extension
        layer_name = os.path.splitext(os.path.basename(csv_path))[0]
        layer_name += '_%sy' % investigation_time
        self.layer = import_layer_from_csv(
            self, csv_path, layer_name, self.iface,
            wkt_field='boundary', delimiter='\t',
            lines_to_skip_count=1,
            save_as_shp=self.save_as_shp_ckb.isChecked(), dest_shp=dest_shp)
        self.layer.setCustomProperty('investigation_time', investigation_time)
        style_by = self.style_by_cbx.itemData(self.style_by_cbx.currentIndex())
        if style_by == 'mag':
            self.style_maps(layer=self.layer, style_by=style_by)
        else:  # 'trt'
            self.style_categorized(layer=self.layer, style_by=style_by)
