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
from svir.utilities.utils import import_layer_from_csv
from svir.dialogs.load_output_as_layer_dialog import LoadOutputAsLayerDialog


class LoadSourcegroupsAsLayerDialog(LoadOutputAsLayerDialog):
    """
    Modal dialog to load sourcegroups from an oq-engine output, as layer
    """

    def __init__(self, iface, viewer_dock, session, hostname, calc_id,
                 output_type='sourcegroups', path=None, mode=None):
        assert output_type == 'sourcegroups'
        LoadOutputAsLayerDialog.__init__(
            self, iface, viewer_dock, session, hostname, calc_id,
            output_type, path, mode)
        self.create_save_as_shp_ckb()
        self.setWindowTitle('Load seismic source groups from CSV, as layer')
        self.adjustSize()
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setEnabled(bool(self.path))

    def load_from_csv(self):
        if self.mode == 'testing':
            dest_shp = tempfile.mkstemp(suffix='.shp')[1]
        else:
            dest_shp = None  # the destination file will be selected via GUI
        csv_path = self.path_le.text()
        # extract the name of the csv file and remove the extension
        layer_name = os.path.splitext(os.path.basename(csv_path))[0]
        self.layer = import_layer_from_csv(
            self, csv_path, layer_name, self.iface,
            save_as_shp=self.save_as_shp_ckb.isChecked(), dest_shp=dest_shp,
            zoom_to_layer=False, has_geom=False)

    def populate_out_dep_widgets(self):
        # no widgets to populate
        pass
