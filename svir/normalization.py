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

from numpy import (nan,
                   isnan,
                   mean,
                   std)
from scipy.stats import rankdata

class Normalization(object):
    """
    Collection of methods for normalizing/standardizing a list of numbers or
    a layer's attribute
    """
    def __init__(self, input_list):
        self.input_list = input_list

    def rank(self):
        ret_list = list(rankdata(self.input_list))
        return ret_list

    def z_score(self):
        # remove elements in list that are nan
        valid_nums = [n for n in self.input_list if not isnan(n)]
        mean_val = mean(valid_nums)
        stddev_val = std(valid_nums)
        z_list = [1.0 * (num - mean_val) / stddev_val for num in valid_nums]
        # in case I don't have any nan in input, I can simply return z_list
        if len(valid_nums) == len(self.input_list):
            return z_list
        # otherwise, deal with nan
        ret_list = list()
        for n in self.input_list:
            if isnan(n):
                ret_list.append(nan)
            else:
                ret_list.append(z_list.pop(0))
        assert len(z_list) == 0
        return ret_list

    def min_max(self):
        # TODO: what happens if the input list contains any nan?
        list_min = min(self.input_list)
        list_max = max(self.input_list)
        # Get the range of the list
        list_range = float(list_max - list_min)
        # Normalize
        ret_list = map(lambda x: (x - list_min) / list_range, self.input_list)
        return ret_list


def normalize_attribute(layer, attr_name, algorithm):
    if algorithm == 'rank':
        pass
    elif algorithm == 'z_score':
        pass
    elif algorithm == 'min_max':
        pass
    else:
        raise NotImplementedError

