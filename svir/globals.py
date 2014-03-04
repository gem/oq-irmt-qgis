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

DEBUG = False

INT_FIELD_TYPE_NAME = "integer"
DOUBLE_FIELD_TYPE_NAME = "double"
REAL_FIELD_TYPE_NAME = "Real"

NUMERIC_FIELD_TYPES = (INT_FIELD_TYPE_NAME,
                       REAL_FIELD_TYPE_NAME,
                       DOUBLE_FIELD_TYPE_NAME)

STRING_FIELD_TYPE_NAME = "String"
TEXT_FIELD_TYPE_NAME = "text"

TEXTUAL_FIELD_TYPES = (STRING_FIELD_TYPE_NAME,
                       TEXT_FIELD_TYPE_NAME)
