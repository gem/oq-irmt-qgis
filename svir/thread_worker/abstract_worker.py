# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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

import traceback
from qgis.PyQt import QtCore
from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar

from qgis.PyQt.QtCore import Qt, QThread
from qgis.PyQt.QtGui import QProgressBar, QPushButton

from svir.utilities.utils import tr, UserAbortedNotification


class AbstractWorker(QtCore.QObject):
    """Abstract worker, ihnerit from this and implement the work method"""

    # available signals
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(float)
    toggle_show_progress = QtCore.pyqtSignal(bool)
    toggle_show_cancel = QtCore.pyqtSignal(bool)
    set_message = QtCore.pyqtSignal(str)

    # private signal, don't use in concrete workers this is automatically
    # emitted if the result is not None
    successfully_finished = QtCore.pyqtSignal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.is_killed = False

    def run(self):
        try:
            result = self.work()
            self.finished.emit(result)
        except UserAbortedNotification:
            self.finished.emit(None)
        except Exception, e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
            self.finished.emit(None)

    def work(self):
        """ Reimplement this putting your calculation here
            available are:
            * self.progress.emit(0-100)
            * self.killed
            :returns: a python object - use None if killed is true
        """

        raise NotImplementedError

    def kill(self):
        self.is_killed = True
        self.set_message.emit(tr('Aborting...'))
        self.toggle_show_progress.emit(False)


def start_worker(worker, message_bar, message):
    """
    Configure the QgsMessageBar with a :guilabel:`Cancel` button and start
    the worker in a new thread

    :param worker: the worker to be started
    :param message_bar: the message bar to be used to display progress
    :param message: a message describing the task to be performed
    """
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

    worker.set_message.connect(lambda message: set_worker_message(
        message, message_bar_item))

    worker.toggle_show_progress.connect(lambda show: toggle_worker_progress(
        show, progress_bar))

    worker.toggle_show_cancel.connect(lambda show: toggle_worker_cancel(
        show, cancel_button))

    worker.finished.connect(lambda result: worker_finished(
        result, thread, worker, message_bar, message_bar_item))

    worker.error.connect(lambda e, exception_str: worker_error(
        e, exception_str, message_bar))

    worker.progress.connect(progress_bar.setValue)
    thread.started.connect(worker.run)
    thread.start()
    return thread, message_bar_item


def toggle_worker_progress(show_progress, progress_bar):
    """
    Set the progress to the given progress bar

    :param show_progress:
        if `True`, a 0 to 100 progress will be displayed;
        otherwise, an unquantified progress
    :type show_progress: bool
    """
    progress_bar.setMinimum(0)
    if show_progress:
        progress_bar.setMaximum(100)
    else:
        # show an undefined progress
        progress_bar.setMaximum(0)


def toggle_worker_cancel(show_cancel, cancel_button):
    """
    Show or hide the cancel button

    :param show_cancel: indicating if the :guilabel:`Cancel` button has to
                        be shown
    :type show_cancel: bool
    :param cancel_button: the button to be shown or hidden
    """
    cancel_button.setVisible(show_cancel)


def set_worker_message(message, message_bar_item):
    """
    Set the message bar to display the given message
    """
    message_bar_item.setText(message)


def worker_finished(result, thread, worker, message_bar, message_bar_item):
    """
    Cleanup to be executed when the worker has completed its task
    """
    # remove widget from message bar
    message_bar.popWidget(message_bar_item)
    if result is not None:
        # report the result
        worker.successfully_finished.emit(result)

    # clean up the worker and thread
    worker.deleteLater()
    thread.quit()
    thread.wait()
    thread.deleteLater()


def worker_error(e, exception_string, message_bar):
    """
    Notify the user that something went wrong
    """
    message_bar.pushMessage(
        'Something went wrong! See the message log for more information.',
        duration=0,
        level=QgsMessageBar.CRITICAL)
    QgsMessageLog.logMessage(
        'Worker thread raised an exception: %s' % exception_string,
        'IRMT worker',
        level=QgsMessageLog.CRITICAL)
