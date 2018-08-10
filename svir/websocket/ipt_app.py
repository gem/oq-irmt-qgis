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
from shutil import copyfile, rmtree
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QSettings, QDir, QFileInfo
from svir.websocket.web_app import WebApp


class IptApp(WebApp):

    def __init__(self, wss, message_bar):
        super(IptApp, self).__init__('ipt', wss, message_bar)
        ipt_allowed_meths = [
            'select_file', 'select_files', 'ls_ipt_dir', 'on_same_fs',
            'rm_file_from_ipt_dir', 'rename_file_in_ipt_dir',
            'read_file_in_ipt_dir', 'run_oq_engine_calc',
            'save_str_to_file', 'clear_ipt_dir',
            'select_and_copy_files_to_ipt_dir']
        self.allowed_meths.extend(ipt_allowed_meths)

    def on_same_fs(self):
        """
        Check if the engine server has access to the ipt_dir
        """
        checksum_file_path = None
        try:
            checksum_file_path, local_checksum = \
                self.wss.irmt_thread.get_ipt_checksum()
            on_same_fs = self.wss.irmt_thread.on_same_fs(
                checksum_file_path, local_checksum)
        except Exception as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': on_same_fs, 'reason': 'ok'}
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
            #     resp = {'ret': 1, 'content': None, 'reason': str(exc)}
            #     return resp

    def select_file(self):
        """
        Open a file browser to select a single file in the ipt_dir,
        and return the name of the selected files
        """
        try:
            ipt_dir = self.wss.irmt_thread.ipt_dir
            file_name, _ = QFileDialog.getOpenFileName(
                self.wss.irmt_thread.parent(), 'Select file', ipt_dir)
            basename = os.path.basename(file_name)
        except Exception as exc:
            resp = {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            resp = {'ret': 0, 'content': basename, 'reason': 'ok'}
        return resp

    def select_files(self):
        """
        Open a file browser to select multiple files in the ipt_dir,
        and return the list of names of selected files
        """
        try:
            ipt_dir = self.wss.irmt_thread.ipt_dir
            file_names, _ = QFileDialog.getOpenFileNames(
                self.wss.irmt_thread.parent(), 'Select files', ipt_dir)
            ls = [os.path.basename(file_name) for file_name in file_names]
        except Exception as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': ls, 'reason': 'ok'}

    def select_and_copy_files_to_ipt_dir(self):
        """
        Open a file browser pointing to the most recently browsed directory,
        where multiple files can be selected. The selected files will be
        copied inside the ipt_dir
        """
        try:
            default_dir = QSettings().value('irmt/ipt_browsed_dir',
                                            QDir.homePath())
            text = 'The selected files will be copied to the ipt directory'
            file_paths, _ = QFileDialog.getOpenFileNames(
                self.wss.irmt_thread.parent(), text, default_dir)
            if not file_paths:
                return {'ret': 1, 'reason': 'No file was selected'}
            selected_dir = QFileInfo(file_paths[0]).dir().path()
            QSettings().setValue('irmt/ipt_browsed_dir', selected_dir)
            ipt_dir = self.wss.irmt_thread.ipt_dir
            for file_path in file_paths:
                basename = os.path.basename(file_path)
                copyfile(file_path, os.path.join(ipt_dir, basename))
        except Exception as exc:
            return {'ret': 2, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    def save_str_to_file(self, content, file_name):
        """
        :param content: string to be saved in the file
        :param file_name: basename of the file to be saved into the ipt_dir
        """
        ipt_dir = self.wss.irmt_thread.ipt_dir
        try:
            basename = os.path.basename(file_name)
            with open(os.path.join(ipt_dir, basename), "w") as f:
                f.write(content)
        except Exception as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    def read_file_in_ipt_dir(self, file_name):
        """
        :param file_name: basename of the file to be read from the ipt_dir
        """
        ipt_dir = self.wss.irmt_thread.ipt_dir
        try:
            basename = os.path.basename(file_name)
            with open(os.path.join(ipt_dir, basename), "r") as f:
                content = f.read()
        except Exception as exc:
            return {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            return {'ret': 0, 'content': content, 'reason': 'ok'}

    def ls_ipt_dir(self):
        ipt_dir = self.wss.irmt_thread.ipt_dir
        try:
            ls = os.listdir(ipt_dir)
        except OSError as exc:
            resp = {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            resp = {'ret': 0, 'content': ls, 'reason': 'ok'}
        return resp

    def clear_ipt_dir(self):
        try:
            ipt_dir = self.wss.irmt_thread.ipt_dir
            rmtree(ipt_dir)
            ipt_dir = self.wss.irmt_thread.get_ipt_dir()
        except Exception as exc:
            resp = {'ret': 1, 'content': None, 'reason': str(exc)}
        else:
            resp = {'ret': 0, 'content': None, 'reason': 'ok'}
        return resp

    def rm_file_from_ipt_dir(self, file_name):
        """
        :param file_name: name of the file to be removed from the ipt_dir
        """
        ipt_dir = self.wss.irmt_thread.ipt_dir
        basename = os.path.basename(file_name)
        file_path = os.path.join(ipt_dir, basename)
        try:
            os.remove(file_path)
        except OSError as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    def rename_file_in_ipt_dir(self, old_name, new_name):
        """
        :param old_name: name of the file to be renamed
        :param new_name: new name to be assigned to the file
        """
        ipt_dir = self.wss.irmt_thread.ipt_dir
        old_basename = os.path.basename(old_name)
        new_basename = os.path.basename(new_name)
        old_path = os.path.join(ipt_dir, old_basename)
        new_path = os.path.join(ipt_dir, new_basename)
        try:
            os.rename(old_path, new_path)
        except OSError as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    def run_oq_engine_calc(self, file_names):
        """
        It opens the dialog showing the list of calculations on the engine
        server, and automatically runs an oq-engine calculation, given a list
        of input files to be collected from the ipt_dir
        :param file_names: list of names of the input files
        :returns: a dict with a return value and a possible reason of failure
        """
        file_names = file_names if file_names else None
        try:
            self.wss.irmt_thread.drive_oq_engine_server()
            drive_engine_dlg = \
                self.wss.irmt_thread.drive_oq_engine_server_dlg
            drive_engine_dlg.run_calc(file_names=file_names,
                                      directory=self.wss.irmt_thread.ipt_dir)
        except Exception as exc:
            return {'ret': 1, 'reason': str(exc)}
        else:
            return {'ret': 0, 'reason': 'ok'}

    # def delegate_download(self, action_url, method, headers, data,
    #                       js_cb_func, js_cb_object_id):
    #     """
    #     :param action_url: url to call on ipt api
    #     :param method: string like 'POST'
    #     :param headers: list of strings
    #     :param data: list of dictionaries {name (string) value(string)}
    #     :param delegate_download_js_cb: javascript callback
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
