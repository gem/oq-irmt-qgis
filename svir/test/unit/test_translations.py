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

import os
import pytest


@pytest.fixture
def clean_lang_env():
    """
    Ensure the LANG environment variable is cleared before the test
    and restored (if it existed) after.
    """
    old_lang = os.environ.get('LANG')
    if 'LANG' in os.environ:
        del os.environ['LANG']
    yield
    if old_lang is not None:
        os.environ['LANG'] = old_lang
    elif 'LANG' in os.environ:
        del os.environ['LANG']


def test_qgis_translations(qgis_app, clean_lang_env):
    """Test that translations load and resolve correctly."""
    from qgis.PyQt.QtCore import QCoreApplication, QTranslator

    # Resolve paths relative to this file
    # Current file is in svir/test/unit/
    # i18n is in svir/i18n/ (3 levels up from this file's dir)
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    file_path = os.path.join(base_dir, 'i18n', 'it.qm')

    assert os.path.exists(file_path), f"Translation file missing at: {file_path}"  # NOQA

    translator = QTranslator()
    loaded = translator.load(file_path)
    assert loaded, f"Failed to load translator from {file_path}"

    QCoreApplication.installTranslator(translator)

    expected_message = 'Buon giorno'
    # Use the QGIS translation context
    real_message = QCoreApplication.translate("@default", 'Good morning')
    assert real_message == expected_message
