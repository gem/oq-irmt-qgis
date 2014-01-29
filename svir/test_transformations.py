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


class RankTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = NORMALIZATION_ALGS["RANK"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_rank_direct_average(self):
        rank_list = self.alg(self.input_list, variant_name="AVERAGE", inverse=False)
        self.assertEqual(rank_list, [4.5, 1, 4.5, 2, 4.5, 7, 4.5])

    def test_rank_direct_min(self):
        rank_list = self.alg(self.input_list, variant_name="MIN", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 7, 3])

    def test_rank_direct_max(self):
        rank_list = self.alg(self.input_list, variant_name="MAX", inverse=False)
        self.assertEqual(rank_list, [6, 1, 6, 2, 6, 7, 6])

    def test_rank_direct_dense(self):
        rank_list = self.alg(self.input_list, variant_name="DENSE", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 4, 3])

    def test_rank_direct_ordinal(self):
        rank_list = self.alg(self.input_list, variant_name="ORDINAL", inverse=False)
        self.assertEqual(rank_list, [3, 1, 4, 2, 5, 7, 6])

    def test_rank_inverse_average(self):
        rank_list = self.alg(self.input_list, variant_name="AVERAGE", inverse=True)
        self.assertEqual(rank_list, [3.5, 7, 3.5, 6, 3.5, 1, 3.5])

    def test_rank_inverse_min(self):
        rank_list = self.alg(self.input_list, variant_name="MIN", inverse=True)
        self.assertEqual(rank_list, [2, 7, 2, 6, 2, 1, 2])

    def test_rank_inverse_max(self):
        rank_list = self.alg(self.input_list, variant_name="MAX", inverse=True)
        self.assertEqual(rank_list, [5, 7, 5, 6, 5, 1, 5])

    def test_rank_inverse_dense(self):
        rank_list = self.alg(self.input_list, variant_name="DENSE", inverse=True)
        self.assertEqual(rank_list, [2, 4, 2, 3, 2, 1, 2])

    def test_rank_inverse_ordinal(self):
        rank_list = self.alg(self.input_list, variant_name="ORDINAL", inverse=True)
        self.assertEqual(rank_list, [2, 7, 3, 6, 4, 1, 5])


class MinMaxTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = NORMALIZATION_ALGS["MIN_MAX"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_min_max_direct(self):
        rank_list = self.alg(self.input_list, inverse=False)
        self.assertEqual(rank_list,  [0.6666666666666666,
                                      0.0,
                                      0.6666666666666666,
                                      0.3333333333333333,
                                      0.6666666666666666,
                                      1.0,
                                      0.6666666666666666])

    def test_min_max_inverse(self):
        rank_list = self.alg(self.input_list, inverse=True)
        self.assertEqual(rank_list, [0.33333333333333337,
                                     1.0,
                                     0.33333333333333337,
                                     0.6666666666666667,
                                     0.33333333333333337,
                                     0.0,
                                     0.33333333333333337])


class ZScoreTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = NORMALIZATION_ALGS["Z_SCORE"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_z_score_direct(self):
        rank_list = self.alg(self.input_list, inverse=False)
        self.assertEqual(rank_list, [0.3244428422615252,
                                     -1.9466570535691505,
                                     0.3244428422615252,
                                     -0.81110710565381261,
                                     0.3244428422615252,
                                     1.459992790176863,
                                     0.3244428422615252])

    def test_z_score_inverse(self):
        rank_list = self.alg(self.input_list, inverse=True)
        self.assertEqual(rank_list, [-4.2177569493998259,
                                     -1.9466570535691505,
                                     -4.2177569493998259,
                                     -3.0822070014844885,
                                     -4.2177569493998259,
                                     -5.3533068973151643,
                                     -4.2177569493998259])


class Log10TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_log10_direct(self):
        pass

    def test_log10_inverse(self):
        pass


class QuadraticTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_quadratic_direct(self):
        pass

    def test_quadratic_inverse(self):
        pass


if __name__ == '__main__':
    unittest.main()