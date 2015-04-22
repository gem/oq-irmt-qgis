# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014-2015 by GEM Foundation
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

import traceback

from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QThread
from PyQt4.QtGui import QProgressBar, QPushButton
from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar


class AbstractWorker(QtCore.QObject):
    """Abstract worker, ihnerit from this and implement the work method"""

    # available signals
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(float)
    toggle_show_progress = QtCore.pyqtSignal(bool)

    # private signal, don't use in concrete workers this is automatically
    # emitted if the result is not None
    successfully_finished = QtCore.pyqtSignal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.killed = False

    def run(self):
        try:
            result = self.work()
            self.finished.emit(result)
        except Exception, e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
            self.finished.emit(None)

    def work(self):
        """ Reimplement this putting your calculation here
            available are:
                self.progress.emit(0-100)
                self.killed
            :returns a python object - use None if killed is true
        """

        raise NotImplementedError

    def kill(self):
        self.killed = True


def start_worker(worker, message_bar, message):
    # configure the QgsMessageBar
    message_bar_item = message_bar.createMessage(message)
    progress_bar = QProgressBar()
    progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    cancel_button = QPushButton()
    cancel_button.setText('Cancel')
    cancel_button.clicked.connect(worker.kill)
    message_bar_item.layout().addWidget(progress_bar)
    message_bar_item.layout().addWidget(cancel_button)
    message_bar.pushWidget(message_bar_item, message_bar.INFO)

    # start the worker in a new thread
    thread = QThread(message_bar.parent())
    worker.moveToThread(thread)
    worker.toggle_show_progress.connect(lambda show: toggle_worker_progress(
        show, progress_bar))
    worker.finished.connect(lambda result: worker_finished(
        result, thread, worker, message_bar, message_bar_item))
    worker.error.connect(lambda e, exception_str: worker_error(
        e, exception_str, message_bar))
    worker.progress.connect(progress_bar.setValue)
    thread.started.connect(worker.run)
    thread.start()
    return thread, message_bar_item


def toggle_worker_progress(show_progress, progress_bar):
    progress_bar.setMinimum(0)
    if show_progress:
        progress_bar.setMaximum(100)
    else:
        # show an undefined progress
        progress_bar.setMaximum(0)


def worker_finished(result, thread, worker, message_bar, message_bar_item):
        # remove widget from message bar
        message_bar.popWidget(message_bar_item)
        if result is not None:
            # report the result
            message_bar.pushMessage('%s.' % str(result))
            worker.successfully_finished.emit(result)

        # clean up the worker and thread
        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()


def worker_error(e, exception_string, message_bar):
    # notify the user that something went wrong
    message_bar.pushMessage(
        'Something went wrong! See the message log for more information.',
        level=QgsMessageBar.CRITICAL,
        duration=3)
    QgsMessageLog.logMessage(
        'Worker thread raised an exception: %s' % exception_string,
        'SVIR worker',
        level=QgsMessageLog.CRITICAL)