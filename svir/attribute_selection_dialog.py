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
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSlot
from ui.ui_attribute_selection import Ui_AttributeSelctionDialog
from utils import tr


class AttributeSelectionDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    what are the attributes, in the loss layer and in the region layer,
    that contain the loss data and the region id
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_AttributeSelctionDialog()
        self.ui.setupUi(self)

    @pyqtSlot(str)
    def on_zone_id_attr_name_loss_cbox_currentIndexChanged(self):
        zone_id_loss = self.ui.zone_id_attr_name_loss_cbox.currentText()
        use_geometries = (zone_id_loss == tr("Use zonal geometries"))
        self.ui.zone_id_attr_name_zone_cbox.setDisabled(use_geometries)
