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

import time

from svir.metadata.metadata_utilities import (
    valid_iso_xml, ISO_METADATA_KEYWORD_TAG, ISO_METADATA_KEYWORD_NESTING,
    generate_iso_metadata)


def test_valid_iso_xml(tmp_path):
    """Test ISO XML validation and auto-generation of missing tags."""
    # pytest's tmp_path provides a unique temporary directory
    xml_file = tmp_path / "test_metadata.xml"
    filename = str(xml_file)

    # valid_iso_xml should create a new file if it doesn't exist
    tree = valid_iso_xml(filename)
    root = tree.getroot()
    assert root.find(ISO_METADATA_KEYWORD_TAG) is not None

    # Navigate the nesting to find specific tags
    path_step1 = ISO_METADATA_KEYWORD_NESTING[0]
    path_step2 = ISO_METADATA_KEYWORD_NESTING[1]
    path_step3 = ISO_METADATA_KEYWORD_NESTING[2]
    data_identification = root.find(f"{path_step1}/{path_step2}")
    supplemental_info = root.find(f"{path_step1}/{path_step2}/{path_step3}")

    # Remove the tag to invalidate the XML structure
    data_identification.remove(supplemental_info)

    # Verify the specific keyword tag is now missing
    assert root.find(ISO_METADATA_KEYWORD_TAG) is None

    # Running valid_iso_xml again should fix/re-generate the missing parts
    tree_fixed = valid_iso_xml(filename)
    assert tree_fixed.getroot().find(ISO_METADATA_KEYWORD_TAG) is not None


def test_generate_iso_metadata():
    """Test that ISO metadata string contains expected keywords and dates."""
    today = time.strftime("%Y-%m-%d")
    keywords = {
        'category': 'exposure',
        'datatype': 'itb',
        'subcategory': 'building',
        'title': 'Test TITLE'
    }
    metadata_xml = generate_iso_metadata(keywords)

    # Check for title substitution
    assert '<gco:CharacterString>Test TITLE' in metadata_xml, (
        "XML should include the title 'Test TITLE'"
    )

    # Check for date generation
    assert today in metadata_xml, (
        f"XML should include today's date ({today})"
    )
