"""
button that when is clicked with whatsThis mode on opens an URL

Contact : marco@opengis.ch

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.
"""

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '26/11/2015'


from PyQt4.QtCore import Qt, QUrl, QEvent
from PyQt4.QtGui import QToolButton, QWhatsThis, QDesktopServices


class QToolButtonWithHelpLink(QToolButton):
    def __init__(self, action, help_url):
        super(QToolButtonWithHelpLink, self).__init__()
        #self.setAttribute(Qt.WA_CustomWhatsThis)
        self.setDefaultAction(action)
        self.help_url = help_url
        self.setWhatsThis('<a href="%s">Click for documentation</a>' % help_url)

    def event(self, event):
        if event.type() == QEvent.WhatsThis:
            self.open_doc()
            return True
        return super(QToolButtonWithHelpLink, self).event(event)

    def mousePressEvent(self, event):
        if QWhatsThis.inWhatsThisMode() and event.button() == Qt.LeftButton:
            self.open_doc()
        else:
            super(QToolButtonWithHelpLink, self).mousePressEvent(event)

    def open_doc(self):
        print 'Opening : %s' % self.help_url
        QDesktopServices.openUrl(QUrl(self.help_url))
        QWhatsThis.leaveWhatsThisMode()
