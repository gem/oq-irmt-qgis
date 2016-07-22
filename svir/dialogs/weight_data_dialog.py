# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

from copy import deepcopy
import json
from qgis.gui import QgsMessageBar

from PyQt4.QtCore import (Qt,
                          QUrl,
                          QSettings,
                          pyqtProperty,
                          pyqtSignal,
                          pyqtSlot,
                          )
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox,
                         QPrinter,
                         )

from svir.utilities.shared import (DEFAULT_OPERATOR,
                                   OPERATORS_DICT,
                                   NUMERIC_FIELD_TYPES,
                                   NODE_TYPES,
                                   DEBUG)
from svir.utilities.utils import (get_field_names,
                                  confirmation_on_close,
                                  ask_for_destination_full_path_name,
                                  tr,
                                  log_msg,
                                  get_ui_class,
                                  )

FORM_CLASS = get_ui_class('ui_weight_data.ui')


class WeightDataDialog(QDialog, FORM_CLASS):
    """
    Modal dialog allowing to select weights in a d3.js visualization
    """

#   QVariantMap is to map a JSON to dict see:
#   http://pyqt.sourceforge.net/Docs/PyQt4/incompatibilities.html#pyqt4-v4-7-4
#   this is for javascript to emit when it changes the json
    json_updated = pyqtSignal(['QVariantMap'], name='json_updated')
    # Python classes should connect to json_cleaned
    json_cleaned = pyqtSignal(['QVariantMap'], name='json_cleaned')

    def __init__(self, iface, project_definition):
        self.iface = iface
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)

        self.added_attrs_ids = set()
        self.discarded_feats = set()
        self.any_changes_made = False

        # keep track of changes made to the tree while on-the-fly calculations
        # are off (the tree has changed, but indices haven't been recalculated)
        self.modified_project_definition = None

        self.active_layer_numeric_fields = []
        self.update_active_layer_numeric_fields()
        # keep track of the fact that the user has explicitly selected a field
        # to base the style on. Note that also the selection of the empty item
        # means that the user explicitly wants the system to use the default
        # behavior.
        self.style_by_field_selected = False

        self.project_definition = deepcopy(project_definition)
        try:
            proj_title = self.project_definition['title']
        except KeyError:
            proj_title = 'Untitled'
        dialog_title = (
            'Set weights and operators for project: "%s"' % proj_title)
        self.setWindowTitle(dialog_title)

        self.web_view = self.web_view
        self.web_view.page().mainFrame().setScrollBarPolicy(
            Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.web_view.page().mainFrame().setScrollBarPolicy(
            Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.web_view.load(QUrl('qrc:/plugins/irmt/weight_data.html'))

        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageSize(QPrinter.A4)
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setPrintRange(QPrinter.AllPages)
        self.printer.setOrientation(QPrinter.Portrait)
        self.printer.setDocName(proj_title)
        self.printer.setCreator(
            'GEM Integrated Risk Modelling Toolkit QGIS Plugin')

        self.frame = self.web_view.page().mainFrame()

        self.frame.javaScriptWindowObjectCleared.connect(self.setup_js)
        self.web_view.loadFinished.connect(self.show_tree)
        self.json_updated.connect(self.handle_json_updated)
        self.populate_style_by_field_cbx()

        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

    def closeEvent(self, event):
        confirmation_on_close(self, event)

    def reject(self):
        confirmation_on_close(self)

    def update_project_definition(self, project_definition):
        self.project_definition = deepcopy(project_definition)
        self.populate_style_by_field_cbx()

    def update_active_layer_numeric_fields(self):
        self.active_layer_numeric_fields = [
            field.name()
            for field in self.iface.activeLayer().dataProvider().fields()
            if field.typeName() in NUMERIC_FIELD_TYPES]

    def populate_style_by_field_cbx(self):
        self.update_active_layer_numeric_fields()
        fields_in_proj_def = get_field_names(self.project_definition)
        fields_for_styling = [
            field for field in self.active_layer_numeric_fields
            if field in fields_in_proj_def]
        # block signals to avoid performing the onchange actions while adding
        # items programmatically
        self.style_by_field_cbx.blockSignals(True)
        self.style_by_field_cbx.clear()
        self.style_by_field_cbx.addItem('')
        self.style_by_field_cbx.addItems(fields_for_styling)
        if 'style_by_field' in self.project_definition:
            idx = self.style_by_field_cbx.findText(
                self.project_definition['style_by_field'])
            self.style_by_field_cbx.setCurrentIndex(idx)
        # reactivate the signals, so the user's changes will trigger something
        self.style_by_field_cbx.blockSignals(False)

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

    def handle_json_updated(self, data):
        self.any_changes_made = True
        if DEBUG:
            import pprint
            ppdata = pprint.pformat(data, indent=4)
            log_msg('in handle_json_updated, data=\n%s' % ppdata)

        if self.on_the_fly_ckb.isChecked():
            self.project_definition = self.clean_json([data])
            self._manage_style_by_field()
            self.json_cleaned.emit(self.project_definition)

            # nothing has changed since the last recalculation
            self.modified_project_definition = None
        else:
            # keep track of the current status of the project definition
            # as it is in the d3 tree, so it can be used when OK is pressed
            self.modified_project_definition = self.clean_json([data])

    def _manage_style_by_field(self):
        if self.style_by_field_selected:
            if self.style_by_field_cbx.currentText():
                self.project_definition['style_by_field'] = \
                    self.style_by_field_cbx.currentText()
            elif 'style_by_field' in self.project_definition:
                # if the empty item is selected, clean the project definition
                del self.project_definition['style_by_field']

    def clean_json(self, data):
        # this method takes a list of dictionaries and removes some unneeded
        # keys. It recurses into the children elements

        if data == []:
            return data

        ignore_keys = ['depth', 'x', 'y', 'id', 'x0', 'y0', 'parent']
        for element in data:
            for key in ignore_keys:
                element.pop(key, None)
            if 'children' in element:
                self.clean_json(element['children'])
        # return the main element
        return data[0]

    @pyqtSlot()
    def on_print_btn_clicked(self):
        dest_full_path_name = ask_for_destination_full_path_name(
            self, filter='Pdf files (*.pdf)')
        if not dest_full_path_name:
            return
        self.printer.setOutputFileName(dest_full_path_name)
        try:
            self.web_view.print_(self.printer)
        except:
            self.iface.messageBar().pushMessage(
                tr("Error"),
                'It was impossible to create the pdf',
                level=QgsMessageBar.CRITICAL)
        else:
            self.iface.messageBar().pushMessage(
                tr("Info"),
                'Project definition printed as pdf and saved to: %s'
                % dest_full_path_name,
                level=QgsMessageBar.INFO,
                duration=8)

    @pyqtSlot(str)
    def on_style_by_field_cbx_currentIndexChanged(self):
        self.style_by_field_selected = True
        self._manage_style_by_field()
        self.json_updated.emit(self.project_definition)

    @pyqtProperty(str)
    def json_str(self):
        # This method gets exposed to JS thanks to @pyqtProperty(str)
        return json.dumps(self.project_definition,
                          sort_keys=False,
                          indent=2,
                          separators=(',', ': '))

    @pyqtProperty(str)
    def DEFAULT_OPERATOR(self):
        return DEFAULT_OPERATOR

    @pyqtProperty(bool)
    def DEV_MODE(self):
        developer_mode = QSettings().value(
            '/irmt/developer_mode', True, type=bool)

        return developer_mode

    @pyqtProperty(str)
    def OPERATORS(self):
        return ';'.join(OPERATORS_DICT.values())

    @pyqtProperty(str)
    def ACTIVE_LAYER_NUMERIC_FIELDS(self):
        return ';'.join(sorted(self.active_layer_numeric_fields))

    @pyqtProperty(str)
    def NODE_TYPES(self):
        return ';'.join(["%s:%s" % (k, v) for k, v in NODE_TYPES.iteritems()])

    def print_self_for_debug(self):
        msg = """
        var qt_page = {
            ACTIVE_LAYER_NUMERIC_FIELDS: "%s",
            DEFAULT_OPERATOR: "%s",
            NODE_TYPES: "%s",
            OPERATORS: "%s",
            json_str: '%s',
            json_updated: function (updated_json_str) {
                console.log("json_updated signal emitted with this JSON:");
                console.log(updated_json_str)
            },
            DEV_MODE: %s
        };""" % (self.ACTIVE_LAYER_NUMERIC_FIELDS,
                 self.DEFAULT_OPERATOR,
                 self.NODE_TYPES,
                 self.OPERATORS,
                 self.json_str.replace('\n', ''),
                 str(self.DEV_MODE).lower())
        log_msg(msg)
