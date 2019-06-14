# -*- coding: utf-8 -*-
#
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2015 by GEM Foundation
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

import math
from numpy import mean, std, argwhere, amax, amin, log10, log
from qgis.core import NULL

from svir.utilities.utils import Register

TRANSFORMATION_ALGS = Register()
RANK_VARIANTS = ('AVERAGE', 'MIN', 'MAX', 'DENSE', 'ORDINAL')
QUADRATIC_VARIANTS = ('INCREASING', 'DECREASING')
LOG10_VARIANTS = ('INCREMENT BY ONE IF ZEROS ARE FOUND',
                  'IGNORE ZEROS')


def transform(features_dict, algorithm, variant_name="", inverse=False):
    """
    Use the chosen algorithm (and optional variant and/or inversion)
    on the input dict, and
    return a dict containing the transformed values with the original ids
    and the list of invalid input values (or None)

    :param features_dict: dictionary containing the features to transform
    :param algorithm: the function to be used to transform the data
    :param variant_name: the (optional) variant to be used
    :param inverse: a boolean (default False) to run the inverse function
                    if available
    :returns: (transformed_dict, invalid_input_values)
    """
    # make a copy of the dictionary containing features (ids and values) and
    # remove elements containing missing values, so the transformation is
    # performed only on the subset of valid values
    f_dict_copy = features_dict.copy()
    # elements with null value will be saved in another dict, so they can be
    # re-added afterwards
    dict_of_null_values = {}
    for key, value in f_dict_copy.items():
        if type(value) in (NULL, type(None)):
            dict_of_null_values[key] = value
    for key in list(dict_of_null_values.keys()):
        del f_dict_copy[key]
    transformed_list, invalid_input_values = algorithm(
        list(f_dict_copy.values()), variant_name, inverse)
    transformed_dict = dict(
        list(zip(list(f_dict_copy.keys()), transformed_list)))
    # add to the transformed_dict the null elements that were removed
    transformed_dict.update(dict_of_null_values)
    return transformed_dict, invalid_input_values


@TRANSFORMATION_ALGS.add('RANK')
def rank(input_values, variant_name="AVERAGE", inverse=False):
    """Assign ranks to data, dealing with ties appropriately.

    :param input_values: the list of numbers to rank
    :param variant_name: available variants are
                         [AVERAGE, MIN, MAX, DENSE, ORDINAL]
                         and they correspond to
                         different strategies on how to cope with ties
                         (default: AVERAGE)
    :param inverse: instead of giving the highest rank to the biggest
                    input value, give the highest rank to the smallest
                    input value
    :returns: list of ranks corresponding to the input data
    :raises: NotImplementedError if variant_name is not implemented
    """
    input_copy = input_values[:]
    len_input_values = len(input_values)
    rank_list = [0] * len_input_values
    previous_ties = 0
    if not inverse:  # high values get high ranks
        # obtain a value above the maximum value contained in input_values,
        # so it will never be picked as the minimum element of the list
        above_max_input = max([value for value in input_values]) + 1
        curr_idx = 1
        while curr_idx <= len_input_values:
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
        below_min_input = min([value if value is not None else None
                              for value in input_values]) - 1
        curr_idx = len_input_values
        while curr_idx > 0:
            top_indices = argwhere(
                input_copy == amax(input_copy)).flatten().tolist()
            top_amount = len(top_indices)
            for top_idx in top_indices:
                if variant_name == "AVERAGE":
                    rank_list[top_idx] = (
                        len_input_values - (2 * curr_idx - top_amount - 1) /
                        2.0)
                elif variant_name == "MIN":
                    rank_list[top_idx] = len_input_values - curr_idx + 1
                elif variant_name == "MAX":
                    rank_list[top_idx] = (
                        len_input_values - curr_idx + top_amount)
                elif variant_name == "DENSE":
                    rank_list[top_idx] = \
                        len_input_values - curr_idx - previous_ties + 1
                elif variant_name == "ORDINAL":
                    rank_list[top_idx] = len_input_values - curr_idx + 1
                    curr_idx -= 1
                else:
                    raise NotImplementedError(
                        "%s variant not implemented" % variant_name)
                input_copy[top_idx] = below_min_input
            if variant_name != "ORDINAL":
                curr_idx -= top_amount
            previous_ties += top_amount - 1
    return rank_list, None


@TRANSFORMATION_ALGS.add('Z_SCORE')
def z_score(input_values, variant_name=None, inverse=False):
    r"""
    Direct:
        :math:`f(x_i) = \frac{x_i - \mu_x}{\sigma_x}`
    Inverse:
        Multiply each input by -1, before doing exactly the same
    """
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    mean_val = mean([value for value in input_values if value is not None])
    stddev_val = std([value for value in input_values if value is not None])
    if stddev_val == 0:
        raise ValueError("The Z-Score transformation can not be performed "
                         "if the standard deviation of the input values is 0")
    input_copy = input_values[:]
    if inverse:
        # multiply each input_values element by -1
        input_copy[:] = [-x if x is not None else None for x in input_values]
    output_values = [
        float((x - mean_val) / stddev_val)
        if x is not None else None
        for x in input_copy]
    return output_values, None


@TRANSFORMATION_ALGS.add('MIN_MAX')
def min_max(input_values, variant_name=None, inverse=False):
    r"""
    Direct:
        :math:`f(x_i) = \frac{x_i - \min(x)}{\max(x) - \min(x)}`
    Inverse:
        :math:`f(x_i) = 1 - \frac{x_i - \min(x)}{\max(x) - \min(x)}`
    """
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    min_value = min((value for value in input_values if value is not None))
    max_value = max((value for value in input_values if value is not None))
    # Get the range of the list
    min_max_range = float(max_value - min_value)
    if min_max_range == 0:
        raise ValueError("The min_max transformation can not be performed"
                         " if the range of valid values (max-min) is zero.")
    # Transform
    if inverse:
        output_values = [1.0 - ((x - min_value) / min_max_range)
                         if x is not None else None
                         for x in input_values]
    else:
        output_values = [(x - min_value) / min_max_range
                         if x is not None else None
                         for x in input_values]
    return output_values, None


@TRANSFORMATION_ALGS.add('LOG10')
def log10_(input_values,
           variant_name='IGNORE ZEROS',
           inverse=False):
    """
    Accept only input_values containing positive (or zero) values
    In case of zeros:

    * the variant IGNORE ZEROS produces NULL as output when any input is
      zero
    * the variant INCREMENT BY ONE IF ZEROS ARE FOUND increments all input
      data by 1

    Then use numpy.log10 function to perform the log10 transformation on the
    list of values
    """
    if inverse:
        raise NotImplementedError(
            "Inverse transformation for log10 is not implemented")
    if variant_name not in LOG10_VARIANTS:
        raise NotImplementedError(
            "%s variant not implemented" % variant_name)
    if any(n == 0 for n in input_values):
        if variant_name == 'INCREMENT BY ONE IF ZEROS ARE FOUND':
            corrected_input = [input_value + 1 for input_value in input_values]
            output_values = [
                float(value) if value is not None else None
                for value in list(log10(corrected_input))]
            return output_values, None
        elif variant_name == 'IGNORE ZEROS':
            output_values = []
            for input_value in input_values:
                if input_value in (0, NULL):
                    output_value = NULL
                    output_values.append(output_value)
                else:
                    output_values.append(log10(input_value))
            for i, value in enumerate(output_values):
                if value in (NULL, None):
                    continue
                output_values[i] = float(value)
            return output_values, None
    output_values = [float(value) for value in list(log10(input_values))]
    return output_values, None


@TRANSFORMATION_ALGS.add('QUADRATIC')
def simple_quadratic(input_values, variant_name="INCREASING", inverse=False):
    r"""
    Simple quadratic transformation :math:`(bottom = 0)`

    :math:`quadratic(x_i) = \frac{(x_i - bottom)^2}{(\max(x) - bottom)^2}`
    :math:`\Rightarrow`
    :math:`simple\_quadratic(x_i) = \frac{x_i^2}{\max(x)^2}`

    Inverse:
        For each output x, the final output will be 1 - x
    """
    bottom = 0.0
    max_input = max(input_values)
    if max_input - bottom == 0:
        raise ZeroDivisionError("It is impossible to perform the "
                                "transformation if the maximum "
                                "input value is 0")
    squared_range = (max_input - bottom) ** 2
    if variant_name == "INCREASING":
        output_values = [
            (x - bottom) ** 2 / squared_range for x in input_values]
    elif variant_name == "DECREASING":
        output_values = [(max_input - (x - bottom)) ** 2 / squared_range
                         for x in input_values]

    else:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    if inverse:
        output_values[:] = [1.0 - x for x in output_values]
    return output_values, None


@TRANSFORMATION_ALGS.add('SIGMOID')
def sigmoid(input_values, variant_name="", inverse=False):
    r"""
    Logistic sigmoid function:
        :math:`f(x) = \frac{1}{1 + e^{-x}}`

    Inverse function:
        :math:`f(x) = \ln(\frac{x}{1-x})`
    """
    if variant_name:
        raise NotImplementedError("%s variant not implemented" % variant_name)
    output_values = []
    invalid_input_values = []
    if inverse:
        for y in input_values:
            try:
                output = float(log(y / (1 - y)))
            except Exception:
                output = NULL
                invalid_input_values.append(y)
            output_values.append(output)
    else:  # direct
        for x in input_values:
            try:
                output = float(1 / (1 + math.exp(-x)))
            except Exception:
                output = NULL
                invalid_input_values.append(x)
            output_values.append(output)
    return output_values, invalid_input_values
