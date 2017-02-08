
# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014 by GEM Foundation
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

import numpy
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (works by side effect)
import matplotlib.pyplot as plt
from PyQt4.QtCore import pyqtSlot, QDir, QSettings, QFileInfo

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QComboBox,
                         QLabel,
                         QCheckBox,
                         )

from svir.utilities.utils import get_ui_class

FORM_CLASS = get_ui_class('ui_load_npz_as_layer.ui')


class PlotFromNpzDialog(QDialog, FORM_CLASS):
    """
    Modal dialog to plot total damage or damage by taxonomy from a npz file
    obtained by a scenario damage calculation performed by the oq-engine
    """
    def __init__(self, iface, output_type, npz_path=None):
        # sanity check
        if output_type not in (
                'dmg_total', 'dmg_by_taxon'):
            raise NotImplementedError(output_type)
        self.iface = iface
        self.npz_path = npz_path
        self.npz_file = None
        self.output_type = output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.define_gui_elements()
        self.adjust_gui_for_output_type()
        if self.npz_path:
            self.npz_path_le.setText(self.npz_path)
            self.npz_file = self.get_npz_file_handler()
            self.populate_rlz_cbx()
            self.populate_loss_type_cbx()
            self.set_ok_button()
        self.default_field_name = None

    def define_gui_elements(self):
        self.rlz_lbl = QLabel('Realization (different realizations'
                              ' will be loaded into separate layer groups)')
        self.rlz_cbx = QComboBox()
        self.rlz_cbx.setEnabled(False)
        # self.rlz_cbx.currentIndexChanged['QString'].connect(
        #     self.on_rlz_changed)
        self.loss_type_lbl = QLabel(
            'Loss Type (used for default styling)')
        self.loss_type_cbx = QComboBox()
        self.loss_type_cbx.setEnabled(False)
        self.loss_type_cbx.currentIndexChanged['QString'].connect(
            self.on_loss_type_changed)
        self.exclude_no_dmg_lbl = QLabel('Exclude "no damage"')
        self.exclude_no_dmg_ckb = QCheckBox()
        self.exclude_no_dmg_ckb.setChecked(True)

    def adjust_gui_for_output_type(self):
        if self.output_type == 'dmg_total':
            self.setWindowTitle('Plot total damage from NPZ')
        elif self.output_type == 'dmg_by_taxon':
            self.setWindowTitle('Plot damage by taxonomy from NPZ')
        self.verticalLayout.addWidget(self.rlz_lbl)
        self.verticalLayout.addWidget(self.rlz_cbx)
        self.verticalLayout.addWidget(self.loss_type_lbl)
        self.verticalLayout.addWidget(self.loss_type_cbx)
        self.verticalLayout.addWidget(self.exclude_no_dmg_lbl)
        self.verticalLayout.addWidget(self.exclude_no_dmg_ckb)
        self.adjustSize()

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.npz_path = self.open_file_dialog()

    def on_loss_type_changed(self):
        self.loss_type = self.loss_type_cbx.currentText()
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select oq-engine output to import')
        filters = self.tr('NPZ files (*.npz)')
        default_dir = QSettings().value('irmt/load_as_layer_dir',
                                        QDir.homePath())
        npz_path = QFileDialog.getOpenFileName(
            self, text, default_dir, filters)
        if npz_path:
            selected_dir = QFileInfo(npz_path).dir().path()
            QSettings().setValue('irmt/load_as_layer_dir', selected_dir)
            self.npz_path = npz_path
            self.npz_path_le.setText(self.npz_path)
            self.npz_file = self.get_npz_file_handler()
            self.populate_rlz_cbx()
            self.populate_loss_type_cbx()

    def get_npz_file_handler(self):
        return numpy.load(self.npz_path, 'r')

    def populate_rlz_cbx(self):
        pass

    def populate_loss_type_cbx(self):
        self.loss_types = self.npz_file[self.output_type].dtype.names
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(self.loss_types)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.loss_type_cbx.currentIndex() != -1)

    def plot_taxonomy_damage_dist(self, loss_type, dmg_states):
        '''
        Plots the damage distribution for the specified taxonomies
        '''
        taxonomies = self.npz_file['assetcol/taxonomies'].value.tolist()
        # discard stddev (do not show error bars)
        dmg_by_taxon = self.npz_file['dmg_by_taxon'][loss_type]['mean']
        if self.exclude_no_dmg_ckb.isChecked():
            # exclude the first element, that is 'no damage'
            dmg_states = dmg_states[1:]
        # build a 3d plot, where:
        # x: damage states
        # y: taxonomies
        # z: damage fractions
        indX = numpy.arange(len(dmg_states))  # the x locations for the groups
        indZ = numpy.arange(len(taxonomies))  # the y locations for the groups
        bar_width = 0.3
        padding_left = 0

        fig = plt.figure(figsize=(16, 9))
        ax = fig.add_subplot(111, projection='3d')
        bar_width = 0.5

        for z, dmg_dist in enumerate(dmg_by_taxon):
            dmg_dist = dmg_dist[0]  # nested structure
            if self.exclude_no_dmg_ckb.isChecked():
                # exclude the first element, that is 'no damage'
                dmg_dist = dmg_dist[1:]
            ys = dmg_dist
            ax.bar(indX, height=ys, zs=z, zdir='y', width=bar_width,
                   color='IndianRed', linewidth=1.5, alpha=0.6)

        ax.set_xticks(indX+padding_left+bar_width/2, minor=False)
        ax.set_xticklabels(dmg_states)
        ax.set_xlabel('Damage States', fontsize=16)

        ax.set_yticks(indZ+1, minor=False)
        ax.set_yticklabels(taxonomies)
        ax.set_ylabel('Taxonomies', fontsize=16)

        ax.set_zlabel('Damage Fractions', fontsize=16)
        plt.title('Damage distribution by taxonomy', fontsize=20)

        plt.show()

    def plot_total_damage_dist(self, loss_type, dmg_states):
        '''
        Plots the total damage distribution
        '''
        self.dataset = self.npz_file['dmg_total']
        means = self.dataset[loss_type]['mean'].tolist()[0]
        stddevs = self.dataset[loss_type]['stddev'].tolist()[0]
        if self.exclude_no_dmg_ckb.isChecked():
            # exclude the first element, that is 'no damage'
            means = means[1:]
            stddevs = stddevs[1:]
            dmg_states = dmg_states[1:]

        indX = numpy.arange(len(dmg_states))  # the x locations for the groups
        # indZ = numpy.arange(len(taxonomies))  #   y locations for the groups
        error_config = {'ecolor': '0.3', 'linewidth': '2'}
        bar_width = 0.3
        padding_left = 0

        plt.figure(figsize=(16, 9))

        plt.bar(indX+padding_left, height=means, width=bar_width,
                yerr=stddevs, error_kw=error_config, color='IndianRed',
                linewidth=1.5, alpha=0.6)
        plt.title('Damage distribution (all taxonomies)', fontsize=20)
        plt.xlabel('Damage state', fontsize=16)
        plt.ylabel('Number of assets in damage state', fontsize=16)
        plt.xticks(indX+padding_left+bar_width/2., dmg_states)
        plt.margins(.25, 0)
        plt.show()

    def accept(self):
        loss_type = self.loss_type_cbx.currentText()
        crm = numpy.load(self.npz_file, 'composite_risk_model')
        dmg_states = crm.attrs['damage_states'].tolist()
        if self.output_type == 'dmg_total':
            # self.plot_dmg_total(loss_type, dmg_states)
            self.plot_total_damage_dist(loss_type, dmg_states)
        elif self.output_type == 'dmg_by_taxon':
            # self.plot_dmg_by_taxon(loss_type, dmg_states)
            self.plot_taxonomy_damage_dist(loss_type, dmg_states)
        self.npz_file.close()
        super(PlotFromNpzDialog, self).accept()

    # FIXME: also cancel should close the npz file
