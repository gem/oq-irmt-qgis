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
import abc
from numpy import mean, std
from scipy.stats import rankdata
from register import Register

NORMALIZATION_ALGS = Register()
RANK_METHODS = ['average', 'min', 'max', 'dense', 'ordinal']


class NormalizationAlg(object):
    """
    Abstract class to be implemented by all the normalization algorithms
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_dict):
        self.input_dict = input_dict
        self.input_keys = self.input_dict.keys()
        self.input_values = self.input_dict.values()

    @abc.abstractmethod
    def normalize(self, method=None):
        raise NotImplementedError

    def rebuild_dict(self, normalized_list):
        return dict(zip(self.input_keys, normalized_list))

@NORMALIZATION_ALGS.add('RANK')
class Rank(NormalizationAlg):
    """
    Assign ranks to data, dealing with ties appropriately. Ranks begin at 1.
    The method argument controls how ranks are assigned to equal values
    """
    def normalize(self, method=None):
        # FIXME: obsolete version of rankdata doesn't accept method parameter
        ranked_list = list(rankdata(self.input_values))
        return self.rebuild_dict(ranked_list)

@NORMALIZATION_ALGS.add('Z_SCORE')
class Zscore(NormalizationAlg):
    """
    Normalized(e_i) = (e_i - mean(e)) / std(e)
    """
    def normalize(self, method=None):
        mean_val = mean(self.input_values)
        stddev_val = std(self.input_values)
        z_list = [
            1.0 * (num - mean_val) / stddev_val for num in self.input_values]
        return self.rebuild_dict(z_list)

@NORMALIZATION_ALGS.add('MIN_MAX')
class MinMax(NormalizationAlg):
    """
    Normalized(e_i) = (e_i - min(e)) / (max(e) - min(e))
    """
    def normalize(self, method=None):
        list_min = min(self.input_values)
        list_max = max(self.input_values)
        # Get the range of the list
        list_range = float(list_max - list_min)
        # Normalize
        ret_list = map(
            lambda x: (x - list_min) / list_range, self.input_values)
        return self.rebuild_dict(ret_list)
