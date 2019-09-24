# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2019 by GEM Foundation
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

import unittest
from qgis.PyQt.QtWidgets import QWidget
from svir.ui.multi_select_combo_box import MultiSelectComboBox


class MultiSelectComboBoxMultiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wdg = QWidget()
        cls.mscb = MultiSelectComboBox(cls.wdg)

    def setUp(self):
        self.mscb.clear()

    def test_addItem(self):
        self.mscb.addItem('first', selected=True)
        self.mscb.addItem('second', selected=False)
        self.assertEqual(self.mscb.get_selected_items(), ['first'])
        self.assertEqual(self.mscb.get_unselected_items(), ['second'])

    def test_addItems(self):
        self.mscb.addItems(['first', 'second'], selected=True)
        self.assertEqual(
            self.mscb.get_selected_items(), ['first', 'second'])
        self.assertEqual(self.mscb.count(), 2)
        self.mscb.addItems(['third', 'fourth'], selected=False)
        self.assertEqual(
            self.mscb.get_selected_items(), ['first', 'second'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['third', 'fourth'])
        self.assertEqual(self.mscb.count(), 4)

    def test_add_selected_items(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.assertEqual(
            self.mscb.get_selected_items(), ['first', 'second'])
        self.assertEqual(self.mscb.count(), 2)

    def test_add_unselected_items(self):
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['third', 'fourth'])
        self.assertEqual(self.mscb.count(), 2)

    def test_clear(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.assertEqual(self.mscb.count(), 4)
        self.mscb.clear()
        self.assertEqual(self.mscb.count(), 0)

    def test_count(self):
        self.assertEqual(self.mscb.count(), 0)
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.assertEqual(self.mscb.count(), 4)

    def test_currentText(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.add_selected_items(['fifth'])
        self.assertEqual(self.mscb.currentText(), ['first', 'second', 'fifth'])

    # def test_get_selected_items(self):
    #     # tested in test_addItems
    #     pass

    # def test_get_unselected_items(self):
    #     # tested in test_addItems
    #     pass

    def test_resetSelection(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.resetSelection()
        self.assertEqual(self.mscb.get_selected_items(), [])

    def test_selected_count(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.assertEqual(self.mscb.selected_count(), 2)

    def test_setCurrentText(self):
        self.mscb.add_unselected_items(['first', 'second'])
        self.mscb.setCurrentText(['first', 'third'])
        self.assertEqual(self.mscb.get_selected_items(), ['first'])

    def test_set_idxs_selection(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.set_idxs_selection([0], checked=False)
        self.assertEqual(
            self.mscb.get_selected_items(), ['second', 'third', 'fourth'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['first'])
        self.mscb.set_idxs_selection([2, 3], checked=True)
        self.assertEqual(self.mscb.get_selected_items(), ['third', 'fourth'])
        self.assertEqual(self.mscb.get_unselected_items(), ['first', 'second'])

    def test_set_items_selection(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.set_items_selection(['first'], checked=False)
        self.assertEqual(
            self.mscb.get_selected_items(), ['second', 'third', 'fourth'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['first'])
        self.mscb.set_items_selection(['third', 'fourth'], checked=True)
        self.assertEqual(self.mscb.get_selected_items(), ['third', 'fourth'])
        self.assertEqual(self.mscb.get_unselected_items(), ['first', 'second'])

    def test_set_selected_items(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.set_selected_items(['third'])
        self.assertEqual(
            self.mscb.get_selected_items(), ['third'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['first', 'second', 'fourth'])

    def test_set_unselected_items(self):
        self.mscb.add_selected_items(['first', 'second'])
        self.mscb.add_unselected_items(['third', 'fourth'])
        self.mscb.set_unselected_items(['first'])
        self.assertEqual(
            self.mscb.get_selected_items(), ['second', 'third', 'fourth'])
        self.assertEqual(
            self.mscb.get_unselected_items(), ['first'])


class MultiSelectComboBoxMonoTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wdg = QWidget()
        cls.mscb = MultiSelectComboBox(cls.wdg, mono=True)

    def test_fixme(self):
        pass


if __name__ == '__main__':
    unittest.main()
