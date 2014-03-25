# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2014-03-24
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

import json

from PyQt4.QtCore import (Qt,
                          QUrl,
                          QSettings,
                          pyqtProperty,
                          pyqtSignal)

from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from PyQt4.QtWebKit import QWebSettings

from ui.ui_weight_data import Ui_WeightDataDialog


class WeightDataDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """

    # QVariantMap is to map a JSON to dict see:
    # http://pyqt.sourceforge.net/Docs/PyQt4/incompatibilities.html#pyqt4-v4-7-4
    json_updated = pyqtSignal(['QVariantMap'], name='json_updated')

    def __init__(self, iface, project_definition):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_WeightDataDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.project_definition = project_definition

        self.web_view = self.ui.web_view
        self.web_view.load(QUrl('qrc:/plugins/svir/weight_data.html'))
        self.frame = self.web_view.page().mainFrame()

        self.setup_context_menu()

        self.frame.javaScriptWindowObjectCleared.connect(self.setup_js)
        self.web_view.loadFinished.connect(self.show_tree)
        self.json_updated.connect(self.handle_json_updated)

    def setup_context_menu(self):
        settings = QSettings()
        # TODO (MB) add a place to set this
        developer_mode = settings.value(
            '/svir/developer_mode', True, type=bool)
        if developer_mode is True:
            self.web_view.page().settings().setAttribute(
                QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

    def setup_js(self):
        # pass a reference (called qt_page) of self to the JS world
        self.frame.addToJavaScriptWindowObject("qt_page", self)

    def show_tree(self):
        # start the tree
        self.frame.evaluateJavaScript("init_tree()")

    def handle_json_updated(self, data):
        self.project_definition = data

    @pyqtProperty(str)
    def json_str(self):
        #This method gets exposed to JS thanks to @pyqtProperty(str)
        return json.dumps(self.project_definition)
