# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2013 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

# Copyright (c) 2010-2013, GEM Foundation.
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
"""
from numpy import mean, std, argwhere, amax, amin, log10
from register import Register

NORMALIZATION_ALGS = Register()
RANK_VARIANTS = ['AVERAGE', 'MIN', 'MAX', 'DENSE', 'ORDINAL']
QUADRATIC_VARIANTS = ['INCREASING', 'DECREASING']


def normalize(features_dict, algorithm, variant_name="", inverse=False):
    """
    Use the chosen algorithm (and optional variant) on the input dict, and
    return a dict containing the normalized values with the original ids
    """
    ids = features_dict.keys()
    values = features_dict.values()
    normalized_list = algorithm(values, variant_name, inverse)
    return dict(zip(ids, normalized_list))


@NORMALIZATION_ALGS.add('RANK')
def rank(input_list, variant_name="AVERAGE", inverse=False):
    """Assign ranks to data, dealing with ties appropriately.

    Args:
        input_list: the list of numbers to rank
        variant_name: available variants are
            [AVERAGE, MIN, MAX, DENSE, ORDINAL] and they correspond to
            different strategies on how to cope with ties (default: AVERAGE)
        inverse: instead of giving the highest rank to the biggest input value,
            give the highest rank to the smallest input value
    Returns:
        list of ranks corresponding to the input data
    Raises:
        NotImplementedError: if variant_name is not implemented
    """
    input_copy = input_list[:]
    len_input_list = len(input_list)
    rank_list = [0] * len_input_list
    previous_ties = 0
    if not inverse:  # high values get high ranks
        # obtain a value above the maximum value contained in input_list,
        # so it will never be picked as the minimum element of the list
        above_max_input = max(input_list) + 1
        curr_idx = 1
        while curr_idx <= len_input_list:
            # get the list of indices of the min elements of input_copy.
            # note that we might have ties.
            bottom_indices = argwhere(
                input_copy == amin(input_copy)).flatten().tolist()
            bottom_amount = len(bottom_indices)
            for bottom_idx in bottom_indices:
                if variant_name == "AVERAGE":
                    # e.g., if 4 inputs are equal, and they would receive
                    # ranks from 3 to 6, all of them will obtain rank 4.5
                    # Afterwards the ranks increase from 7 on.
                    rank_list[bottom_idx] = \
                        (2 * curr_idx + bottom_amount - 1) / 2.0
                elif variant_name == "MIN":
                    # e.g., if 4 inputs are equal, and they would receive
                    # ranks from 3 to 6, all of them will obtain rank 3.
                    # Afterwards the ranks increase from 7 on.
                    rank_list[bottom_idx] = curr_idx
                elif variant_name == "MAX":
                    # e.g., if 4 inputs are equal, and they would receive
                    # ranks from 3 to 6, all of them will obtain rank 6
                    # Afterwards the ranks increase from 7 on.
                    rank_list[bottom_idx] = curr_idx + bottom_amount - 1
                elif variant_name == "DENSE":
                    # the same as for "MIN", but instead of ranking the
                    # next elements counting from 7 on, the ranks will
                    # increase from 4 on (no "jumps").
                    rank_list[bottom_idx] = curr_idx - previous_ties
                elif variant_name == "ORDINAL":
                    # the ties are ranked in a "ordinal" way, assigning
                    # the smallest rank to the leftmost tie found, and so on.
                    rank_list[bottom_idx] = curr_idx
                    curr_idx += 1
                else:
                    raise NotImplementedError(
                        "%s variant not implemented" % variant_name)
                # "discard" the tie, so it will not be found as the min in
                # the next iteration (instead of removing it, which would
                # modify the list indices, I make it bigger than the
                # biggest input)
                input_copy[bottom_idx] = above_max_input
            if variant_name != "ORDINAL":
                # necessary adjustment in case of "ORDINAL"
                curr_idx += bottom_amount
            # necessary for the "DENSE" variant, to keep a count of ties
            previous_ties += bottom_amount - 1

    else:  # inverse, i.e., small inputs get high ranks
        # same as the direct methods, but proceeding top->down
        below_min_input = min(input_list) - 1
        curr_idx = len_input_list
        while curr_idx > 0:
            top_indices = argwhere(
                input_copy == amax(input_copy)).flatten().tolist()
            top_amount = len(top_indices)
            for top_idx in top_indices:
                if variant_name == "AVERAGE":
                    rank_list[top_idx] = \
                        len_input_list - (2 * curr_idx - top_amount - 1) / 2.0
                elif variant_name == "MIN":
                    rank_list[top_idx] = len_input_list - curr_idx + 1
                elif variant_name == "MAX":
                    rank_list[top_idx] = len_input_list - curr_idx + top_amount
                elif variant_name == "DENSE":
                    rank_list[top_idx] = \
                        len_input_list - curr_idx - previous_ties + 1
                elif variant_name == "ORDINAL":
                    rank_list[top_idx] = len_input_list - curr_idx + 1
                    curr_idx -= 1
                else:
                    raise NotImplementedError(
                        "%s variant not implemented" % variant_name)
                input_copy[top_idx] = below_min_input
            if variant_name != "ORDINAL":
                curr_idx -= top_amount
            previous_ties += top_amount - 1
    return rank_list


@NORMALIZATION_ALGS.add('Z_SCORE')
def z_score(input_list, variant_name=None, inverse=False):
    """
    Direct:
        Normalized(e_i) = (e_i - mean(e)) / stddev(e)
    Inverse:
        Multiply each input by -1, before doing exactly the same
    """
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    mean_val = mean(input_list)
    stddev_val = std(input_list)
    input_copy = input_list[:]
    if inverse:
        # multiply each input_list element by -1
        input_copy[:] = [-x for x in input_list]
    output_list = [
        1.0 * (num - mean_val) / stddev_val for num in input_copy]
    return output_list


@NORMALIZATION_ALGS.add('MIN_MAX')
def min_max(input_list, variant_name=None, inverse=False):
    """
    Direct:
        Normalized(e_i) = (e_i - min(e)) / (max(e) - min(e))
    Inverse:
        Normalized(e_i) = 1 - [(e_i - min(e)) / (max(e) - min(e))]

    """
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    list_min = min(input_list)
    list_max = max(input_list)
    # Get the range of the list
    list_range = float(list_max - list_min)
    # Normalize
    if inverse:
        output_list = map(
            lambda x: 1.0 - ((x - list_min) / list_range), input_list)
    else:
        output_list = map(
            lambda x: (x - list_min) / list_range, input_list)
    return output_list


@NORMALIZATION_ALGS.add('LOG10')
def log10_(input_list, variant_name=None, inverse=False):
    """
    Accept only input_list containing positive (or zero) values
    In case of zeros, set those values to 1 (this differs from the built-in
    QGIS log10 function available in the field calculator, which returns None
    in case of zeros)
    Then use numpy.log10 function to perform the log10 transformation on the
    list of values
    """
    if variant_name:
        # TODO: Perhaps it would be better to use the variant to let the user
        #       choose if setting input zeros to one or not
        raise NotImplementedError("%s variant not implemented" % variant_name)
    if inverse:
        raise NotImplementedError(
            "Inverse transformation for log10 is not implemented")
    if any(n < 0 for n in input_list):
        raise ValueError("log10 transformation can not be performed if "
                         "the field contains negative values")
    input_copy = []
    for input_value in input_list:
        corrected_value = input_value if input_value > 0 else 1.0
        input_copy.append(corrected_value)
    output_list = list(log10(input_copy))
    return output_list


@NORMALIZATION_ALGS.add('QUADRATIC')
def simple_quadratic(input_list, variant_name="INCREASING", inverse=False):
    """
    Simple quadratic transformation (bottom = 0)
        quadratic(e_i) = (e_i - bottom)^2 / (max(e) - bottom)^2
    ==>
        simple_quadratic(e_i) = e_i^2 / max(e)^2

    Inverse:
        For each output x, the final output will be 1 - x
    """
    bottom = 0.0
    max_input = max(input_list)
    if max_input - bottom == 0:
        raise ZeroDivisionError("It is impossible to perform the "
                                "transformation if the maximum "
                                "input value is 0")
    squared_range = (max_input - bottom) ** 2
    if variant_name == "INCREASING":
        output_list = map(
            lambda x: (x - bottom) ** 2 / squared_range, input_list)
    elif variant_name == "DECREASING":
        output_list = map(
            lambda x: (max_input - (x - bottom)) ** 2 / squared_range,
            input_list)

    else:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    if inverse:
        output_list[:] = [1.0 - x for x in output_list]
    return output_list

