# coding=utf-8
"""**SAFE (Scenario Assessment For Emergencies) - API**

The purpose of the module is to provide a well defined public API
for the packages that constitute the SAFE engine. Modules using SAFE
should only need to import functions from here.

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '05/10/2012'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')


DEFAULTS = dict()
#Defaults for iso_19115_template.xml
DEFAULTS['ISO19115_TITLE'] = 'SVIR analysis result'
DEFAULTS['ISO19115_LICENSE'] = 'Free use with accreditation (Affero GPL)'


# noinspection PyUnresolvedReferences
# this is used when we are in safe without access to qgis (e.g. web ) and is
# monkey patched in safe_qgis.__init__
def get_defaults(default=None):
    """Get defaults for aggregation / post processing.

    :param default: Optional parameter if you only want a specific default.
    :type default: str

    :return: A single value (when default is passed) or a dict of values.
    :rtype: str, int, float, dict
    """
    if default is None:
        return DEFAULTS
    elif default in DEFAULTS:
        return DEFAULTS[default]
    else:
        return None
