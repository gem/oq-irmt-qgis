# Developed By: Henry Burton
#
# Edited by: Hua Kang
#
# Objective: GenerateCommunityLevelRecoveryCurve
#
# Date: August 26, 2016

import csv
import os
import time
import matplotlib.pyplot as plt
from svir.recovery_modeling.building import Building

"""
Object-oriented Programming(OOP) is used to model post-earthquake community
recovery of residential community.  In this Programming, four classes are
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
   function of the time it takes to a higher or lower functioning state given a
   set of explanatory variables such as the extent of damage to the building.
"""


def plot_community_based_recovery_curve():
    start = time.clock()  # FIXME
    # Step 1: Define attributes of objects in each class

    # Define Attributes of Constructuon & Engineering Service Class

    # data_dir = os.path.join('recovery_modeling', 'input_data')
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'input_data')

    # Initialize assessment times
    inspectionTimes = []
    assessmentTimes = []
    mobilizationTimes = []
    repairTimes = []
    recoveryTimes = []

    # load assessment times
    inspectionTimesData = os.path.join(data_dir, 'InspectionTimes.txt')

    # Seperate data in different lines so that inspection time of each damage
    # state has its own line.
    for line in open(inspectionTimesData, 'r+').readlines():
        New_line = line.split()
        inspectionTimes.append(New_line[0])

    assessmentTimesData = os.path.join(data_dir, 'AssessmentTimes.txt')

    # Seperate data in different lines so that assessment time of each damage
    # state has its own line.
    for line in open(assessmentTimesData, 'r+').readlines():
        New_line = line.split()
        assessmentTimes.append(New_line[0])

    mobilizationTimesData = os.path.join(data_dir, 'MobilizationTimes.txt')

    # Seperate data in different lines so that mobilization time of each damage
    # state has its own line.
    for line in open(mobilizationTimesData, 'r+').readlines():
        New_line = line.split()
        mobilizationTimes.append(New_line[0])

    repairTimesData = os.path.join(data_dir, 'RepairTimes.txt')

    # Seperate data in different lines so that mobilization time of each damage
    # state has its own line.
    for line in open(repairTimesData, 'r+').readlines():
        New_line = line.split()
        repairTimes.append(New_line[0])

    recoveryTimesData = os.path.join(data_dir, 'RecoveryTimes.txt')

    # Seperate data in different lines so that mobilization time of each damage
    # state has its own line.
    for line in open(recoveryTimesData, 'r+').readlines():
        New_line = line.split()
        recoveryTimes.append(New_line[0])

    # PAOLO: remove
    # # Initialize lead time dispersion
    # leadTimeDispersion = []

    # Load lead time dispersion
    leadTimeDispersionData = os.path.join(data_dir, 'LeadTimeDispersion.txt')

    for line in open(leadTimeDispersionData, 'r+').readlines():
        leadTimeDispersion = float(line.split()[0])

    # Initialize repair time dispersion
    repairTimeDispersion = []

    # Load repair time dispersion
    repairTimeDispersionData = os.path.join(
        data_dir, 'RepairTimeDispersion.txt')

    for line in open(repairTimeDispersionData, 'r+').readlines():
        repairTimeDispersion = float(line.split()[0])

    # Step 3: Incorporate Napa Data to community recovery model

    # ############# MAIN ###################################################

    # Initialize number of damage simulations
    numberOfDamageSimulations = []

    # Load number of damage simulations
    numberOfDamageSimulationsData = os.path.join(
        data_dir, 'NumberOfDamageSimulations.txt')

    for line in open(numberOfDamageSimulationsData, 'r+').readlines():
        numberOfDamageSimulations = int(line.split()[0])

    dmgByAssetBayAreaData = os.path.join(
        data_dir, 'dmg_by_asset_bay_area.csv')

    # Load Loss-based damage state probabilities
    with open(dmgByAssetBayAreaData, 'r') as f:
        reader = csv.reader(f)
        dmg_by_asset_bay_area = list(reader)

    LossBasedDamageStateProbabilities = [
        [0 for x in range(5)] for y in range(len(dmg_by_asset_bay_area)-1)]

    for i in range(len(dmg_by_asset_bay_area)-1):
        for j in range(5):
            LossBasedDamageStateProbabilities[i][j] = dmg_by_asset_bay_area[
                i+1][j+4]

    # Load Transfer Probability
    # Note: There is a 5*6 matrix where rows describe loss-based damage states
    # (No damage/Slight/Moderate/Extensive/Complete) and columns present
    # recovery-based damage states(No damage/Trigger inspection/Loss Function
    # /Not Occupiable/Irreparable/Collapse). The element(i,j) in the matrix is
    # the probability of recovery-based damage state j occurs given loss-based
    # damage state i

    transferProbabilitiesData = os.path.join(
        data_dir, 'transferProbabilities.csv')

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
            # Generate recovery function for current building/simulation using
            # the given damage state probability distribution
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
                timeList)
            # PAOLO: which approach? Disaggregation or aggregation?
            # Call for
            # disaggregateApproachToGenerateBuildingLevelRecoveryFunctions
            # in building class
            # z = Napa.disaggregateApproachToGenerateBuildingLevelRecoveryFunctions()

            # Call for
            # aggregateApproachToGenerateBuildingLevelRecoveryFunctions in
            # building class
            z = Napa.aggregateApproachToGenerateBuildingLevelRecoveryFunctions()

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
        os.path.join(data_dir, "communityLevelRecoveryFunction.txt"), "w")
    f3.write(str(communityRecoveryFunction))
    f3.close()

    end = time.clock()
    print (end - start)
