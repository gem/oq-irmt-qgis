# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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
"""
from xml.etree import ElementTree
from PyQt4 import Qt

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QListWidgetItem)

from oq_irmt.ui.ui_download_layer import Ui_DownloadLayerDialog
from oq_irmt.utilities.utils import WaitCursorManager, SvNetworkError

NS_NET_OPENGIS_WFS = '{http://www.opengis.net/wfs}'


class DownloadLayerDialog(QDialog):
    """
    Modal dialog giving to the user the possibility to select and download one
    of the projects available on the OQ-Platform
    """
    def __init__(self, downloader):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_DownloadLayerDialog()
        self.ui.setupUi(self)
        # login to platform, to be able to retrieve sv indices
        self.sv_downloader = downloader

        self.ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        self.ui.layer_lbl.setText('Project definition')

        self.layer_id = None  # needed after ok is pressed
        self.extra_infos = {}

        self.set_ok_button()
        with WaitCursorManager():
            self.get_capabilities()

    @pyqtSlot()
    def on_layers_lst_itemSelectionChanged(self):
        layer_id = self.ui.layers_lst.currentItem().data(Qt.Qt.ToolTipRole)
        if layer_id is not None:
            self.layer_id = layer_id
            self.ui.layer_lbl.setText('Project details for "%s"' % layer_id)
            layer_infos = self.extra_infos[layer_id]
            bb = layer_infos['Bounding Box']
            layer_infos_str = "Title:\n\t" + layer_infos['Title']
            layer_infos_str += "\nAbstract:\n\t" + layer_infos['Abstract']
            layer_infos_str += "\nBounding box:"
            layer_infos_str += "\n\tminx = " + bb['minx']
            layer_infos_str += "\n\tminy = " + bb['miny']
            layer_infos_str += "\n\tmaxx = " + bb['maxx']
            layer_infos_str += "\n\tmaxy = " + bb['maxy']
            layer_infos_str += "\nKeywords:\n\t" + layer_infos['Keywords']
            self.ui.layer_detail.setText(layer_infos_str)
        self.set_ok_button()

    def set_ok_button(self):
        self.ok_button.setDisabled(
            len(self.ui.layers_lst.selectedItems()) == 0)

    def get_capabilities(self):
        wfs = '/geoserver/wfs?'
        params = ('SERVICE=WFS'
                  '&VERSION=1.0.0'
                  '&REQUEST=GetCapabilities'
                  '&SRSNAME=EPSG:4326')
        url = '%s%s%s' % (self.sv_downloader.host, wfs, params)
        result = self.sv_downloader.sess.get(url)
        if result.status_code == 200:
            self.parse_get_capabilities(result.content)
        else:
            raise SvNetworkError(
                "Unable to download layers: %s" % result.error)

    def parse_get_capabilities(self, xml):
        # this raises a IOError if the file doesn't exist
        root = ElementTree.fromstring(xml)
        layers = root.find('%sFeatureTypeList' % NS_NET_OPENGIS_WFS)

        for layer in layers:
            try:
                keywords = layer.find('%sKeywords' % NS_NET_OPENGIS_WFS).text
                if keywords is not None and 'SVIR_QGIS_Plugin' in keywords:
                    title = layer.find('%sTitle' % NS_NET_OPENGIS_WFS).text
                    layer_id = layer.find('%sName' % NS_NET_OPENGIS_WFS).text
                    abstract = layer.find(
                        '%sAbstract' % NS_NET_OPENGIS_WFS).text
                    bbox = layer.find(
                        '%sLatLongBoundingBox' % NS_NET_OPENGIS_WFS).attrib

                    self.extra_infos[layer_id] = {
                        'Title': title,
                        'Abstract': abstract,
                        'Keywords': keywords,
                        'Bounding Box': bbox}

                    # update combo box
                    item = QListWidgetItem()
                    item.setData(Qt.Qt.DisplayRole, title)
                    item.setData(Qt.Qt.ToolTipRole, layer_id)
                    self.ui.layers_lst.addItem(item)
            except AttributeError:
                continue
