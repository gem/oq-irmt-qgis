# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2016-06-29
#        copyright            : (C) 2016 by GEM Foundation
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

from qgis.PyQt.QtWebKit import QWebPage
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDialog, QDialogButtonBox
from third_party import requests
from svir.utilities.utils import get_ui_class

FORM_CLASS = get_ui_class('ui_ipt.ui')


class IptDialog(QDialog, FORM_CLASS):
    """Docstring for IptDialog. """

    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        qurl = QUrl(
            # 'https://platform.openquake.org/ipt')
            # FIXME: loading a page that offers a link to download a small txt
            'http://www.sample-videos.com/download-sample-text-file.php')
        self.web_view.setUrl(qurl)

        # downloadRequested(QNetworkRequest) is a signal that is triggered in
        # the web page when the user right-clicks on a link and chooses "save
        # link as". Instead of proceeding with the normal workflow (asking the
        # user where to save the file) the control is passed to self.download,
        # that retrieves the file and prints its contents
        self.web_view.page().downloadRequested.connect(
            self.handle_downloadRequested)

        # NOTE: without the following line, linkClicked is not emitted, but
        # we would need to delegate only one specific link!
        self.web_view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.web_view.page().linkClicked.connect(self.handle_linkClicked)

        self.web_view.page().linkHovered.connect(self.handle_linkHovered)

    def handle_downloadRequested(self, request):
        print('Downloaded file:')
        resp = requests.get(request.url().toString())
        print(resp.content)

    def handle_linkClicked(self, url):
        print('Downloaded file:')
        resp = requests.get(url.toString())
        print(resp.content)

    def handle_linkHovered(self, link, title, text_content):
        print(link)

    def on_set_example_btn_clicked(self):
        qurl = QUrl(
            'https://platform.openquake.org/ipt/?tab_id=1&example_id=99')
        self.web_view.setUrl(qurl)

    def on_back_btn_clicked(self):
        self.web_view.back()
