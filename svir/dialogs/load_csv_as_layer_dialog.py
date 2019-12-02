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
from svir.utilities.utils import (
    import_layer_from_csv, log_msg, write_metadata_to_layer)
from svir.utilities.shared import OQ_CSV_TO_LAYER_TYPES
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadCsvAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Dialog to load as layer a basic csv with no geometries, to be
    browsed through its attribute table
    """

    def __init__(self, drive_engine_dlg, iface, viewer_dock, session, hostname,
                 calc_id, output_type, path=None, mode=None,
                 engine_version=None):
        assert output_type in OQ_CSV_TO_LAYER_TYPES, output_type
        LoadOutputAsLayerDialog.__init__(
            self, drive_engine_dlg, iface, viewer_dock, session, hostname,
            calc_id, output_type=output_type, path=path, mode=mode,
            engine_version=engine_version)
        self.create_file_size_indicator()
        self.setWindowTitle('Load %s from CSV, as layer' % output_type)
        self.populate_out_dep_widgets()
        self.adjustSize()
        self.set_ok_button()
        # TODO: add a warning in case the file size exceeds a threshold
        # self.show()
        if self.ok_button.isEnabled():
            self.accept()
        else:
            self.show()

    def set_ok_button(self):
        self.ok_button.setEnabled(bool(self.path))

    def populate_out_dep_widgets(self):
        self.show_file_size()

    def load_from_csv(self):
        if self.mode == 'testing':
            save_dest = tempfile.mkstemp(suffix='.gpkg')[1]
            save_format = 'GPKG'
        else:
            save_dest = None  # the destination file will be selected via GUI
            save_format = None
        csv_path = self.path
        # extract the name of the csv file and remove the extension
        layer_name = os.path.splitext(os.path.basename(csv_path))[0]
        try:
            self.layer = import_layer_from_csv(
                self, csv_path, layer_name, self.iface,
                save_format=save_format, save_dest=save_dest,
                zoom_to_layer=False, has_geom=False)
        except RuntimeError as exc:
            log_msg(str(exc), level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
            return
        write_metadata_to_layer(
            self.drive_engine_dlg, self.output_type, self.layer)
        log_msg('Layer %s was loaded successfully' % layer_name,
                level='S', message_bar=self.iface.messageBar())
        self.iface.showAttributeTable(self.layer)
