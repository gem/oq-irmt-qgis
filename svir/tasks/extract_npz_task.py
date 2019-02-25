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

import io
import sys
import numpy
import tempfile
from time import sleep
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QThread, pyqtSignal, pyqtSlot
from numpy.lib.npyio import NpzFile
from svir.utilities.utils import log_msg


class TaskCanceled(Exception):
    pass


class ExtractFailed(Exception):
    pass


class ExtractNpzTask(QgsTask):

    is_canceled_sig = pyqtSignal()

    def __init__(
            self, description, flags, session, hostname, calc_id,
            output_type, on_success, on_error, params=None):
        super().__init__(description, flags)
        self.session = session
        self.hostname = hostname
        self.calc_id = calc_id
        self.output_type = output_type
        self.on_success = on_success
        self.on_error = on_error
        self.dest_folder = tempfile.gettempdir()
        self.extract_url = '%s/v1/calc/%s/extract/%s' % (
            self.hostname, self.calc_id, self.output_type)
        print('Extracting', self.extract_url, file=sys.stderr)
        self.extract_params = params
        self.exception = None
        log_msg('GET: %s, with parameters: %s'
                % (self.extract_url, self.extract_params), level='I')

    def run(self):
        try:
            self.extract_npz(
                self.session, self.extract_url, self.extract_params)
        except Exception as exc:
            self.exception = exc
            return False
        else:
            if self.exception is not None:
                return False
            else:
                return True

    def finished(self, success):
        if success:
            self.on_success(self.extracted_npz)
        else:
            self.on_error(self.exception)

    def extract_npz(self, session, extract_url, extract_params):
        self.setProgress(-1)
        if self.isCanceled():
            self.is_canceled_sig.emit()
            raise TaskCanceled
        self.extract_thread = ExtractThread(
            session, extract_url, extract_params, self.dest_folder)
        self.extract_thread.progress_sig[float].connect(self.set_progress)
        self.extract_thread.extracted_npz_sig[NpzFile].connect(
            self.set_extracted_npz)
        self.extract_thread.exception_sig[Exception].connect(
            self.on_exception)
        self.is_canceled_sig.connect(self.extract_thread.set_canceled)
        self.extract_thread.start()
        while True:
            sleep(0.1)
            if self.extract_thread.isFinished():
                return True
            if self.isCanceled():
                # NOTE: deleteLater would be a cleaner way, but it does not
                # actually kill the get, so the machine remains busy until a
                # response is produced
                # self.extract_thread.deleteLater()
                del(self.extract_thread)
                raise TaskCanceled

    @pyqtSlot(float)
    def set_progress(self, progress):
        self.setProgress(progress)

    @pyqtSlot(NpzFile)
    def set_extracted_npz(self, extracted_npz):
        self.extracted_npz = extracted_npz

    @pyqtSlot(Exception)
    def on_exception(self, exc):
        self.exception = exc


class ExtractThread(QThread):

    progress_sig = pyqtSignal(float)
    extracted_npz_sig = pyqtSignal(NpzFile)
    exception_sig = pyqtSignal(Exception)

    def __init__(self, session, url, params, dest_folder):
        self.session = session
        self.url = url
        self.params = params
        self.dest_folder = dest_folder
        self.is_canceled = False
        super().__init__()

    def run(self):
        # FIXME: enable the user to set verify=True
        # FIXME: stream = True breaks things unexpectedly in some cases
        #        (content-length differs from len(resp.content)
        resp = self.session.get(self.url, params=self.params, verify=False)
        # , stream=True)
        err_msg = "Unable to extract %s with parameters %s" % (
            self.url, self.params)

        if not resp.ok:
            self.exception_sig.emit(ExtractFailed(
                "%s (%s): %s" % (err_msg, resp.reason, resp.content)))
            return

        # FIXME: use stream=True
        # filename = resp.headers['content-disposition'].split(
        #     'filename=')[1]
        # filepath = os.path.join(self.dest_folder, filename)
        # tot_len = resp.headers.get('content-length')
        # with open(filepath, "wb") as f:
        #     if tot_len is None:
        #         f.write(resp.content)
        #     else:
        #         tot_len = int(tot_len)
        #         dl = 0
        #         chunk_size = max(tot_len // 10000, 10)  # avoid size 0
        #         for data in resp.iter_content(chunk_size=chunk_size):
        #             if self.is_canceled:
        #                 raise TaskCanceled
        #             dl += len(data)
        #             f.write(data)
        #             progress = dl / tot_len * 100
        #             self.progress_sig.emit(progress)
        # extracted_npz = numpy.load(filepath)
        if not resp.content:
            self.exception_sig.emit(ExtractFailed(
                "%s: returned an empty content" % err_msg))
            return
        try:
            extracted_npz = numpy.load(io.BytesIO(resp.content))
        except Exception as exc:
            self.exception_sig.emit(exc)
            return
        if not isinstance(extracted_npz, NpzFile):
            self.exception_sig.emit(
                ExtractFailed("%s: not a valid NPZ. Response: (%s) %s" % (
                    err_msg, resp.reason, resp.content)))
            return

        self.extracted_npz_sig.emit(extracted_npz)

        # FIXME: use stream=True
        # os.remove(filepath)

    def set_canceled(self):
        self.is_canceled = True
