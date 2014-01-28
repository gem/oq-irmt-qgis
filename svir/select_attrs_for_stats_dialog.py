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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayerRegistry

from ui_select_attrs_for_stats import Ui_SelectAttrsForStatsDialog

from globals import NUMERIC_FIELD_TYPES

class SelectAttrsForStatsDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    a layer containing SVI and aggregated losses, and to pick
    the attributes containing such data in order to perform some
    common statistics on them
    """
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SelectAttrsForStatsDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

    @pyqtSlot(str)
    def on_layer_cbx_currentIndexChanged(self):
        self.reload_attribs_cbx()

    def reload_attribs_cbx(self):
        # reset combo boxes
        self.ui.svi_attr_cbx.clear()
        self.ui.aggr_loss_attr_cbx.clear()
        # populate attribute combo boxes with the list of attributes of the
        # layer specified in the layer combo box
        layer = QgsMapLayerRegistry.instance().mapLayers().values()[
            self.ui.layer_cbx.currentIndex()]
        # populate combo boxes with field names taken by layers
        dp = layer.dataProvider()
        fields = list(dp.fields())
        no_numeric_fields = True
        for field in fields:
            # add numeric fields only
            if field.typeName() in NUMERIC_FIELD_TYPES:
                self.ui.svi_attr_cbx.addItem(field.name())
                self.ui.aggr_loss_attr_cbx.addItem(field.name())
                no_numeric_fields = False
        self.ok_button.setDisabled(no_numeric_fields)
