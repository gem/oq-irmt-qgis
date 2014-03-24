# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2014-03-24
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

# create the dialog for zoom to point
from PyQt4.QtCore import QUrl
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)

from ui.ui_weight_data import Ui_WeightDataDialog


class WeightDataDialog(QDialog):
    """
    Modal dialog allowing to select a raster or vector layer
    containing loss data points and a vector layer containing polygons
    that define the zones for which data need to be aggregated. When
    both are selected and are valid files, they can be loaded by clicking OK
    """
    def __init__(self, iface):
        self.iface = iface
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WeightDataDialog()
        self.ui.setupUi(self)
        self.ui.web_view.load(
            QUrl().fromLocalFile(
                '/home/marco/dev/GEM/qt-experiments/svir/resources/d3.html'))
        # Disable ok_button until loss and zonal layers are selected
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.ui.web_view.loadFinished.connect(self.load_finished)

    def load_finished(self):
        print '********************'
        result = self.sender().page().mainFrame().evaluateJavaScript("f1('test param')");
        print result
