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


import json

from abstract_worker import AbstractWorker


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
        return self.upload_shp()

    def upload_shp(self):
        files = {'layer_title': self.file_stem,
                 'base_file': ('%s.shp' % self.file_stem,
                               open('%s.shp' % self.file_stem, 'rb')),
                 'dbf_file': ('%s.dbf' % self.file_stem,
                              open('%s.dbf' % self.file_stem, 'rb')),
                 'shx_file': ('%s.shx' % self.file_stem,
                              open('%s.shx' % self.file_stem, 'rb')),
                 'prj_file': ('%s.prj' % self.file_stem,
                              open('%s.prj' % self.file_stem, 'rb')),
                 'xml_file': ('%s.xml' % self.file_stem,
                              open('%s.xml' % self.file_stem, 'r')),
                 }
        permissions = ('{"authenticated":"_none",'
                       '"anonymous":"_none",'
                       '"users":[["%s","layer_readwrite"],["%s","layer_admin"]]'
                       '}') % (self.username, self.username)
        payload = {'charset': ['UTF-8'],
                   'permissions': [permissions]}

        r = self.session.post(
            self.hostname + '/layers/upload', data=payload, files=files)

        response = json.loads(r.text)
        try:
            return self.hostname + response['url'], True
        except KeyError:
            if 'errors' in response:
                raise KeyError(response['errors'])
            else:
                raise KeyError("The server did not provide error messages")
