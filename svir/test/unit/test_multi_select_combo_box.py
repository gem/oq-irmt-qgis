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

import pytest
from qgis.PyQt.QtWidgets import QWidget
from svir.ui.multi_select_combo_box import MultiSelectComboBox


@pytest.fixture
def mscb_multi():
    """Provides a MultiSelectComboBox in MULTI mode."""
    wdg = QWidget()
    multi = MultiSelectComboBox(wdg, mono=False)
    yield multi
    multi.clear()


@pytest.fixture
def mscb_mono():
    """Provides a MultiSelectComboBox in MONO mode."""
    wdg = QWidget()
    mono = MultiSelectComboBox(wdg, mono=True)
    yield mono
    mono.clear()


class TestMultiSelectComboBoxMulti:

    def test_addItem(self, mscb_multi):
        mscb_multi.addItem('first', selected=True)
        mscb_multi.addItem('second', selected=False)
        assert mscb_multi.get_selected_items() == ['first']
        assert mscb_multi.get_unselected_items() == ['second']

    def test_addItems(self, mscb_multi):
        mscb_multi.addItems(['first', 'second'], selected=True)
        assert mscb_multi.get_selected_items() == ['first', 'second']
        assert mscb_multi.count() == 2
        mscb_multi.addItems(['third', 'fourth'], selected=False)
        assert mscb_multi.get_selected_items() == ['first', 'second']
        assert mscb_multi.get_unselected_items() == ['third', 'fourth']
        assert mscb_multi.count() == 4

    def test_add_selected_items(self, mscb_multi):
        mscb_multi.add_selected_items(['first', 'second'])
        assert mscb_multi.get_selected_items() == ['first', 'second']
        assert mscb_multi.count() == 2

    def test_clear(self, mscb_multi):
        mscb_multi.add_selected_items(['first'])
        mscb_multi.clear()
        assert mscb_multi.count() == 0

    def test_currentText(self, mscb_multi):
        mscb_multi.add_selected_items(['first', 'second'])
        mscb_multi.add_unselected_items(['third'])
        mscb_multi.add_selected_items(['fifth'])
        assert mscb_multi.currentText() == ['first', 'second', 'fifth']

    def test_resetSelection(self, mscb_multi):
        mscb_multi.add_selected_items(['first', 'second'])
        mscb_multi.resetSelection()
        assert mscb_multi.get_selected_items() == []

    def test_set_idxs_selection(self, mscb_multi):
        mscb_multi.add_selected_items(['first', 'second'])  # 0, 1
        mscb_multi.add_unselected_items(['third', 'fourth'])  # 2, 3
        mscb_multi.set_idxs_selection([0], checked=False)
        assert mscb_multi.get_selected_items() == ['second', 'third', 'fourth']
        mscb_multi.set_idxs_selection([2, 3], checked=True)
        assert mscb_multi.get_selected_items() == ['third', 'fourth']


class TestMultiSelectComboBoxMono:

    def test_addItem(self, mscb_mono):
        mscb_mono.addItem('first', selected=True)
        mscb_mono.addItem('second', selected=False)
        assert mscb_mono.currentText() == 'first'

    def test_currentText(self, mscb_mono):
        mscb_mono.add_selected_items(['first', 'second'])
        assert mscb_mono.currentText() == 'first'

    def test_get_selected_items(self, mscb_mono):
        mscb_mono.add_selected_items(['first', 'second'])
        # In mono mode, only the first item in the list becomes selected
        assert mscb_mono.get_selected_items() == ['first']

    def test_resetSelection(self, mscb_mono):
        mscb_mono.add_selected_items(['first', 'second'])
        mscb_mono.resetSelection()
        assert mscb_mono.currentIndex() == -1
