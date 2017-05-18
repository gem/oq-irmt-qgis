
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

from PyQt4.QtCore import QTimer, QObject, SIGNAL
from PyQt4.QtGui import QDialog
from svir.utilities.utils import get_ui_class

FORM_CLASS = get_ui_class('ui_show_full_report.ui')


class ShowConsoleDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to display the console log of a OQ-Engine calculation
    """

    def __init__(self, driver_dialog, calc_id):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.driver_dialog = driver_dialog
        self.calc_id = calc_id
        self.text_browser.clear()
        self.timer = QTimer()
        QObject.connect(
            self.timer, SIGNAL('timeout()'), self.refresh_calc_log)
        self.timer.start(1000)  # refresh time in milliseconds

    def refresh_calc_log(self):
        calc_log = self.driver_dialog.get_calc_log(self.calc_id)
        if calc_log:
            self.text_browser.append(calc_log)
