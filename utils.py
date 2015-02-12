# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013-2015 by GEM Foundation
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
import collections
import json
import os
from time import time
from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QApplication, QProgressBar, QToolButton, QFileDialog, \
    QMessageBox
from qgis.core import QgsMapLayerRegistry
from settings_dialog import SettingsDialog
from qgis.gui import QgsMessageBar
from shared import DEBUG


def tr(message):
    return QApplication.translate('Svir', message)


def count_heading_commented_lines(fname):
    # count top lines in the file starting with '#'
    with open(fname) as f:
        lines_to_skip_count = 0
        for line in f:
            li = line.strip()
            if li.startswith('#'):
                lines_to_skip_count += 1
            else:
                break
    if DEBUG:
        print "The file contains %s heading lines starting with #" % (
            lines_to_skip_count)
    return lines_to_skip_count


def get_credentials(iface):
    qs = QSettings()
    hostname = qs.value('svir/platform_hostname', '')
    username = qs.value('svir/platform_username', '')
    password = qs.value('svir/platform_password', '')
    if not (hostname and username and password):
        SettingsDialog(iface).exec_()
        hostname = qs.value('svir/platform_hostname', '')
        username = qs.value('svir/platform_username', '')
        password = qs.value('svir/platform_password', '')
    return hostname, username, password


def clear_progress_message_bar(msg_bar, msg_bar_item=None):
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
    msg_bar.pushWidget(progress_message_bar, msg_bar.INFO)
    return progress_message_bar, progress


def assign_default_weights(svi_themes):
    # count themes and indicators and assign default weights
    # using 2 decimal points (%.2f)
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
    for l in QgsMapLayerRegistry.instance().mapLayers().values():
        layer_type_allowed = bool(layer_types is None
                                  or l.type() in layer_types)
        layer_id_allowed = bool(skip_layer_ids is None
                                or l.id() not in skip_layer_ids)
        if layer_type_allowed and layer_id_allowed:
            combo.addItem(l.name())


def reload_attrib_cbx(combo, layer, *valid_field_types):
    """
    Load attributes of a layer into a combobox. Can filter by field data type.
    the additional filter can be NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES, ...

    :param combo: The combobox to be repopulated
    :type combo: QComboBox
    :param layer: The QgsVectorLayer from where the fields are read
    :type layer: QgsVectorLayer
    :param *valid_field_types: multiple tuples containing types
    :type *valid_field_types: tuple, tuple, ...
    """
    field_types = set()
    for field_type in valid_field_types:
        field_types.update(field_type)

    # reset combo box
    combo.clear()
    # populate combo box with field names taken by layers
    dp = layer.dataProvider()
    fields = list(dp.fields())
    for field in fields:
        # add if in field_types
        if not field_types or field.typeName() in field_types:
            combo.addItem(field.name())


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
        layer.setSelectedFeatures(list(new_feature_ids))
    else:
        layer.setSelectedFeatures(list(old_feature_ids))


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
    session_resp = session.post(login_url,
                                data={
                                    "username": username,
                                    "password": password
                                })
    if session_resp.status_code != 200:  # 200 means successful:OK
        error_message = ('Unable to get session for login: %s' %
                         session_resp.content)
        raise SvNetworkError(error_message)


def upload_shp(host, session, file_stem, username):
    files = {'layer_title': file_stem,
             'base_file': ('file.shp', open('%s.shp' % file_stem, 'rb')),
             'dbf_file': ('file.dbf', open('%s.dbf' % file_stem, 'rb')),
             'shx_file': ('file.shx', open('%s.shx' % file_stem, 'rb')),
             'prj_file': ('file.prj', open('%s.prj' % file_stem, 'rb')),
             'xml_file': ('file.xml', open('%s.xml' % file_stem, 'r')),
             }
    permissions = ('{"authenticated":"_none",'
                   '"anonymous":"_none",'
                   '"users":[["%s","layer_readwrite"],["%s","layer_admin"]]'
                   '}') % (username, username)
    payload = {'charset': ['UTF-8'],
               'permissions': [permissions]}

    r = session.post(host + '/layers/upload', data=payload, files=files)
    response = json.loads(r.text)
    try:
        return host + response['url'], True
    except KeyError:
        if 'errors' in response:
            return response['errors'], False
        else:
            return "The server did not provide error messages", False


def ask_for_download_destination(parent, text='Download destination'):
    return QFileDialog.getExistingDirectory(
        parent,
        text,
        os.path.expanduser("~"))


def files_exist_in_destination(destination, file_names,):
        file_exists_in_destination = []
        for file_name in file_names:
            file_path = os.path.join(destination, file_name)
            if os.path.isfile(file_path):
                file_exists_in_destination.append(file_path)
        return file_exists_in_destination


def confirm_overwrite(parent, files):
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
    def __init__(self, msg=None, iface=None):
        self.msg = msg
        self.iface = iface
        self.has_message = msg and iface
        self.message = None

    def __enter__(self):
        if self.has_message:
            self.message = self.iface.messageBar().createMessage(
                tr('Info'), tr(self.msg))
            self.message = self.iface.messageBar().pushWidget(
                self.message, level=QgsMessageBar.INFO)
            QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def __exit__(self, type, value, traceback):
        QApplication.restoreOverrideCursor()
        if self.has_message:
            self.iface.messageBar().popWidget(self.message)


class SvNetworkError(Exception):
    pass


class ReadMetadataError(Exception):
    """When a metadata xml is not correctly formatted can't be read"""
    suggestion = (
        'Check that the file is correct')
