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
from utils import multipart_encode_for_requests, UserAbortedNotification


class UploadWorker(AbstractWorker):
    """worker, implement the work method here and raise exceptions if needed"""

    def __init__(self, hostname, session, file_stem, username):
        AbstractWorker.__init__(self)
        self.hostname = hostname
        self.session = session
        self.file_stem = file_stem
        self.username = username

    def work(self):
        # self.toggle_show_progress.emit(True)
        permissions = ('{"authenticated":"_none",'
                       '"anonymous":"_none",'
                       '"users":[["%s","layer_readwrite"],["%s","layer_admin"]]'
                       '}') % (self.username, self.username)

        data = {'layer_title': self.file_stem,
                'base_file': open('%s.shp' % self.file_stem, 'rb'),
                'dbf_file': open('%s.dbf' % self.file_stem, 'rb'),
                'shx_file': open('%s.shx' % self.file_stem, 'rb'),
                'prj_file': open('%s.prj' % self.file_stem, 'rb'),
                'xml_file': open('%s.xml' % self.file_stem, 'r'),
                'charset': ['UTF-8'],
                'permissions': [permissions]
                }

        print 'PERMISSIONS', permissions
        # generate headers and gata-generator an a requests-compatible format
        # and provide our progress-callback
        data_generator, headers = multipart_encode_for_requests(
            data, cb=self.progress_cb)

        # use the requests-lib to issue a post-request with out data attached
        r = self.session.post(
            self.hostname + '/layers/upload',
            data=data_generator,
            headers=headers
        )
        response = json.loads(r.text)
        print 'RESPONSE', response
        try:
            return self.hostname + response['url'], True
        except KeyError:
            if 'errors' in response:
                raise KeyError(response['errors'])
            else:
                raise KeyError("The server did not provide error messages")

    # this is your progress callback
    def progress_cb(self, param, current, total):
        if self.is_killed:
            raise UserAbortedNotification('USER Killed')
        if not param:
            return
        # check out
        # http://tcd.netinf.eu/doc/classnilib_1_1encode_1_1MultipartParam.html
        # for a complete list of the properties param provides to you
        progress = float(current) / float(total) * 100
        self.progress.emit(progress)
        # print "PROGRESS: {0} ({1}) - {2:d}/{3:d} - {4:.2f}%".format(
        #   param.name, param.filename, current, total, progress)
