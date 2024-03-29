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
from time import sleep
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QThread, pyqtSignal, pyqtSlot
from svir.utilities.utils import log_msg


class TaskCanceled(Exception):
    pass


class DownloadFailed(Exception):
    pass


class DownloadOqOutputTask(QgsTask):

    is_canceled_sig = pyqtSignal()

    def __init__(
            self, description, flags, output_id, outtype,
            output_type, dest_folder, session, hostname, on_success, on_error,
            del_task, task_id, current_calc_id=None):
        super().__init__(description, flags)
        self.output_id = output_id
        self.outtype = outtype
        self.output_type = output_type
        self.dest_folder = dest_folder
        self.session = session
        self.hostname = hostname
        self.on_success = on_success
        self.on_error = on_error
        self.del_task = del_task
        self.task_id = task_id
        self.current_calc_id = current_calc_id
        self.exception = None

        if self.current_calc_id:
            self.download_url = "%s/v1/calc/%s/datastore" % (
                self.hostname, self.current_calc_id)
        else:
            self.download_url = (
                "%s/v1/calc/result/%s?export_type=%s&dload=true" % (
                    self.hostname, self.output_id, self.outtype))
        log_msg('GET: %s' % self.download_url, level='I', print_to_stderr=True)

    def run(self):
        try:
            self.download_output(self.session, self.download_url)
        except Exception as exc:
            self.exception = exc
            return False
        else:
            return True

    def finished(self, success):
        if success:
            self.on_success(
                output_id=self.output_id,
                output_type=self.output_type,
                filepath=self.filepath)
        else:
            self.on_error(self.exception)
        self.del_task(self.task_id)

    def download_output(self, session, download_url):
        self.setProgress(-1)
        if self.isCanceled():
            self.is_canceled_sig.emit()
            raise TaskCanceled
        self.download_thread = DownloadThread(
            session, download_url, self.dest_folder)
        self.download_thread.progress_sig[float].connect(self.set_progress)
        self.download_thread.filepath_sig[str].connect(self.set_filepath)
        self.download_thread.exception_sig[Exception].connect(
            self.set_exception)
        self.is_canceled_sig.connect(self.download_thread.set_canceled)
        self.download_thread.start()
        while True:
            sleep(0.1)
            if self.exception is not None:
                raise self.exception
            if self.download_thread.isFinished():
                return True
            if self.isCanceled():
                # NOTE: deleteLater would be a cleaner way, but it does not
                # actually kill the get, so the machine remains busy until a
                # response is produced
                # self.download_thread.deleteLater()
                del self.download_thread
                raise TaskCanceled

    @pyqtSlot(float)
    def set_progress(self, progress):
        self.setProgress(progress)

    @pyqtSlot(str)
    def set_filepath(self, filepath):
        self.filepath = filepath

    @pyqtSlot(Exception)
    def set_exception(self, exception):
        self.exception = exception


class DownloadThread(QThread):

    progress_sig = pyqtSignal(float)
    filepath_sig = pyqtSignal(str)
    exception_sig = pyqtSignal(Exception)

    def __init__(self, session, url, dest_folder):
        self.session = session
        self.url = url
        self.dest_folder = dest_folder
        self.is_canceled = False
        super().__init__()

    def run(self):
        # FIXME: enable the user to set verify=True
        resp = self.session.get(self.url, verify=False, stream=True)
        if not resp.ok:
            err_msg = (
                'Unable to download the output.\n%s: %s.\n%s'
                % (resp.status_code, resp.reason, resp.text))
            self.exception_sig.emit(DownloadFailed(err_msg))
            return
        filename = resp.headers['content-disposition'].split(
            'filename=')[1]
        filepath = os.path.join(self.dest_folder, filename)
        self.filepath_sig.emit(filepath)
        tot_len = resp.headers.get('content-length')
        with open(filepath, "wb") as f:
            if tot_len is None:
                f.write(resp.content)
            else:
                tot_len = int(tot_len)
                dl = 0
                chunk_size = max(tot_len//100, 100)  # avoid size 0
                for data in resp.iter_content(chunk_size=chunk_size):
                    if self.is_canceled:
                        raise TaskCanceled
                    dl += len(data)
                    f.write(data)
                    progress = dl / tot_len * 100
                    self.progress_sig.emit(progress)

    def set_canceled(self):
        self.is_canceled = True
