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
    input_copy = input_list[:]
    len_input_list = len(input_list)
    rank_list = [0]*len_input_list
    previous_ties = 0
    if not inverse:
        # obtain a value above the maximum value contained in input_list,
        # so it will never be picked as the minimum element of the list
        above_max_input = max(input_list) + 1
        curr_idx = 1
        while curr_idx <= len_input_list:
            # get the list of indices of the min elements of input_copy
            bottom_indices = argwhere(
                input_copy == amin(input_copy)).flatten().tolist()
            bottom_amount = len(bottom_indices)
            for bottom_idx in bottom_indices:
                if variant_name == "AVERAGE":
                    rank_list[bottom_idx] = \
                        (2 * curr_idx + bottom_amount - 1) / 2.0
                elif variant_name == "MIN":
                    rank_list[bottom_idx] = curr_idx
                elif variant_name == "MAX":
                    rank_list[bottom_idx] = curr_idx + bottom_amount - 1
                elif variant_name == "DENSE":
                    rank_list[bottom_idx] = curr_idx - previous_ties
                elif variant_name == "ORDINAL":
                    rank_list[bottom_idx] = curr_idx
                    curr_idx += 1
                else:
                    raise NotImplementedError(
                        "%s variant not implemented" % variant_name)
                input_copy[bottom_idx] = above_max_input
            if variant_name != "ORDINAL":
                curr_idx += bottom_amount
            previous_ties += bottom_amount - 1

    else:  # inverse
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
def z_score(input_list, variant_name="", inverse=False):
    """
    Normalized(e_i) = (e_i - mean(e)) / std(e)
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
def min_max(input_list, variant_name="", inverse=False):
    """
    Normalized(e_i) = (e_i - min(e)) / (max(e) - min(e))
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
            lambda x: 1 - ((x - list_min) / list_range), input_list)
    else:
        output_list = map(
            lambda x: (x - list_min) / list_range, input_list)
    return output_list


@NORMALIZATION_ALGS.add('LOG10')
def log10(input_list, variant_name="", inverse=False):
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    if inverse:
        raise NotImplementedError(
            "Inverse transformation for log10 is not implemented")
    if any(n < 0 for n in input_list):
        raise ValueError("log10 transformation can not be performed if "
                         "the field contains negative values")
    output_list = log10(input_list)
    return output_list


@NORMALIZATION_ALGS.add('QUADRATIC')
def quadratic(input_list, variant_name="", inverse=False):
    min_input = min(input_list)
    max_input = max(input_list)
    squared_range = (max_input - min_input)**2
    if variant_name == "INCREASING":
        output_list = map(
            lambda x: (x - min_input)**2 / squared_range, input_list)
    elif variant_name == "DECREASING":
        output_list = map(
            lambda x: (max_input-(x-min_input)**2)/squared_range, input_list)
    else:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    if inverse:
        output_list[:] = [1 - x for x in output_list]
    return output_list

