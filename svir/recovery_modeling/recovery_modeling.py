
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

import os
import json
import bisect
try:
    import matplotlib
    matplotlib.use('Qt4Agg')
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise ImportError(
        'There was a problem importing matplotlib. If you are using'
        ' a 64bit version of QGIS on Windows, please try using'
        ' a 32bit version instead. %s' % exc)
from collections import defaultdict
from qgis.PyQt.QtCore import QSettings
from svir.recovery_modeling.building import Building
from svir.utilities.utils import (
                                  create_progress_message_bar,
                                  clear_progress_message_bar,
                                  get_layer_setting,
                                  )
from svir.utilities.shared import NUMERIC_FIELD_TYPES, RECOVERY_DEFAULTS

HEADING_FIELDS_TO_DISCARD = 4
DAYS_BEFORE_EVENT = 0
MARGIN_DAYS_AFTER = 400
MIN_SAMPLES = 250
# SVI_WEIGHT_COEFF = 1  # FIXME: Let the user set this parameter


class RecoveryModeling(object):
    """
    Modeling post-earthquake community recovery of residential community.

    Methodology:
    Time-based method is utilized which characterize a probability density
    function of the time it takes to a higher or lower functioning state given
    a set of explanatory variables such as the extent of damage to the
    building.
    """

    def __init__(self, dmg_by_asset_features, approach, iface,
                 svi_layer=None, output_data_dir=None, save_bldg_curves=False):
        self.iface = iface
        self.svi_layer = svi_layer
        self.dmg_by_asset_features = dmg_by_asset_features
        self.approach = approach
        self.output_data_dir = output_data_dir
        self.save_bldg_curves = save_bldg_curves

        self.transferProbabilities = get_transfer_probabilities(
            self.iface.activeLayer())
        self.n_loss_based_dmg_states = len(self.transferProbabilities)
        self.n_recovery_based_dmg_states = len(self.transferProbabilities[0])

    def collect_zonal_data(self, probs_field_names, integrate_svi=False,
                           zone_field_name=None):
        # build dictionary zone_id -> dmg_by_asset_probs
        zonal_dmg_by_asset_probs = defaultdict(list)
        zonal_asset_refs = defaultdict(list)
        try:
            first_feat = self.dmg_by_asset_features[0]
        except IndexError:
            return zonal_dmg_by_asset_probs, zonal_asset_refs
        probs_fields_idxs = sorted([
            first_feat.fieldNameIndex(probs_field_names[i])
            for i in range(len(probs_field_names))])
        if integrate_svi and self.svi_layer is not None:
            # FIXME self.svi_field_name is temporarily ignored
            # svi_by_zone = dict()
            for zone_feat in self.svi_layer.getFeatures():
                zone_id = str(zone_feat[zone_field_name])
                # FIXME self.svi_field_name is temporarily ignored
                # svi_value = zone_feat[self.svi_field_name]
                # svi_by_zone[zone_id] = svi_value
            msg = 'Reading damage state probabilities...'
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            tot_features = len(self.dmg_by_asset_features)
            for feat_idx, dmg_by_asset_feat in enumerate(
                    self.dmg_by_asset_features, start=1):
                zone_id = dmg_by_asset_feat[zone_field_name]
                # FIXME: hack to handle case in which the zone id is an integer
                # but it is stored as Real
                try:
                    zone_id = str(int(zone_id))
                except:
                    zone_id = str(zone_id)
                # FIXME: same hack as above
                asset_ref = dmg_by_asset_feat['asset_ref']
                try:
                    asset_ref = str(int(asset_ref))
                except:
                    asset_ref = str(asset_ref)
                dmg_by_asset_probs = [dmg_by_asset_feat.attributes()[idx]
                                      for idx in probs_fields_idxs]
                zonal_dmg_by_asset_probs[zone_id].append(dmg_by_asset_probs)
                zonal_asset_refs[zone_id].append(asset_ref)
                progress_perc = feat_idx / float(tot_features) * 100
                progress.setValue(progress_perc)
            clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        else:  # ignore svi
            msg = 'Reading damage state probabilities...'
            msg_bar_item, progress = create_progress_message_bar(
                self.iface.messageBar(), msg)
            tot_features = len(self.dmg_by_asset_features)
            for idx, dmg_by_asset_feat in enumerate(
                    self.dmg_by_asset_features, start=1):
                dmg_by_asset_probs = [dmg_by_asset_feat.attributes()[idx]
                                      for idx in probs_fields_idxs]
                asset_ref = dmg_by_asset_feat['asset_ref']
                zonal_dmg_by_asset_probs['ALL'].append(dmg_by_asset_probs)
                zonal_asset_refs['ALL'].append(asset_ref)
                progress_perc = idx / float(tot_features) * 100
                progress.setValue(progress_perc)
            clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        return zonal_dmg_by_asset_probs, zonal_asset_refs

    def get_times(self, times_type):
        times = get_layer_setting(self.iface.activeLayer(), times_type)
        if times is None:
            times_str = QSettings().value('irmt/%s' % times_type, '')
            if times_str:
                times = json.loads(times_str)
            else:
                times = list(RECOVERY_DEFAULTS[times_type])
        return times

    def generate_community_level_recovery_curve(
            self, zone_id, zonal_dmg_by_asset_probs,
            zonal_asset_refs, writer=None, integrate_svi=False, seed=None,
            n_simulations=1, n_zones=1, zone_index=1):

        # TODO: use svi_by_zone[zone_id] to adjust recovery times (how?)

        dmg_by_asset_probs = zonal_dmg_by_asset_probs[zone_id]
        asset_refs = zonal_asset_refs[zone_id]

        (LossBasedDamageStateProbabilities,
            RecoveryBasedDamageStateProbabilities,
            fractionCollapsedAndIrreparableBuildings) = \
            self.loss_based_to_recovery_based_probs(dmg_by_asset_probs)

        # FIXME self.svi_field_name is temporarily ignored
        # svi_value = svi_by_zone[zone_id] if integrate_svi else None

        # NOTE: If we don't read times again for each zone, time increases
        # across zones. This is not optimal, but almost instantaneous.
        inspectionTimes = self.get_times('inspection_times')
        assessmentTimes = self.get_times('assessment_times')
        mobilizationTimes = self.get_times('mobilization_times')
        repairTimes = self.get_times('repair_times')
        recoveryTimes = self.get_times('recovery_times')

        # NOTE: when aggregating by zone we are constantly increasing
        # the times with this approach
        (timeList, inspectionTimes,
            assessmentTimes, mobilizationTimes) = self.calculate_times(
            fractionCollapsedAndIrreparableBuildings, inspectionTimes,
            assessmentTimes, mobilizationTimes, repairTimes)
        # assessmentTimes, mobilizationTimes, repairTimes, svi_value)

        # Initialize community recovery function
        communityRecoveryFunction = [0 for x in range(len(timeList))]
        New_communityRecoveryFunction = [
            0 for x in range(len(timeList)+DAYS_BEFORE_EVENT)]

        # FIXME: temporarily disabled for testing purposes
        # # PH,PT: we want to ensure we perform at least MIN_SAMPLES samples
        # # in order to reduce variation in values due to a small sample
        # # space.
        # if n_simulations * len(asset_refs) < MIN_SAMPLES:
        #     n_simulations = MIN_SAMPLES / len(asset_refs)

        # Looping over all damage simulations
        for sim in range(n_simulations):
            simulationRecoveryFunction = \
                self.generate_simulation_recovery_curve(
                    timeList, LossBasedDamageStateProbabilities,
                    RecoveryBasedDamageStateProbabilities, inspectionTimes,
                    recoveryTimes, repairTimes, assessmentTimes,
                    mobilizationTimes, zone_id, asset_refs, zone_index,
                    n_zones, sim, n_simulations, seed)
            # Sum up all building level recovery function
            # TODO: use enumerate instead
            for timePoint in range(len(timeList)):
                communityRecoveryFunction[timePoint] \
                    += simulationRecoveryFunction[timePoint]

        # Calculate community level recovery function
        # TODO: use enumerate instead
        for timePoint in range(len(timeList)):
            communityRecoveryFunction[timePoint] /= \
                n_simulations

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
        # highlight values at observation days (after 6, 12 and 18 months)
        obs_days = [DAYS_BEFORE_EVENT + day for day in (0, 180, 360, 540)]
        xlabels = ['event', '6 months', '12 months', '18 months']
        plt.plot(New_timeList, New_communityRecoveryFunction)
        if writer is not None:
            row = [zone_id]
        for obs_day in obs_days:
            if obs_day < len(New_communityRecoveryFunction):
                value_at_obs_day = New_communityRecoveryFunction[obs_day]
                if obs_day != DAYS_BEFORE_EVENT:  # no vert. line at event time
                    plt.axvline(x=obs_day, linestyle='dotted')
                i = obs_day
                j = value_at_obs_day
                plt.annotate(
                    '%.3f' % j,
                    xy=(i, j),
                    xytext=(-35, 5),
                    textcoords='offset points')
            else:
                value_at_obs_day = 'NA'
            if writer is not None:
                row.append(value_at_obs_day)
        # TODO: add x value and vertical line when y is 95% recovery
        days_to_recover_95_perc = 'NA'
        for day in [DAYS_BEFORE_EVENT + day for day in timeList]:
            value = New_communityRecoveryFunction[day]
            if value > 0.95:
                plt.axvline(x=day, linestyle='dashed')
                # insert day in obs_days at the right ordered index
                position = bisect.bisect(obs_days, day)
                bisect.insort(obs_days, day)
                days_to_recover_95_perc = day - DAYS_BEFORE_EVENT
                xlabels.insert(position, "%s days" % days_to_recover_95_perc)
                break
        if writer is not None:
            row.insert(1, days_to_recover_95_perc)
            writer.writerow(row)
        if self.output_data_dir is not None:
            plt.xticks(obs_days, xlabels, rotation='vertical')
            plt.xlabel('Time (days)')
            plt.ylabel('Normalized recovery level')
            plt.title('Community level recovery curve for zone %s' % zone_id)
            plt.ylim((0.0, 1.2))
            plt.tight_layout()
            # plt.show()
            filestem = os.path.join(
                self.output_data_dir, "recovery_function_zone_%s" % zone_id)
            fig.savefig(filestem + '.png')
        plt.close(fig)

        if self.output_data_dir is not None:
            # Save community recovery function
            f3 = open(filestem + '.txt', "w")
            f3.write(str(New_communityRecoveryFunction))
            f3.close()
        return New_communityRecoveryFunction

    def generate_simulation_recovery_curve(
            self, timeList, LossBasedDamageStateProbabilities,
            RecoveryBasedDamageStateProbabilities, inspectionTimes,
            recoveryTimes, repairTimes, assessmentTimes, mobilizationTimes,
            zone_id, asset_refs, zone_index, n_zones, simulation,
            n_simulations, seed=None):
        # Looping over all buildings in community
        # Initialize building level recovery function
        simulationRecoveryFunction = [
            0 for x in range(len(timeList))]
        msg = ('Calculating recovery curve for '
               'zone %s (%s/%s), simulation %s/%s'
               % (zone_id, zone_index, n_zones, simulation + 1, n_simulations))
        msg_bar_item, progress = create_progress_message_bar(
            self.iface.messageBar(), msg)
        tot_bldgs = len(LossBasedDamageStateProbabilities)
        # TODO: use enumerate instead
        # TODO: perhaps iterate enumerating by asset_ref
        for bldg_idx in range(tot_bldgs):
            # Generate recovery function for current
            # building/simulation using the given damage state
            # probability distribution
            currentSimulationBuildingLevelDamageStateProbabilities = \
                RecoveryBasedDamageStateProbabilities[bldg_idx]
            # call building class within Napa Data
            # PAOLO: building number is not used. Instead, we need to
            # make available to the building all the imported data
            napa_bldg = Building(
                self.iface,
                inspectionTimes, recoveryTimes, repairTimes,
                currentSimulationBuildingLevelDamageStateProbabilities,
                timeList, assessmentTimes, mobilizationTimes)
            approach = self.approach
            # approach can be aggregate or disaggregate
            building_level_recovery_function = \
                napa_bldg.generateBldgLevelRecoveryFunction(approach, seed)
            if self.output_data_dir is not None and self.save_bldg_curves:
                output_by_building_dir = os.path.join(
                    self.output_data_dir, 'by_building')
                if not os.path.exists(output_by_building_dir):
                    os.makedirs(output_by_building_dir)
                asset_ref = asset_refs[bldg_idx]
                output_filename = os.path.join(
                    output_by_building_dir,
                    "zone_%s_bldg_%s.txt" % (zone_id, asset_ref))
                with open(output_filename, 'w') as f:
                    f.write(str(building_level_recovery_function))
            # The following lines plot building level curves
            # fig = plt.figure()
            # plt.plot(timeList, building_level_recovery_function)
            # plt.xlabel('Time (days)')
            # plt.ylabel('Normalized recovery level')
            # plt.title('Building level recovery curve')
            # plt.ylim((0.0, 1.2))
            # plt.show()
            # plt.close(fig)
            # Assign buidling level recovery function
            # TODO: use enumerate instead
            for timePoint in range(len(timeList)):
                simulationRecoveryFunction[timePoint] += \
                    building_level_recovery_function[timePoint]
            progress_perc = bldg_idx / float(tot_bldgs) * 100
            progress.setValue(progress_perc)
        clear_progress_message_bar(self.iface.messageBar(), msg_bar_item)
        return simulationRecoveryFunction

    def loss_based_to_recovery_based_probs(self, dmg_by_asset_probs):
        LossBasedDamageStateProbabilities = \
            [[0 for x in range(self.n_loss_based_dmg_states)]
             for y in range(len(dmg_by_asset_probs))]

        for i in range(len(dmg_by_asset_probs)):
            for j in range(self.n_loss_based_dmg_states):
                LossBasedDamageStateProbabilities[i][j] = \
                    dmg_by_asset_probs[i][j]  # ex dmg_by_asset_probs[i+1][j+4]

        # Mapping from Loss-based to recovery-based building damage states
        RecoveryBasedDamageStateProbabilities = [
            [0 for x in range(6)] for y in range(len(dmg_by_asset_probs))]

        fractionCollapsedAndIrreparableBuildings = 0
        # TODO: use enumerate instead
        for i in range(len(LossBasedDamageStateProbabilities)):
            for j in range(self.n_recovery_based_dmg_states):
                for s in range(self.n_loss_based_dmg_states):
                    RecoveryBasedDamageStateProbabilities[i][j] += (
                        float(LossBasedDamageStateProbabilities[i][s])
                        * float(self.transferProbabilities[s][j]))
                    if (j == self.n_loss_based_dmg_states - 1
                            or j == self.n_loss_based_dmg_states):
                        fractionCollapsedAndIrreparableBuildings += \
                            RecoveryBasedDamageStateProbabilities[i][j]

        fractionCollapsedAndIrreparableBuildings = \
            fractionCollapsedAndIrreparableBuildings / len(dmg_by_asset_probs)
        return (LossBasedDamageStateProbabilities,
                RecoveryBasedDamageStateProbabilities,
                fractionCollapsedAndIrreparableBuildings)

    def calculate_times(
            self, fractionCollapsedAndIrreparableBuildings,
            inspectionTimes, assessmentTimes, mobilizationTimes,
            repairTimes):  # FIXME self.svi_field_name is temporarily ignored
            # repairTimes, svi_value):
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
                   + int(max(repairTimes)) + MARGIN_DAYS_AFTER)

        # PAOLO: TODO We have to find a proper way to use the SVI to adjust the
        # recovery times. For now we are not using it, but we are aggregating
        # assets by the same zones for which the SVI is defined
        # if svi_value:
        #     maxTime = int(round(maxTime * SVI_WEIGHT_COEFF * svi_value))

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


def get_transfer_probabilities(layer):
    transfer_probabilities = get_layer_setting(
        layer, 'transfer_probabilities')
    if transfer_probabilities is None:
        transfer_probabilities_str = QSettings().value(
            'irmt/transfer_probabilities', None)
        if transfer_probabilities_str is None:
            transfer_probabilities = list(RECOVERY_DEFAULTS[
                'transfer_probabilities'])
        else:
            transfer_probabilities = json.loads(transfer_probabilities_str)
    return transfer_probabilities


def fill_fields_multiselect(fields_multiselect, layer):
    if fields_multiselect is None or layer is None:
        return
    fields = layer.fields()
    field_names = [field.name() for field in fields]
    transfer_probabilities = get_transfer_probabilities(layer)
    n_loss_based_dmg_states = len(transfer_probabilities)
    # select fields that contain probabilities
    # i.e., ignore asset id, taxonomy, lon and lat (first
    # HEADING_FIELDS_TO_DISCARD items)
    # and get only columns containing means, discarding
    # those containing stddevs, therefore getting one item
    # out of two for the remaining columns
    # Other fields can be safely added to the tail of the layer,
    # without affecting this calculation
    probs_slice = slice(
        HEADING_FIELDS_TO_DISCARD,
        HEADING_FIELDS_TO_DISCARD + 2*n_loss_based_dmg_states, 2)
    try:
        default_field_names = field_names[probs_slice]
    except:
        default_field_names = []
    other_fields = [field for field in fields
                    if field.name() not in default_field_names
                    and field.typeName() in NUMERIC_FIELD_TYPES]
    other_field_names = [field.name() for field in other_fields]
    fields_multiselect.set_selected_items(default_field_names)
    fields_multiselect.set_unselected_items(other_field_names)
