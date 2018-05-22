# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2018 by GEM Foundation
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
from svir.utilities.utils import import_layer_from_csv, log_msg
from svir.utilities.shared import OQ_BASIC_CSV_TO_LAYER_TYPES
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadBasicCsvAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load as layer a basic csv with no geometries, to be
    browsed through its attribute table
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type, path=None, mode=None, engine_version=None):
        assert output_type in OQ_BASIC_CSV_TO_LAYER_TYPES, output_type
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)
        self.create_file_hlayout()
        self.create_file_size_indicator()
        self.setWindowTitle('Load %s from CSV, as layer' % output_type)
        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()
        self.file_browser_tbn.setEnabled(True)
        if self.path:
            self.path_le.setText(self.path)

    def set_ok_button(self):
        self.ok_button.setEnabled(bool(self.path))

    def populate_out_dep_widgets(self):
        self.show_file_size()

    def load_from_csv(self):
        if self.mode == 'testing':
            dest_shp = tempfile.mkstemp(suffix='.shp')[1]
        else:
            dest_shp = None  # the destination file will be selected via GUI
        csv_path = self.path_le.text()
        # extract the name of the csv file and remove the extension
        layer_name = os.path.splitext(os.path.basename(csv_path))[0]
        try:
            self.layer = import_layer_from_csv(
                self, csv_path, layer_name, self.iface,
                save_as_shp=False, dest_shp=dest_shp,
                zoom_to_layer=False, has_geom=False)
        except RuntimeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar())
            return
        log_msg('Layer %s was loaded successfully' % layer_name,
                level='S', message_bar=self.iface.messageBar())
        self.iface.showAttributeTable(self.layer)
