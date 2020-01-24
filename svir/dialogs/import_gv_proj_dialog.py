# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2020-01-23
#        copyright            : (C) 2020 by GEM Foundation
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

import json
import traceback
from requests import Session
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QTableWidgetItem
from svir.utilities.utils import get_ui_class, log_msg, geoviewer_login
from svir.utilities.shared import DEFAULT_GEOVIEWER_PROFILES


FORM_CLASS = get_ui_class('ui_import_gv_proj.ui')


class ImportGvProjDialog(QDialog, FORM_CLASS):
    """
        # TODO: open a dialog with a list of projects showing chosen properties
        # TODO: download the selected project
    """
    def __init__(self, message_bar):
        self.message_bar = message_bar
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        project_list = self.get_project_list()
        if not project_list:
            return
        # QMessageBox.information(
        #     self, "Info", json.dumps(project_list, indent=4),
        #     QMessageBox.Ok)
        self.show_project_list(project_list)

    def show_project_list(self, project_list):
        fields_to_display = ('name', )  # FIXME
        self.list_of_projects_tbl.setRowCount(len(project_list))
        self.list_of_projects_tbl.setColumnCount(len(fields_to_display))
        for row, project in enumerate(project_list):
            if not project['fields']['downloadable']:
                continue
            for col, field in enumerate(fields_to_display):
                item = QTableWidgetItem(project['fields'][field])
                self.list_of_projects_tbl.setItem(row, col, item)

    def get_project_list(self):
        mySettings = QSettings()
        profiles = json.loads(mySettings.value(
            'irmt/geoviewer_profiles', DEFAULT_GEOVIEWER_PROFILES))
        # FIXME: make a utility function to retrieve credentials from settings
        profile = profiles['Local OpenQuake GeoViewer']
        session = Session()
        hostname, username, password = (profile['hostname'],
                                        profile['username'],
                                        profile['password'])
        session.auth = (username, password)
        try:
            geoviewer_login(hostname, username, password, session)
        except Exception as exc:
            err_msg = "Unable to connect (see Log Message Panel for details)"
            log_msg(err_msg, level='C', message_bar=self.message_bar,
                    exception=exc)
            return
        project_list_url = hostname + '/api/project_list/'
        try:
            resp = session.get(project_list_url, timeout=10)
        except Exception:
            msg = "Unable to retrieve the list of projects.\n%s" % (
                traceback.format_exc())
            raise RuntimeError(msg)
        if resp.status_code != 200:  # 200 means successful:OK
            error_message = ('Unable to retrieve the list of projects: %s' %
                             resp.text)
            raise RuntimeError(error_message)
        project_list = json.loads(resp.text)
        return project_list
