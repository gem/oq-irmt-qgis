# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2015 by GEM Foundation
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

import numpy
import collections
import json
import os
import sys
import traceback
import locale
import zlib
import io
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from copy import deepcopy
from time import time
from pprint import pformat
from qgis.core import (
                       QgsProject,
                       QgsMessageLog,
                       QgsVectorLayer,
                       QgsVectorFileWriter,
                       )
from qgis.core import Qgis
from qgis.gui import QgsMessageBar, QgsMessageBarItem

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSettings, QUrl, QUrlQuery
from qgis.PyQt.QtWidgets import (
                                 QApplication,
                                 QProgressBar,
                                 QToolButton,
                                 QFileDialog,
                                 QMessageBox,
                                 QDialog,
                                 QTextBrowser,
                                 QVBoxLayout,
                                 )
from qgis.PyQt.QtGui import QColor

from svir.utilities.shared import (
                                   DEBUG,
                                   DEFAULT_SETTINGS,
                                   DEFAULT_PLATFORM_PROFILES,
                                   DEFAULT_ENGINE_PROFILES,
                                   )

F32 = numpy.float32

_IRMT_VERSION = None


def get_irmt_version():
    """
    Get the plugin's version from metadata.txt
    """
    global _IRMT_VERSION
    if _IRMT_VERSION is None:
        metadata_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'metadata.txt')
        with open(metadata_path, 'r', newline='') as f:
            for line in f:
                if line.startswith('version='):
                    _IRMT_VERSION = line.split('=')[1].strip()
    return _IRMT_VERSION


def log_msg(message, tag='GEM OpenQuake IRMT plugin', level='I',
            message_bar=None, duration=None, exception=None,
            print_to_stderr=False):
    """
    Add a message to the QGIS message log. If a messageBar is provided,
    the same message will be displayed also in the messageBar. In the latter
    case, warnings and critical messages will have no timeout, whereas
    info messages will have a duration of 5 seconds.

    :param message: the message
    :param tag: the log topic
    :param level:
        the importance level
        'I' -> Qgis.Info,
        'W' -> Qgis.Warning,
        'C' -> Qgis.Critical,
        'S' -> Qgis.Success,
    :param message_bar: a `QgsMessageBar` instance
    :param duration: how long (in seconds) the message will be displayed (use 0
        to keep the message visible indefinitely, or None to use
        the default duration of the chosen level
    :param exception: an optional exception, from which the traceback will be
        extracted and written in the log. When the exception is provided,
        an additional button in the `QgsMessageBar` allows to visualize the
        traceback in a separate window.
    :print_to_stderr: if True, the error message will be printed also to stderr
    """
    levels = {
              'I': Qgis.Info,
              'W': Qgis.Warning,
              'C': Qgis.Critical,
              'S': Qgis.Success,
              }
    if level not in levels:
        raise ValueError('Level must be one of %s' % levels.keys())
    tb_text = ''
    if exception is not None:
        tb_lines = traceback.format_exception(
            exception.__class__, exception, exception.__traceback__)
        tb_text = '\n' + ''.join(tb_lines)

    # if we are running nosetests, exit on critical errors
    if 'nose' in sys.modules and level == 'C':
        raise RuntimeError(message)
    else:
        log_verbosity = QSettings().value('irmt/log_level', 'W')
        if (level == 'C'
                or level == 'W' and log_verbosity in ('S', 'I', 'W')
                or level in ('I', 'S') and log_verbosity in ('I', 'S')):
            QgsMessageLog.logMessage(
                tr(message) + tb_text, tr(tag), levels[level])
            if exception is not None:
                tb_btn = QToolButton(message_bar)
                tb_btn.setText('Show Traceback')
                tb_btn.clicked.connect(lambda: _on_tb_btn_clicked(tb_text))
        if message_bar is not None:
            if level == 'S':
                title = 'Success'
                duration = duration if duration is not None else 8
            elif level == 'I':
                title = 'Info'
                duration = duration if duration is not None else 8
            elif level == 'W':
                title = 'Warning'
                duration = duration if duration is not None else 0
            elif level == 'C':
                title = 'Error'
                duration = duration if duration is not None else 0
            max_msg_len = 200
            if len(message) > max_msg_len:
                message = ("%s[...]" % message[:max_msg_len])
            if exception is None:
                message_bar.pushMessage(tr(title),
                                        tr(message),
                                        levels[level],
                                        duration)
            else:
                mb_item = QgsMessageBarItem(
                    tr(title), tr(message), tb_btn, levels[level], duration)
                message_bar.pushItem(mb_item)
        if print_to_stderr:
            print('\t\t%s' % message, file=sys.stderr)


def _on_tb_btn_clicked(message):
    vbox = QVBoxLayout()
    dlg = QDialog()
    dlg.setWindowTitle('Traceback')
    text_browser = QTextBrowser()
    formatted_msg = highlight(message, PythonLexer(), HtmlFormatter(full=True))
    text_browser.setHtml(formatted_msg)
    vbox.addWidget(text_browser)
    dlg.setLayout(vbox)
    dlg.setMinimumSize(700, 500)
    dlg.exec_()


def tr(message):
    """
    Leverage QApplication.translate to translate a message

    :param message: the message to be translated
    :returns: the return value of `QApplication.translate('Irmt', message)`
    """
    return QApplication.translate('Irmt', message)


def confirmation_on_close(parent, event=None):
    """
    Open a QMessageBox to confirm closing a dialog discarding changes

    :param parent: the parent dialog that is being closed
    :param event: event that triggered this dialog (e.g. reject or closeEvent)
    """
    msg = tr("WARNING: all unsaved changes will be lost. Are you sure?")
    reply = QMessageBox.question(
        parent, 'Message', msg, QMessageBox.Yes, QMessageBox.No)
    if event is not None:
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    else:
        if reply == QMessageBox.Yes:
            parent.__class__.__base__.reject(parent)


def replace_fields(sub_tree_root, before, after):
    """
    Recursively search the project definition for 'field's equal to the
    string before and replace the value with the string after.
    It is useful, e.g., when we transform a field that is tracked by the
    project definition, and we obtain a new field that we want to track
    instead of the original one.
    It works by side-effect, modifying the passed project definition.

    :param sub_tree_root:
        node of a project definition. From that node (used as root) towards the
        leaves of the tree, the function will recursively search for nodes with
        a 'field' property that contains the string before
    :param before: string to be replaced
    :param after: new value for the replaced string
    """
    if 'field' in sub_tree_root and sub_tree_root['field'] == before:
        sub_tree_root['field'] = after
    if 'children' in sub_tree_root:
        for child in sub_tree_root['children']:
            replace_fields(child, before, after)


def count_heading_commented_lines(fname):
    """
    count top lines in the file starting with '#'
    """
    with open(fname, 'r', newline='') as f:
        lines_to_skip_count = 0
        for line in f:
            li = line.strip()
            if li.startswith('#'):
                lines_to_skip_count += 1
            else:
                break
    if DEBUG:
        log_msg("The file contains %s heading lines starting with #" % (
            lines_to_skip_count))
    return lines_to_skip_count


def set_operator(sub_tree, operator):
    """
    if the root of the sub_tree has children, set the operator to be used to
    combine the children. If any of the children have children, set also
    their operators to the same one applied to the root.

    :param sub_tree: root of the subtree to which we want to set the operator
    :param operator: the operator to be applied
    :returns: the modified subtree
    """
    node = deepcopy(sub_tree)
    if 'children' in node:
        for child_idx, child in enumerate(node['children']):
            modified_child = set_operator(child, operator)
            node['children'][child_idx] = modified_child
        node['operator'] = operator
    return node


def get_node(sub_tree, name):
    """
    Browse the tree (recursively searching each node's children), looking for
    a node with a specific name.

    :param sub_tree: root of the subtree through which we want to search
    :param name: name of the node to be searched
    :returns: the node, if found, otherwise None
    """
    if 'name' in sub_tree and sub_tree['name'] == name:
        found_node = sub_tree
        return found_node
    if 'children' in sub_tree:
        for child in sub_tree['children']:
            found_node = get_node(child, name)
            if found_node:
                return found_node
    return None  # not found


def get_field_names(sub_tree, field_names=None):
    """
    Return a list of all the field names defined in the project definition

    :sub_tree: root of the subtree for which we want to collect field names
    :param field_names: an accumulator that is extended browsing the tree
                        recursively (if None, a list will be created) and
                        collecting the field names
    :returns: the accumulator
    """
    if field_names is None:
        field_names = set()
    if 'field' in sub_tree:
        field_names.add(sub_tree['field'])
    if 'children' in sub_tree:
        for child in sub_tree['children']:
            child_field_names = get_field_names(child, field_names)
            field_names = field_names.union(child_field_names)
    return field_names


def clear_progress_message_bar(msg_bar, msg_bar_item=None):
    """
    Clear the progress message bar
    """
    if msg_bar_item:
        msg_bar.popWidget(msg_bar_item)
    else:
        msg_bar.clearWidgets()


def create_progress_message_bar(msg_bar, msg, no_percentage=False):
    """
    Use the messageBar of QGIS to display a message describing what's going
    on (typically during a time-consuming task), and a bar showing the
    progress of the process.

    :param msg: Message to be displayed, describing the current task
    :type: str

    :returns: progress object on which we can set the percentage of
              completion of the task through progress.setValue(percentage)
    :rtype: QProgressBar
    """
    progress_message_bar = msg_bar.createMessage(msg)
    progress = QProgressBar()
    if no_percentage:
        progress.setRange(0, 0)
    progress_message_bar.layout().addWidget(progress)
    msg_bar.pushWidget(progress_message_bar, Qgis.Info)
    return progress_message_bar, progress


def assign_default_weights(svi_themes):
    """
    Count themes and indicators and assign default weights
    using 2 decimal points (%.2f)

    :param svi_themes: list of nodes corresponding to socioeconomic themes
    """
    themes_count = len(svi_themes)
    theme_weight = float('%.2f' % (1.0 / themes_count))
    for i, theme in enumerate(svi_themes):
        theme['weight'] = theme_weight
        for indicator in theme['children']:
            indicator_weight = 1.0 / len(theme['children'])
            indicator_weight = '%.2f' % indicator_weight
            indicator['weight'] = float(indicator_weight)


def reload_layers_in_cbx(combo, layer_types=None, skip_layer_ids=None):
    """
    Load layers into a combobox. Can filter by layer type.
    the additional filter can be QgsMapLayer.VectorLayer, ...

    :param combo: The combobox to be repopulated
    :type combo: QComboBox
    :param layer_types: list containing types or None if all type accepted
    :type layer_types: [QgsMapLayer.LayerType, ...]
    :param skip_layer_ids: list containing layers to be skipped in the combobox
     or None if all layers accepted
    :type skip_layer_ids: [QgsMapLayer ...]
    """
    combo.clear()
    for l in list(QgsProject.instance().mapLayers().values()):
        layer_type_allowed = bool(layer_types is None
                                  or l.type() in layer_types)
        layer_id_allowed = bool(skip_layer_ids is None
                                or l.id() not in skip_layer_ids)
        if layer_type_allowed and layer_id_allowed:
            combo.addItem(l.name(), l)


def reload_attrib_cbx(
        combo, layer, prepend_empty_item=False, *valid_field_types):
    """
    Load attributes of a layer into a combobox. Can filter by field data type.
    the optional filter can be NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES, ...
    if no filter is specified all fields are returned

    :param combo: The combobox to be repopulated
    :type combo: QComboBox
    :param layer: The QgsVectorLayer from where the fields are read
    :type layer: QgsVectorLayer
    :param prepend_empty_item: if to prepend an empty item to the combo
    :type layer: Bool
    :param \*valid_field_types: multiple tuples containing types
    :type \*valid_field_types: tuple, tuple, ...
    """
    field_types = set()
    for field_type in valid_field_types:
        field_types.update(field_type)

    # reset combo box
    combo.clear()
    # populate combo box with field names taken by layers
    fields = list(layer.fields())

    if prepend_empty_item:
        combo.addItem(None)

    for field in fields:
        # add if in field_types
        if not field_types or field.typeName() in field_types:
            combo.addItem(field.name(), field)


def toggle_select_features(layer, use_new, new_feature_ids, old_feature_ids):
    """
    Toggles feature selection between two sets.

    :param layer: The QgsVectorLayer where the selection is applied
    :type layer: QgsVectorLayer
    :param use_new: which list to select
    :type use_new: bool
    :param new_feature_ids: The list to select if use_new is true
    :type new_feature_ids: QgsFeatureIds
    :param old_feature_ids: The list to select if use_new is false
    :type old_feature_ids: QgsFeatureIds
    """
    if use_new:
        layer.selectByIds(list(new_feature_ids))
    else:
        layer.selectByIds(list(old_feature_ids))


def toggle_select_features_widget(title, text, button_text, layer,
                                  new_feature_ids, old_feature_ids):
    """
    Create a widget for QgsMessageBar to switch between two sets.

    :param title: The title
    :type title: str
    :param text: The text message
    :type text: str
    :param button_text: The text on the toggle button
    :type button_text: str
    :param layer: The QgsVectorLayer where the selection is applied
    :type layer: QgsVectorLayer
    :param new_feature_ids: The list to select if use_new is true
    :type new_feature_ids: QgsFeatureIds
    :param old_feature_ids: The list to select if use_new is false
    :type old_feature_ids: QgsFeatureIds

    :returns: the widget
    """
    widget = QgsMessageBar.createMessage(title, text)
    button = QToolButton(widget)
    button.setCheckable(True)
    button.setText(button_text)
    button.toggled.connect(
        lambda on,
        layer=layer,
        new_feature_ids=new_feature_ids,
        old_feature_ids=old_feature_ids:
        toggle_select_features(layer,
                               on,
                               new_feature_ids,
                               old_feature_ids))
    widget.layout().addWidget(button)
    return widget


def platform_login(host, username, password, session):
    """
    Logs in a session to a platform

    :param host: The host url
    :type host: str
    :param username: The username
    :type username: str
    :param password: The password
    :type password: str
    :param session: The session to be autenticated
    :type session: Session
    """
    login_url = host + '/account/ajax_login'
    _login(login_url, username, password, session)


def engine_login(host, username, password, session):
    """
    Logs in a session to a engine server

    :param host: The host url
    :type host: str
    :param username: The username
    :type username: str
    :param password: The password
    :type password: str
    :param session: The session to be autenticated
    :type session: Session
    """
    login_url = host + '/accounts/ajax_login/'
    _login(login_url, username, password, session)


def _login(login_url, username, password, session):
    try:
        session_resp = session.post(login_url,
                                    data={
                                        "username": username,
                                        "password": password
                                    },
                                    timeout=10,
                                    )
    except Exception:
        msg = "Unable to login. %s" % traceback.format_exc()
        raise SvNetworkError(msg)
    if session_resp.status_code != 200:  # 200 means successful:OK
        error_message = ('Unable to login: %s' %
                         session_resp.text)
        raise SvNetworkError(error_message)


def update_platform_project(host,
                            session,
                            project_definition,
                            platform_layer_id):
    """
    Add a project definition to one of the available projects on the
    OpenQuake Platform

    :param host: url of the OpenQuake Platform server
    :param session: authenticated session to be used
    :param project_definition: the project definition to be added
    :param platform_layer_id: the id of the platform layer to be updated

    :returns: the server's response
    """
    proj_def_str = json.dumps(project_definition,
                              sort_keys=False,
                              indent=2,
                              separators=(',', ': '))
    payload = {'layer_name': platform_layer_id,
               'project_definition': proj_def_str}
    resp = session.post(host + '/svir/add_project_definition', data=payload)
    return resp


def ask_for_destination_full_path_name(
        parent, text='Save File', filter='Shapefiles (*.shp)'):
    """
    Open a dialog to ask for a destination full path name, initially pointing
    to the home directory.
    QFileDialog by defaults asks for confirmation if an existing file is
    selected and it automatically resolves symlinks.

    :param parent: the parent dialog
    :param text: the dialog's title text
    :param filter:
        filter files by specific formats. Default: 'Shapefiles (\*.shp)'
        A more elaborate example:

        "Images (\*.png \*.xpm \*.jpg);;
        Text files (\*.txt);;XML files (\*.xml)"

    :returns: full path name of the destination file
    """
    full_path_name, _ = QFileDialog.getSaveFileName(
        parent, text, directory=os.path.expanduser("~"), filter=filter)
    if full_path_name:
        return full_path_name


def ask_for_download_destination_folder(parent, text='Download destination'):
    """
    Open a dialog to ask for a download destination folder, initially pointing
    to the home directory.

    :param parent: the parent dialog
    :param text: the dialog's title text

    :returns: full path of the destination folder
    """
    return QFileDialog.getExistingDirectory(
        parent,
        text,
        os.path.expanduser("~"))


def files_exist_in_destination(destination, file_names):
    """
    Check if any of the provided file names exist in the destination folder

    :param destination: destination folder
    :param file_names: list of file names

    :returns: list of file names that already exist in the destination folder
    """
    existing_files_in_destination = []
    for file_name in file_names:
        file_path = os.path.join(destination, file_name)
        if os.path.isfile(file_path):
            existing_files_in_destination.append(file_path)
    return existing_files_in_destination


def confirm_overwrite(parent, files):
    """
    Open a dialog to ask for user's confirmation on file overwriting
    """
    return QMessageBox.question(
        parent,
        'Overwrite existing files?',
        'If you continue the following files will be '
        'overwritten: %s\n\n'
        'Continue?' % '\n'.join(files),
        QMessageBox.Yes | QMessageBox.No)


class Register(collections.OrderedDict):
    """
    Useful to keep (in a single point) a register of available variants of
    something, e.g. a set of different transformation algorithms
    """
    def add(self, tag):
        """
        Add a new variant to the OrderedDict
        For instance, if we add a class implementing a specific transformation
        algorithm, the register will keep track of a new item having as key the
        name of the algorithm and as value the class implementing the algorithm
        """
        def dec(obj):
            self[tag] = obj
            return obj
        return dec


class TraceTimeManager(object):
    """
    Wrapper to check how much time is needed to complete a block of code

    :param message: message describing the task to be monitored
    :param debug: if False, nothing will be done. Otherwise, times will be
                  measured and logged
    """
    def __init__(self, message, debug=False):
        self.debug = debug
        self.message = message
        self.t_start = None
        self.t_stop = None

    def __enter__(self):
        if self.debug:
            log_msg(self.message)
            self.t_start = time()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.debug:
            self.t_stop = time()
            log_msg("Completed in %f" % (self.t_stop - self.t_start))


class WaitCursorManager(object):
    """
    Wrapper to be used for a time-consuming block of code, that changes the
    mouse cursor and adds an info message to the messageBar
    """
    def __init__(self, msg=None, message_bar=None):
        self.msg = msg
        self.message_bar = message_bar
        self.has_message = msg and message_bar
        self.message = None

    def __enter__(self):
        if self.has_message:
            self.message = self.message_bar.createMessage(
                tr('Info'), tr(self.msg))
            self.message = self.message_bar.pushWidget(
                self.message, level=Qgis.Info)
            QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, exc_type, exc_value, traceback):
        QApplication.restoreOverrideCursor()
        if self.has_message:
            self.message_bar.popWidget(self.message)


class SvNetworkError(Exception):
    pass


class UserAbortedNotification(Exception):
    pass


class ReadMetadataError(Exception):
    """When a metadata xml is not correctly formatted can't be read"""
    suggestion = (
        'Check that the file is correct')


def write_layer_suppl_info_to_qgs(layer_id, suppl_info):
    """
    Write into the QgsProject the given supplemental information, associating
    it with the given layer id.

    :param layer_id: id of the layer for which we want to update the
                     corresponding supplemental_information
    :param suppl_info: the supplemental information
    """
    # TODO: upgrade old project definitions
    # set the QgsProject's property
    QgsProject.instance().writeEntry(
        'irmt', layer_id,
        json.dumps(suppl_info,
                   sort_keys=False,
                   indent=2,
                   separators=(',', ': ')))

    # avoids not finding the layer_id in supplemental_info
    read_layer_suppl_info_from_qgs(layer_id, suppl_info)
    if DEBUG:
        prop_suppl_info, found = QgsProject.instance().readEntry('irmt',
                                                                 layer_id)
        assert found, 'After writeEntry, readEntry did not find the same item!'
        prop_suppl_info_obj = json.loads(prop_suppl_info)
        prop_suppl_info_str = pformat(prop_suppl_info_obj, indent=4)
        log_msg(("Project property 'supplemental_information[%s]'"
                 " updated: \n%s") % (layer_id, prop_suppl_info_str))


def read_layer_suppl_info_from_qgs(layer_id, supplemental_information):
    """
    Read from the QgsProject the supplemental information associated to the
    given layer

    :param layer_id: the layer id for which we want to retrieve the
                     supplemental information
    :param supplemental_information: the supplemental information to be updated

    :returns: a tuple, with the returned supplemental information and a
              boolean indicating if such property is available
    """
    layer_suppl_info_str, _ = QgsProject.instance().readEntry(
        'irmt', layer_id, '{}')
    supplemental_information[layer_id] = json.loads(layer_suppl_info_str)

    if DEBUG:
        suppl_info_str = pformat(supplemental_information[layer_id], indent=4)
        log_msg(("self.supplemental_information[%s] synchronized"
                 " with project, as: \n%s") % (layer_id, suppl_info_str))


def insert_platform_layer_id(
        layer_url, active_layer_id, supplemental_information):
    """
    Insert the platform layer id into the supplemental information

    :param layer_url: url of the OpenQuake Platform layer
    :param active_layer_id: id of the QGIS layer that is currently selected
    :param supplemental_information: the supplemental information
    """
    platform_layer_id = layer_url.split('/')[-1]
    suppl_info = supplemental_information[active_layer_id]
    if 'platform_layer_id' not in suppl_info:
        suppl_info['platform_layer_id'] = platform_layer_id
    write_layer_suppl_info_to_qgs(active_layer_id, suppl_info)


def get_ui_class(ui_file):
    """Get UI Python class from .ui file.
       Can be filename.ui or subdirectory/filename.ui

    :param ui_file: The file of the ui in svir.ui
    :type ui_file: str
    """
    os.path.sep.join(ui_file.split('/'))
    ui_file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            'ui',
            ui_file
        )
    )
    return uic.loadUiType(ui_file_path)[0]


def save_layer_setting(layer, setting, value):
    if layer is not None:
        QgsProject.instance().writeEntry(
            'irmt', '%s/%s' % (layer.id(), setting),
            json.dumps(value))


def get_layer_setting(layer, setting):
    if layer is not None:
        value_str, found = QgsProject.instance().readEntry(
            'irmt', '%s/%s' % (layer.id(), setting), '')
        if found and value_str:
            value = json.loads(value_str)
            return value
    return None


def save_layer_as_shapefile(orig_layer, dest_path, crs=None):
    if crs is None:
        crs = orig_layer.crs()
    old_lc_numeric = locale.getlocale(locale.LC_NUMERIC)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    writer_error = QgsVectorFileWriter.writeAsVectorFormat(
        orig_layer, dest_path, 'utf-8', crs, 'ESRI Shapefile')
    locale.setlocale(locale.LC_NUMERIC, old_lc_numeric)
    return writer_error


def _check_type(
        variable, setting_name, expected_type, default_value, message_bar):
    # return the variable as it is or restore the default if corrupted
    if not isinstance(variable, expected_type):
        msg = ('The type of the stored setting "%s" was not valid,'
               ' so the default has been restored.' % setting_name)
        log_msg(msg, level='C', message_bar=message_bar)
        variable = default_value
    return variable


def get_style(layer, message_bar, restore_defaults=False):
    settings = QSettings()
    if restore_defaults:
        color_from_rgba = DEFAULT_SETTINGS['color_from_rgba']
    else:
        try:
            color_from_rgba = settings.value(
                'irmt/style_color_from',
                DEFAULT_SETTINGS['color_from_rgba'],
                type=int)
        except TypeError:
            msg = ('The type of the stored setting "style_color_from" was not'
                   ' valid, so the default has been restored.')
            log_msg(msg, level='C', message_bar=message_bar)
            color_from_rgba = DEFAULT_SETTINGS['color_from_rgba']
    color_from = QColor().fromRgba(color_from_rgba)
    if restore_defaults:
        color_to_rgba = DEFAULT_SETTINGS['color_to_rgba']
    else:
        try:
            color_to_rgba = settings.value(
                'irmt/style_color_to',
                DEFAULT_SETTINGS['color_to_rgba'],
                type=int)
        except TypeError:
            msg = ('The type of the stored setting "style_color_to" was not'
                   ' valid, so the default has been restored.')
            log_msg(msg, level='C', message_bar=message_bar)
            color_to_rgba = DEFAULT_SETTINGS['color_to_rgba']
    color_to = QColor().fromRgba(color_to_rgba)
    mode = (DEFAULT_SETTINGS['style_mode']
            if restore_defaults
            else settings.value(
                'irmt/style_mode', DEFAULT_SETTINGS['style_mode'], type=int))
    classes = (DEFAULT_SETTINGS['style_classes']
               if restore_defaults
               else settings.value(
                   'irmt/style_classes',
                   DEFAULT_SETTINGS['style_classes'],
                   type=int))
    # look for the setting associated to the layer if available
    force_restyling = None
    if layer is not None:
        # NOTE: We can't use %s/%s instead of %s_%s, because / is a special
        #       character
        value, found = QgsProject.instance().readBoolEntry(
            'irmt', '%s_%s' % (layer.id(), 'force_restyling'))
        if found:
            force_restyling = value
    if restore_defaults:
        force_restyling = DEFAULT_SETTINGS['force_restyling']
    # FIXME QGIS3: at project level, qgis pretends to find a value as false,
    #              even when it should be not found, so it prevents layers
    #              to be styled
    #
    # otherwise look for the setting at project level
    # if force_restyling is None:
    #     value, found = QgsProject.instance().readBoolEntry(
    #         'irmt', 'force_restyling')
    #     if found:
    #         force_restyling = value
    # if again the setting is not found, look for it at the general level
    if force_restyling is None:
        force_restyling = settings.value(
            'irmt/force_restyling',
            DEFAULT_SETTINGS['force_restyling'],
            type=bool)
    return {
        'color_from': color_from,
        'color_to': color_to,
        'mode': mode,
        'classes': classes,
        'force_restyling': force_restyling
    }


def clear_widgets_from_layout(layout):
    """
    Recursively remove all widgets from the layout, except from nested
    layouts. If any of such widgets is a layout, then clear its widgets
    instead of deleting it.
    """
    for i in reversed(list(range(layout.count()))):
        item = layout.itemAt(i)
        # check if the item is a sub-layout (nested inside the layout)
        sublayout = item.layout()
        if sublayout is not None:
            clear_widgets_from_layout(sublayout)
            continue
        # check if the item is a widget
        widget = item.widget()
        if widget is not None:
            # NOTE: in the past, we were setting the parent to None, which
            #       is a valid alternative to delete the widget. This approach
            #       is probably a little safer
            widget.deleteLater()


def import_layer_from_csv(parent,
                          csv_path,
                          layer_name,
                          iface,
                          longitude_field='lon',
                          latitude_field='lat',
                          delimiter=',',
                          quote='"',
                          lines_to_skip_count=0,
                          wkt_field=None,
                          save_as_shp=False,
                          dest_shp=None,
                          zoom_to_layer=True,
                          has_geom=True,
                          subset=None,
                          add_to_legend=True,
                          add_on_top=False):
    url = QUrl.fromLocalFile(csv_path)
    url_query = QUrlQuery()
    url_query.addQueryItem('type', 'csv')
    if has_geom:
        if wkt_field is not None:
            url_query.addQueryItem('wktField', wkt_field)
        else:
            url_query.addQueryItem('xField', longitude_field)
            url_query.addQueryItem('yField', latitude_field)
        url_query.addQueryItem('spatialIndex', 'no')
        url_query.addQueryItem('crs', 'epsg:4326')
    url_query.addQueryItem('subsetIndex', 'no')
    url_query.addQueryItem('watchFile', 'no')
    url_query.addQueryItem('delimiter', delimiter)
    url_query.addQueryItem('quote', quote)
    url_query.addQueryItem('skipLines', str(lines_to_skip_count))
    url_query.addQueryItem('trimFields', 'yes')
    if subset is not None:
        # NOTE: it loads all features and applies a filter in visualization
        url_query.addQueryItem('subset', subset)  # i.e. '"fieldname" != 0'
    url.setQuery(url_query)
    layer_uri = url.toString()
    layer = QgsVectorLayer(layer_uri, layer_name, "delimitedtext")
    if save_as_shp:
        dest_filename = dest_shp
        if not dest_filename:
            dest_filename, file_filter = QFileDialog.getSaveFileName(
                parent,
                'Save shapefile as...',
                os.path.expanduser("~"),
                'Shapefiles (*.shp)')
        if dest_filename:
            if dest_filename[-4:] != ".shp":
                dest_filename += ".shp"
        else:
            return
        writer_error, error_msg = save_layer_as_shapefile(layer, dest_filename)
        if writer_error:
            raise RuntimeError(
                'Could not save shapefile. %s: %s' % (writer_error,
                                                      error_msg))
        layer = QgsVectorLayer(dest_filename, layer_name, 'ogr')
    if layer.isValid():
        if add_to_legend:
            if add_on_top:
                root = QgsProject.instance().layerTreeRoot()
                QgsProject.instance().addMapLayer(layer, False)
                root.insertLayer(0, layer)
            else:
                QgsProject.instance().addMapLayer(layer, True)
            iface.setActiveLayer(layer)
            if zoom_to_layer:
                iface.zoomToActiveLayer()
    else:
        raise RuntimeError('Unable to load layer')
    return layer


def listdir_fullpath(path):
    return [os.path.join(path, filename) for filename in os.listdir(path)]


class InvalidHeaderError(Exception):
    pass


def get_params_from_comment_line(comment_line):
    """
    :param commented_line: a line starting with "# "
    :returns: an OrderedDict with parameter -> value

    >>> get_params_from_comment_line('# investigation_time=1000.0')
    OrderedDict([('investigation_time', '1000.0')])

    >>> get_params_from_comment_line("# p1=10, p2=20")
    OrderedDict([('p1', '10'), ('p2', '20')])

    >>> get_params_from_comment_line('h1, h2, h3')
    Traceback (most recent call last):
        ...
    svir.utilities.utils.InvalidHeaderError: Unable to extract parameters from line:
    h1, h2, h3
    because the line does not start with "# "

    >>> get_params_from_comment_line("# p1=10,p2=20")
    Traceback (most recent call last):
        ...
    svir.utilities.utils.InvalidHeaderError: Unable to extract parameters from line:
    # p1=10,p2=20
    """
    err_msg = 'Unable to extract parameters from line:\n%s' % comment_line
    if not comment_line.startswith('# '):
        raise InvalidHeaderError(
            err_msg + '\nbecause the line does not start with "# "')
    try:
        comment, rest = comment_line.split('# ', 1)
    except IndexError:
        raise InvalidHeaderError(err_msg)
    params_dict = collections.OrderedDict()
    param_defs = rest.split(', ')
    for param_def in param_defs:
        try:
            name, value = param_def.split('=')
        except ValueError:
            raise InvalidHeaderError(err_msg)
        else:
            params_dict[name] = value
    return params_dict


def warn_scipy_missing(message_bar):
    msg = ("This functionality requires scipy. Please install it"
           " and restart QGIS to enable it.")
    log_msg(msg, level='C', message_bar=message_bar)


def get_credentials(server):
    """
    Get from the QSettings the credentials to access the OpenQuake Engine
    or the OpenQuake Platform.
    If those settings are not found, use defaults instead.

    :param server: it can be either 'platform' or 'engine'

    :returns: tuple (hostname, username, password)

    """
    qs = QSettings()
    default_profiles = json.loads(
        qs.value(
            'irmt/%s_profiles',
            (DEFAULT_PLATFORM_PROFILES if server == 'platform'
                else DEFAULT_ENGINE_PROFILES)))
    default_profile = default_profiles[list(default_profiles.keys())[0]]
    hostname = qs.value('irmt/%s_hostname' % server,
                        default_profile['hostname'])
    username = qs.value('irmt/%s_username' % server,
                        default_profile['username'])
    password = qs.value('irmt/%s_password' % server,
                        default_profile['password'])
    return hostname, username, password


def get_checksum(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    checksum = zlib.adler32(data, 0) & 0xffffffff
    return checksum


def extract_npz(
        session, hostname, calc_id, output_type, message_bar, params=None):
    url = '%s/v1/calc/%s/extract/%s' % (hostname, calc_id, output_type)
    log_msg('GET: %s, with parameters: %s' % (url, params), level='I',
            print_to_stderr=True)
    resp = session.get(url, params=params)
    if not resp.ok:
        msg = "Unable to extract %s with parameters %s: %s" % (
            url, params, resp.reason)
        log_msg(msg, level='C', message_bar=message_bar, print_to_stderr=True)
        return
    resp_content = resp.content
    if not resp_content:
        msg = 'GET %s returned an empty content!' % url
        log_msg(msg, level='C', message_bar=message_bar, print_to_stderr=True)
        return
    return numpy.load(io.BytesIO(resp_content))


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def get_file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)


class ServerError(Exception):
    pass


class RedirectionError(Exception):
    pass


def check_is_lockdown(hostname, session):
    # try retrieving the engine version and see if the server
    # returns an HTTP 403 (Forbidden) error
    engine_version_url = "%s/v1/engine_version" % hostname
    with WaitCursorManager():
        # it can raise exceptions, caught by self.attempt_login
        # FIXME: enable the user to set verify=True
        resp = session.get(
            engine_version_url, timeout=10, verify=False,
            allow_redirects=False)
        if resp.status_code == 403:
            return True
        elif resp.status_code == 302:
            raise RedirectionError(
                "Error %s loading %s: please check the url" % (
                    resp.status_code, resp.url))
        if not resp.ok:
            raise ServerError(
                "Error %s loading %s: %s" % (
                    resp.status_code, resp.url, resp.reason))
    return False


def get_loss_types(session, hostname, calc_id, message_bar):
    composite_risk_model_attrs = extract_npz(
        session, hostname, calc_id, 'composite_risk_model.attrs',
        message_bar=message_bar)
    # casting loss_types to string, otherwise numpy complains when creating
    # array of zeros with data type as follows:
    # [('lon', F32), ('lat', F32), (loss_type, F32)])
    loss_types = [
        str(loss_type)
        for loss_type in composite_risk_model_attrs['loss_types']]
    return loss_types
