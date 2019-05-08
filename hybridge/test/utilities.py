
# coding=utf-8
"""Helper module for gui test suite."""


import codecs
import hashlib
import logging
import os
import re
import sys

from qgis.PyQt import QtWidgets
from qgis.utils import iface

QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None
LOGGER = logging.getLogger('OpenQuake')
GEOCRS = 4326  # constant for EPSG:GEOCRS Geographic CRS id
GOOGLECRS = 3857  # constant for EPSG:GOOGLECRS Google Mercator id
# DEVNULL = open(os.devnull, 'w')


__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'


def get_dock():
    """Get a dock for testing.

    If you call this function from a QGIS Desktop, you will get the real dock,
    however, you use a fake QGIS interface, it will create a fake dock for you.

    :returns: A dock.
    :rtype: QDockWidget
    """
    # Don't move this import.
    from svir.dialogs.viewer_dock import ViewerDock as DockObject
    if iface:
        docks = iface.mainWindow().findChildren(QtWidgets.QDockWidget)
        for dock in docks:
            if isinstance(dock, DockObject):
                return dock
        else:
            return DockObject(iface)
    else:
        return DockObject(IFACE)


def assert_hash_for_file(hash_string, filename):
    """Assert that a files hash matches its expected hash.
    :param filename:
    :param hash_string:
    """
    file_hash = hash_for_file(filename)
    message = (
        'Unexpected hash'
        '\nGot: %s'
        '\nExpected: %s' % (file_hash, hash_string))
    if file_hash != hash_string:
        raise Exception(message)


def hash_for_file(filename):
    """Return an md5 checksum for a file
    :param filename:
    """
    path = filename
    with open(path, 'rb') as f:
        data = f.read()
    data_hash = hashlib.md5()
    data_hash.update(data)
    data_hash = data_hash.hexdigest()
    return data_hash


def compare_wkt(a, b, tol=0.000001):
    """Helper function to compare WKT geometries with given tolerance
    Taken from QGIS test suite

    :param a: Input WKT geometry
    :type a: str

    :param b: Expected WKT geometry
    :type b: str

    :param tol: compare tolerance
    :type tol: float

    :return: True on success, False on failure
    :rtype: bool
    """
    r = re.compile(r'-?\d+(?:\.\d+)?(?:[eE]\d+)?')

    # Text might upper or lower case
    a = a.upper()
    b = b.upper()

    # Might have a space between the text and coordinates
    geometry_type = a.split('(', 1)
    a = geometry_type[0].replace(' ', '') + '('.join(geometry_type[1:])
    geometry_type = b.split('(', 1)
    b = geometry_type[0].replace(' ', '') + '('.join(geometry_type[1:])

    # compare the structure
    a0 = r.sub("#", a)
    b0 = r.sub("#", b)
    if a0 != b0:
        return False

    # compare the numbers with given tolerance
    a0 = r.findall(a)
    b0 = r.findall(b)
    if len(a0) != len(b0):
        return False

    for (a1, b1) in zip(a0, b0):
        if abs(float(a1) - float(b1)) > tol:
            return False

    return True


def assert_and_emit(signal, assertion, p1, p2, msg):
    try:
        assertion(p1, p2, msg)
    except Exception as exc:
        signal.emit(exc)
        raise exc
