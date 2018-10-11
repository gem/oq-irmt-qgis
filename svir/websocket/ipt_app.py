# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2018 by GEM Foundation
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

import os
import traceback
import shutil
import zipfile
from shutil import copy, rmtree
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QSettings, QDir, QFileInfo, QUrl, QStandardPaths
from qgis.PyQt.QtNetwork import (
    QNetworkRequest, QHttpMultiPart, QHttpPart, QNetworkAccessManager)
from qgis.PyQt.QtGui import QIcon
from svir.websocket.web_app import WebApp
from svir.utilities.utils import log_msg
from svir.utilities.shared import REQUEST_ATTRS


class IllegalPathException(Exception):
    pass


def dir_is_legal(app_dir, full_abs_path):
    return (full_abs_path.startswith(app_dir + '/') or
            full_abs_path == app_dir)


class IptApp(WebApp):

    def __init__(self, action, wss, message_bar):
        super().__init__('ipt', action, wss, message_bar)
        self.icon_standard = QIcon(":/plugins/irmt/ipt.svg")
        self.icon_connected = QIcon(":/plugins/irmt/ipt_connected.svg")
        ipt_allowed_meths = [
            'select_file', 'ls', 'on_same_fs',
            'delete_file', 'move_file',
            'read_file', 'run_oq_engine_calc',
            'save_str_to_file', 'clear_dir',
            'select_and_copy_file_to_dir',
            'create_dir', 'delete_dir',
            'delegate_download', 'build_zip', 'save_as']
        self.allowed_meths.extend(ipt_allowed_meths)

    def on_same_fs(self, api_uuid):
        """
        Check if the engine server has access to the app_dir
        """
        checksum_file_path = None
        try:
            checksum_file_path, local_checksum = \
                self.wss.irmt_thread.get_ipt_checksum()
            on_same_fs = self.wss.irmt_thread.on_same_fs(
                checksum_file_path, local_checksum)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('on_same_fs: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': on_same_fs, 'reason': 'ok'}
        finally:
            os.remove(checksum_file_path)
            # FIXME
            # try:
            #     os.remove(checksum_file_path)
            # except OSError as exc:
            #     # the file should have just been created and it should be
            #     # possible to remove it. Otherwise, we display a QGIS-side
            #     # error with the reason why it was impossible to delete the
            #     # file.
            #     resp = {
            #    '    success': False, 'content': None, 'reason': str(exc)}
            #     return resp

    def select_file(self, api_uuid, *args):
        """
        Open a file browser to select one or multiple files in the app_dir,
        and return the list of names of selected files
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir

        if len(args) > 0:
            path = args[0]
            loc_path = os.path.join(*path.split('/'))
            full_path = os.path.abspath(os.path.join(app_dir, loc_path))
            if not dir_is_legal(app_dir, full_path):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}

        is_multi = False
        if len(args) > 1:
            is_multi = args[1]

        title = 'Select files' if is_multi else 'Select file'
        if len(args) > 2:
            title = args[2]

        try:
            if is_multi:
                file_names, _ = QFileDialog.getOpenFileNames(
                    self.wss.irmt_thread.parent(), title, full_path)
            else:
                file_name, _ = QFileDialog.getOpenFileName(
                    self.wss.irmt_thread.parent(), title, full_path)
                file_names = [file_name]

            ls = [os.path.basename(file_name) for file_name in file_names]
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('select_file: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': ls, 'reason': 'ok'}

    def select_and_copy_file_to_dir(self, api_uuid, *args):
        """
        Open a file browser pointing to the most recently browsed directory, or
        from a given path, where multiple files can be selected. The selected
        files will be copied inside the app_dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        path = None
        full_path = app_dir

        if len(args) > 0:
            path = args[0]
            full_path = os.path.abspath(os.path.join(app_dir, path))
            if not dir_is_legal(app_dir, full_path):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}

        is_multi = False
        if len(args) > 1:
            is_multi = args[1]

        title = (
            ('The selected files will be copied to the %s directory' %
             self.app_name)
            if is_multi else 'The selected file will be copied to'
            ' the %s directory' % self.app_name)
        if len(args) > 2:
            title = args[2]

        try:
            default_dir = QSettings().value('irmt/ipt_browsed_dir',
                                            QDir.homePath())
            app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]

            if is_multi:
                file_names, _ = QFileDialog.getOpenFileNames(
                    self.wss.irmt_thread.parent(), title, default_dir)
            else:
                file_name, _ = QFileDialog.getOpenFileName(
                    self.wss.irmt_thread.parent(), title, default_dir)
                file_names = [file_name] if file_name else []
            if not file_names:
                return {'success': False,
                        'content': None,
                        'reason': 'No file was selected'}
            selected_dir = QFileInfo(file_names[0]).dir().path()
            QSettings().setValue('irmt/ipt_browsed_dir', selected_dir)
            basenames = []
            for file_name in file_names:
                basename = os.path.basename(file_name)
                basenames.append(basename)
                copy(file_name, full_path)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('select_and_copy_file_to_dir: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': basenames, 'reason': msg}
        else:
            return {'success': True, 'content': basenames, 'reason': 'ok'}

    def save_str_to_file(self, api_uuid, content, file_path):
        """
        :param content: string to be saved in the file
        :param file_path: path of the file to be saved into the app_dir
        """
        rel_path = os.path.dirname(file_path)
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = os.path.abspath(os.path.join(app_dir, rel_path))
        if not dir_is_legal(app_dir, full_path):
            msg = 'Unable to access the directory %s' % rel_path
            return {'success': False, 'content': None, 'reason': msg}
        try:
            basename = os.path.basename(file_path)
            with open(os.path.join(full_path, basename), "w") as f:
                f.write(content)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('save_str_to_file: an error occurred. '
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def read_file(self, api_uuid, file_path):
        """
        :param file_path: basename of the file to be read from the app_dir
        """
        rel_path = os.path.dirname(file_path)
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = os.path.abspath(os.path.join(app_dir, rel_path))
        if not dir_is_legal(app_dir, full_path):
            msg = 'Unable to access the directory %s' % rel_path
            return {'success': False, 'content': None, 'reason': msg}
        try:
            basename = os.path.basename(file_path)
            with open(os.path.join(full_path, basename), "r") as f:
                content = f.read()
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('read_file: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': content, 'reason': 'ok'}

    def ls(self, api_uuid, *args):
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir

        if len(args) > 0:
            path = args[0]
            full_path = os.path.abspath(os.path.join(app_dir, path))
            if not dir_is_legal(app_dir, full_path):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}

        try:
            ls = os.listdir(full_path)
            for i, f in enumerate(ls):
                if os.path.isdir(os.path.join(full_path, f)):
                    ls[i] = ls[i] + '/'
        except OSError as exc:
            resp = {'success': False, 'content': None, 'reason': str(exc)}
        else:
            resp = {'success': True, 'content': ls, 'reason': 'ok'}
        return resp

    def clear_dir(self, api_uuid, *args):
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.abspath(os.path.join(app_dir, path))
            if not dir_is_legal(app_dir, full_path):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        try:
            rmtree(full_path)
            # recreates any missing app_dir
            self.wss.irmt_thread.get_webapp_dirs()
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('clean_dir: an error occurred.'
                   ' Please see the IRMT log for details.')
            resp = {'success': False, 'content': None, 'reason': msg}
        else:
            resp = {'success': True, 'content': None, 'reason': 'ok'}
        return resp

    def delete_file(self, api_uuid, file_path):
        """
        :param file_path: name of the file to be removed from the app_dir
        """
        loc_file_path = os.path.join(*file_path.split('/'))
        rel_path = os.path.dirname(loc_file_path)
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = os.path.abspath(os.path.join(app_dir, rel_path))
        if not dir_is_legal(app_dir, full_path):
            msg = 'Unable to access the directory %s' % rel_path
            return {'success': False, 'content': None, 'reason': msg}
        basename = os.path.basename(loc_file_path)
        file_path = os.path.join(full_path, basename)
        try:
            os.remove(file_path)
        except OSError as exc:
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def move_file(self, api_uuid, old_path, new_path):
        """
        :param old_path: path of the file to be renamed
        :param new_path: new path to be assigned to the file
        """
        loc_old_path = os.path.join(*old_path.split('/'))
        loc_new_path = os.path.join(*new_path.split('/'))
        rel_old_path = os.path.dirname(loc_old_path)
        rel_new_path = os.path.dirname(loc_new_path)
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_old_path = os.path.abspath(os.path.join(app_dir, rel_old_path))
        if not dir_is_legal(app_dir, full_old_path):
            msg = 'Unable to access the directory %s' % old_path
            return {'success': False, 'content': None, 'reason': msg}
        full_new_path = os.path.abspath(os.path.join(app_dir, rel_new_path))
        if not dir_is_legal(app_dir, full_new_path):
            msg = 'Unable to access the directory %s' % new_path
            return {'success': False, 'content': None, 'reason': msg}
        old_basename = os.path.basename(loc_old_path)
        new_basename = os.path.basename(loc_new_path)
        old_filepath = os.path.join(full_old_path, old_basename)
        new_filepath = os.path.join(full_new_path, new_basename)
        try:
            os.rename(old_filepath, new_filepath)
        except OSError as exc:
            # FIXME: don't use exc value as API result
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def create_dir(self, api_uuid, dir_name):
        """
        :param dirname: name of the directory to be created under the ipt dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        loc_dir_name = os.path.join(*dir_name.split('/'))
        try:
            full_path = os.path.abspath(os.path.join(app_dir, loc_dir_name))
            if not dir_is_legal(app_dir, full_path):
                msg = 'Unable to create the directory %s' % dir_name
                return {'success': False, 'content': None, 'reason': msg}
            os.makedirs(full_path)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('create_dir: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def delete_dir(self, api_uuid, dir_name):
        """
        :param dirname: name of the directory to be deleted from the ipt dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        try:
            loc_dir_name = os.path.join(*dir_name.split('/'))
            full_path = os.path.join(app_dir, loc_dir_name)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to delete the directory %s' % dir_name
                return {'success': False, 'content': None, 'reason': msg}
            shutil.rmtree(full_path)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('delete_dir: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def run_oq_engine_calc(self, api_uuid, rel_paths=None):
        """
        :param rel_paths:
            list of paths of the input files to be used to run a oq-engine
            calculation (paths are relative to the app_dir)
        :returns:
            a dict with a return value and a possible reason of failure
        """
        abs_paths = None
        if rel_paths is not None:
            abs_paths = []
            app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
            for rel_path in rel_paths:
                loc_rel_path = os.path.join(*rel_path.split('/'))
                abs_path = os.path.abspath(os.path.join(app_dir, loc_rel_path))
                if (not dir_is_legal(app_dir, abs_path) or
                        not os.path.isfile(abs_path)):
                    msg = 'Unable to access the file %s' % rel_path
                    return {'success': False, 'content': None, 'reason': msg}
                abs_paths.append(abs_path)
        try:
            self.wss.irmt_thread.drive_oq_engine_server()
            drive_engine_dlg = \
                self.wss.irmt_thread.drive_oq_engine_server_dlg
            drive_engine_dlg.run_calc(file_names=abs_paths)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('run_oq_engine_calc: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def build_zip(self, api_uuid, content, zip_name):
        """
        :param content:
            [[<"file"|"string">, <dest-name>, <src-file-path|src-file-content>]
             , [...]]
        :param zip_name: <file-name>
        :returns:
            {'success': True, 'content': <dest-file-fullname>, 'reason': 'ok'}
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]

        abs_temp_path = os.path.abspath(os.path.join(app_dir, 'Temp'))
        if not os.path.exists(abs_temp_path):
            os.makedirs(abs_temp_path)

        loc_zip_name = os.path.join(*zip_name.split('/'))
        abs_zip_name = os.path.abspath(os.path.join(app_dir, 'Temp',
                                                    loc_zip_name))
        abs_zip_dir = os.path.dirname(abs_zip_name)
        msg = "Unknown error"
        if not dir_is_legal(app_dir, abs_zip_dir):
            msg = 'Unable to write %s' % zip_name
            return {'success': False, 'content': None, 'reason': msg}

        try:
            with zipfile.ZipFile(abs_zip_name, 'w') as zipped_file:
                for item in content:
                    item_type, dest_name, src_file_smth = item

                    norm_dest_name = os.path.normpath(dest_name)
                    if norm_dest_name.startswith(os.pardir):
                        msg = 'Illegal path %s' % dest_name
                        raise IllegalPathException(msg)

                    if item_type == 'file':
                        src_file_path = src_file_smth
                        abs_src_file_path = os.path.abspath(
                            os.path.join(app_dir, src_file_path))
                        abs_src_file_dir = os.path.dirname(abs_src_file_path)
                        if not dir_is_legal(app_dir, abs_src_file_dir):
                            msg = 'Unable to write %s' % src_file_path
                            raise IllegalPathException(msg)
                        zipped_file.write(abs_src_file_path,
                                          arcname=norm_dest_name)

                    elif item_type == 'string':
                        src_file_content = src_file_smth
                        zipped_file.writestr(norm_dest_name, src_file_content)

                    else:
                        msg = ('Content type must be "string" or "file".'
                               ' "%s" is invalid.' % item_type)
                        raise TypeError(msg)
        except (IllegalPathException, TypeError):
            if os.path.exists(abs_zip_name):
                os.remove(abs_zip_name)
            return {'success': False, 'content': None, 'reason': str(msg)}
        except Exception:
            if os.path.exists(abs_zip_name):
                os.remove(abs_zip_name)
            log_msg(traceback.format_exc(), level='C')
            msg = ('build_zip: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True,
                    'content': 'Temp' + '/' + '/'.join(
                        loc_zip_name.split(os.path.sep)),
                    'reason': 'ok'}

    def save_as(self, api_uuid, file_src, suggested_name):
        """
        Opens a file browser to save the file-src, setting as default name
        the suggested-name. By default, the directory to save the file into
        is the system Downloads directory. In case the Downloads directory is
        not found, the user home directory is used instead, as fallback.
        :param file_src: path of the source file to be copied
        :param suggested_name: suggested name for the file to be created
        :returns:
            {'success': True, 'content': None, 'reason': 'ok'}
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        loc_file_src = os.path.join(*file_src.split('/'))
        rel_dir_src = os.path.dirname(loc_file_src)
        full_dir_src = os.path.abspath(os.path.join(app_dir, rel_dir_src))
        if not dir_is_legal(app_dir, full_dir_src):
            msg = 'Unable to access the directory %s' % rel_dir_src
            return {'success': False, 'content': None, 'reason': msg}
        full_path_src = os.path.join(full_dir_src, os.path.basename(file_src))
        if not os.path.isfile(full_path_src):
            msg = '%s is not a file' % file_src
            return {'success': False, 'content': None, 'reason': msg}
        try:
            dest_dir = QStandardPaths.standardLocations(
                QStandardPaths.DownloadLocation)[0]
        except Exception:
            dest_dir = os.path.expanduser("~")
        default_dest_name = os.path.join(
            dest_dir, os.path.basename(suggested_name))
        dest_file, _ = QFileDialog.getSaveFileName(
            self.wss.irmt_thread.parent(), 'Save as...', default_dest_name)
        if not dest_file:
            msg = 'Canceled'
            return {'success': False, 'content': None, 'reason': msg}
        try:
            copy(full_path_src, dest_file)
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = ('save_as: an error occurred.'
                   ' Please see the IRMT log for details.')
            return {'success': False, 'content': None, 'reason': msg}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    # def delegate_download_old(self, action_url, method, headers, data,
    #                           js_cb_func, js_cb_object_id, api_uuid=None):
    #     """
    #     :param action_url: url to call on ipt api
    #     :param method: string like 'POST'
    #     :param headers: list of strings
    #     :param data: list of dictionaries {name (string) value(string)}
    #     :param js_cb_func: javascript callback
    #     :param js_cb_object_id: id of the javascript object to be called back
    #     """
    #     # TODO: Accept also methods other than POST
    #     if method != 'POST':
    #         self.call_js_cb(js_cb_func, js_cb_object_id, None, 1,
    #                         'Method %s not allowed' % method)
    #         return False
    #     if ':' in action_url:
    #         qurl = QUrl(action_url)
    #     elif action_url.startswith('/'):
    #         qurl = QUrl("%s%s" % (self.wss.irmt_thread.host, action_url))
    #     else:
    #         url = "%s/%s" % (
    #             '/'.join([str(x) for x in self.wss.irmt_thread.web_view.url(
    #                      ).toEncoded().split('/')[:-1]]), action_url)
    #         qurl = QUrl(url)
    #     manager = self.wss.irmt_thread.web_view.page().networkAccessManager()
    #     request = QNetworkRequest(qurl)
    #     request.setAttribute(REQUEST_ATTRS['instance_finished_cb'],
    #                          self.manager_finished_cb)
    #     request.setAttribute(REQUEST_ATTRS['js_cb_object_id'],
    #                          js_cb_object_id)
    #     request.setAttribute(REQUEST_ATTRS['js_cb_func'],
    #                          js_cb_func)
    #     for header in headers:
    #         request.setRawHeader(header['name'], header['value'])
    #     multipart = QHttpMultiPart(QHttpMultiPart.FormDataType)
    #     for d in data:
    #         part = QHttpPart()
    #         part.setHeader(QNetworkRequest.ContentDispositionHeader,
    #                        "form-data; name=\"%s\"" % d['name'])
    #         part.setBody(d['value'])
    #         multipart.append(part)
    #     reply = manager.post(request, multipart)
    #     # NOTE: needed to avoid segfault!
    #     multipart.setParent(reply)  # delete the multiPart with the reply
    #     return True

    def delegate_download(
            self, api_uuid, action_url, method, headers, data):
        """
        :param api_uuid: id of the request coming from the websocket, to be
            used to keep track of pending requests
        :param action_url: url to call on ipt api
        :param method: string like 'POST'
        :param headers: list of strings
        :param data: list of dictionaries {name (string) value(string)}
        """

        try:
            # TODO: Accept also methods other than POST
            if method != 'POST':
                # self.call_js_cb(js_cb_func, None, 1,
                #                 'Method %s not allowed' % method)
                return False
            # if ':' in action_url:
            #     qurl = QUrl(action_url)
            # elif action_url.startswith('/'):
            #     qurl = QUrl("%s%s" % (self.wss.irmt_thread.host, action_url))
            # else:
            #     # FIXME: build the full url, if needed
            #     url = "%s/%s" % (
            #         '/'.join([str(x) for x in self.wss.irmt_thread.web_view.url(
            #                  ).toEncoded().split('/')[:-1]]), action_url)
            #     qurl = QUrl(url)
            qurl = QUrl(action_url)
            # manager = self.wss.irmt_thread.web_view.page().networkAccessManager()
            gem_header_name = b"Gem--Qgis-Oq-Irmt--Ipt"
            gem_header_value = b"0.1.0"
            manager = GemQNetworkAccessManager(
                gem_header_name, gem_header_value, parent=self)
            # manager = QNetworkAccessManager()
            manager.finished.connect(self.manager_finished_cb)
            request = QNetworkRequest(qurl)
            request.setAttribute(REQUEST_ATTRS['instance_finished_cb'],
                                 self.manager_finished_cb)
            # request.setAttribute(REQUEST_ATTRS['js_cb_object_id'],
            #                      js_cb_object_id)
            request.setAttribute(REQUEST_ATTRS['uuid'], api_uuid)
            for header in headers:
                name = header['name'].encode('utf-8')
                value = header['value'].encode('utf-8')
                request.setRawHeader(name, value)
            multipart = QHttpMultiPart(QHttpMultiPart.FormDataType)
            for d in data:
                part = QHttpPart()
                part.setHeader(QNetworkRequest.ContentDispositionHeader,
                               "form-data; name=\"%s\"" % d['name'])
                part.setBody(d['value'].encode('utf-8'))
                multipart.append(part)
            reply = manager.post(request, multipart)
            # reply = manager.post(request)
            # # NOTE: needed to avoid segfault!
            multipart.setParent(reply)  # delete the multiPart with the reply
            result = {'success': True, 'content': None, 'reason': 'started'}
        except Exception:
            log_msg(traceback.format_exc(), level='C')
            msg = 'An error occurred. Please see the IRMT log for details.'
            result = {'success': False, 'content': None, 'reason': msg}
        return (result, False)
# // hyb_msg = {'app':<app_name> , 'msg':<api_msg>}
# // api_msg = {'msg'|'reply': <app_msg>, 'uuid':<uuid> }
# // app_msg = {<('command', 'args':[]) |
#                ('result': <cmd_msg>, complete: <True|False>)>}
# // cmd_msg = <obj|bool>
    def manager_finished_cb(self, reply):
        try:
            temp_absfile = None
            uuid = reply.request().attribute(
                REQUEST_ATTRS['uuid'], None)
            # js_cb_object_id = reply.request().attribute(
            #     REQUEST_ATTRS['js_cb_object_id'], None)
            # js_cb_func = reply.request().attribute(
            #     REQUEST_ATTRS['js_cb_func'], None)
            # if js_cb_object_id is None or js_cb_object_id is None:
            #     self.call_js_cb(js_cb_func, js_cb_object_id, file_name, 2,
            #                     'Unable to extract attributes from request')
            #     return
            content_disposition = reply.rawHeader(
                'Content-Disposition'.encode('utf-8'))
            # expected format: 'attachment; filename="exposure_model.xml"'
            # sanity check
            if 'filename'.encode('utf-8') not in content_disposition:
                # resp = {
                #    'success': True, 'content': file_name, 'reason': 'ok'}
                # self.call_js_cb(js_cb_func, file_name, 4,
                #                 'File name not found')
                return
            file_name = str(content_disposition.split('"')[1], 'utf-8')
            file_content = str(reply.readAll(), 'utf-8')
            app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
            loc_temp_name = os.path.join('Downloads', uuid + '.tmp')
            temp_absfile = os.path.join(app_dir, loc_temp_name)
            if not os.path.exists(os.path.dirname(temp_absfile)):
                os.makedirs(os.path.dirname(temp_absfile))

            with open(temp_absfile, "w") as f:
                f.write(file_content)
            # self.call_js_cb(js_cb_func, file_name, 0)
            result = {'success': True, 'realpath':
                      '/'.join(loc_temp_name.split(os.path.sep)),
                      'content': file_name, 'reason': 'ok'}
            app_msg = {'complete': True, 'result': result}
        except Exception:
            if temp_absfile is not None and os.path.exists(temp_absfile):
                os.remove(temp_absfile)
            log_msg(traceback.format_exc(), level='C')
            msg = 'An error occurred. Please see the IRMT log for details.'
            result = {'success': False, 'realpath': None,
                      'content': None, 'reason': msg}
            app_msg = {'result': result, 'complete': True}
        api_msg = {'reply': app_msg, 'uuid': uuid}
        self.send(api_msg)


class GemQNetworkAccessManager(QNetworkAccessManager):
    """
    A modified version of QNetworkAccessManager, that adds a header to each
    request and that uses a persistent cookie jar.
    """

    def __init__(self, gem_header_name, gem_header_value, parent=None):
        super().__init__(parent)
        self.gem_header_name = gem_header_name
        self.gem_header_value = gem_header_value
        # self.setCookieJar(PersistentCookieJar())

    def createRequest(self, op, req, outgoingData):
        req = self.add_header_to_request(req)
        return super(GemQNetworkAccessManager, self).createRequest(
            op, req, outgoingData)

    def add_header_to_request(self, request):
        request.setRawHeader(self.gem_header_name, self.gem_header_value)
        return request
