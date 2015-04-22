# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014-2015 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/
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
"""


from abstract_worker import AbstractWorker
from utils import upload_shp


class UploadWorker(AbstractWorker):
    """worker, implement the work method here and raise exceptions if needed"""

    def __init__(self, hostname, session, file_stem, username):
        AbstractWorker.__init__(self)
        self.hostname = hostname
        self.session = session
        self.file_stem = file_stem
        self.username = username

    def work(self):
        self.toggle_show_progress.emit(False)
        # if success == 'False', layer_url will contain the error message
        layer_url, success = upload_shp(
            self.hostname, self.session, self.file_stem, self.username)
        return str(layer_url), str(success)