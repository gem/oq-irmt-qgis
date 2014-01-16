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

from normalization_algs import NORMALIZATION_ALGS
import unittest

class DataTransformationTestCase(unittest.TestCase):

    def setUp(self):
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_rank_direct(self):
        alg = NORMALIZATION_ALGS["RANK"]

        rank_list = alg(self.input_list, variant_name="AVERAGE", inverse=False)
        self.assertEqual(rank_list, [4.5, 1, 4.5, 2, 4.5, 7, 4.5])

        rank_list = alg(self.input_list, variant_name="MIN", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 7, 3])

        rank_list = alg(self.input_list, variant_name="MAX", inverse=False)
        self.assertEqual(rank_list, [6, 1, 6, 2, 6, 7, 6])

        rank_list = alg(self.input_list, variant_name="DENSE", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 4, 3])

        rank_list = alg(self.input_list, variant_name="ORDINAL", inverse=False)
        self.assertEqual(rank_list, [3, 1, 4, 2, 5, 7, 6])

    def test_rank_inverse(self):
        alg = NORMALIZATION_ALGS["RANK"]

        rank_list = alg(self.input_list, variant_name="AVERAGE", inverse=True)
        self.assertEqual(rank_list, [3.5, 7, 3.5, 6, 3.5, 1, 3.5])

        # rank_list = alg(self.input_list, variant_name="MIN", inverse=True)
        # self.assertEqual(rank_list, [2, 7, 2, 6, 2, 1, 2])
        #
        # rank_list = alg(self.input_list, variant_name="MAX", inverse=True)
        # self.assertEqual(rank_list, [5, 7, 5, 6, 5, 1, 5])
        #
        # rank_list = alg(self.input_list, variant_name="DENSE", inverse=True)
        # self.assertEqual(rank_list, [2, 4, 2, 3, 2, 1, 2])
        #
        # rank_list = alg(self.input_list, variant_name="ORDINAL", inverse=True)
        # self.assertEqual(rank_list, [2, 7, 3, 6, 4, 1, 5])

    def test_z_score_direct(self):
        pass

    def test_z_score_inverse(self):
        pass

    def test_min_max_direct(self):
        pass

    def test_min_max_inverse(self):
        pass

if __name__ == '__main__':
    unittest.main()