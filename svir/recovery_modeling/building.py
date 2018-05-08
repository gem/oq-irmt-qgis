from builtins import range
from builtins import object
import random
import math
from qgis.PyQt.QtCore import QSettings
from svir.utilities.shared import RECOVERY_DEFAULTS
from svir.utilities.utils import get_layer_setting

from svir import IS_SCIPY_INSTALLED
if IS_SCIPY_INSTALLED:
    from scipy.stats import norm


class Building(object):

    def __init__(self, iface, inspectionTimes, recoveryTimes, repairTimes,
                 currentDamageStateProbabilities, timeList, assessmentTimes,
                 mobilizationTimes):
        self.inspectionTimes = inspectionTimes
        self.recoveryTimes = recoveryTimes
        self.repairTimes = repairTimes
        self.currentDamageStateProbabilities = currentDamageStateProbabilities
        self.timeList = timeList
        self.assessmentTimes = assessmentTimes
        self.mobilizationTimes = mobilizationTimes
        self.iface = iface
        self.layer = self.iface.activeLayer()
        # PAOLO: how many of these files whould be read from here?
        self.leadTimeDispersion = get_layer_setting(
            self.layer, 'lead_time_dispersion')
        if self.leadTimeDispersion is None:
            self.leadTimeDispersion = float(QSettings().value(
                'irmt/lead_time_dispersion',
                RECOVERY_DEFAULTS['lead_time_dispersion']))
        self.repairTimeDispersion = get_layer_setting(
            self.layer, 'repair_time_dispersion')
        if self.repairTimeDispersion is None:
            self.repairTimeDispersion = float(QSettings().value(
                'irmt/repair_time_dispersion',
                RECOVERY_DEFAULTS['repair_time_dispersion']))

    def generateBldgLevelRecoveryFunction(self, approach, seed=None):
        if approach == 'Disaggregate':
            return \
                self._disaggregateBuildingLevelRecoveryFunction(seed)
        elif approach == 'Aggregate':
            return self._aggregateBuildingLevelRecoveryFunction(seed)
        else:
            raise NotImplementedError(approach)

    def _aggregateBuildingLevelRecoveryFunction(self, seed):
        # Simulate lead time dispersions
        if seed is not None:
            random.seed(seed)
        randomNumber = random.random()
        # Simulate lead times
        simulateRecoveryTimes = []
        for i in range(len(self.inspectionTimes)):
            simulateRecoveryTimes.append("")
        # Calculate simulated inspection time/assessment time/mobilization time
        # based on lead time dispersion
        for i in range(len(self.recoveryTimes)):
            if int(self.repairTimes[i]) > 0:
                simulateRecoveryTimes[i] = math.exp(
                    norm.ppf(randomNumber,
                             loc=math.log(float(self.recoveryTimes[i])),
                             scale=self.repairTimeDispersion))
            else:
                simulateRecoveryTimes[i] = 0
        # Inititalize array that stores the recovery function
        Functionality = [[0 for x in range(len(self.inspectionTimes))]
                         for y in range(len(self.timeList))]
        buildingLevelRecoveryFunction = [0 for x in range(len(self.timeList))]

        # Loop over time array and solve for functionality
        for i in range(len(self.timeList)):
            expectedFunctionality = 0
            # Loop over number of damage states
            for j in range(len(self.inspectionTimes)):
                if i < simulateRecoveryTimes[j]:
                    Functionality[i][j] = 0
                else:
                    Functionality[i][j] = 1
                expectedFunctionality += (
                    Functionality[i][j]
                    * self.currentDamageStateProbabilities[j])
            # Expected functionality
            buildingLevelRecoveryFunction[i] = expectedFunctionality
        return buildingLevelRecoveryFunction

    def _disaggregateBuildingLevelRecoveryFunction(self, seed):
        # PAOLO: moved leadTimeDispersion and repairTimeDispersion to the
        # building init

        # Simulate lead time dispersions
        if seed is not None:
            random.seed(seed)
        randomNumber = random.random()

        # Simulate lead times
        simulateInspectionTimes = []
        simulateAssessmentTimes = []
        simulateMobilizationTimes = []
        simulateRepairTimes = []

        for i in range(len(self.inspectionTimes)):
            simulateInspectionTimes.append("")
            simulateAssessmentTimes.append("")
            simulateMobilizationTimes.append("")
            simulateRepairTimes.append("")

        # Calculate simulated inspection time/assessment time/mobilization time
        # based on lead time dispersion
        for i in range(len(self.inspectionTimes)):
            if int(self.inspectionTimes[i]) > 0:
                simulateInspectionTimes[i] = math.exp(
                    norm.ppf(randomNumber,
                             loc=math.log(float(self.inspectionTimes[i])),
                             scale=self.leadTimeDispersion))
            else:
                simulateInspectionTimes[i] = 0
            if int(self.assessmentTimes[i]) > 0:
                simulateAssessmentTimes[i] = math.exp(
                    norm.ppf(randomNumber,
                             loc=math.log(float(self.assessmentTimes[i])),
                             scale=self.leadTimeDispersion))
            else:
                simulateAssessmentTimes[i] = 0
            if int(self.mobilizationTimes[i]) > 0:
                simulateMobilizationTimes[i] = math.exp(
                    norm.ppf(randomNumber,
                             loc=math.log(float(self.mobilizationTimes[i])),
                             scale=self.leadTimeDispersion))
            else:
                simulateMobilizationTimes[i] = 0
            if int(self.repairTimes[i]) > 0:
                simulateRepairTimes[i] = math.exp(
                    norm.ppf(randomNumber,
                             loc=math.log(float(self.repairTimes[i])),
                             scale=self.repairTimeDispersion))
            else:
                simulateRepairTimes[i] = 0

        # Inititalize array that stores the recovery function
        Functionality = [[0 for x in range(len(self.inspectionTimes))]
                         for y in range(len(self.timeList))]
        buildingLevelRecoveryFunction = [0 for x in range(len(self.timeList))]

        # Loop over time array and solve for functionality
        for i in range(len(self.timeList)):
            expectedFunctionality = 0
            # Loop over number of damage states
            for j in range(len(self.inspectionTimes)):
                # Functionality for Inspection damage state
                if j == 0:
                    Functionality[i][j] = 1
                elif j == 1:
                    if i < simulateInspectionTimes[j]:
                        Functionality[i][j] = 0
                    else:
                        Functionality[i][j] = 1
                # Functionality for Loss Function or NotOccupiable damage state
                elif j == 2 or j == 3:
                    if i < (simulateInspectionTimes[j]
                            + simulateAssessmentTimes[j]
                            + simulateMobilizationTimes[j]
                            + simulateRepairTimes[j]):
                        Functionality[i][j] = 0
                    else:
                        Functionality[i][j] = 1
                # Functionality for Irreparable damage state
                elif j == 4:
                    if i < (simulateAssessmentTimes[j] +
                            simulateMobilizationTimes[j] +
                            simulateRepairTimes[j]):
                        Functionality[i][j] = 0
                    else:
                        Functionality[i][j] = 1
                # Functionality for Collapse damage state
                elif j == 5:
                    if i < (simulateMobilizationTimes[j] +
                            simulateRepairTimes[j]):
                        Functionality[i][j] = 0
                    else:
                        Functionality[i][j] = 1

                expectedFunctionality += (
                    Functionality[i][j]
                    * self.currentDamageStateProbabilities[j])
            # Expected functionality
            buildingLevelRecoveryFunction[i] = expectedFunctionality
        return buildingLevelRecoveryFunction
