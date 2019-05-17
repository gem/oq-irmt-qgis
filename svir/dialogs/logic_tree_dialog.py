# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2019 by GEM Foundation
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

import json

from qgis.PyQt.QtCore import (
    Qt, QUrl, QSettings, pyqtProperty, pyqtSlot)
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtPrintSupport import QPrinter

from svir.utilities.shared import DEBUG
from svir.utilities.utils import (
                                  confirmation_on_close,
                                  ask_for_destination_full_path_name,
                                  log_msg,
                                  get_ui_class,
                                  )

FORM_CLASS = get_ui_class('ui_logic_tree.ui')


if DEBUG:
    # turn on developer tools in webkit so we can get at the
    # javascript console for debugging (it causes segfaults in tests, so it has
    # to be kept disabled while it is not used for debugging).
    QWebSettings.globalSettings().setAttribute(
        QWebSettings.DeveloperExtrasEnabled, True)


class LogicTreeDialog(QDialog, FORM_CLASS):
    """
    Dialog allowing to edit a logic tree in a d3.js visualization
    """

    def __init__(self, iface, logic_tree):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)

        self.logic_tree = logic_tree
        self.setWindowTitle("Logic Tree")

        self.web_view = self.web_view
        self.web_view.page().mainFrame().setScrollBarPolicy(
            Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.web_view.page().mainFrame().setScrollBarPolicy(
            Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        # self.web_view.load(QUrl('qrc:/plugins/irmt/logic_tree.html'))
        self.web_view.load(QUrl('qrc:/plugins/irmt/tree_example.html'))

        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageSize(QPrinter.A4)
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setPrintRange(QPrinter.AllPages)
        self.printer.setOrientation(QPrinter.Portrait)
        self.printer.setDocName("Logic Tree")
        self.printer.setCreator(
            'GEM Integrated Risk Modelling Toolkit QGIS Plugin')

        self.frame = self.web_view.page().mainFrame()

        self.frame.javaScriptWindowObjectCleared.connect(self.setup_js)
        self.web_view.loadFinished.connect(self.show_tree)

        if not DEBUG:
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

        self.web_view.settings().setAttribute(
            QWebSettings.JavascriptEnabled, True)

    def closeEvent(self, event):
        confirmation_on_close(self, event)

    def reject(self):
        confirmation_on_close(self)

    def setup_js(self):
        # pass a reference (called qt_page) of self to the JS world
        # to expose a member of self to js you need to declare it as property
        # see for example self.json_str()

        if DEBUG:
            log_msg("######################### for weight_data_debug.html")
            self.print_self_for_debug()
            log_msg("######################### end for weight_data_debug.html")

        self.frame.addToJavaScriptWindowObject('qt_page', self)

    def show_tree(self):
        # start the tree
        self.frame.evaluateJavaScript('init_tree()')

    @pyqtSlot()
    def on_print_btn_clicked(self):
        dest_full_path_name = ask_for_destination_full_path_name(
            self, filter='Pdf files (*.pdf)')
        if not dest_full_path_name:
            return
        self.printer.setOutputFileName(dest_full_path_name)
        try:
            self.web_view.print_(self.printer)
        except Exception as exc:
            msg = 'It was impossible to create the pdf'
            log_msg(msg, level='C', message_bar=self.iface.messageBar(),
                    exception=exc)
        else:
            msg = ('Project definition printed as pdf and saved to: %s'
                   % dest_full_path_name)
            log_msg(msg, level='S', message_bar=self.iface.messageBar())

    @pyqtProperty(str)
    def json_str(self):
        # This method gets exposed to JS thanks to @pyqtProperty(str)
        return json.dumps(self.logic_tree,
                          sort_keys=False,
                          indent=2,
                          separators=(',', ': '))

    @pyqtProperty(bool)
    def DEV_MODE(self):
        developer_mode = QSettings().value(
            '/irmt/developer_mode', True, type=bool)

        return developer_mode

    def print_self_for_debug(self):
        msg = """
        var qt_page = {
            json_str: '%s',
            },
            DEV_MODE: %s
        };""" % (self.json_str.replace('\n', ''),
                 str(self.DEV_MODE).lower())
        log_msg(msg)
