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

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import (QDialog,
                         QDialogButtonBox)
from qgis.core import QgsMapLayer

from svir.utilities.utils import (get_ui_class,
                                  read_config_file,
                                  reload_layers_in_cbx,
                                  reload_attrib_cbx)
from svir.recovery_modeling.building import Building

FORM_CLASS = get_ui_class('ui_recovery_modeling.ui')


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
        layer = self.svi_layer_cbx.itemData(selected_index)
        reload_attrib_cbx(self.svi_field_name_cbx, layer)
        reload_attrib_cbx(self.zone_field_name_cbx, layer)

    def generate_community_level_recovery_curve(self):
        # Developed By: Henry Burton
        # Edited by: Hua Kang
        # Adapted to work within this plugin by: Paolo Tormene
        # Objective: GenerateCommunityLevelRecoveryCurve
        # Date: August 26, 2016
        DAYS_BEFORE_EVENT = 200
        WHY_400 = DAYS_BEFORE_EVENT * 2
        WHY_231 = 2.31
        WHY_022 = 0.22
        WHY_05 = 0.5
        WHY_100 = 100
        start = time.clock()  # FIXME
        # Step 1: Define attributes of objects in each class

        # Define Attributes of Constructuon & Engineering Service Class
        recovery_modeling_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'recovery_modeling')

        input_data_dir = os.path.join(recovery_modeling_dir, 'input_data')
        output_data_dir = os.path.join(recovery_modeling_dir, 'output_data')

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

        dmgByAssetBayAreaData = os.path.join(
            input_data_dir, 'dmg_by_asset_bay_area.csv')

        # Load Loss-based damage state probabilities
        with open(dmgByAssetBayAreaData, 'r') as f:
            reader = csv.reader(f)
            dmg_by_asset_bay_area = list(reader)

        LossBasedDamageStateProbabilities = [
            [0 for x in range(5)] for y in range(len(dmg_by_asset_bay_area)-1)]

        # the header of dmg_by_asset_bay_area.csv is something like:
        # 'asset_ref', 'taxonomy', 'lon', 'lat',
        # 'probability(structural-no_damage)',
        # 'probability(structural-slight)', 'probability(structural-moderate)',
        # 'probability(structural-extensive)',
        # 'probability(structural-complete)'
        # Therefore, we need to read probabilities from the fifth column
        for i in range(len(dmg_by_asset_bay_area)-1):
            for j in range(5):
                LossBasedDamageStateProbabilities[i][j] = \
                    dmg_by_asset_bay_area[i+1][j+4]

        # Load Transfer Probability
        # Note: There is a 5*6 matrix where rows describe loss-based damage
        # states (No damage/Slight/Moderate/Extensive/Complete) and columns
        # present recovery-based damage states(No damage/Trigger
        # inspection/Loss Function /Not Occupiable/Irreparable/Collapse). The
        # element(i,j) in the matrix is the probability of recovery-based
        # damage state j occurs given loss-based damage state i

        transferProbabilitiesData = os.path.join(
            input_data_dir, 'transferProbabilities.csv')

        with open(transferProbabilitiesData, 'r') as f:
            reader = csv.reader(f)
            transferProbabilities = list(reader)

        # Mapping from Loss-based to recovery-based building damage states
        RecoveryBasedDamageStateProbabilities = [
            [0 for x in range(6)] for y in range(len(dmg_by_asset_bay_area)-1)]

        fractionCollapsedAndIrreparableBuildings = 0
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
                len(dmg_by_asset_bay_area)-1)

        # PAOLO and VENETIA: the paper refers to a metodology by Comerio
        # (2006): "a performance index can be developed to relate the fraction
        # of collapsed buildings within a particular region, and used to
        # account for delays caused by regional socioeconomic effects" Since we
        # will multiply results by a social vulnerability index, we are
        # wondering if this correction is still needed.  Otherwise, we can keep
        # this, and add a further correction when we take into account the
        # socioeconomic index.

        # Compute lead time adjustment factor
        leadTimeFactor = WHY_05 * (
            WHY_231 + WHY_022 * fractionCollapsedAndIrreparableBuildings
            * WHY_100) / WHY_231

        # Generate Time Vector Used for Recovery Function
        # Maximum time in days

        maxTime = (int(max(inspectionTimes))
                   + int(max(assessmentTimes))
                   + int(max(mobilizationTimes))
                   + int(max(repairTimes)) + WHY_400)

        # Time List
        timeList = [x for x in range(maxTime)]

        # Calculate lead time by mutiply lead time factor
        for i in range(len(inspectionTimes)):
            inspectionTimes[i] = leadTimeFactor * float(inspectionTimes[i])
            assessmentTimes[i] = leadTimeFactor * float(assessmentTimes[i])
            mobilizationTimes[i] = leadTimeFactor * float(mobilizationTimes[i])

        # Initialize community recovery function
        communityRecoveryFunction = [0 for x in range(len(timeList))]
        New_communityRecoveryFunction = [
            0 for x in range(len(timeList)+DAYS_BEFORE_EVENT)]

        # Looping over all damage simulations
        for sim in range(numberOfDamageSimulations):
            # Looping over all buildings in community
            # Initialize building level recovery function
            buildingLevelRecoveryFunction = [0 for x in range(len(timeList))]
            #for bldg in range(len(LossBasedDamageStateProbabilities)):
            for bldg in range(1):
                # Generate recovery function for current building/simulation
                # using the given damage state probability distribution
                currentSimulationBuildingLevelDamageStateProbabilities = \
                    RecoveryBasedDamageStateProbabilities[bldg]
                # call building class within Napa Data
                # PAOLO: building number is not used. Instead, we need to make
                # available to the building all the imported data
                # Napa = Building(bldg)
                napa_bldg = Building(
                    inspectionTimes, recoveryTimes, repairTimes,
                    leadTimeDispersion, repairTimeDispersion,
                    currentSimulationBuildingLevelDamageStateProbabilities,
                    timeList, assessmentTimes, mobilizationTimes)
                approach = self.approach_cbx.currentText()
                # approach can be aggregate or disaggregate
                z = napa_bldg.generateBldgLevelRecoveryFunction(approach)
                # Assign buidling level recovery function
                for timePoint in range(len(timeList)):
                    buildingLevelRecoveryFunction[timePoint] += z[timePoint]
                    # Sum up all building level recovery function
            for timePoint in range(len(timeList)):
                communityRecoveryFunction[timePoint] \
                    += buildingLevelRecoveryFunction[timePoint]

        # PAOLO: instead of calculating the community level recovery function
        # on all points, we should aggregate points by the same zones defined
        # for the socioeconomic dataset, and then we should produce a community
        # recovery function for each zone.
        # This has to be done on the damage by asset layer
        # (For the aggregation we can use SAGA:
        #  "Add Polygon Attributes to Points", i.e.
        #  processing.runalg('saga:addpolygonattributestopoints', input,
        #                    polygons, field, output))

        # Calculate community level recovery function
        for timePoint in range(len(timeList)):
            communityRecoveryFunction[timePoint] /= numberOfDamageSimulations

        # PAOLO: should we plot this?
        # Plot community level recovery curve
        # plt.plot(timeList, communityRecoveryFunction)
        # plt.show()

        # Plot community level recovery curve which can presents the number of
        # occupants before earthquake
        New_timeList = [x for x in range(len(timeList)+DAYS_BEFORE_EVENT)]
        for i in range(len(timeList)+DAYS_BEFORE_EVENT):
            if i < DAYS_BEFORE_EVENT:
                New_communityRecoveryFunction[i] = 1
            else:
                New_communityRecoveryFunction[i] = (
                    communityRecoveryFunction[i - DAYS_BEFORE_EVENT]
                    / len(LossBasedDamageStateProbabilities))

        plt.plot(New_timeList, New_communityRecoveryFunction)
        plt.xlabel('Time (days)')
        plt.ylabel('Normalized recovery level')
        plt.title('Community level recovery curve')
        plt.ylim((0.0, 1.2))
        plt.show()

        # PAOLO: what to save?
        # Save community recovery function
        f3 = open(
            os.path.join(output_data_dir,
                         "communityLevelRecoveryFunction.txt"), "w")
        f3.write(str(communityRecoveryFunction))
        f3.close()

        end = time.clock()
        print (end - start)

    def accept(self):
        if not self.integrate_svi_check.isChecked():
            self.generate_community_level_recovery_curve()
        else:
            self.generate_zone_level_recovery_curve()
            # TODO remove this return
            return
        super(RecoveryModelingDialog, self).accept()

    def generate_zone_level_recovery_curve(self):
        svi_layer = self.svi_layer_cbx.itemData(
                self.svi_layer_cbx.currentIndex())
        svi_field_name = self.svi_field_name_cbx.currentText()
        zone_field_name = self.zone_field_name_cbx.currentText()
        dmg_by_asset_layer = self.iface.activeLayer()

        # call saga