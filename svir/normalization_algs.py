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
from numpy import mean, std
from scipy.stats import rankdata
from register import Register

NORMALIZATION_ALGS = Register()
RANK_VARIANTS = ['average', 'min', 'max', 'dense', 'ordinal']  # still unused


def normalize(features_dict, algorithm, variant_name=""):
    """
    Use the chosen algorithm (and optional variant) on the input dict, and
    return a dict containing the normalized values with the original ids
    """
    ids = features_dict.keys()
    values = features_dict.values()
    if variant_name:
        normalized_list = algorithm(values, variant_name)
    else:
        normalized_list = algorithm(values)
    return dict(zip(ids, normalized_list))


@NORMALIZATION_ALGS.add('RANK')
def rank(input_list, variant_name):
    """
    Assign ranks to data, dealing with ties appropriately. Ranks begin at 1.
    The variant_name argument determines how to cope with equal values.
    """
    # FIXME: obsolete version of rankdata doesn't accept method parameter
    # after updating scipy, we could use:
    # rankdata(input_list, variant_name)
    if variant_name:
        raise NotImplementedError(
            "%s variant not implemented yet" % variant_name)
    output_list = list(rankdata(input_list))
    return output_list


@NORMALIZATION_ALGS.add('Z_SCORE')
def z_score(input_list):
    """
    Normalized(e_i) = (e_i - mean(e)) / std(e)
    """
    mean_val = mean(input_list)
    stddev_val = std(input_list)
    output_list = [
        1.0 * (num - mean_val) / stddev_val for num in input_list]
    return output_list


@NORMALIZATION_ALGS.add('MIN_MAX')
def min_max(input_list):
    """
    Normalized(e_i) = (e_i - min(e)) / (max(e) - min(e))
    """
    list_min = min(input_list)
    list_max = max(input_list)
    # Get the range of the list
    list_range = float(list_max - list_min)
    # Normalize
    output_list = map(
        lambda x: (x - list_min) / list_range, input_list)
    return output_list
