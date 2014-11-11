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
"""


import unittest

from PyQt4.QtGui import QIcon

from utilities import get_qgis_app
QGIS_APP, CANVAS, PARENT, IFACE = get_qgis_app()

import svir
SVIR = svir.classFactory(IFACE)
#SVIR.ui = svir.plugin.dlg.ui  # useful for shorthand later


class SvirTest(unittest.TestCase):
    """Test SVIR works."""

    def setUp(self):
        """Runs before each test."""
        pass

    def tearDown(self):
        """Runs after each test."""
        pass

    def test_icon_png(self):
        """Test we can click OK."""
        path = ':/plugins/SVIR/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())

    def test_toggle_active_actions(self):
        #print SVIR.registered_actions()
        #self.assertFalse()
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(SvirTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
