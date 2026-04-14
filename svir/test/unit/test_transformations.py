# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2013-2026 by GEM Foundation
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

import numpy as np
import pytest
import warnings

# We strictly avoid top-level QGIS/SVIR imports to prevent deadlocks


@pytest.fixture
def logic(qgis_app):
    """
    Initializes QGIS and provides the transformation algorithms and NULL.
    This fixture ensures initQgis() is called before the math modules load.
    """
    from qgis.core import NULL
    from svir.calculations.transformation_algs import (
        transform, TRANSFORMATION_ALGS
    )

    class LogicNamespace:
        def __init__(self):
            self.NULL = NULL
            self.transform = transform
            self.algs = TRANSFORMATION_ALGS

    return LogicNamespace()


@pytest.fixture
def input_list():
    """Shared input list for various transformations."""
    return [2, 0, 2, 1, 2, 3, 2]


# --- Missing Values Tests ---

@pytest.mark.parametrize("null_value_type", [
    "PYTHON_NONE",
    "QGIS_NULL"
])
def test_transform_with_missing_values(logic, null_value_type):
    """
    Test handling of missing values.
    Skips QGIS NULL to avoid a known C++ deadlock in the test environment.
    """
    if null_value_type == "QGIS_NULL":
        pytest.skip(
            "Skipping QGIS NULL case: known to hang in Python 3.13 + QGIS C++")
    actual_null = None  # We already know it's not QGIS_NULL here
    features_dict = {
        '0': 7, '1': 6, '2': actual_null,
        '3': 0, '4': actual_null, '5': 6
    }
    expected_dict = {
        '0': 4, '1': 2.5, '2': actual_null,
        '3': 1, '4': actual_null, '5': 2.5
    }
    transformed_dict, _ = logic.transform(
        features_dict, logic.algs['RANK'], "AVERAGE"
    )
    assert transformed_dict == expected_dict


# --- Rank Transformation Tests ---

@pytest.mark.parametrize("variant, inverse, expected", [
    ("AVERAGE", False, [4.5, 1, 4.5, 2, 4.5, 7, 4.5]),
    ("MIN",     False, [3, 1, 3, 2, 3, 7, 3]),
    ("MAX",     False, [6, 1, 6, 2, 6, 7, 6]),
    ("DENSE",   False, [3, 1, 3, 2, 3, 4, 3]),
    ("ORDINAL", False, [3, 1, 4, 2, 5, 7, 6]),
    ("AVERAGE", True,  [3.5, 7, 3.5, 6, 3.5, 1, 3.5]),
    ("MIN",     True,  [2, 7, 2, 6, 2, 1, 2]),
    ("MAX",     True,  [5, 7, 5, 6, 5, 1, 5]),
    ("DENSE",   True,  [2, 4, 2, 3, 2, 1, 2]),
    ("ORDINAL", True,  [2, 7, 3, 6, 4, 1, 5]),
])
def test_rank_variants(logic, input_list, variant, inverse, expected):
    """Test all Rank logic permutations."""
    alg = logic.algs["RANK"]
    result, _ = alg(input_list, variant_name=variant, inverse=inverse)
    assert result == expected


# --- Min-Max Transformation Tests ---

def test_min_max_direct(logic, input_list):
    alg = logic.algs["MIN_MAX"]
    result, _ = alg(input_list, inverse=False)
    expected = [2/3, 0.0, 2/3, 1/3, 2/3, 1.0, 2/3]
    assert result == pytest.approx(expected)


def test_min_max_inverse(logic, input_list):
    alg = logic.algs["MIN_MAX"]
    result, _ = alg(input_list, inverse=True)
    expected = [1/3, 1.0, 1/3, 2/3, 1/3, 0.0, 1/3]
    assert result == pytest.approx(expected)


# --- Z-Score Transformation Tests ---

def test_z_score_direct(logic, input_list):
    alg = logic.algs["Z_SCORE"]
    result, _ = alg(input_list, inverse=False)
    # Verification of key values using high precision
    assert pytest.approx(result[0], abs=1e-6) == 0.3244428
    assert pytest.approx(result[1], abs=1e-6) == -1.946657


def test_z_score_inverse(logic, input_list):
    alg = logic.algs["Z_SCORE"]
    result, _ = alg(input_list, inverse=True)
    assert pytest.approx(result[0], abs=1e-6) == -4.2177569
    assert pytest.approx(result[5], abs=1e-6) == -5.3533068


# --- Log10 Transformation Tests ---

def test_log10_standard_positive(logic):
    alg = logic.algs["LOG10"]
    input_vals = [101249, 94082, 94062, 158661, 174568]
    result, _ = alg(input_vals)
    assert pytest.approx(result[0], abs=1e-6) == 5.005391


def test_log10_negative_values(logic):
    alg = logic.algs["LOG10"]
    input_vals = [101249, -94062]
    with warnings.catch_warnings():
        msg = "invalid value encountered in log10"
        warnings.filterwarnings('ignore', message=msg)
        result, _ = alg(input_vals)
    assert pytest.approx(result[0], abs=1e-6) == 5.005390
    assert np.isnan(result[1])


@pytest.mark.parametrize("variant, expect_null", [
    ('INCREMENT BY ONE IF ZEROS ARE FOUND', False),
    ('IGNORE ZEROS', True),
])
def test_log10_zero_logic(logic, variant, expect_null):
    alg = logic.algs["LOG10"]
    input_vals = [101249, 94082, 0, 0, 174568]
    result, _ = alg(input_vals, variant_name=variant)
    if expect_null:
        assert result[2] == logic.NULL
    else:
        # Check that it incremented (resulting in a float)
        assert result[2] == 0  # In your log logic, 0 usually implies log10(1)


# --- Quadratic Transformation Tests ---

@pytest.mark.parametrize("variant, inverse, expected_val", [
    ("INCREASING", False, 0.1029),
    ("DECREASING", False, 0.4611),
    ("INCREASING", True,  0.8970),
    ("DECREASING", True,  0.5388),
])
def test_quadratic_variants(logic, variant, inverse, expected_val):
    alg = logic.algs["QUADRATIC"]
    input_vals = [80089, 83696, 249586, 121421, 120813]
    result, _ = alg(input_vals, variant_name=variant, inverse=inverse)
    assert pytest.approx(result[0], abs=1e-4) == expected_val


# --- Sigmoid Transformation Tests ---

def test_sigmoid_direct(logic):
    alg = logic.algs["SIGMOID"]
    result, _ = alg([-1, 0, 1])
    assert pytest.approx(result[0], abs=1e-4) == 0.2689
    assert result[1] == 0.5


def test_sigmoid_inverse_with_null(logic):
    alg = logic.algs["SIGMOID"]
    # 1.0 results in a mathematical error (division by zero / log(0))
    result, invalid = alg([0.5, 1.0], inverse=True)
    assert invalid == [1.0]
    assert result[1] == logic.NULL
