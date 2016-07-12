# -*- coding: utf-8 -*-
#/***************************************************************************
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
    # check dependencies
    try:
        import sys
        oq_hazardlib_path = '/home/marco/dev/GEM/oq-hazardlib'
        oq_engine_path = '/home/marco/dev/GEM/oq-engine'
        if oq_hazardlib_path not in sys.path:
            sys.path.append(oq_hazardlib_path)
        if oq_engine_path not in sys.path:
            sys.path.append(oq_engine_path)
        import h5py
        from openquake.baselib import hdf5
    except ImportError:
        raise ImportError('Please install h5py, oq-hazardlib and oq-engine')

    # load Irmt class from file Irmt
    from svir.irmt import Irmt
    return Irmt(iface)

try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)
