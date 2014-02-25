# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)

from ui.ui_choose_sv_data_source import Ui_ChooseSvDataSourceDialog


class ChooseSvDataSourceDialog(QDialog):
    """
    Simple dialog to ask the user to choose between downloading data through
    the OpenQuake Platform or using one of the available layers
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_ChooseSvDataSourceDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.ui.layer_rbn.toggled.connect(self.update_ok_button)
        self.ui.platform_rbn.toggled.connect(self.update_ok_button)

    def update_ok_button(self):
        self.ok_button.setEnabled(self.ui.layer_rbn.isChecked() or
                                  self.ui.platform_rbn.isChecked())
