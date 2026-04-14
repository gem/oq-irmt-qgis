# -*- coding: utf-8 -*-
# /***************************************************************************
# Irmt
#                                 A QGIS plugin
# OpenQuake Integrated Risk Modelling Toolkit
#                              -------------------
#        begin                : 2013-10-24
#        copyright            : (C) 2014-2026 by GEM Foundation
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

import os
import gc
import pytest
from qgis.core import QgsVectorLayer, QgsField

from svir.calculations.process_layer import ProcessLayer
from svir.utilities.shared import (
    INT_FIELD_TYPE, INT_FIELD_TYPE_NAME,
    STRING_FIELD_TYPE, STRING_FIELD_TYPE_NAME
)


@pytest.fixture
def data_dir():
    """Resolve path to the process_layer data directory."""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir, 'data', 'process_layer'
        )
    )


@pytest.fixture
def projection_layers(data_dir):
    """Load layers for projection testing."""
    subdir = os.path.join(data_dir, 'check_projections')
    layers = {
        'loss_4326': QgsVectorLayer(
            os.path.join(subdir, 'loss_layer_epsg4326.shp'),
            'loss_4326', 'ogr'),
        'zonal_4326': QgsVectorLayer(
            os.path.join(subdir, 'zonal_layer_epsg4326.shp'),
            'zonal_4326', 'ogr'),
        'zonal_4269': QgsVectorLayer(
            os.path.join(subdir, 'zonal_layer_epsg4269.shp'),
            'zonal_4269', 'ogr')
    }
    yield layers
    layers.clear()
    gc.collect()


@pytest.fixture
def compare_layers(data_dir):
    """Load layers for content comparison testing."""
    subdir = os.path.join(data_dir, 'compare')

    layers = {
        'a': QgsVectorLayer(os.path.join(subdir, 'layer_a.shp'), 'a', 'ogr'),
        'b': QgsVectorLayer(os.path.join(subdir, 'layer_b.shp'), 'b', 'ogr'),
        'c': QgsVectorLayer(os.path.join(subdir, 'layer_c.shp'), 'c', 'ogr'),
        'd': QgsVectorLayer(os.path.join(subdir, 'layer_d.shp'), 'd', 'ogr')
    }
    yield layers
    layers.clear()
    gc.collect()


@pytest.fixture
def memory_layer():
    """Create a fresh memory layer for attribute testing."""
    uri = 'Point?crs=epsg:4326'
    return QgsVectorLayer(uri, 'TestLayer', 'memory')


# Projection Tests

def test_same_projections(projection_layers):
    """Test that identical projections are correctly identified."""
    res, _ = ProcessLayer(
        projection_layers['loss_4326']).has_same_projection_as(
            projection_layers['zonal_4326'])
    assert res is True


def test_different_projections(projection_layers):
    """Test that different projections are correctly identified."""
    res, _ = ProcessLayer(
        projection_layers['loss_4326']).has_same_projection_as(
            projection_layers['zonal_4269'])
    assert res is False


# --- Content Comparison Tests ---

def test_same_content_equal_layers(compare_layers):
    """Test layers with identical content."""
    res = ProcessLayer(compare_layers['a']).has_same_content_as(
        compare_layers['b'])
    assert res is True


@pytest.mark.parametrize(
    "primary,secondary", [('c', 'a'), ('a', 'c'), ('a', 'd')])
def test_different_content(compare_layers, primary, secondary):
    """Test various cases where layer content differs."""
    res = ProcessLayer(compare_layers[primary]).has_same_content_as(
        compare_layers[secondary]
    )
    assert res is False


# Attribute Tests

def test_find_attribute_id(memory_layer):
    """Test attribute ID lookup and error handling."""
    field_one = QgsField('first', STRING_FIELD_TYPE)
    field_one.setTypeName(STRING_FIELD_TYPE_NAME)
    field_two = QgsField('second', INT_FIELD_TYPE)
    field_two.setTypeName(INT_FIELD_TYPE_NAME)

    ProcessLayer(memory_layer).add_attributes([field_one, field_two])

    proc = ProcessLayer(memory_layer)
    assert proc.find_attribute_id('first') is not None
    assert proc.find_attribute_id('second') is not None

    with pytest.raises(AttributeError):
        proc.find_attribute_id('dummy')


def test_add_attributes_duplicate_handling(memory_layer):
    """Test that duplicate field names are handled with suffixes."""
    proc = ProcessLayer(memory_layer)

    # Helper to generate fresh field objects to avoid mutation issues
    def get_fields():
        return [
            QgsField('first', STRING_FIELD_TYPE),
            QgsField('second', INT_FIELD_TYPE)
        ]

    # Initial add: expects 'first', 'second'
    res1 = proc.add_attributes(get_fields())
    assert res1 == {'first': 'first', 'second': 'second'}

    # Duplicate names: expects 'first_1', 'second_1'
    res2 = proc.add_attributes(get_fields())
    assert res2 == {'first': 'first_1', 'second': 'second_1'}

    # Triplicate names: expects 'first_2', 'second_2'
    res3 = proc.add_attributes(get_fields())
    assert res3 == {'first': 'first_2', 'second': 'second_2'}
