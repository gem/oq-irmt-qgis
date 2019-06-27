# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013 by GEM Foundation
#        email                : devops@openquake.org
# ***************************************************************************/
#
# Copyright (c) 2013-2014, GEM Foundation.
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


def classFactory(iface):
    # load Irmt class from file Irmt
    from svir.irmt import Irmt
    return Irmt(iface)


try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)

IS_SCIPY_INSTALLED = None
try:
    import scipy  # NOQA
except ImportError:
    IS_SCIPY_INSTALLED = False
else:
    IS_SCIPY_INSTALLED = True

IS_MATPLOTLIB_INSTALLED = None
try:
    import matplotlib  # NOQA
except ImportError:
    IS_MATPLOTLIB_INSTALLED = False
else:
    IS_MATPLOTLIB_INSTALLED = True
