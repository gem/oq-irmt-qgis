# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2026 by GEM Foundation
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

import os
import sys
import pytest
from qgis.core import QgsApplication


# Update sys.path BEFORE any svir or processing imports
standard_plugin_path = '/usr/share/qgis/python/plugins'
if (os.path.exists(standard_plugin_path)
        and standard_plugin_path not in sys.path):
    sys.path.append(standard_plugin_path)


@pytest.fixture(scope="session", autouse=True)
def qgis_app():
    """Initialize QGIS and the Processing framework."""
    # Hardcoded common Linux QGIS plugin path
    standard_plugin_path = '/usr/share/qgis/python/plugins'

    if os.path.exists(standard_plugin_path):
        if standard_plugin_path not in sys.path:
            sys.path.append(standard_plugin_path)

    # Initialize QGIS
    qgs = QgsApplication([], False)
    if not os.path.exists(qgs.prefixPath()):
        qgs.setPrefixPath('/usr', True)

    qgs.initQgis()
    # Initialize Processing
    try:
        import processing  # NOQA
        from processing.core.Processing import Processing
        Processing.initialize()
    except ImportError:
        pytest.fail(
            "Could not import 'processing'. Check if QGIS is installed "
            "and the plugin path is correct."
        )
    yield qgs
    qgs.exitQgis()


@pytest.fixture
def iface(mocker):
    """
    Provides a mocked QGIS interface.
    Requires the 'pytest-mock' plugin installed.
    """
    from qgis.testing.mocked import get_iface
    return get_iface()


def test_dumb(iface):
    """Test nothing, but verify iface is accessible."""
    assert iface is not None
