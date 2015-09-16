# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013-2015 by GEM Foundation
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
from PyQt4.QtGui import QDialog, QDialogButtonBox

from oq_irmt.ui.ui_attribute_selection import Ui_AttributeSelctionDialog
from oq_irmt.utilities.utils import tr
from oq_irmt.utilities.shared import NUMERIC_FIELD_TYPES, TEXTUAL_FIELD_TYPES


class AttributeSelectionDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select
    what are the attributes, in the loss layer and in the region layer,
    that contain the loss data and the region id
    """
    def __init__(self, loss_layer, zonal_layer):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_AttributeSelctionDialog()
        self.ui.setupUi(self)
        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.set_ok_button()

        # if the loss layer does not contain an attribute specifying the ids of
        # zones, the user must not be forced to select such attribute, so we
        # add an "empty" option to the combobox
        self.ui.zone_id_attr_name_loss_cbox.addItem(
            tr("Use zonal geometries"))

        # if the zonal_layer doesn't have a field containing a unique zone id,
        # the user can choose to add such unique id
        self.ui.zone_id_attr_name_zone_cbox.addItem(
            tr("Add field with unique zone id"))

        # Load in the comboboxes only the names of the attributes compatible
        # with the following analyses: only numeric for losses and only
        # string for zone ids
        default_zone_id_loss = None
        for field in loss_layer.dataProvider().fields():
            # for the zone id accept both numeric or textual fields
            self.ui.zone_id_attr_name_loss_cbox.addItem(field.name())
            # Accept only numeric fields to contain loss data
            if field.typeName() in NUMERIC_FIELD_TYPES:
                self.ui.loss_attrs_multisel.add_unselected_items(
                    [field.name()])
            elif field.typeName() in TEXTUAL_FIELD_TYPES:
                default_zone_id_loss = field.name()
            else:
                raise TypeError("Unknown field: type is %d, typeName is %s" % (
                    field.type(), field.typeName()))
        if default_zone_id_loss:
            default_idx = self.ui.zone_id_attr_name_loss_cbox.findText(
                default_zone_id_loss)
            if default_idx != -1:  # -1 for not found
                self.ui.zone_id_attr_name_loss_cbox.setCurrentIndex(
                    default_idx)
        default_zone_id_zonal = None
        for field in zonal_layer.dataProvider().fields():
            # for the zone id accept both numeric or textual fields
            self.ui.zone_id_attr_name_zone_cbox.addItem(field.name())
            # by default, set the selection to the first textual field
            if field.typeName() in TEXTUAL_FIELD_TYPES:
                default_zone_id_zonal = field.name()
        if default_zone_id_zonal:
            default_idx = self.ui.zone_id_attr_name_zone_cbox.findText(
                default_zone_id_zonal)
            if default_idx != -1:  # -1 for not found
                self.ui.zone_id_attr_name_zone_cbox.setCurrentIndex(
                    default_idx)

        self.ui.loss_attrs_multisel.selection_changed.connect(
            self.set_ok_button)

    def set_ok_button(self):
        self.ok_button.setEnabled(
            self.ui.loss_attrs_multisel.selected_widget.count() > 0)
