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

import csv
import os
import time
import matplotlib.pyplot as plt
from collections import defaultdict

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayer
from qgis.gui import QgsMessageBar
from svir.calculations.aggregate_loss_by_zone import add_zone_id_to_points

from svir.utilities.utils import (get_ui_class,
                                  read_config_file,
                                  reload_layers_in_cbx,
                                  reload_attrib_cbx,
                                  WaitCursorManager,
                                  tr,
                                  create_progress_message_bar,
                                  clear_progress_message_bar,
                                  )
from svir.recovery_modeling.building import Building

FORM_CLASS = get_ui_class('ui_recovery_modeling.ui')

DAYS_BEFORE_EVENT = 200
SVI_WEIGHT_COEFF = 1  # FIXME: Let the user set this parameter


class RecoveryModelingDialog(QDialog, FORM_CLASS):
    """
    Modal dialog giving to perform recovery modeling analysis.

    Object-oriented Programming(OOP) is used to model post-earthquake community
    recovery of residential community.

    PAOLO: FIXME In the last version, we only have a Building class
    In this Programming, four classes are
    adopted, namely Building Class, Ground Motion FIelds Class, Constructuon &
    Enigneering Service Class and Community Class.

    In each class, a set of data and functions work together to complete a task
    which we call attributes and functions.  Attribute is used to specify if
    and how object properties are accessed within the programming environment
    Function is used to create/altere to achieve task or functionality and
    return the attributes of an object

    Procedure of this OOP Programming:
    Step 1: Define attributes of objects in each class
    Step 2: Set up functions in each class
    Step 3: Incorporate Napa Data to community recovery model

    Methodology:
    Time-based method is utilized which characterize a probability density
    function of the time it takes to a higher or lower functioning state given
    a set of explanatory variables such as the extent of damage to the
    building.
    """
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.set_ok_button()
        self.populate_approach_cbx()
        reload_layers_in_cbx(self.svi_layer_cbx, [QgsMapLayer.VectorLayer])
        recovery_modeling_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'recovery_modeling')
        self.input_data_dir = os.path.join(recovery_modeling_dir, 'input_data')
        self.output_data_dir = os.path.join(
            recovery_modeling_dir, 'output_data')
        self.dmg_by_asset_layer = self.iface.activeLayer()

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def populate_approach_cbx(self):
        self.approach_cbx.addItems(['Aggregate', 'Disaggregate'])

    @pyqtSlot(str)
    def on_approach_cbx_currentIndexChanged(self, selected_text):
        # we might need to ask the user to provide the necessary files
        pass

    @pyqtSlot(int)
    def on_svi_layer_cbx_currentIndexChanged(self, selected_index):
        self.svi_layer = self.svi_layer_cbx.itemData(selected_index)
        reload_attrib_cbx(self.svi_field_name_cbx, self.svi_layer)
        reload_attrib_cbx(self.zone_field_name_cbx, self.svi_layer)

    def generate_community_level_recovery_curve(self, integrate_svi=True):
        # Developed By: Henry Burton
        # Edited by: Hua Kang
        # Reimplemented for this plugin by: Paolo Tormene and Marco Bernasocchi
        # Objective: GenerateCommunityLevelRecoveryCurve
        # Initial date: August 26, 2016

        if integrate_svi:
            self.svi_layer = self.svi_layer_cbx.itemData(
                    self.svi_layer_cbx.currentIndex())
            self.svi_field_name = self.svi_field_name_cbx.currentText()
            self.zone_field_name = self.zone_field_name_cbx.currentText()

        start = time.clock()  # FIXME
        # Step 1: Define attributes of objects in each class

        # Define Attributes of Constructuon & Engineering Service Class

        # read configuration files
        inspectionTimes = read_config_file('InspectionTimes.txt')
        assessmentTimes = read_config_file('AssessmentTimes.txt')
        mobilizationTimes = read_config_file('MobilizationTimes.txt')
        repairTimes = read_config_file('RepairTimes.txt')
        recoveryTimes = read_config_file('RecoveryTimes.txt')
        leadTimeDispersion = read_config_file(
            'LeadTimeDispersion.txt', float)
        repairTimeDispersion = read_config_file(
            'RepairTimeDispersion.txt', float)

        # Step 3: Incorporate Napa Data to community recovery model

        # ############# MAIN #################################################
        numberOfDamageSimulations = read_config_file(
            'NumberOfDamageSimulations.txt', int)[0]

        # build dictionary zone_id -> dmg_by_asset
        zonal_dmg_by_asset = defaultdict(list)
        if integrate_svi:
            svi_by_zone = dict()
            for zone_feat in self.svi_layer.getFeatures():
                zone_id = str(zone_feat[self.zone_field_name])
                svi_value = zone_feat[self.svi_field_name]
                svi_by_zone[zone_id] = svi_value
            msg = 'Reading damage state probabilities...'
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            tot_features = self.dmg_by_asset_layer.featureCount()
            for feat_idx, dmg_by_asset_feat in enumerate(
                    self.dmg_by_asset_layer.getFeatures()):
                progress_perc = feat_idx / float(tot_features) * 100
                progress.setValue(progress_perc)
                zone_id = dmg_by_asset_feat[self.zone_field_name]
                # FIXME: hack to handle case in which the zone id is an integer
                # but it is stored as Real
                try:
                    zone_id = str(int(zone_id))
                except:
                    zone_id = str(zone_id)
                # select fields that contain probabilities
                # i.e., ignore asset id and taxonomy (first 2 items)
                # and get only columns containing means, discarding
                # those containing stddevs, therefore getting one item
                # out of two for the remaining columns
                # Also discard the last field, containing zone ids
                dmg_by_asset_probs = dmg_by_asset_feat.attributes()[
                    2:-1:2]
                zonal_dmg_by_asset[zone_id].append(dmg_by_asset_probs)
            clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        else:  # ignore svi
            msg = 'Reading damage state probabilities...'
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            tot_features = self.dmg_by_asset_layer.featureCount()
            for idx, dmg_by_asset_feat in enumerate(
                    self.dmg_by_asset_layer.getFeatures()):
                progress_perc = idx / float(tot_features) * 100
                progress.setValue(progress_perc)
                # we don't have any field containing zone ids, to be discarded
                dmg_by_asset_probs = dmg_by_asset_feat.attributes()[2::2]
                zonal_dmg_by_asset['ALL'].append(dmg_by_asset_probs)
            clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)

        tot_zones = len(zonal_dmg_by_asset)
        msg = 'Calculating zone-level recovery curves...'
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)
        # for each zone, calculate a zone-level recovery function
        for idx, zone_id in enumerate(zonal_dmg_by_asset.keys()):
            progress_perc = idx / float(tot_zones) * 100
            progress.setValue(progress_perc)

            # TODO: use svi_by_zone[zone_id] to adjust recovery times (how?)

            dmg_by_asset = zonal_dmg_by_asset[zone_id]

            (LossBasedDamageStateProbabilities,
             RecoveryBasedDamageStateProbabilities,
             fractionCollapsedAndIrreparableBuildings) = \
                self.loss_based_to_recovery_based_probs(dmg_by_asset)

            svi_value = svi_by_zone[zone_id] if integrate_svi else None
            (timeList, inspectionTimes,
             assessmentTimes, mobilizationTimes) = self.calculate_times(
                fractionCollapsedAndIrreparableBuildings, inspectionTimes,
                assessmentTimes, mobilizationTimes, repairTimes, svi_value)

            # Initialize community recovery function
            communityRecoveryFunction = [0 for x in range(len(timeList))]
            New_communityRecoveryFunction = [
                0 for x in range(len(timeList)+DAYS_BEFORE_EVENT)]

            # self.generate_building_level_recovery_curve()  # FIXME
            # Looping over all damage simulations
            for sim in range(numberOfDamageSimulations):
                # Looping over all buildings in community
                # Initialize building level recovery function
                buildingLevelRecoveryFunction = [
                    0 for x in range(len(timeList))]
                # TODO: use enumerate instead
                for bldg in range(len(LossBasedDamageStateProbabilities)):
                    # Generate recovery function for current
                    # building/simulation using the given damage state
                    # probability distribution
                    currentSimulationBuildingLevelDamageStateProbabilities = \
                        RecoveryBasedDamageStateProbabilities[bldg]
                    # call building class within Napa Data
                    # PAOLO: building number is not used. Instead, we need to
                    # make available to the building all the imported data
                    napa_bldg = Building(
                        inspectionTimes, recoveryTimes, repairTimes,
                        leadTimeDispersion, repairTimeDispersion,
                        currentSimulationBuildingLevelDamageStateProbabilities,
                        timeList, assessmentTimes, mobilizationTimes)
                    approach = self.approach_cbx.currentText()
                    # approach can be aggregate or disaggregate
                    z = napa_bldg.generateBldgLevelRecoveryFunction(approach)
                    # The following lines plot building level curves
                    # fig = plt.figure()
                    # plt.plot(timeList, z)
                    # plt.xlabel('Time (days)')
                    # plt.ylabel('Normalized recovery level')
                    # plt.title('Building level recovery curve')
                    # plt.ylim((0.0, 1.2))
                    # plt.show()
                    # Assign buidling level recovery function
                    # TODO: use enumerate instead
                    for timePoint in range(len(timeList)):
                        buildingLevelRecoveryFunction[timePoint] += z[
                            timePoint]
                # Sum up all building level recovery function
                # TODO: use enumerate instead
                for timePoint in range(len(timeList)):
                    communityRecoveryFunction[timePoint] \
                        += buildingLevelRecoveryFunction[timePoint]

            # PAOLO: instead of calculating the community level recovery
            # function on all points, we should aggregate points by the same
            # zones defined for the socioeconomic dataset, and then we should
            # produce a community recovery function for each zone.
            # This has to be done on the damage by asset layer
            # (For the aggregation we can use SAGA:
            #  "Add Polygon Attributes to Points", i.e.
            #  processing.runalg('saga:addpolygonattributestopoints', input,
            #                    polygons, field, output))

            # Calculate community level recovery function
            # TODO: use enumerate instead
            for timePoint in range(len(timeList)):
                communityRecoveryFunction[timePoint] /= \
                    numberOfDamageSimulations

            # PAOLO: should we plot this?
            # Plot community level recovery curve
            # plt.plot(timeList, communityRecoveryFunction)
            # plt.show()

            # Plot community level recovery curve which can presents the number
            # of occupants before earthquake
            New_timeList = [x for x in range(len(timeList)+DAYS_BEFORE_EVENT)]
            # TODO: use enumerate instead
            for i in range(len(timeList)+DAYS_BEFORE_EVENT):
                if i < DAYS_BEFORE_EVENT:
                    New_communityRecoveryFunction[i] = 1
                else:
                    New_communityRecoveryFunction[i] = (
                        communityRecoveryFunction[i - DAYS_BEFORE_EVENT]
                        / len(LossBasedDamageStateProbabilities))

            fig = plt.figure()
            plt.plot(New_timeList, New_communityRecoveryFunction)
            plt.xlabel('Time (days)')
            plt.ylabel('Normalized recovery level')
            plt.title('Community level recovery curve for zone %s' % zone_id)
            plt.ylim((0.0, 1.2))
            # plt.show()
            filestem = os.path.join(
                self.output_data_dir, "recovery_function_zone_%s" % zone_id)
            fig.savefig(filestem + '.png')

            # Save community recovery function
            f3 = open(filestem + '.txt', "w")
            f3.write(str(communityRecoveryFunction))
            f3.close()

            end = time.clock()
            print (end - start)
        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)

    def loss_based_to_recovery_based_probs(self, dmg_by_asset):
        LossBasedDamageStateProbabilities = [
            [0 for x in range(5)] for y in range(len(dmg_by_asset)-1)]

        for i in range(len(dmg_by_asset)-1):
            for j in range(5):
                LossBasedDamageStateProbabilities[i][j] = \
                    dmg_by_asset[i+1][j]  # was dmg_by_asset[i+1][j+4]

        # Load Transfer Probability Note: There is a 5*6 matrix where rows
        # describe loss-based damage states (No
        # damage/Slight/Moderate/Extensive/Complete) and columns present
        # recovery-based damage states(No damage/Trigger inspection/Loss
        # Function /Not Occupiable/Irreparable/Collapse). The element(i,j)
        # in the matrix is the probability of recovery-based damage state j
        # occurs given loss-based damage state i

        transferProbabilitiesData = os.path.join(
            self.input_data_dir, 'transferProbabilities.csv')

        with open(transferProbabilitiesData, 'r') as f:
            reader = csv.reader(f)
            transferProbabilities = list(reader)

        # Mapping from Loss-based to recovery-based building damage states
        RecoveryBasedDamageStateProbabilities = [
            [0 for x in range(6)] for y in range(len(dmg_by_asset)-1)]

        fractionCollapsedAndIrreparableBuildings = 0
        # TODO: use enumerate instead
        for i in range(len(LossBasedDamageStateProbabilities)):
            for j in range(len(transferProbabilities[0])):
                for s in range(len(transferProbabilities)):
                    RecoveryBasedDamageStateProbabilities[i][j] += (
                        float(LossBasedDamageStateProbabilities[i][s])
                        * float(transferProbabilities[s][j]))
                    if j == 4 or j == 5:
                        fractionCollapsedAndIrreparableBuildings += \
                            RecoveryBasedDamageStateProbabilities[i][j]

        fractionCollapsedAndIrreparableBuildings = \
            fractionCollapsedAndIrreparableBuildings / (
                len(dmg_by_asset)-1)
        return (LossBasedDamageStateProbabilities,
                RecoveryBasedDamageStateProbabilities,
                fractionCollapsedAndIrreparableBuildings)

    def calculate_times(
            self, fractionCollapsedAndIrreparableBuildings,
            inspectionTimes, assessmentTimes, mobilizationTimes,
            repairTimes, svi_value):
        # PAOLO and VENETIA: the paper refers to a metodology by Comerio
        # (2006): "a performance index can be developed to relate the
        # fraction of collapsed buildings within a particular region, and
        # used to account for delays caused by regional socioeconomic
        # effects" Since we will multiply results by a social vulnerability
        # index, we are wondering if this correction is still needed.
        # Otherwise, we can keep this, and add a further correction when we
        # take into account the socioeconomic index.

        # Compute lead time adjustment factor
        # FIXME: HB said that 0.5, 2.31 and 0.22 are parameters based on an
        # empirical equation. We could simplify the formula, if those
        # parameters don't have any clear meaning as they are
        leadTimeFactor = 0.5 * (
            2.31 + 0.22 * fractionCollapsedAndIrreparableBuildings
            * 100) / 2.31

        # Generate Time Vector Used for Recovery Function
        # Maximum time in days

        maxTime = (int(max(inspectionTimes))
                   + int(max(assessmentTimes))
                   + int(max(mobilizationTimes))
                   + int(max(repairTimes)) + DAYS_BEFORE_EVENT * 2)

        # PAOLO: I guess we could use svi_by_zone[zone_id] to adjust
        # the leadTimeFactor, for instance:
        if svi_value:
            # FIXME to build timeList we need an integer, but it sounds bad
            maxTime = int(round(maxTime * SVI_WEIGHT_COEFF * svi_value))

        # Time List
        timeList = range(maxTime)

        # Calculate lead time by mutiply lead time factor
        # TODO: use enumerate instead
        for i in range(len(inspectionTimes)):
            inspectionTimes[i] = leadTimeFactor * float(inspectionTimes[i])
            assessmentTimes[i] = leadTimeFactor * float(assessmentTimes[i])
            mobilizationTimes[i] = (
                leadTimeFactor * float(mobilizationTimes[i]))
        return (timeList, inspectionTimes, assessmentTimes, mobilizationTimes)

    def accept(self):
        if self.integrate_svi_check.isChecked():
            self.zone_field_name = self.zone_field_name_cbx.currentText()
            (_, self.dmg_by_asset_layer, self.svi_layer,
             self.zone_field_name) = add_zone_id_to_points(
                self.iface, None, self.dmg_by_asset_layer,
                self.svi_layer, None, self.zone_field_name)
        with WaitCursorManager('Generating recovery curves...', self.iface):
            self.generate_community_level_recovery_curve(
                self.integrate_svi_check.isChecked())
        self.iface.messageBar().pushMessage(
            tr("Info"),
            'Recovery curves have been saved to [%s]' % self.output_data_dir,
            level=QgsMessageBar.INFO, duration=0)
        super(RecoveryModelingDialog, self).accept()
