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

# Copyright (c) 2010-2013, GEM Foundation.
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
import collections
from time import time
from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QApplication
from platform_settings_dialog import PlatformSettingsDialog


def tr(message):
    return QApplication.translate('Svir', message)


def get_credentials(iface):
    qs = QSettings()
    hostname = qs.value('platform_settings/hostname', '')
    username = qs.value('platform_settings/username', '')
    password = qs.value('platform_settings/password', '')
    if not (hostname and username and password):
        PlatformSettingsDialog(iface).exec_()
        hostname = qs.value('platform_settings/hostname', '')
        username = qs.value('platform_settings/username', '')
        password = qs.value('platform_settings/password', '')
    return hostname, username, password


class Register(collections.OrderedDict):
    """
    Useful to keep (in a single point) a register of available variants of
    something, e.g. a set of different normalization/standardization algorithms
    """
    def add(self, tag):
        """
        Add a new variant to the OrderedDict
        For instance, if we add a class implementing a specific normalization
        algorithm, the register will keep track of a new item having as key the
        name of the algorithm and as value the class implementing the algorithm
        """
        def dec(obj):
            self[tag] = obj
            return obj
        return dec


class TraceTimeManager(object):
    def __init__(self, message, debug=False):
        self.debug = debug
        self.message = message
        self.t_start = None
        self.t_stop = None

    def __enter__(self):
        if self.debug:
            print self.message
            self.t_start = time()

    def __exit__(self, type, value, traceback):
        if self.debug:
            self.t_stop = time()
            print "Completed in %f" % (self.t_stop - self.t_start)


class LayerEditingManager(object):
    def __init__(self, layer, message, debug=False):
        self.layer = layer
        self.message = message
        self.debug = debug

    def __enter__(self):
        self.layer.startEditing()
        if self.debug:
            print "BEGIN", self.message

    def __exit__(self, type, value, traceback):
        self.layer.commitChanges()
        self.layer.updateExtents()
        if self.debug:
            print "END", self.message


class WaitCursorManager(object):
    def __enter__(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, type, value, traceback):
        QApplication.restoreOverrideCursor()
