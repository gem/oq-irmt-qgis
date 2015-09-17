# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Integrated Risk Modelling Toolkit
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

import os
import shutil
import json
from qgis.core import QgsVectorFileWriter

from oq_irmt.thread_worker.abstract_worker import AbstractWorker
from oq_irmt.utilities.shared import DEBUG
from oq_irmt.utilities.utils import (multipart_encode_for_requests,
                                     UserAbortedNotification,
                                     tr,
                                     )


class UploadWorker(AbstractWorker):
    """worker, to upload data to a platform"""

    def __init__(self, hostname, session, file_stem, username, current_layer):
        AbstractWorker.__init__(self)
        self.hostname = hostname
        self.session = session
        self.file_stem = file_stem
        self.username = username
        self.current_layer = current_layer
        self.upload_size_msg = None

    def work(self):
        # To upload the layer to the platform, we need it to be a shapefile.
        # So we need to check if the active layer is stored as a shapefile and,
        # if it isn't, save it as a shapefile
        data_file = '%s%s' % (self.file_stem, '.shp')
        if self.current_layer.storageType() == 'ESRI Shapefile':
            # copy the shapefile (with all its files) into the temporary
            # directory, using self.file_stem as name
            self.set_message.emit(tr(
                'Preparing the files to be uploaded...'))
            layer_source = self.current_layer.publicSource()
            layer_source_stem = layer_source[:-4]  # remove '.shp'
            for ext in ['shp', 'dbf', 'shx', 'prj']:
                src = "%s.%s" % (layer_source_stem, ext)
                dst = "%s.%s" % (self.file_stem, ext)
                shutil.copyfile(src, dst)
        else:
            # if it's not a shapefile, we need to build a shapefile from it
            self.set_message.emit(tr(
                'Writing the shapefile to be uploaded...'))
            QgsVectorFileWriter.writeAsVectorFormat(
                self.current_layer,
                data_file,
                'utf-8',
                self.current_layer.crs(),
                'ESRI Shapefile')
        file_size_mb = os.path.getsize(data_file)
        file_size_mb += os.path.getsize(self.file_stem + '.shx')
        file_size_mb += os.path.getsize(self.file_stem + '.dbf')
        # convert bytes to MB
        file_size_mb = file_size_mb / 1024 / 1024
        self.upload_size_msg = tr('Uploading ~%s MB...' % file_size_mb)
        self.set_message.emit(self.upload_size_msg)
        permissions = {"authenticated": "_none",
                       "anonymous": "_none",
                       "users": [[self.username, "layer_readwrite"],
                                 [self.username, "layer_admin"]]
                       }

        data = {'layer_title': os.path.basename(self.file_stem),
                'base_file': open('%s.shp' % self.file_stem, 'rb'),
                'dbf_file': open('%s.dbf' % self.file_stem, 'rb'),
                'shx_file': open('%s.shx' % self.file_stem, 'rb'),
                'prj_file': open('%s.prj' % self.file_stem, 'rb'),
                'xml_file': open('%s.xml' % self.file_stem, 'r'),
                'charset': 'UTF-8',
                'permissions': json.dumps(permissions)
                }

        # generate headers and data-generator an a requests-compatible format
        # and provide our progress-callback
        data_generator, headers = multipart_encode_for_requests(
            data, cb=self.progress_cb)

        # use the requests-lib to issue a post-request with out data attached
        r = self.session.post(
            self.hostname + '/layers/upload',
            data=data_generator,
            headers=headers
        )

        try:
            response = json.loads(r.text)
            return self.hostname + response['url'], True
        except KeyError:
            if 'errors' in response:
                raise KeyError(response['errors'])
            else:
                raise KeyError("The server did not provide error messages")
        except ValueError:
            raise RuntimeError(r.text)

    # this is your progress callback
    def progress_cb(self, param, current, total):
        if self.is_killed:
            raise UserAbortedNotification('Upload aborted by user')
        if not param:
            return
        # check out
        # http://tcd.netinf.eu/doc/classnilib_1_1encode_1_1MultipartParam.html
        # for a complete list of the properties param provides to you
        progress = float(current) / float(total) * 100
        self.progress.emit(progress)
        # here we remove the progress bar and the cancel button since the
        # server side processing kicks in at 100% but we allow for some
        # rounding.
        if progress > 99:
            self.toggle_show_progress.emit(False)
            self.toggle_show_cancel.emit(False)
            self.set_message.emit(
                self.upload_size_msg + ' ' + tr('(processing on Platform)'))
        if DEBUG:
            print "PROGRESS: {0} ({1}) - {2:d}/{3:d} - {4:.2f}%".format(
                param.name, param.filename, current, total, progress)
