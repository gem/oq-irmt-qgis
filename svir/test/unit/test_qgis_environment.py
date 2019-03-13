
# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -
**ISClipper test suite.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'tim@kartoza.com'
__date__ = '20/01/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import unittest

from qgis.core import QgsProviderRegistry



from qgis.testing import start_app
from qgis.testing.mocked import get_iface

QGIS_APP = start_app()
IFACE = get_iface()


class QGISTest(unittest.TestCase):
    """Test the QGIS Environment."""

    def test_qgis_environment(self):
        """QGIS environment has the expected providers."""
        # noinspection PyUnresolvedReferences
        r = QgsProviderRegistry.instance()

        # print 'Provider count: %s' % len(r.providerList())
        assert 'gdal' in r.providerList()
        assert 'ogr' in r.providerList()
        assert 'postgres' in r.providerList()
        assert 'delimitedtext' in r.providerList()
        # assert 'wfs' in r.providerList()


if __name__ == '__main__':
    unittest.main()
