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

from qgis.core import QgsField
from qgis.PyQt.QtCore import QVariant
from svir.calculations.process_layer import ProcessLayer


def add_attribute(proposed_attr_name, dtype, layer):
    # TODO: map numpy types to qt types more precisely to optimize storage
    if dtype == 'S':
        qtype = QVariant.String
        qname = 'String'
    elif dtype == 'U':
        qtype = QVariant.ULongLong
        qname = 'ULongLong'
    elif dtype == 'I':
        qtype = QVariant.LongLong
        qname = 'LongLong'
    else:  # NOTE: treating everything else (including 'F') as double
        qtype = QVariant.Double
        qname = 'Double'
    field = QgsField(proposed_attr_name, qtype)
    field.setTypeName(qname)
    assigned_attr_names = ProcessLayer(layer).add_attributes(
        [field])
    assigned_attr_name = assigned_attr_names[proposed_attr_name]
    return assigned_attr_name
