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
import os
import tempfile
from oq_svir.calculations.import_sv_data import PLATFORM_EXPORT_VARIABLES_DATA

from oq_svir.thread_worker.abstract_worker import AbstractWorker
from oq_svir.utilities.utils import SvNetworkError, tr, UserAbortedNotification


class DownloadPlatformDataWorker(AbstractWorker):
    """worker, to download data from a platform"""

    def __init__(self,
                 sv_downloader,
                 sv_variables_ids,
                 load_geometries,
                 country_iso_codes):
        AbstractWorker.__init__(self)
        self.downloader = sv_downloader
        self.sv_variables_ids = sv_variables_ids
        self.load_geometries = load_geometries
        self.country_iso_codes = country_iso_codes

    def work(self):
        self.set_message.emit(
            tr('Waiting for the OpenQuake Platform to export the data...'))
        self.toggle_show_progress.emit(False)
        page = self.downloader.host + PLATFORM_EXPORT_VARIABLES_DATA
        data = dict(sv_variables_ids=self.sv_variables_ids,
                    export_geometries=self.load_geometries,
                    country_iso_codes=self.country_iso_codes)
        result = self.downloader.sess.post(page, data=data, stream=True)

        self.set_message.emit(tr('Downloading data from platform'))

        self.toggle_show_progress.emit(True)
        if result.status_code == 200:
            # save csv on a temporary file
            fd, fname = tempfile.mkstemp(suffix='.csv')
            os.close(fd)
            # All the fields of the csv file will be considered as text fields
            # unless a .csvt file with the same name as the .csv file is used
            # to specify the field types.
            # For the type descriptor, use the same name as the csv file
            fname_types = fname.split('.')[0] + '.csvt'
            # We expect iso, country_name, v1, v2, ... vn
            # Count variables ids
            sv_variables_count = len(self.sv_variables_ids.split(','))
            # build the string that describes data types for the csv
            types_string = '"String","String"' + ',"Real"' * sv_variables_count
            if self.load_geometries:
                types_string += ',"String"'
            with open(fname_types, 'w') as csvt:
                csvt.write(types_string)
            with open(fname, 'w') as csv_file:
                n_countries_to_download = len(self.country_iso_codes)
                n_downloaded_countries = 0
                for line in result.iter_lines():
                    if self.is_killed:
                        raise UserAbortedNotification(
                            'Download aborted by user')

                    csv_file.write(line + os.linesep)
                    n_downloaded_countries += 1
                    progress = (1.0 * n_downloaded_countries /
                                n_countries_to_download * 100)
                    self.progress.emit(progress)

                msg = 'The socioeconomic data has been saved into %s' % fname
                return fname, msg
        else:
            raise SvNetworkError(result.content)
