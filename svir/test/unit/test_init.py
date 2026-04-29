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
import logging
import configparser
import pytest

LOGGER = logging.getLogger('OpenQuake')


@pytest.fixture
def metadata_path():
    """Fixture to resolve the path to metadata.txt."""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            os.pardir,
            'metadata.txt'
        )
    )


def test_read_init(qgis_app, metadata_path):
    """Test that the plugin __init__ will validate."""
    required_metadata = [
        'name',
        'description',
        'version',
        'qgisMinimumVersion',
        'email',
        'author'
    ]

    LOGGER.info(f"Checking metadata at: {metadata_path}")

    parser = configparser.ConfigParser()
    parser.optionxform = str

    assert os.path.exists(metadata_path), (
        f"metadata.txt not found at {metadata_path}"
    )

    parser.read(metadata_path)

    assert parser.has_section('general'), (
        f"Cannot find a section named 'general' in {metadata_path}"
    )

    metadata_dict = dict(parser.items('general'))

    for expectation in required_metadata:
        error_msg = (
            f"Cannot find metadata '{expectation}' in "
            f"metadata source ({metadata_path})."
        )
        assert expectation in metadata_dict, error_msg
