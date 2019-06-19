# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QDialog
from svir.utilities.utils import get_ui_class

FORM_CLASS = get_ui_class('ui_text_browser.ui')


class ShowConsoleDialog(QDialog, FORM_CLASS):
    """
    Non-modal dialog to display the console log of a OQ-Engine calculation
    """

    def __init__(self, driver_dialog, calc_id):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.driver_dialog = driver_dialog
        self.calc_id = calc_id
        # when re-opening the dialog for a calculation, display the log from
        # the beginning
        self.driver_dialog.calc_log_line[calc_id] = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_calc_log)
        self.timer.start(3000)  # refresh time in milliseconds
        # show the log before the first iteration of the timer
        self.refresh_calc_log()

    def refresh_calc_log(self):
        calc_status = self.driver_dialog.get_calc_status(self.calc_id)
        if calc_status is None:
            self.reject()
            return
        if calc_status['status'] in ('complete', 'failed'):
            self.timer.stop()
        calc_log = self.driver_dialog.get_calc_log(self.calc_id)
        if calc_log:
            self.text_browser.append(calc_log)

    def reject(self):
        self.timer.stop()
        super().reject()
