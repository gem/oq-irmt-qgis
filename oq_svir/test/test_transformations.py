# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Svir
                                 A QGIS plugin
 OpenQuake Social Vulnerability and Integrated Risk
                              -------------------
        begin                : 2013-10-24
        copyright            : (C) 2014 by GEM Foundation
        email                : devops@openquake.org
 ***************************************************************************/

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

import unittest
import qgis

from oq_svir.calculations.transformation_algs import (
    transform,
    TRANSFORMATION_ALGS)


class MissingValuesTestCase(unittest.TestCase):

    def test_transform_with_missing_values(self):
        # when retrieving data through the platform, the SQL query produces
        # NULL in case of missing values, where the type of those NULL elements
        # is QPyNullVariant
        # Here we test that case and the case of simple None elements
        null_values = (qgis.QPyNullVariant(float), None)
        for null_value in null_values:
            features_dict = {'0': 7,
                             '1': 6,
                             '2': null_value,
                             '3': 0,
                             '4': null_value,
                             '5': 6}
            expected_dict = {'0': 4,
                             '1': 2.5,
                             '2': null_value,
                             '3': 1,
                             '4': null_value,
                             '5': 2.5}
            alg = TRANSFORMATION_ALGS['RANK']
            variant = "AVERAGE"
            transformed_dict, missing_values = transform(
                features_dict, alg, variant)
            self.assertEqual(transformed_dict, expected_dict)


class RankTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["RANK"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_rank_direct_average(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="AVERAGE", inverse=False)
        self.assertEqual(rank_list, [4.5, 1, 4.5, 2, 4.5, 7, 4.5])

    def test_rank_direct_min(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="MIN", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 7, 3])

    def test_rank_direct_max(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="MAX", inverse=False)
        self.assertEqual(rank_list, [6, 1, 6, 2, 6, 7, 6])

    def test_rank_direct_dense(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="DENSE", inverse=False)
        self.assertEqual(rank_list, [3, 1, 3, 2, 3, 4, 3])

    def test_rank_direct_ordinal(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="ORDINAL", inverse=False)
        self.assertEqual(rank_list, [3, 1, 4, 2, 5, 7, 6])

    def test_rank_inverse_average(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="AVERAGE", inverse=True)
        self.assertEqual(rank_list, [3.5, 7, 3.5, 6, 3.5, 1, 3.5])

    def test_rank_inverse_min(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="MIN", inverse=True)
        self.assertEqual(rank_list, [2, 7, 2, 6, 2, 1, 2])

    def test_rank_inverse_max(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="MAX", inverse=True)
        self.assertEqual(rank_list, [5, 7, 5, 6, 5, 1, 5])

    def test_rank_inverse_dense(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="DENSE", inverse=True)
        self.assertEqual(rank_list, [2, 4, 2, 3, 2, 1, 2])

    def test_rank_inverse_ordinal(self):
        rank_list, _ = self.alg(
            self.input_list, variant_name="ORDINAL", inverse=True)
        self.assertEqual(rank_list, [2, 7, 3, 6, 4, 1, 5])


class MinMaxTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["MIN_MAX"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_min_max_direct(self):
        min_max_list, _ = self.alg(self.input_list, inverse=False)
        self.assertEqual(min_max_list, [0.6666666666666666,
                                        0.0,
                                        0.6666666666666666,
                                        0.3333333333333333,
                                        0.6666666666666666,
                                        1.0,
                                        0.6666666666666666])

    def test_min_max_inverse(self):
        min_max_list, _ = self.alg(self.input_list, inverse=True)
        self.assertEqual(min_max_list, [0.33333333333333337,
                                        1.0,
                                        0.33333333333333337,
                                        0.6666666666666667,
                                        0.33333333333333337,
                                        0.0,
                                        0.33333333333333337])


class ZScoreTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["Z_SCORE"]
        self.input_list = [2, 0, 2, 1, 2, 3, 2]

    def test_z_score_direct(self):
        z_score_list, _ = self.alg(self.input_list, inverse=False)
        expected_list = [0.3244428422615252,
                         -1.9466570535691505,
                         0.3244428422615252,
                         -0.81110710565381261,
                         0.3244428422615252,
                         1.459992790176863,
                         0.3244428422615252]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(z_score_list[i], expected_list[i], places=6)

    def test_z_score_inverse(self):
        z_score_list, _ = self.alg(self.input_list, inverse=True)
        expected_list = [-4.2177569493998259,
                         -1.9466570535691505,
                         -4.2177569493998259,
                         -3.0822070014844885,
                         -4.2177569493998259,
                         -5.3533068973151643,
                         -4.2177569493998259]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(z_score_list[i], expected_list[i], places=6)


class Log10TestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["LOG10"]

    def test_log10_all_positive_values(self):
        input_list = [101249,
                      94082,
                      94062,
                      158661,
                      174568]
        log10_list, _ = self.alg(input_list)
        expected_list = [5.005391,
                         4.973507,
                         4.973414,
                         5.200470,
                         5.241965]
        for i in range(len(input_list)):
            self.assertAlmostEqual(log10_list[i], expected_list[i], places=6)

    def test_log10_with_negative_values(self):
        input_list = [101249,
                      94082,
                      -94062,
                      -158661,
                      174568]
        self.assertRaises(ValueError, self.alg, input_list)

    def test_log10_incrementing_by_one_case_no_zeros_found(self):
        input_list = [101249,
                      94082,
                      94062,
                      158661,
                      174568]
        log10_list, _ = self.alg(
            input_list, variant_name='INCREMENT BY ONE IF ZEROS ARE FOUND')
        expected_list = [5.005391,
                         4.973507,
                         4.973414,
                         5.200470,
                         5.241965]
        for i in range(len(input_list)):
            self.assertAlmostEqual(log10_list[i], expected_list[i], places=6)

    def test_log10_incrementing_by_one_case_zeros_found(self):
        input_list = [101249,
                      94082,
                      0,
                      0,
                      174568]
        log10_list, _ = self.alg(
            input_list, variant_name='INCREMENT BY ONE IF ZEROS ARE FOUND')
        expected_list = [5.005395,
                         4.973511,
                         0,
                         0,
                         5.241967]
        for i in range(len(input_list)):
            self.assertAlmostEqual(log10_list[i], expected_list[i], places=6)

    def test_log10_with_zeros_unchanged(self):
        input_list = [101249,
                      94082,
                      0,
                      0,
                      174568]
        log10_list, _ = self.alg(
            input_list, variant_name='IGNORE ZEROS')
        expected_list = [5.005391,
                         4.973507,
                         qgis.QPyNullVariant(float),
                         qgis.QPyNullVariant(float),
                         5.241965]
        for i in range(len(input_list)):
            self.assertAlmostEqual(log10_list[i], expected_list[i], places=6)


class QuadraticTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["QUADRATIC"]
        self.input_list = [80089,
                           83696,
                           249586,
                           121421,
                           120813]

    def test_quadratic_direct_increasing(self):
        quadratic_list, _ = self.alg(
            self.input_list, variant_name="INCREASING", inverse=False)
        expected_list = [0.102969,
                         0.112452,
                         1.000000,
                         0.236672,
                         0.234308]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(
                quadratic_list[i], expected_list[i], places=4)

    def test_quadratic_direct_decreasing(self):
        quadratic_list, _ = self.alg(
            self.input_list, variant_name="DECREASING", inverse=False)
        expected_list = [0.461194,
                         0.441774,
                         0.000000,
                         0.263693,
                         0.266201]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(
                quadratic_list[i], expected_list[i], places=4)

    def test_quadratic_inverse_increasing(self):
        quadratic_list, _ = self.alg(
            self.input_list, variant_name="INCREASING", inverse=True)
        expected_list = [0.897032,
                         0.887548,
                         0.000000,
                         0.763328,
                         0.765692]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(
                quadratic_list[i], expected_list[i], places=4)

    def test_quadratic_inverse_decreasing(self):
        quadratic_list, _ = self.alg(
            self.input_list, variant_name="DECREASING", inverse=True)
        expected_list = [0.538806,
                         0.558266,
                         1.000000,
                         0.736307,
                         0.733799]
        for i in range(len(self.input_list)):
            self.assertAlmostEqual(
                quadratic_list[i], expected_list[i], places=4)


class SigmoidTestCase(unittest.TestCase):

    def setUp(self):
        self.alg = TRANSFORMATION_ALGS["SIGMOID"]

    def test_sigmoid_direct(self):
        input_list = [-1,
                      0,
                      1,
                      -0.3,
                      0.3]
        sigmoid_list, _ = self.alg(input_list)
        expected_list = [0.268941421,
                         0.5,
                         0.7310585790,
                         0.425557483,
                         0.574442517]
        for i in range(len(input_list)):
            self.assertAlmostEqual(
                sigmoid_list[i], expected_list[i], places=4)

    def test_sigmoid_inverse(self):
        input_list = [0.268941421,
                      0.5,
                      0.7310585790,
                      0.425557483,
                      0.574442517]
        sigmoid_list, _ = self.alg(input_list, inverse=True)
        expected_list = [-1,
                         0,
                         1,
                         -0.3,
                         0.3]
        for i in range(len(input_list)):
            self.assertAlmostEqual(
                sigmoid_list[i], expected_list[i], places=4)

    def test_sigmoid_inverse_zero_division(self):
        input_list = [0.268941421,
                      0.5,
                      1,
                      0.425557483,
                      0.574442517]
        sigmoid_list, invalid_input_values = self.alg(input_list, inverse=True)
        expected_list = [-1,
                         0,
                         qgis.QPyNullVariant(float),
                         -0.3,
                         0.3]
        self.assertEqual(invalid_input_values, [1])
        for i in range(len(input_list)):
            if expected_list[i] != qgis.QPyNullVariant(float):
                self.assertAlmostEqual(
                    sigmoid_list[i], expected_list[i], places=4)


if __name__ == '__main__':
    unittest.main()
