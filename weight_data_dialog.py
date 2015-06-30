# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
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
from copy import deepcopy

import json

from PyQt4.QtCore import (Qt,
                          QUrl,
                          QSettings,
                          pyqtProperty,
                          pyqtSignal,
                          pyqtSlot,
                          )

from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from PyQt4.QtWebKit import QWebSettings

from ui.ui_weight_data import Ui_WeightDataDialog

from shared import (DEFAULT_OPERATOR,
                    OPERATORS_DICT,
                    NUMERIC_FIELD_TYPES,
                    NODE_TYPES,
                    DEBUG)
from utils import get_field_names


class WeightDataDialog(QDialog):
    """
    Modal dialog allowing to select weights in a d3.js visualization
    """

    # QVariantMap is to map a JSON to dict see:
    #http://pyqt.sourceforge.net/Docs/PyQt4/incompatibilities.html#pyqt4-v4-7-4
    # this is for javascript to emit when it changes the json
    json_updated = pyqtSignal(['QVariantMap'], name='json_updated')
    # Python classes should connect to json_cleaned
    json_cleaned = pyqtSignal(['QVariantMap'], name='json_cleaned')

    def __init__(self, iface, project_definition):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_WeightDataDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.added_attrs_ids = set()
        self.discarded_feats = set()
        self.any_changes_made = False
        self.active_layer_numeric_fields = []
        self.set_active_layer_numeric_fields()

        self.project_definition = deepcopy(project_definition)
        try:
            proj_title = self.project_definition['title']
        except KeyError:
            proj_title = 'untitled'
        dialog_title = (
            'Set weights and operators for project: "%s"' % proj_title)
        self.setWindowTitle(dialog_title)

        self.web_view = self.ui.web_view
        self.web_view.load(QUrl('qrc:/plugins/svir/weight_data.html'))
        self.frame = self.web_view.page().mainFrame()

        self.setup_context_menu()

        self.frame.javaScriptWindowObjectCleared.connect(self.setup_js)
        self.web_view.loadFinished.connect(self.show_tree)
        self.json_updated.connect(self.handle_json_updated)
        self.populate_style_by_field_cbx()

    def update_project_definition(self, project_definition):
        self.project_definition = deepcopy(project_definition)
        self.populate_style_by_field_cbx()

    def set_active_layer_numeric_fields(self):
        self.active_layer_numeric_fields = [
            field.name()
            for field in self.iface.activeLayer().dataProvider().fields()
            if field.typeName() in NUMERIC_FIELD_TYPES]

    def populate_style_by_field_cbx(self):
        self.set_active_layer_numeric_fields()
        fields_in_proj_def = get_field_names(self.project_definition)
        fields_for_styling = [
            field for field in self.active_layer_numeric_fields
            if field in fields_in_proj_def]
        # block signals to avoid performing the onchange actions while adding
        # items programmatically
        self.ui.style_by_field_cbx.blockSignals(True)
        self.ui.style_by_field_cbx.clear()
        self.ui.style_by_field_cbx.addItem('')
        self.ui.style_by_field_cbx.addItems(fields_for_styling)
        if 'style_by_field' in self.project_definition:
            idx = self.ui.style_by_field_cbx.findText(
                self.project_definition['style_by_field'])
            self.ui.style_by_field_cbx.setCurrentIndex(idx)
        # reactivate the signals, so the user's changes will trigger something
        self.ui.style_by_field_cbx.blockSignals(False)

    def setup_context_menu(self):
        settings = QSettings()
        developer_mode = settings.value(
            '/svir/developer_mode', True, type=bool)
        if developer_mode is True:
            self.web_view.page().settings().setAttribute(
                QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

    def setup_js(self):
        # pass a reference (called qt_page) of self to the JS world
        # to expose a member of self to js you need to declare it as property
        # see for example self.json_str()
        self.frame.addToJavaScriptWindowObject('qt_page', self)

    def show_tree(self):
        # start the tree
        self.frame.evaluateJavaScript('init_tree()')

    def handle_json_updated(self, data):
        self.any_changes_made = True
        if DEBUG:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            print 'in handle_json_updated, data='
            pp.pprint(data)

        self.project_definition = self.clean_json([data])
        self.json_cleaned.emit(self.project_definition)

    def clean_json(self, data):
        # this method takes a list of dictionaries and removes some unneeded
        # keys. It recurses into the children elements
        ignore_keys = ['depth', 'x', 'y', 'id', 'x0', 'y0', 'parent']
        for element in data:
            for key in ignore_keys:
                element.pop(key, None)
            if 'children' in element:
                self.clean_json(element['children'])
        return data[0]

    @pyqtSlot(str)
    def on_style_by_field_cbx_currentIndexChanged(self):
        if self.ui.style_by_field_cbx.currentText():
            self.project_definition['style_by_field'] = \
                self.ui.style_by_field_cbx.currentText()
        elif 'style_by_field' in self.project_definition:
            # if the empty item is selected, clean the project definition
            del self.project_definition['style_by_field']

    @pyqtProperty(str)
    def json_str(self):
        #This method gets exposed to JS thanks to @pyqtProperty(str)
        return json.dumps(self.project_definition,
                          sort_keys=False,
                          indent=2,
                          separators=(',', ': '))

    @pyqtProperty(str)
    def DEFAULT_OPERATOR(self):
        return DEFAULT_OPERATOR

    @pyqtProperty(str)
    def OPERATORS(self):
        return ';'.join(OPERATORS_DICT.values())

    @pyqtProperty(str)
    def ACTIVE_LAYER_NUMERIC_FIELDS(self):
        return ';'.join(self.active_layer_numeric_fields)

    @pyqtProperty(str)
    def NODE_TYPES(self):
        return ';'.join(["%s:%s" % (k, v) for k, v in NODE_TYPES.iteritems()])
