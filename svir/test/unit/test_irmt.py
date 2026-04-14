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
import pytest
import svir

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QFile


@pytest.fixture
def plugin_dir():
    """Fixture to provide the absolute path to the plugin directory."""
    return os.path.dirname(svir.__file__)


@pytest.fixture
def iface():
    """Provide a mocked QGIS interface."""
    from qgis.testing.mocked import get_iface
    return get_iface()


def test_icon_png(plugin_dir):
    """Test that the plugin icon exists and can be loaded as a QIcon."""
    icon_path = os.path.join(plugin_dir, 'resources', 'icon.svg.png')
    # Verification using QFile
    assert QFile.exists(icon_path), f"Resource not found: {icon_path}"
    icon = QIcon(icon_path)
    # Verification that the icon is a valid image
    assert not icon.isNull(), f"Icon at {icon_path} is null or invalid."


def test_toggle_active_actions():
    """Placeholder for testing registered actions."""
    # The original unittest version contained only the
    # following commented lines
    # print(IRMT.registered_actions())
    # self.assertFalse()
    pass
