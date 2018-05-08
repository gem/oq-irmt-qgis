"""
button that when is clicked with whatsThis mode on opens an URL

Contact : marco@opengis.ch

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.
"""
from __future__ import print_function
from svir.utilities.shared import DEBUG

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '26/11/2015'


from qgis.PyQt.QtCore import QUrl, QEvent
from qgis.PyQt.QtWidgets import QToolButton, QWhatsThis
from qgis.PyQt.QtGui import QDesktopServices


class QToolButtonWithHelpLink(QToolButton):
    def __init__(self, action, help_url):
        super(QToolButtonWithHelpLink, self).__init__()
        self.setDefaultAction(action)
        self.help_url = help_url
        self.setWhatsThis(
            '<a href="%s">Click for documentation</a>' % help_url)

    def event(self, event):
        if event.type() == QEvent.WhatsThis:
            self.open_doc()
            return True
        return super(QToolButtonWithHelpLink, self).event(event)

    def open_doc(self):
        if DEBUG:
            print('Opening : %s' % self.help_url)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.help_url))
        QWhatsThis.leaveWhatsThisMode()
