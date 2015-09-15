# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -
**Exception Classes.**

Custom exception classes for the IS application.

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '12/10/2014'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import os
import time
import unittest
import tempfile
import uuid

from metadata.metadata_utilities import (
    valid_iso_xml,
    ISO_METADATA_KEYWORD_TAG,
    ISO_METADATA_KEYWORD_NESTING, generate_iso_metadata)


class TestCase(unittest.TestCase):

    def test_valid_iso_xml(self):
        # test when XML file is non existent
        # NOTE: we are not creating a new temporary file here, but just
        # attempting to look for a non-existing file.
        # valid_iso_xml will create a new xml file from a template, if the
        # filename is not found.
        random_name = '%s.xml' % uuid.uuid4()
        filename = os.path.join(tempfile.gettempdir(), random_name)
        tree = valid_iso_xml(filename)
        root = tree.getroot()
        self.assertIsNotNone(root.find(ISO_METADATA_KEYWORD_TAG))

        data_identification = root.find(ISO_METADATA_KEYWORD_NESTING[0] + '/'
                                        + ISO_METADATA_KEYWORD_NESTING[1])
        supplemental_info = root.find(ISO_METADATA_KEYWORD_NESTING[0] + '/'
                                      + ISO_METADATA_KEYWORD_NESTING[1] + '/'
                                      + ISO_METADATA_KEYWORD_NESTING[2])

        data_identification.remove(supplemental_info)
        # the xml should now miss the supplementalInformation tag
        self.assertIsNone(root.find(ISO_METADATA_KEYWORD_TAG))

        # lets fix the xml
        tree = valid_iso_xml(filename)
        self.assertIsNotNone(tree.getroot().find(ISO_METADATA_KEYWORD_TAG))
        os.remove(filename)

    def test_generate_iso_metadata(self):
        today = time.strftime("%Y-%m-%d")
        keywords = {
            'category': 'exposure',
            'datatype': 'itb',
            'subcategory': 'building',
            'title': 'Test TITLE'}

        metadata_xml = generate_iso_metadata(keywords)
        # lets see if the title substitution went well
        self.assertIn(
            '<gco:CharacterString>Test TITLE',
            metadata_xml,
            'XML should include %s' % today)

        # lets check if the date generation worked
        self.assertIn(
            today,
            metadata_xml,
            'XML should include today\'s date (%s)' % today)


if __name__ == '__main__':
    my_suite = unittest.makeSuite(TestCase, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(my_suite)
