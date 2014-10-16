# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2013-2014, GEM Foundation.
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
import StringIO
import csv
from third_party.requests import Session

# FIXME Change exposure to sv when app is ready on platform
PLATFORM_EXPORT_SV_CATEGORY_NAMES = "/svir/export_sv_category_names"
PLATFORM_EXPORT_SV_DATA_BY_VARIABLES_IDS = \
    "/svir/export_sv_data_by_variables_ids"
PLATFORM_EXPORT_SV_THEMES = "/svir/list_themes"
PLATFORM_EXPORT_SV_SUBTHEMES = "/svir/list_subthemes_by_theme"
PLATFORM_EXPORT_SV_NAMES = "/svir/export_variables_info"
PLATFORM_EXPORT_VARIABLES_DATA_BY_IDS = "/svir/export_variables_data_by_ids"


class SvDownloadError(Exception):
    pass


class SvDownloader(object):
    def __init__(self, host):
        self.host = host
        self._login = host + '/account/ajax_login'
        self.sess = Session()

    def login(self, username, password):
        session_resp = self.sess.post(self._login,
                                      data={
                                          "username": username,
                                          "password": password
                                      })
        if session_resp.status_code != 200:  # 200 means successful:OK
            error_message = ('Unable to get session for login: %s' %
                             session_resp.content)
            raise SvDownloadError(error_message)

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

    def get_names(self, name_filter=None, keywords=None, theme=None, subtheme=None):
        page = self.host + PLATFORM_EXPORT_SV_NAMES
        params = dict(name=name_filter,
                      keywords=keywords,
                      theme=theme,
                      subtheme=subtheme)
        result = self.sess.get(page, params=params)
        if result.status_code == 200:
            names = [l for l in result.content.splitlines() if l and l[0] != '#']
        return names[1:]

    def get_data_by_variables_ids(self, sv_variables_ids):
        page = self.host + PLATFORM_EXPORT_VARIABLES_DATA_BY_IDS
        params = dict(sv_variables_ids=sv_variables_ids)
        result = self.sess.get(page, params=params)
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
            with open(fname_types, 'w') as csvt:
                csvt.write(types_string)
            with open(fname, 'w') as csv:
                csv.write(result.content)
                msg = 'Downloaded %d lines into %s' % (
                    result.content.count('\n'), fname)
                return fname, msg
        else:
            raise SvDownloadError(result.content)
