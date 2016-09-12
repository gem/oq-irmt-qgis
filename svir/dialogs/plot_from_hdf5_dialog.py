
# -*- coding: utf-8 -*-
#/***************************************************************************
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

import os
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsPoint,
                       QgsGeometry,
                       QgsMapLayerRegistry,
                       QgsSymbolV2,
                       QgsSymbolLayerV2Registry,
                       QgsOuterGlowEffect,
                       QgsSingleSymbolRendererV2,
                       QgsVectorGradientColorRampV2,
                       QgsGraduatedSymbolRendererV2,
                       QgsRendererRangeV2,
                       QgsProject,
                       )
from PyQt4.QtCore import pyqtSlot, QDir

from PyQt4.QtGui import (QDialogButtonBox,
                         QDialog,
                         QFileDialog,
                         QColor,
                         QComboBox,
                         QSpinBox,
                         QLabel,
                         QCheckBox,
                         )

from openquake.baselib import hdf5

from svir.utilities.shared import DEBUG
from svir.utilities.utils import (LayerEditingManager,
                                  WaitCursorManager,
                                  get_ui_class,
                                  )
from svir.calculations.calculate_utils import (add_numeric_attribute,
                                               add_textual_attribute,
                                               )

FORM_CLASS = get_ui_class('ui_load_hdf5_as_layer.ui')


class PlotFromHdf5Dialog(QDialog, FORM_CLASS):
    """
    Modal dialog to plot total damage or damage by taxonomy from a hdf5 file
    obtained by a scenario damage calculation performed by the oq-engine
    """
    def __init__(self, iface, output_type, hdf5_path=None):
        # sanity check
        if output_type not in (
                'dmg_total', 'dmg_by_taxon'):
            raise NotImplementedError(output_type)
        self.iface = iface
        self.hdf5_path = hdf5_path
        self.hfile = None
        self.output_type = output_type
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)
        # Disable ok_button until all comboboxes are filled
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setDisabled(True)
        self.open_hdfview_btn.setDisabled(True)
        self.define_gui_elements()
        self.adjust_gui_for_output_type()
        if self.hdf5_path:
            self.hdf5_path_le.setText(self.hdf5_path)
            self.hfile = self.get_hdf5_file_handler()
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
            self.setWindowTitle('Plot total damage from HDF5')
        elif self.output_type == 'dmg_by_taxon':
            self.setWindowTitle('Plot damage by taxonomy from HDF5')
        self.verticalLayout.addWidget(self.rlz_lbl)
        self.verticalLayout.addWidget(self.rlz_cbx)
        self.verticalLayout.addWidget(self.loss_type_lbl)
        self.verticalLayout.addWidget(self.loss_type_cbx)
        self.verticalLayout.addWidget(self.exclude_no_dmg_lbl)
        self.verticalLayout.addWidget(self.exclude_no_dmg_ckb)
        self.adjustSize()


    @pyqtSlot(str)
    def on_hdf5_path_le_textChanged(self):
        self.open_hdfview_btn.setDisabled(
            self.hdf5_path_le.text() == '')

    @pyqtSlot()
    def on_open_hdfview_btn_clicked(self):
        file_path = self.hdf5_path_le.text()
        if file_path:
            to_run = "hdfview " + file_path
            # FIXME make system independent
            os.system(to_run)

    @pyqtSlot()
    def on_file_browser_tbn_clicked(self):
        self.hdf5_path = self.open_file_dialog()

    # def on_rlz_changed(self):
    #     self.dataset = self.hdata.get(self.rlz_cbx.currentText())

    def on_loss_type_changed(self):
        self.loss_type = self.loss_type_cbx.currentText()
        self.set_ok_button()

    def open_file_dialog(self):
        """
        Open a file dialog to select the data file to be loaded
        """
        text = self.tr('Select oq-engine output to import')
        filters = self.tr('HDF5 files (*.hdf5)')
        hdf5_path = QFileDialog.getOpenFileName(
            self, text, QDir.homePath(), filters)
        if hdf5_path:
            self.hdf5_path = hdf5_path
            self.hdf5_path_le.setText(self.hdf5_path)
            self.hfile = self.get_hdf5_file_handler()
            self.populate_rlz_cbx()
            self.populate_loss_type_cbx()

    def get_hdf5_file_handler(self):
        # FIXME: will the file be closed correctly?
        # with hdf5.File(self.hdf5_path, 'r') as hf:
        return hdf5.File(self.hdf5_path, 'r')

    def populate_rlz_cbx(self):
        pass

    def populate_loss_type_cbx(self):
        self.loss_types = self.hfile.get(self.output_type).dtype.names
        self.loss_type_cbx.clear()
        self.loss_type_cbx.setEnabled(True)
        self.loss_type_cbx.addItems(self.loss_types)

    def set_ok_button(self):
        self.ok_button.setEnabled(self.loss_type_cbx.currentIndex() != -1)

    def plot_dmg_total(self, loss_type, dmg_states):
        self.dataset = self.hfile.get('dmg_total')
        means = self.dataset[loss_type]['mean'].tolist()[0]
        stddevs = self.dataset[loss_type]['stddev'].tolist()[0]
        if self.exclude_no_dmg_ckb.isChecked():
            # exclude the first element, that is 'no damage'
            means = means[1:]
            stddevs = stddevs[1:]
            dmg_states = dmg_states[1:]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ## the data
        N = len(means)
        ## necessary variables
        ind = np.arange(N)                # the x locations for the groups
        width = 0.35                      # the width of the bars
        ## the bars
        rects1 = ax.bar(ind, means, width,
                        color='white',
                        yerr=stddevs,
                        error_kw=dict(elinewidth=2,ecolor='black'))
        # axes and labels
        # ax.set_xlim(-width,len(ind)+width)
        ax.set_xlim(-width,len(ind))
        # ax.set_ylim(0, 45)
        ax.set_xlabel('Damage state')
        ax.set_ylabel('Number of assets in damage state')
        ax.set_title('Damage distribution (all taxonomies)')
        xTickMarks = dmg_states
        # ax.set_xticks(ind+width)
        ax.set_xticks(ind + width/2.)
        xtickNames = ax.set_xticklabels(xTickMarks)
        # plt.setp(xtickNames, rotation=45, fontsize=10)
        ## add a legend
        # ax.legend( (rects1[0], ), ('Men', ) )
        plt.show()

    def plot_dmg_by_taxon(self, loss_type, dmg_states):
        taxonomies = self.hfile.get('assetcol/taxonomies').value.tolist()
        # discard stddev (do not show error bars)
        dmg_by_taxon = self.hfile.get('dmg_by_taxon')[loss_type]['mean']
        # build a 3d plot, where:
        # x: damage states
        # y: taxonomies
        # z: damage fractions
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # for taxonomy_id, dmg in enumerate(dmg_by_taxon):
        #     taxonomy = taxonomies[taxonomy_id]
        #     ax.bar(ta)
        # for taxonomy_id, taxonomy in enumerate(taxonomies):
        for taxonomy_id, dmg in enumerate(dmg_by_taxon):
            for dmg_state_id, dmg_state in enumerate(dmg_states):
                # the 0 is to workaround a strange structure in the data
                dmg_fraction = dmg_by_taxon[taxonomy_id][0][dmg_state_id]
                ax.bar(dmg_state_id, dmg_fraction,
                    zs=range(len(taxonomies)), zdir='y', alpha=0.8)
        ax.set_xlabel('Damage States')
        ax.set_ylabel('Taxonomies')
        ax.set_zlabel('Damage Fractions')
        ax.set_title('Damage Distribution')
        plt.show()

    def accept(self):
        loss_type = self.loss_type_cbx.currentText()
        dmg_states = self.hfile.get('composite_risk_model').attrs[
            'damage_states'].tolist()
        if self.output_type == 'dmg_total':
            self.plot_dmg_total(loss_type, dmg_states)
        elif self.output_type == 'dmg_by_taxon':
            self.plot_dmg_by_taxon(loss_type, dmg_states)
        self.hfile.close()
        super(PlotFromHdf5Dialog, self).accept()

    # FIXME: also cancel should close the hdf5 file
