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
from defaults import get_defaults
from utils import ReadMetadataError

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '12/10/2014'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')


import copy
import json
import os
import time

from xml.etree import ElementTree

from iso_19115_template import ISO_METADATA_XML_TEMPLATE
from globals import DEBUG


# list of tags to get to the svir project definition.
# this is stored in a list so it can be easily used in a for loop
ISO_METADATA_KEYWORD_NESTING = [
    '{http://www.isotc211.org/2005/gmd}identificationInfo',
    '{http://www.isotc211.org/2005/gmd}MD_DataIdentification',
    '{http://www.isotc211.org/2005/gmd}supplementalInformation',
    '{http://www.isotc211.org/2005/gco}CharacterString']

# flat xpath for the keyword container tag
ISO_METADATA_KEYWORD_TAG = '/'.join(ISO_METADATA_KEYWORD_NESTING)

ElementTree.register_namespace('gmi', 'http://www.isotc211.org/2005/gmi')
ElementTree.register_namespace('gco', 'http://www.isotc211.org/2005/gco')
ElementTree.register_namespace('gmd', 'http://www.isotc211.org/2005/gmd')
ElementTree.register_namespace('csw', 'http://www.opengis.net/cat/csw/2.0.2')
ElementTree.register_namespace('xsi',
                               'http://www.w3.org/2001/XMLSchema-instance')


# MONKEYPATCH CDATA support into Element tree
# inspired by http://stackoverflow.com/questions/174890/#answer-8915039
def CDATA(text=None):
    element = ElementTree.Element('![CDATA[')
    element.text = text
    return element
ElementTree._original_serialize_xml = ElementTree._serialize_xml


def _serialize_xml(write, elem, encoding, qnames, namespaces):
    # print "MONKEYPATCHED CDATA support into Element tree called"
    if elem.tag == '![CDATA[':
        write("\n<%s%s]]>\n" % (elem.tag, elem.text))
        return
    return ElementTree._original_serialize_xml(
        write, elem, encoding, qnames, namespaces)
ElementTree._serialize_xml = ElementTree._serialize['xml'] = _serialize_xml
# END MONKEYPATCH CDATA


def generate_iso_metadata(project_definition=None):
    """Make a valid ISO 19115 XML using the values of get_defaults

    This method will create XML based on the iso_19115_template.py template
    The $placeholders there will be replaced by the values returned from
    defaults.get_defaults. Note that get_defaults takes care of using the
    values set in QGIS settings if available.

    :param project_definition: The project definition to write.
    :type project_definition: dict

    :return: str valid XML
    """

    # get defaults from settings
    template_replacements = copy.copy(get_defaults())

    # create runtime based replacement values
    template_replacements['ISO19115_TODAY_DATETIME'] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    if project_definition is not None:
        if DEBUG:
            print project_definition
        template_replacements['SVIR_PROJECT_DEFINITION'] = '<![CDATA[%s]]>' % \
            json.dumps(project_definition)
        try:
            template_replacements['ISO19115_TITLE'] = \
                project_definition['title']
        except KeyError:
            pass
        try:
            template_replacements['ISO19115_LINEAGE'] = \
                project_definition['source']
        except KeyError:
            template_replacements['ISO19115_LINEAGE'] = ''
        try:
            template_replacements['ISO19115_ORGANIZATION'] = \
                project_definition['organization']
        except KeyError:
            template_replacements['ISO19115_ORGANIZATION'] = ''
        try:
            template_replacements['$ISO19115_EMAIL'] = \
                project_definition['email']
        except KeyError:
            template_replacements['ISO19115_EMAIL'] = ''
        try:
            template_replacements['ISO19115_LICENSE'] = \
                'licensed under ' + project_definition['license']
        except KeyError:
            template_replacements['ISO19115_LICENSE'] = 'no license specified'
        try:
            template_replacements['$ISO19115_URL'] = \
                project_definition['$ISO19115_URL']
        except KeyError:
            template_replacements['ISO19115_URL'] = ''

    else:
        template_replacements['SVIR_PROJECT_DEFINITION'] = ''

    return ISO_METADATA_XML_TEMPLATE.safe_substitute(template_replacements)


def write_iso_metadata_file(xml_filename, project_definition=None):
    """
    Make a valid ISO 19115 XML file using the values of defaults.get_defaults

    This method will create a file based on the iso_19115_template.py template
    The $placeholders there will be replaced by the values returned from
    defaults.get_defaults. Note that get_defaults takes care of using the
    values set in QGIS settings if available.

    :param xml_filename: full path to the file to be generated
    :return:
    """
    xml = generate_iso_metadata(project_definition)
    with open(xml_filename, 'w') as f:
        f.write(xml)
    return xml


def valid_iso_xml(xml_filename):
    """add the necessary tags into an existing xml file or create a new one

    :param xml_filename: name of the xml file
    :return: tree the parsed ElementTree
    """

    if os.path.isfile(xml_filename):
        #the file already has an xml file, we need to check it's structure
        tree = ElementTree.parse(xml_filename)
        root = tree.getroot()
        tag_str = '.'
        parent = root

        # Look for the correct nesting
        for tag in ISO_METADATA_KEYWORD_NESTING:
            tag_str += '/' + tag
            element = root.find(tag_str)
            if element is None:
                element = ElementTree.SubElement(parent, tag)
            parent = element
    else:
        # We create the XML from our template.
        # No more checks are needed since the template must be correct ;)
        write_iso_metadata_file(xml_filename)
        tree = ElementTree.parse(xml_filename)

    return tree


def get_supplemental_info(xml, prefix=None):
    # this raises a IOError if the file doesn't exist
    if os.path.isfile(xml):
        tree = ElementTree.parse(xml)
        root = tree.getroot()
    else:
        root = ElementTree.fromstring(xml)

    keyword_tag = prefix + ISO_METADATA_KEYWORD_TAG
    keyword_element = root.find(keyword_tag)
    # we have an xml file but it has no valid container
    if keyword_element is None:
        raise ReadMetadataError

    return keyword_element.text.split('\n')
