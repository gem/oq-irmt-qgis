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

# create the dialog for zoom to point
from PyQt4.QtCore import Qt, QUrl, QSettings, pyqtProperty, pyqtSignal
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

    json_updated = pyqtSignal([unicode], name='json_updated')

    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_WeightDataDialog()
        self.ui.setupUi(self)

        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.web_view = self.ui.web_view
        self.web_view.load(QUrl('qrc:/plugins/svir/weight_data.html'))
        self.frame = self.web_view.page().mainFrame()

        self.setup_context_menu()

        self.frame.javaScriptWindowObjectCleared.connect(self.setup_js)
        self.web_view.loadFinished.connect(self.show_tree)
        self.json_updated.connect(self.handle_json)

    def setup_js(self):
        self.frame.addToJavaScriptWindowObject("qt_page", self)

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

    def show_tree(self):
        self.frame.evaluateJavaScript("init_tree()")
    
    def handle_json(self, json):
        print 'UPDATED json: %s' % json

    @pyqtProperty(str)
    def json_str(self):
        return self.JSON

    JSON = '{ \
              "name": "ir",\
              "weight": "",\
              "level" : 1,\
              "children": [\
              {\
                "name": "aal",\
                "weight": 0.5,\
                "level": 2\
              },\
              {\
                "name": "svi",\
                "weight": 0.5,\
                "level": 2,\
                "children": [\
                  {\
                    "name": "population",\
                    "weight": 0.16,\
                    "level": 3.2,\
                    "type": "categoryIndicator",\
                    "children": [\
                      {"name": "QFEMALE", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QURBAN", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "MIGFOREIGN", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "MIGMUNICIP", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QFOREIGN", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QAGEDEP", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "POPDENT", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "PPUNIT", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QFHH", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QRENTAL", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QDISABLED", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"},\
                      {"name": "QSSINT", "weight": 0.083, "level": 4.0, "type": "primaryIndicator"}\
                    ]\
                  },\
                  {\
                    "name": "economy",\
                    "weight": 0.16,\
                    "level": 3.2,\
                    "type": "categoryIndicator",\
                    "children": [\
                      {"name": "QUNEMPL", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"},\
                      {"name": "QFEMLBR", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"},\
                      {"name": "QSECOEMPL", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"},\
                      {"name": "QSERVEMPL", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"},\
                      {"name": "QNOSKILLEMPL", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"},\
                      {"name": "PCPP", "weight": 0.167, "level": 4.1, "type": "primaryIndicator"}\
                    ]\
                  },\
                  {\
                    "name": "education",\
                    "weight": 0.16,\
                    "level": 3.2,\
                    "type": "categoryIndicator",\
                    "children": [\
                      {"name": "QEDLESS", "weight": 0.5, "level": 4.2, "type": "primaryIndicator"},\
                      {"name": "EDUTERTIARY", "weight": 0.5, "level": 4.2, "type": "primaryIndicator"}\
                    ]\
                  },\
                  {\
                    "name": "infrastructure",\
                    "weight": 0.16,\
                    "level": 3.2,\
                    "type": "categoryIndicator",\
                    "children": [\
                      {"name": "QBLDREPAIR", "weight": 0.25, "level": 4.4, "type": "primaryIndicator"},\
                      {"name": "NEWBUILD", "weight": 0.25, "level": 4.4, "type": "primaryIndicator"},\
                      {"name": "QPOPNOWATER", "weight": 0.25, "level": 4.4, "type": "primaryIndicator"},\
                      {"name": "QPOPNOWASTE", "weight": 0.25, "level": 4.4, "type": "primaryIndicator"}\
                    ]\
                  },\
                  {\
                    "name": "governance",\
                    "weight": 0.16,\
                    "level": 3.2,\
                    "type": "categoryIndicator",\
                    "children": [\
                      {"name": "CRIMERATE", "weight": 0.33, "level": 4.5, "type": "primaryIndicator"},\
                      {"name": "QNOVOTEMU", "weight": 0.33, "level": 4.5, "type": "primaryIndicator"},\
                      {"name": "QNOVOTEPR", "weight": 0.33, "level": 4.5, "type": "primaryIndicator"}\
                    ]\
                  }\
                ]\
              }\
             ]\
            }'