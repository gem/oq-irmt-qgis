import numpy

from hmtk.registry import CatalogueFunctionRegistry
from hmtk.seismicity.utils import bootstrap_histogram_1D

CATALOGUE_ANALYSIS_METHODS = CatalogueFunctionRegistry()


@CATALOGUE_ANALYSIS_METHODS.add_function(
    depth_bins_nr=numpy.int, normalisation=bool, bootstrap=bool)
def depth_distribution(
        catalogue, depth_bins_nr, normalisation, bootstrap):
    bins = numpy.linspace(catalogue.data['depth'].min(),
                          catalogue.data['depth'].max(),
                          depth_bins_nr + 1)
    return (bins,
            catalogue.get_depth_distribution(bins, normalisation, bootstrap))


@CATALOGUE_ANALYSIS_METHODS.add_function(
    magnitude_bins_nr=numpy.int, normalisation=bool, bootstrap=bool)
def magnitude_distribution(
        catalogue, magnitude_bins_nr, normalisation, bootstrap):
    bins = numpy.linspace(catalogue.data['magnitude'].min(),
                          catalogue.data['magnitude'].max(),
                          magnitude_bins_nr + 1)
    return bins, bootstrap_histogram_1D(
        catalogue.data['magnitude'],
        bins,
        catalogue.data.get('sigmaMagnitude', numpy.zeros(
            catalogue.get_number_events(), dtype=float)),
        normalisation=normalisation,
        number_bootstraps=bootstrap,
        boundaries=(0., None))


@CATALOGUE_ANALYSIS_METHODS.add_function(
    magnitude_bins_nr=numpy.int, depth_bins_nr=numpy.int,
    normalisation=bool, bootstrap=bool)
def magnitude_depth_distribution(
        catalogue, magnitude_bins_nr, depth_bins_nr, normalisation, bootstrap):
    x_bins = numpy.linspace(catalogue.data['magnitude'].min(),
                            catalogue.data['magnitude'].max(),
                            magnitude_bins_nr + 1)
    y_bins = numpy.linspace(catalogue.data['depth'].min(),
                            catalogue.data['depth'].max(),
                            depth_bins_nr + 1)
    return x_bins, y_bins, catalogue.get_magnitude_depth_distribution(
        x_bins, y_bins, normalisation, bootstrap)


@CATALOGUE_ANALYSIS_METHODS.add_function(
    magnitude_bins_nr=numpy.int, time_bins_nr=numpy.int,
    normalisation=bool, bootstrap=bool)
def magnitude_time_distribution(
        catalogue, magnitude_bins_nr, time_bins_nr, normalisation, bootstrap):
    x_bins = numpy.linspace(catalogue.data['magnitude'].min(),
                            catalogue.data['magnitude'].max(),
                            magnitude_bins_nr + 1)
    y_bins = numpy.linspace(catalogue.get_decimal_time().min(),
                            catalogue.get_decimal_time().max(),
                            time_bins_nr + 1)
    return x_bins, y_bins, catalogue.get_magnitude_time_distribution(
        x_bins, y_bins, normalisation, bootstrap)
