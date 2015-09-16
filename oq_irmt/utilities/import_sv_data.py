# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Irmt
                                 A QGIS plugin
 OpenQuake Integrated Risk Modelling Toolkit
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
import StringIO
import csv
from qgis.gui import QgsMessageBar

from oq_irmt.third_party.requests import Session
from oq_irmt.third_party.requests.exceptions import (ConnectionError,
                                             InvalidSchema,
                                             MissingSchema,
                                             ReadTimeout,
                                             )
from oq_irmt.utilities.utils import (SvNetworkError,
                   platform_login,
                   get_credentials,
                   WaitCursorManager,
                   tr,
                   create_progress_message_bar,
                   clear_progress_message_bar,
                   )

PLATFORM_EXPORT_SV_THEMES = "/svir/list_themes"
PLATFORM_EXPORT_SV_SUBTHEMES = "/svir/list_subthemes_by_theme"
PLATFORM_EXPORT_SV_NAMES = "/svir/export_variables_info"
PLATFORM_EXPORT_VARIABLES_DATA = "/svir/export_variables_data"
PLATFORM_EXPORT_COUNTRIES_INFO = "/svir/export_countries_info"


def get_loggedin_downloader(iface):
    hostname, username, password = get_credentials(iface)
    sv_downloader = SvDownloader(hostname)

    try:
        msg = ("Connecting to the OpenQuake Platform...")
        with WaitCursorManager(msg, iface):
            sv_downloader.login(username, password)
        return sv_downloader
    except (SvNetworkError, ConnectionError,
            InvalidSchema, MissingSchema, ReadTimeout) as e:
        err_msg = str(e)
        if isinstance(e, InvalidSchema):
            err_msg += ' (you could try prepending http:// or https://)'
        iface.messageBar().pushMessage(
            tr("Login Error"),
            tr(err_msg),
            level=QgsMessageBar.CRITICAL)
        return None


class SvDownloader(object):
    def __init__(self, host):
        self.host = host
        self.sess = Session()

    def login(self, username, password):
        platform_login(self.host, username, password, self.sess)

    def get_themes(self):
        page = self.host + PLATFORM_EXPORT_SV_THEMES
        themes = []
        result = self.sess.get(page)
        if result.status_code == 200:
            reader = csv.reader(StringIO.StringIO(result.content))
            themes = reader.next()
        return themes

    def get_subthemes_by_theme(self, theme):
        page = self.host + PLATFORM_EXPORT_SV_SUBTHEMES
        params = dict(theme=theme)
        subthemes = []
        result = self.sess.get(page, params=params)
        if result.status_code == 200:
            reader = csv.reader(StringIO.StringIO(result.content))
            subthemes = reader.next()
        return subthemes

    def get_indicators_info(
            self, name_filter=None, keywords=None, theme=None, subtheme=None):
        page = self.host + PLATFORM_EXPORT_SV_NAMES
        params = dict(name=name_filter,
                      keywords=keywords,
                      theme=theme,
                      subtheme=subtheme)
        result = self.sess.get(page, params=params)
        indicators_info = {}
        if result.status_code == 200:
            reader = csv.reader(StringIO.StringIO(result.content))
            header = None
            for row in reader:
                if row[0].startswith('#'):
                    continue
                if not header:
                    header = row
                    continue
                code = row[0]
                indicators_info[code] = dict()
                indicators_info[code]['name'] = row[1].decode('utf-8')
                indicators_info[code]['theme'] = row[2].decode('utf-8')
                indicators_info[code]['subtheme'] = row[3].decode('utf-8')
                indicators_info[code]['description'] = row[4].decode('utf-8')
                indicators_info[code]['measurement_type'] = \
                    row[5].decode('utf-8')
                indicators_info[code]['source'] = row[6].decode('utf-8')
                indicators_info[code]['aggregation_method'] = \
                    row[7].decode('utf-8')
                indicators_info[code]['keywords_str'] = row[8].decode('utf-8')
                # names.append(indicators_main_info[code])
        return indicators_info

    def get_countries_info(self):
        page = self.host + PLATFORM_EXPORT_COUNTRIES_INFO
        result = self.sess.get(page)
        countries_info = {}
        if result.status_code == 200:
            reader = csv.reader(StringIO.StringIO(result.content))
            header = None
            for row in reader:
                if row[0].startswith('#'):
                    continue
                if not header:
                    header = row
                    continue
                iso = row[0]
                countries_info[iso] = row[1].decode('utf-8')
        return countries_info

    def get_sv_data(self,
                    sv_variables_ids,
                    load_geometries,
                    country_iso_codes,
                    message_bar):
        msg_bar_item, progress_ = create_progress_message_bar(
            message_bar,
            'Waiting for the OpenQuake Platform to export the data...',
            no_percentage=True)
        page = self.host + PLATFORM_EXPORT_VARIABLES_DATA
        data = dict(sv_variables_ids=sv_variables_ids,
                    export_geometries=load_geometries,
                    country_iso_codes=country_iso_codes)
        result = self.sess.post(page, data=data, stream=True)
        clear_progress_message_bar(message_bar, msg_bar_item)
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
            sv_variables_count = len(sv_variables_ids.split(','))
            # build the string that describes data types for the csv
            types_string = '"String","String"' + ',"Real"' * sv_variables_count
            if load_geometries:
                types_string += ',"String"'
            with open(fname_types, 'w') as csvt:
                csvt.write(types_string)
            with open(fname, 'w') as csv_file:
                n_countries_to_download = len(country_iso_codes)
                n_downloaded_countries = 0
                msg_bar_item, progress = create_progress_message_bar(
                    message_bar, 'Downloading socioeconomic data...')
                for line in result.iter_lines():
                    csv_file.write(line + os.linesep)
                    n_downloaded_countries += 1
                    progress.setValue(
                        n_downloaded_countries / n_countries_to_download * 100)
                clear_progress_message_bar(message_bar, msg_bar_item)
                msg = 'The socioeconomic data has been saved into %s' % fname
                return fname, msg
        else:
            raise SvNetworkError(result.content)
