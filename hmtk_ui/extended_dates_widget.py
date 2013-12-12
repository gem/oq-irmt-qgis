# -*- coding: utf-8 -*-
"""
/***************************************************************************
allows selection of dates back to 4714 BCE and to to sometime in the year 11
million CE
                              -------------------
        begin                : 2013-10-09
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = 'marco@opengis.ch'
__revision__ = '$selfat:%H$'
__date__ = '9/10/2013'

import sys

from PyQt4.QtCore import QDate, QTime, QDateTime, Qt
from PyQt4.QtGui import (QApplication, QGroupBox, QToolButton, QHBoxLayout,
                         QGridLayout, QLabel, QLineEdit, QCalendarWidget,
                         QTimeEdit, QIcon)

try:
    _encoding = QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class ExtendedDatesWidget(QGroupBox):
    """Widget to allow selection of dates back to 4714 BCE and to to sometime
     in the year 11 million CE. The widget allows to use the full range of
     QDate
    see: http://qt-project.org/doc/qt-4.8/qdate.html#range-of-valid-dates

    If no values are passed, the allowed range for both from and to is the
    full range allowed by QDate.

    You can setup ranges directly at init time or you can pass new ranges
    using the various setters (set_from_min_date, set_to_min_date,
    set_from_max_time,...). For convenience you can also use the datetime
    setters and getters (set_from_min_datetime, get_to_max_datetime, ...)

    This widget insures that from_time is always before to_time

    usage from code:
        self.myWidget = AntiqueDatesWidget()
        self.myLayout.insertWidget(1, self.myWidget)
        self.myWidget.set_from_min_datetime(QtCore.QDateTime())
        self.myWidget.set_to_max_datetime(QtCore.QDateTime())
    usage from designer:
        insert a QGroupBox in your UI file
        optionally give a title to the QGroupBox
        promote it to AntiqueDatesWidget

    Known issues: when opening the calendar widget the first time, the
    widget is not placed 100% correctly. This is because the widget has
    initially no position. This is merely a visual issue.
    """

    def __init__(self,
                 from_min_date=None, from_min_time=None,
                 from_max_date=None, from_max_time=None,
                 to_min_date=None, to_min_time=None,
                 to_max_date=None, to_max_time=None,
                 title='Define time range',
                 from_label='From',
                 to_label='To',
                 parent=None, flags=0):
        QGroupBox.__init__(self, parent)

        #members
        self.from_time = None  # QTime
        self.from_date = None  # QDate
        self.to_time = None  # QTime
        self.to_date = None  # QDate
        self.from_min_date = from_min_date  # QDate
        self.from_min_time = from_min_time  # QTime
        self.from_max_date = from_max_date  # QDate
        self.from_max_time = from_max_time  # QTime
        self.to_min_date = to_min_date  # QDate
        self.to_min_time = to_min_time  # QTime
        self.to_max_date = to_max_date  # QDate
        self.to_max_time = to_max_time  # QTime

        #private gui elements
        self._from_label = QLabel(from_label)
        self._from_date_le = QLineEdit()
        self._from_date_cw = self._make_cw()
        self._from_date_cw_btn = self._make_cw_button()
        self._from_time_te = QTimeEdit()
        self._to_label = QLabel(to_label)
        self._to_date_le = QLineEdit()
        self._to_date_cw = self._make_cw()
        self._to_date_cw_btn = self._make_cw_button()
        self._to_time_te = QTimeEdit()

        self.setTitle(title)
        self._setup_ui()

        # from time ranges and default
        if self.from_min_time is None or not self.from_min_time.isValid():
            self.from_min_time = QTime(0, 0, 0, 0)
        if self.from_max_time is None or not self.from_max_time.isValid():
            self.from_max_time = QTime(23, 59, 59, 999)
        self.from_time = self.from_min_time

        # to time ranges and default
        if self.to_min_time is None or not self.to_min_time.isValid():
            self.to_min_time = QTime(0, 0, 0, 0)
        if self.to_max_time is None or not self.to_max_time.isValid():
            self.to_max_time = QTime(23, 59, 59, 999)
        self.to_time = self.to_max_time

        # from date ranges and default
        if self.from_min_date is None or not self.from_min_date.isValid():
            self.from_min_date = QDate.fromJulianDay(1)
        if self.from_max_date is None or not self.from_max_date.isValid():
            self.from_max_date = QDate.fromJulianDay(sys.maxint)
        self.from_date = self.from_min_date

        # to date ranges and default
        if self.to_min_date is None or not self.to_min_date.isValid():
            self.to_min_date = QDate.fromJulianDay(1)
        if self.to_max_date is None or not self.to_max_date.isValid():
            self.to_max_date = QDate.fromJulianDay(sys.maxint)
        self.to_date = self.to_max_date

        #setup the connections
        self._from_date_cw.clicked.connect(self.set_from_date)
        self._to_date_cw.clicked.connect(self.set_to_date)
        self._from_time_te.timeChanged.connect(self.set_from_time)
        self._to_time_te.timeChanged.connect(self.set_to_time)

        self._update_state()

    def set_from_date(self, date):
        if date.isValid():
            self.from_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)

    def set_to_date(self, date):
        if date.isValid():
            self.to_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)

    def set_from_time(self, time):
        if time.isValid():
            self.from_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_to_time(self, time):
        if time.isValid():
            self.to_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_from_min_date(self, date):
        if date.isValid():
            self.from_min_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)
        
    def set_from_min_time(self, time):
        if time.isValid():
            self.from_min_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_from_max_date(self, date):
        if date.isValid():
            self.from_max_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)

    def set_from_max_time(self, time):
        if time.isValid():
            self.from_max_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_to_min_date(self, date):
        if date.isValid():
            self.to_min_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)

    def set_to_min_time(self, time):
        if time.isValid():
            self.to_min_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_to_max_date(self, date):
        if date.isValid():
            self.to_max_date = date
            self._update_state()
        else:
            raise InvalidDatetimeError('date %s is invalid' % date)

    def set_to_max_time(self, time):
        if time.isValid():
            self.to_max_time = time
            self._update_state()
        else:
            raise InvalidDatetimeError('time %s is invalid' % time)

    def set_from_min_datetime(self, datetime):
        if datetime.isValid():
            self.from_min_date = datetime.date()
            self.from_min_time = datetime.time()
            self._update_state()
        else:
            raise InvalidDatetimeError('datetime %s is invalid' % datetime)

    def set_from_max_datetime(self, datetime):
        if datetime.isValid():
            self.from_max_date = datetime.date()
            self.from_max_time = datetime.time()
            self._update_state()
        else:
            raise InvalidDatetimeError('datetime %s is invalid' % datetime)

    def set_to_min_datetime(self, datetime):
        if datetime.isValid():
            self.to_min_date = datetime.date()
            self.to_min_time = datetime.time()
            self._update_state()
        else:
            raise InvalidDatetimeError('datetime %s is invalid' % datetime)

    def set_to_max_datetime(self, datetime):
        if datetime.isValid():
            self.to_max_date = datetime.date()
            self.to_max_time = datetime.time()
            self._update_state()
        else:
            raise InvalidDatetimeError('datetime %s is invalid' % datetime)

    def get_from_min_datetime(self):
        return QDateTime(self.from_min_date, self.from_min_time)

    def get_from_max_datetime(self):
        return QDateTime(self.from_max_date, self.from_max_time)

    def get_to_min_datetime(self):
        return QDateTime(self.to_min_date, self.to_min_time)

    def get_to_max_datetime(self):
        return QDateTime(self.to_max_date, self.to_max_time)

    def _update_ranges(self):
        """Guarantees that from_datetime is always <= to_datetime"""
        self.from_max_date = self.to_date
        self.to_min_date = self.from_date

        if self.from_date < self.from_min_date:
            self.from_date = self.from_min_date
        elif self.from_date > self.from_max_date:
            self.from_date = self.from_max_date

        if self.to_date < self.to_min_date:
            self.to_date = self.to_min_date
        elif self.to_date > self.to_max_date:
            self.to_date = self.to_max_date

        if self.from_date == self.to_date:
            # in the one day scenario we need to force self.from_max_time to
            # be smaller than self.to_min_time
            self.from_max_time = self.to_time
            self.to_min_time = self.from_time

        #print 'From:'
        #print self.from_min_date, self.from_date, self.from_max_date
        #print self.from_min_time, self.from_time, self.from_max_time
        #print 'To:'
        #print self.to_min_date, self.to_date, self.to_max_date
        #print self.to_min_time, self.to_time, self.to_max_time

        self._from_time_te.setTimeRange(self.from_min_time, self.from_max_time)
        self._to_time_te.setTimeRange(self.to_min_time, self.to_max_time)
        self._from_date_cw.setDateRange(self.from_min_date, self.from_max_date)
        self._from_date_cw.setSelectedDate(self.from_date)
        self._to_date_cw.setDateRange(self.to_min_date, self.to_max_date)
        self._to_date_cw.setSelectedDate(self.to_date)

    def _update_state(self):
        """Update the ranges and the reflect it in the GUI"""
        self._update_ranges()
        self._from_time_te.setTime(self.from_time)
        self._to_time_te.setTime(self.to_time)
        self._from_date_le.setText(self.from_date.toString())
        self._to_date_le.setText(self.to_date.toString())

    def _setup_ui(self):
        self._from_date_le.setEnabled(False)
        self._to_date_le.setEnabled(False)

        layout = QHBoxLayout(self)
        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self._from_label, 0, 0)
        grid_layout.addWidget(self._from_date_le, 0, 1)
        grid_layout.addWidget(self._from_date_cw_btn, 0, 2)
        grid_layout.addWidget(self._from_time_te, 0, 3)
        grid_layout.addWidget(self._to_label, 1, 0)
        grid_layout.addWidget(self._to_date_le, 1, 1)
        grid_layout.addWidget(self._to_date_cw_btn, 1, 2)
        grid_layout.addWidget(self._to_time_te, 1, 3)

        layout.addLayout(grid_layout)
        self._retranslate_ui()

        self._from_date_cw_btn.toggled.connect(
            lambda checked: self._toggle_cw(checked, self._from_date_cw))
        self._to_date_cw_btn.toggled.connect(
            lambda checked: self._toggle_cw(checked, self._to_date_cw))

    def _retranslate_ui(self):
        self._from_time_te.setDisplayFormat(
            _translate("self", "hh:mm:ss", None))
        self._to_time_te.setDisplayFormat(
            _translate("self", "hh:mm:ss", None))
        self._from_label.setText(_translate("self", "From", None))
        self._to_label.setText(_translate("self", "To", None))

    def _toggle_cw(self, checked, cw):
        if checked:
            #disable the other calendar
            if cw == self._from_date_cw:
                self._to_date_cw_btn.setChecked(False)
                pos = self._from_date_cw_btn.pos()
            else:
                self._from_date_cw_btn.setChecked(False)
                pos = self._to_date_cw_btn.pos()

            pos = self.mapToGlobal(pos)
            margin = 20
            cw_width = cw.width() + margin
            #enable this calendar
            cw.show()
            cw.setFocus(Qt.PopupFocusReason)
            cw.move(pos.x() - cw_width, pos.y())
        else:
            cw.close()

    def _close_cw(self, cw):
        if cw == self._from_date_cw:
            self._from_date_cw_btn.setChecked(False)
        else:
            self._to_date_cw_btn.setChecked(False)
        cw.close()

    def _make_cw(self):
        cw = QCalendarWidget()
        # cw.setWindowFlags(cw.windowFlags() |
        #                   Qt.Tool |
        #                   Qt.FramelessWindowHint |
        #                   Qt.WindowStaysOnTopHint)
        cw.activated.connect(lambda: self._close_cw(cw))
        return cw

    @staticmethod
    def _make_cw_button():
        btn = QToolButton()
        btn.setIcon(QIcon.fromTheme('x-office-calendar'))
        btn.setCheckable(True)
        return btn


class InvalidDatetimeError(Exception):
    pass
