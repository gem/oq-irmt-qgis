import os
import sys
import unittest

from PyQt4 import QtCore, QtGui, QtTest

from openquake.nrmllib.node import node_from_xml
from openquake.common.converter import Converter

from customtableview import TripleTableWidget, NoRecordSelected, index


EXAMPLES = os.path.join(os.path.dirname(__file__), 'examples')

APP = QtGui.QApplication(sys.argv, True)


def click(widget):
    return QtTest.QTest.mouseClick(widget, QtCore.Qt.LeftButton)


class TripleTableTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nrmlfile = os.path.join(EXAMPLES, 'vm.xml')
        node = node_from_xml(nrmlfile)[0]
        tableset = Converter.from_node(node).tableset
        cls.widget = TripleTableWidget(tableset, nrmlfile)

        cls.tv0 = cls.widget.tv[0]
        cls.tv1 = cls.widget.tv[1]
        cls.tv2 = cls.widget.tv[2]

        cls.tm0 = cls.tv0.tableModel
        cls.tm1 = cls.tv1.tableModel
        cls.tm2 = cls.tv2.tableModel

    def test_click(self):
        click(self.widget.tv[0])  # row not specified
        with self.assertRaises(NoRecordSelected):
            self.widget.tv[0].current_record()
        click(self.widget.tv[1])  # row not specified
        with self.assertRaises(NoRecordSelected):
            self.widget.tv[1].current_record()

    def test_current_record_tv0(self):
        tv = self.widget.tv[0]
        tv.tableView.setCurrentIndex(index(1, 0))
        self.assertEqual(
            self.widget.tv[0].current_record(),
            ['vm2', 'Buildings', 'Economic_loss', 'SA(0.34)'])

    def test_remove_insert_rows(self):
        self.assertEqual(len(self.tm2.table), 750)  # 750 records
        first3 = self.tm2.table[:3]
        self.tm2.removeRows(0, 3)  # removing the first 3 records
        self.assertEqual(len(self.tm2.table), 747)  # 747 records
        for row in first3:
            self.tm2.table.insert(0, row)
        self.assertEqual(len(self.tm2.table), 750)  # 750 records
