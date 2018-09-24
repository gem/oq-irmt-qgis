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
from shutil import copyfile, rmtree
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QSettings, QDir, QFileInfo, QUrl
from qgis.PyQt.QtNetwork import (
    QNetworkRequest, QHttpMultiPart, QHttpPart, QNetworkAccessManager)
from qgis.PyQt.QtGui import QIcon
from svir.websocket.web_app import WebApp
from svir.utilities.utils import log_msg
from svir.utilities.shared import REQUEST_ATTRS


class IptApp(WebApp):

    def __init__(self, action, wss, message_bar):
        super().__init__('ipt', action, wss, message_bar)
        self.icon_standard = QIcon(":/plugins/irmt/ipt.svg")
        self.icon_connected = QIcon(":/plugins/irmt/ipt_connected.svg")
        ipt_allowed_meths = [
            'select_file', 'ls', 'on_same_fs',
            'delete_file', 'rename_file',
            'read_file', 'run_oq_engine_calc',
            'save_str_to_file', 'clear_dir',
            'select_and_copy_file_to_dir',
            'create_dir', 'delete_dir',
            'delegate_download']
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
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
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
        is_multi = False
        if len(args) > 0:
            is_multi = args[0]

        title = 'Select files' if is_multi else 'Select file'
        if len(args) > 1:
            title = args[1]

        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir

        if len(args) > 2:
            path = args[2]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}

        try:
            if is_multi:
                file_names, _ = QFileDialog.getOpenFileNames(
                    self.wss.irmt_thread.parent(), title, full_path)
            else:
                file_name, _ = QFileDialog.getOpenFileName(
                    self.wss.irmt_thread.parent(), title, full_path)
                file_names = [file_name]

            ls = [os.path.basename(file_name) for file_name in file_names]
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': ls, 'reason': 'ok'}

    def select_and_copy_file_to_dir(self, api_uuid, *args):
        """
        Open a file browser pointing to the most recently browsed directory, or
        from a given path, where multiple files can be selected. The selected
        files will be copied inside the app_dir
        """
        is_multi = False
        if len(args) > 0:
            is_multi = args[0]

        title = (
            'The selected files will be copied to the ipt directory'
            if is_multi else 'The selected file will be copied to'
            ' the ipt directory')
        if len(args) > 1:
            title = args[1]

        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        path = None
        full_path = app_dir

        if len(args) > 2:
            path = args[2]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}

        try:
            if path:
                default_dir = full_path
            else:
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
                copyfile(file_name, os.path.join(app_dir, basename))
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': basenames, 'reason': str(exc)}
        else:
            return {'success': True, 'content': basenames, 'reason': 'ok'}

    def save_str_to_file(self, api_uuid, content, file_name, *args):
        """
        :param content: string to be saved in the file
        :param file_name: basename of the file to be saved into the app_dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        try:
            basename = os.path.basename(file_name)
            with open(os.path.join(full_path, basename), "w") as f:
                f.write(content)
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def read_file(self, api_uuid, file_name, *args):
        """
        :param file_name: basename of the file to be read from the app_dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        try:
            basename = os.path.basename(file_name)
            with open(os.path.join(full_path, basename), "r") as f:
                content = f.read()
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': content, 'reason': 'ok'}

    def ls(self, api_uuid, *args):
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
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
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        try:
            rmtree(full_path)
            # recreates any missing app_dir
            self.wss.irmt_thread.get_webapp_dirs()
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            resp = {'success': False, 'content': None, 'reason': str(exc)}
        else:
            resp = {'success': True, 'content': None, 'reason': 'ok'}
        return resp

    def delete_file(self, api_uuid, file_name, *args):
        """
        :param file_name: name of the file to be removed from the app_dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        basename = os.path.basename(file_name)
        file_path = os.path.join(full_path, basename)
        try:
            os.remove(file_path)
        except OSError as exc:
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def rename_file(self, api_uuid, old_name, new_name, *args):
        """
        :param old_name: name of the file to be renamed
        :param new_name: new name to be assigned to the file
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        full_path = app_dir
        if len(args) > 0:
            path = args[0]
            full_path = os.path.join(full_path, path)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to access the directory %s' % path
                return {'success': False, 'content': None, 'reason': msg}
        old_basename = os.path.basename(old_name)
        new_basename = os.path.basename(new_name)
        old_path = os.path.join(full_path, old_basename)
        new_path = os.path.join(full_path, new_basename)
        try:
            os.rename(old_path, new_path)
        except OSError as exc:
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def create_dir(self, api_uuid, dir_name):
        """
        :param dirname: name of the directory to be created under the ipt dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        try:
            full_path = os.path.join(app_dir, dir_name)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to create the directory %s' % dir_name
                return {'success': False, 'content': None, 'reason': msg}
            os.makedirs(full_path)
            print(os.listdir(app_dir))
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def delete_dir(self, api_uuid, dir_name):
        """
        :param dirname: name of the directory to be deleted from the ipt dir
        """
        app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
        try:
            full_path = os.path.join(app_dir, dir_name)
            if not os.path.abspath(full_path).startswith(app_dir + '/'):
                msg = 'Unable to delete the directory %s' % dir_name
                return {'success': False, 'content': None, 'reason': msg}
            shutil.rmtree(full_path)
            print(os.listdir(app_dir))
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
        else:
            return {'success': True, 'content': None, 'reason': 'ok'}

    def run_oq_engine_calc(self, api_uuid, file_names):
        """
        It opens the dialog showing the list of calculations on the engine
        server, and automatically runs an oq-engine calculation, given a list
        of input files to be collected from the app_dir
        :param file_names: list of names of the input files
        :returns: a dict with a return value and a possible reason of failure
        """
        file_names = file_names if file_names else None
        try:
            self.wss.irmt_thread.drive_oq_engine_server()
            drive_engine_dlg = \
                self.wss.irmt_thread.drive_oq_engine_server_dlg
            drive_engine_dlg.run_calc(file_names=file_names,
                                      directory=self.wss.irmt_thread.webapp_dirs[self.app_name])
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            return {'success': False, 'content': None, 'reason': str(exc)}
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
            print('qurl: %s' % qurl)
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
                print(name)
                print(value)
            print(headers)
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
            print('Right after POST')
            print(reply)
            result = {'success': True, 'content': None, 'reason': 'started'}
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            result = {'success': False, 'content': None, 'reason': str(exc)}
        return {'result': result, 'complete': False}
# // hyb_msg = {'app':<app_name> , 'msg':<api_msg>}
# // api_msg = {'msg'|'reply': <app_msg>, 'uuid':<uuid> }
# // app_msg = {<('command', 'args':[])|('result': <obj|bool>, complete: <True|False>)>}

    def manager_finished_cb(self, reply):
        try:
            print('*' * 20)
            print('manager_finished_cb')
            print(reply)
            file_name = None
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
            print(content_disposition)
            if 'filename'.encode('utf-8') not in content_disposition:
                # resp = {
                #    'success': True, 'content': file_name, 'reason': 'ok'}
                # self.call_js_cb(js_cb_func, file_name, 4,
                #                 'File name not found')
                return
            file_name = str(content_disposition.split('"')[1], 'utf-8')
            print(file_name)
            file_content = str(reply.readAll(), 'utf-8')
            print(file_content)
            app_dir = self.wss.irmt_thread.webapp_dirs[self.app_name]
            with open(os.path.join(app_dir, file_name), "w") as f:
                f.write(file_content)
            # self.call_js_cb(js_cb_func, file_name, 0)
            result = {'success': True, 'content': file_name, 'reason': 'ok'}
            app_msg = {'result': result, 'complete': True}
        except Exception as exc:
            log_msg(traceback.format_exc(), level='C')
            result = {'success': False, 'content': None, 'reason': str(exc)}
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
