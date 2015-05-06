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


import StringIO
import zipfile

from abstract_worker import AbstractWorker


class DownloadPlatformProjectWorker(AbstractWorker):
    """worker, to download an existing project from a platform"""

    def __init__(self,
                 sv_downloader,
                 layer_id):
        AbstractWorker.__init__(self)
        self.downloader = sv_downloader
        self.layer_id = layer_id

    def work(self):
        self.toggle_show_progress.emit(False)
        # download and unzip layer
        shape_url_fmt = (
            '%s/geoserver/wfs?'
            'format_options=charset:UTF-8'
            '&typename=%s'
            '&outputFormat=SHAPE-ZIP'
            '&version=1.0.0'
            '&service=WFS'
            '&request=GetFeature')
        shape_url = shape_url_fmt % (self.downloader.host, self.layer_id)
        request = self.downloader.sess.get(shape_url)

        downloaded_zip = zipfile.ZipFile(StringIO.StringIO(request.content))
        return downloaded_zip
