# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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

from __future__ import print_function
import os
import shutil
import json
from qgis.core import QgsCoordinateReferenceSystem

from svir.thread_worker.abstract_worker import AbstractWorker
from svir.utilities.utils import (
                                  tr,
                                  save_layer_as,
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
        projection = self.current_layer.crs().geographicCrsAuthId()
        if (self.current_layer.storageType() == 'ESRI Shapefile'
                and projection == 'EPSG:4326'):
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
            # if it's not a shapefile or it is in a bad projection,
            # we need to build a shapefile from it
            self.set_message.emit(tr(
                'Writing the shapefile to be uploaded...'))
            writer_error, error_msg = save_layer_as(
                self.current_layer, data_file,
                'ESRI Shapefile',
                crs=QgsCoordinateReferenceSystem(
                    4326, QgsCoordinateReferenceSystem.EpsgCrsId))
            if writer_error:
                raise RuntimeError(
                    'Could not save shapefile. %s: %s' % (writer_error,
                                                          error_msg))
        file_size_mb = os.path.getsize(data_file)
        file_size_mb += os.path.getsize(self.file_stem + '.shx')
        file_size_mb += os.path.getsize(self.file_stem + '.dbf')
        # convert bytes to MB
        file_size_mb = file_size_mb / 1024 / 1024
        self.upload_size_msg = tr('Uploading ~%s MB...' % file_size_mb)
        self.set_message.emit(self.upload_size_msg)
        user_permissions = [
                            'change_layer_style', 'add_layer',
                            'change_layer', 'delete_layer',
                            'view_resourcebase',
                            'download_resourcebase',
                            'publish_resourcebase',
                            ]
        admin_permissions = [
                             'change_layer_data',
                             'change_resourcebase_metadata',
                             'change_resourcebase',
                             'delete_resourcebase',
                             'change_resourcebase_permissions',
                             ]
        admin_permissions.extend(user_permissions)
        permissions = {
                       "admin": {
                                 self.username: admin_permissions
                                 },
                       "users": {
                                 self.username: user_permissions
                                 }
                       }

        files = {'base_file': open('%s.shp' % self.file_stem, 'rb'),
                 'dbf_file': open('%s.dbf' % self.file_stem, 'rb'),
                 'shx_file': open('%s.shx' % self.file_stem, 'rb'),
                 'prj_file': open('%s.prj' % self.file_stem, 'rb'),
                 'xml_file': open('%s.xml' % self.file_stem, 'rb')}
        data = {'layer_title': os.path.basename(self.file_stem),
                'charset': 'UTF-8',
                'permissions': json.dumps(permissions),
                'metadata_uploaded_preserve': True}

        self.progress.emit(-1)

        r = self.session.post(
            self.hostname + '/layers/upload', data=data, files=files)

        self.toggle_show_progress.emit(False)
        self.toggle_show_cancel.emit(False)
        self.set_message.emit(
            self.upload_size_msg + ' ' + tr('(processing on Platform)'))

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
