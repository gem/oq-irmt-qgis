# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2026 by GEM Foundation
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

from qgis.core import QgsProviderRegistry


def test_qgis_environment(qgis_app):
    """
    Test that the QGIS environment is correctly initialized
    with the expected data providers.
    """
    registry = QgsProviderRegistry.instance()
    providers = registry.providerList()

    # Define the core providers we expect to be available
    expected_providers = [
        'gdal',
        'ogr',
        'postgres',
        'delimitedtext'
    ]

    for provider in expected_providers:
        assert provider in providers, (
            f"Provider '{provider}' not found in QGIS registry. "
            f"Available providers: {', '.join(providers)}"
        )


def test_provider_count(qgis_app):
    """
    Check if we have a reasonable number of providers loaded.
    Helpful for debugging environment-specific issues.
    """
    registry = QgsProviderRegistry.instance()
    # Most standard installations have at least 10+ providers
    assert len(registry.providerList()) > 0
