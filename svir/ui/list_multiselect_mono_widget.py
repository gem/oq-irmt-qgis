# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2017-10-04
        copyright            : (C) 2017 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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

from qgis.PyQt.QtGui import QAbstractItemView
from svir.ui.list_multiselect_widget import ListMultiSelectWidget
from svir.utilities.utils import log_msg


class ListMultiSelectMonoWidget(ListMultiSelectWidget):
    """
    This is a strange multiselect widget in which you can actually select
    only one item. A combo box might be used instead. The purpose of using
    this is to make it simpler to migrate to an actual multiselect afterwards,
    once multiple items can be handled server-side.
    """
    def __init__(self, message_bar, parent=None, title=None):
        self.message_bar = message_bar
        super(ListMultiSelectMonoWidget, self).__init__(parent, title)
        self.unselected_widget.setSelectionMode(
            QAbstractItemView.SingleSelection)

    def _select(self):
        if self.selected_widget.count():
            self.unselected_widget.addItem(self.selected_widget.takeItem(0))
        super(ListMultiSelectMonoWidget, self)._select()
