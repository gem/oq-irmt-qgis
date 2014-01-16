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
from numpy import mean, std, argwhere, amax, amin
from scipy.stats import rankdata
from register import Register

NORMALIZATION_ALGS = Register()
RANK_VARIANTS = ['average', 'min', 'max', 'dense', 'ordinal']  # still unused


def normalize(features_dict, algorithm, variant_name="", inverse=False):
    """
    Use the chosen algorithm (and optional variant) on the input dict, and
    return a dict containing the normalized values with the original ids
    """
    ids = features_dict.keys()
    values = features_dict.values()
    if variant_name:
        normalized_list = algorithm(values, variant_name, inverse)
    return dict(zip(ids, normalized_list))

@NORMALIZATION_ALGS.add('RANK')
def rank(input_list, variant_name="AVERAGE", inverse=False):
    input_copy = input_list[:]
    rank_list = [0]*len(input_list)
    previous_ties = 0
    if not inverse:
        # obtain a value above the maximum value contained in input_list,
        # so it will never be picked as the minimum element of the list
        above_max_input = max(input_list) + 1
        if variant_name == "ORDINAL":
            curr_idx = 1
            while curr_idx <= len(input_list):
                bottom_indices = argwhere(
                    input_copy == amin(input_copy)).flatten().tolist()
                for j in bottom_indices:
                    rank_list[j] = curr_idx
                    curr_idx += 1
                    input_copy[j] = above_max_input
        else:
            curr_idx = 1
            while curr_idx <= len(input_list):
                # get the list of indices of the min elements of input_copy
                bottom_indices = argwhere(
                    input_copy == amin(input_copy)).flatten().tolist()
                bottom_amount = len(bottom_indices)
                if bottom_amount == 1:  # no ties
                    bottom_index = bottom_indices.pop()
                    if variant_name == "DENSE":
                        rank_list[bottom_index] = curr_idx - previous_ties
                    else:
                        rank_list[bottom_index] = curr_idx
                    curr_idx += 1
                    # change value instead of removing the item, in order to
                    # avoid modifying the indices of the other elements.
                    # Set to a value above the max, so it does not disturb
                    # while searching the min in the following iterations
                    input_copy[bottom_index] = above_max_input
                else:  # arbitrary number of ties
                    for idx in bottom_indices:
                        if variant_name == "AVERAGE":
                            rank_list[idx] = \
                                (2 * curr_idx + bottom_amount - 1) / 2.0
                        elif variant_name == "MIN":
                            rank_list[idx] = curr_idx
                        elif variant_name == "MAX":
                            rank_list[idx] = curr_idx + bottom_amount - 1
                        elif variant_name == "DENSE":
                            rank_list[idx] = curr_idx - previous_ties
                        else:
                            raise NotImplementedError(
                                "%s variant not implemented" % variant_name)
                        input_copy[idx] = above_max_input
                    curr_idx += bottom_amount
                    previous_ties += bottom_amount - 1

    else:  # inverse
        above_max_input = max(input_list) + 1
        curr_idx = len(input_list)
        while curr_idx > 0:
            bottom_indices = argwhere(
                input_copy == amin(input_copy)).flatten().tolist()
            bottom_amount = len(bottom_indices)
            #print "top_amount = ", top_amount
            if bottom_amount == 1:  # no ties
                bottom_index = bottom_indices.pop()
                rank_list[bottom_index] = curr_idx
                curr_idx -= 1
                input_copy[bottom_index] = above_max_input
            else:  # arbitrary number of ties
                if variant_name == "AVERAGE":
                    for idx in bottom_indices:
                        #print "curr_idx = ", curr_idx
                        rank_list[idx] = \
                            (2 * curr_idx + 1 - bottom_amount) / 2.0
                        input_copy[idx] = above_max_input
                    curr_idx -= bottom_amount
                else:
                    raise NotImplementedError(
                        "%s ranking variant not implemented" % variant_name)
    return rank_list

@NORMALIZATION_ALGS.add('Z_SCORE')
def z_score(input_list, variant_name="", inverse=False):
    """
    Normalized(e_i) = (e_i - mean(e)) / std(e)
    """
    mean_val = mean(input_list)
    stddev_val = std(input_list)
    if inverse:
        # multiply each input_list element by -1
        input_list[:] = [-x for x in input_list]
    output_list = [
        1.0 * (num - mean_val) / stddev_val for num in input_list]
    return output_list

@NORMALIZATION_ALGS.add('MIN_MAX')
def min_max(input_list, variant_name="", inverse=False):
    """
    Normalized(e_i) = (e_i - min(e)) / (max(e) - min(e))
    """
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

def rank_simple(vector, inverse=False):
    if inverse:
        return [(len(vector)-1)-x for x in sorted(
            range(len(vector)), key=vector.__getitem__)]
    else:
        return sorted(range(len(vector)), key=vector.__getitem__)


def rank_data(input_list, variant_name="", inverse=False):
    """
    Assign ranks to data, dealing with ties appropriately. Ranks begin at 1.
    The variant_name argument determines how to cope with equal values.
    """
    # TODO: To be refactored and properly documented
    n = len(input_list)
    # list of ranks of the initial values
    ivec = rank_simple(input_list, inverse)
    # input_list sorted by rank
    # svec = [input_list[rank] for rank in ivec]
    svec = sorted(input_list)
    sumranks = 0
    dupcount = 0
    newarray = [0]*n
    for i in xrange(n):
        sumranks += i
        dupcount += 1
        if i==n-1 or svec[i] != svec[i+1]:
            averank = sumranks / float(dupcount) + 1
            for j in xrange(i-dupcount+1, i+1):
                newarray[ivec[j]] = averank
            sumranks = 0
            dupcount = 0
    return newarray

def rank_scipy(input_list, variant_name="", inverse=False):
    """
    Assign ranks to data, dealing with ties appropriately. Ranks begin at 1.
    The variant_name argument determines how to cope with equal values.
    """
    # FIXME: obsolete version of rankdata doesn't accept method parameter
    # after updating scipy, we could use:
    # rankdata(input_list, variant_name)
    output_list = list(rankdata(input_list))
    return output_list

if __name__ == "__main__":
    #print "TEST FUNCTION rank_data"
    #l = [3, 1, 4, 5, 3, 2]
    #print "l =", l
    #print "rank_data(l) ->", rank_data(l)
    #assert rank_data(l) == [3.5, 1.0, 5.0, 6.0, 3.5, 2.0]
    #print "rank_data(l, inverse=True) ->", rank_data(l, inverse=True)
    #assert rank_data(l, inverse=True) == [3.5, 6.0, 2.0, 1.0, 3.5, 5.0]
    print "TEST FUNCTION my_rank"
    print "*" * 20
    l = [2, 0, 2, 1, 2, 3, 2]
    print "l = ", l
    #ranks = my_rank(l, variant_name="AVERAGE", inverse=False)
    #print "r = ", ranks
    #ranks = my_rank(l, variant_name="AVERAGE", inverse=True)
    print "AVERAGE"
    print "r = ", my_rank(l, variant_name="AVERAGE", inverse=False)
    print "MIN"
    print "r = ", my_rank(l, variant_name="MIN", inverse=False)
    print "MAX"
    print "r = ", my_rank(l, variant_name="MAX", inverse=False)
    print "DENSE"
    print "r = ", my_rank(l, variant_name="DENSE", inverse=False)
    print "ORDINAL"
    print "r = ", my_rank(l, variant_name="ORDINAL", inverse=False)

    print "*" * 20
    print "TEST FUNCTION z_score"
    print "*" * 20
    print "l = ", l
    print "r = ", z_score(l)
    print "r_inverse = ", z_score(l, inverse=True)