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

from svir.utilities.utils import get_ui_class
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

    def set_ok_button(self):
        self.ok_button.setEnabled(True)

    def populate_approach_cbx(self):
        self.approach_cbx.addItems(['Aggregated', 'Disaggregated'])

    @pyqtSlot(str)
    def on_approach_cbx_currentIndexChanged(self):
        # we might need to ask the user to provide the necessary files
        pass

    def generate_community_level_recovery_curve(self):
        # Developed By: Henry Burton
        # Edited by: Hua Kang
        # Adapted to work within this plugin by: Paolo Tormene
        # Objective: GenerateCommunityLevelRecoveryCurve
        # Date: August 26, 2016
        start = time.clock()  # FIXME
        # Step 1: Define attributes of objects in each class

        # Define Attributes of Constructuon & Engineering Service Class
        recovery_modeling_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'recovery_modeling')

        input_data_dir = os.path.join(recovery_modeling_dir, 'input_data')
        output_data_dir = os.path.join(recovery_modeling_dir, 'output_data')

        # Initialize assessment times
        inspectionTimes = []
        assessmentTimes = []
        mobilizationTimes = []
        repairTimes = []
        recoveryTimes = []

        # load assessment times
        inspectionTimesData = os.path.join(
            input_data_dir, 'InspectionTimes.txt')

        # Seperate data in different lines so that inspection time of each
        # damage state has its own line.
        for line in open(inspectionTimesData, 'r+').readlines():
            New_line = line.split()
            inspectionTimes.append(New_line[0])

        assessmentTimesData = os.path.join(
            input_data_dir, 'AssessmentTimes.txt')

        # Seperate data in different lines so that assessment time of each
        # damage state has its own line.
        for line in open(assessmentTimesData, 'r+').readlines():
            New_line = line.split()
            assessmentTimes.append(New_line[0])

        mobilizationTimesData = os.path.join(
            input_data_dir, 'MobilizationTimes.txt')

        # Seperate data in different lines so that mobilization time of each
        # damage state has its own line.
        for line in open(mobilizationTimesData, 'r+').readlines():
            New_line = line.split()
            mobilizationTimes.append(New_line[0])

        repairTimesData = os.path.join(input_data_dir, 'RepairTimes.txt')

        # Seperate data in different lines so that mobilization time of each
        # damage state has its own line.
        for line in open(repairTimesData, 'r+').readlines():
            New_line = line.split()
            repairTimes.append(New_line[0])

        recoveryTimesData = os.path.join(input_data_dir, 'RecoveryTimes.txt')

        # Seperate data in different lines so that mobilization time of each
        # damage state has its own line.
        for line in open(recoveryTimesData, 'r+').readlines():
            New_line = line.split()
            recoveryTimes.append(New_line[0])

        # Load lead time dispersion
        leadTimeDispersionData = os.path.join(
            input_data_dir, 'LeadTimeDispersion.txt')

        for line in open(leadTimeDispersionData, 'r+').readlines():
            leadTimeDispersion = float(line.split()[0])

        # Load repair time dispersion
        repairTimeDispersionData = os.path.join(
            input_data_dir, 'RepairTimeDispersion.txt')

        for line in open(repairTimeDispersionData, 'r+').readlines():
            repairTimeDispersion = float(line.split()[0])

        # Step 3: Incorporate Napa Data to community recovery model

        # ############# MAIN #################################################

        # Initialize number of damage simulations
        numberOfDamageSimulations = []

        # Load number of damage simulations
        numberOfDamageSimulationsData = os.path.join(
            input_data_dir, 'NumberOfDamageSimulations.txt')

        for line in open(numberOfDamageSimulationsData, 'r+').readlines():
            numberOfDamageSimulations = int(line.split()[0])

        dmgByAssetBayAreaData = os.path.join(
            input_data_dir, 'dmg_by_asset_bay_area.csv')

        # Load Loss-based damage state probabilities
        with open(dmgByAssetBayAreaData, 'r') as f:
            reader = csv.reader(f)
            dmg_by_asset_bay_area = list(reader)

        LossBasedDamageStateProbabilities = [
            [0 for x in range(5)] for y in range(len(dmg_by_asset_bay_area)-1)]

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

        for i in range(len(LossBasedDamageStateProbabilities)):
            for j in range(len(transferProbabilities[0])):
                for s in range(len(transferProbabilities)):
                    RecoveryBasedDamageStateProbabilities[i][j] += float(
                        LossBasedDamageStateProbabilities[i][s]) \
                        * float(transferProbabilities[s][j])

        # PAOLO: adjusted or not?
        # Compute lead time adjustment factor
        # leadTimeFactor = 0.5 * (
        #     2.31 + 0.22*fractionCollapsedAndIrreparableBuildings*100)/2.31;
        leadTimeFactor = 1.0
        # Generate Time Vector Used for Recovery Function
        # Maximum time in days

        maxTime = (int(max(inspectionTimes))
                   + int(max(assessmentTimes))
                   + int(max(mobilizationTimes))
                   + int(max(repairTimes)) + 400)

        # Time List
        timeList = [x for x in range(maxTime)]

        # Calculate lead time by mutiply lead time factor
        for i in range(len(inspectionTimes)):
            inspectionTimes[i] = leadTimeFactor * float(inspectionTimes[i])
            assessmentTimes[i] = leadTimeFactor * float(assessmentTimes[i])
            mobilizationTimes[i] = leadTimeFactor * float(mobilizationTimes[i])

        # Initialize community recovery function
        communityRecoveryFunction = [0 for x in range(len(timeList))]
        New_communityRecoveryFunction = [0 for x in range(len(timeList)+200)]

        # Looping over all damage simulations
        for sim in range(numberOfDamageSimulations):
            # Looping over all buildings in community
            # Initialize building level recovery function
            buildingLevelRecoveryFunction = [0 for x in range(len(timeList))]
            for bldg in range(len(LossBasedDamageStateProbabilities)):
                # Generate recovery function for current building/simulation
                # using the given damage state probability distribution
                currentSimulationBuildingLevelDamageStateProbabilities = \
                    RecoveryBasedDamageStateProbabilities[bldg]
                # call building class within Napa Data
                # PAOLO: building number is not used. Instead, we need to make
                # available to the building all the imported data
                # Napa = Building(bldg)
                Napa = Building(
                    inspectionTimes, recoveryTimes, repairTimes,
                    leadTimeDispersion, repairTimeDispersion,
                    currentSimulationBuildingLevelDamageStateProbabilities,
                    timeList, assessmentTimes, mobilizationTimes)
                approach = self.approach_cbx.currentText()
                if approach == 'Disaggregated':
                    # Call for
                    # disaggregateApproachToGenerateBuildingLevelRecoveryFunctions
                    # in building class
                    z = Napa.disaggregateApproachToGenerateBuildingLevelRecoveryFunctions()
                elif approach == 'Aggregated':
                    # Call for
                    # aggregateApproachToGenerateBuildingLevelRecoveryFunctions in
                    # building class
                    z = Napa.aggregateApproachToGenerateBuildingLevelRecoveryFunctions()
                else:
                    raise NotImplementedError(approach)
                # Assign buidling level recovery function
                for timePoint in range(len(timeList)):
                    buildingLevelRecoveryFunction[timePoint] += z[timePoint]
                    # Sum up all building level recovery function
            for timePoint in range(len(timeList)):
                communityRecoveryFunction[timePoint] \
                    += buildingLevelRecoveryFunction[timePoint]

        # Calculate community level recovery function
        for timePoint in range(len(timeList)):
            communityRecoveryFunction[timePoint] /= numberOfDamageSimulations

        # PAOLO: should we plot this?
        # Plot community level recovery curve
        # plt.plot(timeList, communityRecoveryFunction)
        # plt.show()

        # Plot community level recovery curve which can presents the number of
        # occupants before earthquake
        New_timeList = [x for x in range(len(timeList)+200)]
        for i in range(len(timeList)+200):
            if i < 200:
                New_communityRecoveryFunction[i] = 1
            else:
                New_communityRecoveryFunction[i] = communityRecoveryFunction[
                    i - 200] / len(LossBasedDamageStateProbabilities)

        plt.plot(New_timeList, New_communityRecoveryFunction)
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
        self.generate_community_level_recovery_curve()
        super(RecoveryModelingDialog, self).accept()
