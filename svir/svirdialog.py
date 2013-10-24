# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SvirDialog
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                             -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
# create the dialog for zoom to point
from ui_svir import Ui_SvirDialog


class SvirDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SvirDialog()
        self.ui.setupUi(self)
