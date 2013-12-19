import tempfile

import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from hmtk.parsers.catalogue import csv_catalogue_parser as csv


### TODO. We might need a Singleton version of this
class CatalogueModel(object):
    def __init__(self, catalogue):
        self.catalogue = catalogue
        self.completeness_table = self.default_completeness(catalogue)
        self.recurrence_model_output = None
        self.maximum_magnitude_output = None
        self.smoothed_seismicity_output = None
        self.histogram_output = None

        self.last_computed_completeness_table = None

        catalogue.data['Cluster_Index'] = numpy.zeros(
            catalogue.get_number_events())
        catalogue.data['Cluster_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())
        catalogue.data['Completeness_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())

        self.item_model = self.populate_item_model(catalogue)

    def catalogue_keys(self, catalogue=None):
        cat = catalogue or self.catalogue
        all_keys = [k for k in cat.data.keys()
                    if not (isinstance(cat.data[k], numpy.ndarray) and
                            (cat.data[k] == numpy.nan).all()) and
                       not (isinstance(cat.data[k], list) and
                            not cat.data[k])]

        orders = [
            'eventID', 'Agency',
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'latitude', 'longitude', 'depth',
            'magnitude',
            'Cluster_Index', 'Cluster_Flag', 'Completeness_Flag']
        orders = dict(zip(reversed(orders), range(len(orders))))

        return sorted(all_keys, key=lambda k: -orders.get(k, -1))

    def default_completeness(self, catalogue):
        return numpy.array(
            [[numpy.min(catalogue.data['year']),
              numpy.min(catalogue.data['magnitude'])]])

    def completeness_from_threshold(self, threshold):
        return numpy.array(
            [[numpy.min(self.catalogue.data['year']), threshold]])

    def populate_item_model(self, catalogue):
        """
        Populate the item model with the data from event catalogue
        """
        keys = self.catalogue_keys(catalogue)

        item_model = QtGui.QStandardItemModel(
            catalogue.get_number_events(), len(keys))

        for j, key in enumerate(keys):
            item_model.setHorizontalHeaderItem(j, QtGui.QStandardItem(key))
            for i in range(catalogue.get_number_events()):
                event_data = catalogue.data[key]
                if len(event_data):
                    item_model.setItem(
                        i, j, QtGui.QStandardItem(str(event_data[i])))
        return item_model

    def event_at(self, modelIndex):
        return int(
            self.item_model.data(
                self.item_model.index(
                    modelIndex.row(), self.field_idx('eventID'))))

    @classmethod
    def from_csv_file(cls, fname):
        return cls(csv.CsvCatalogueParser(fname).read_file())

    def declustering(self, algorithm, config):
        cluster_index, cluster_flag = algorithm(self.catalogue, config)
        self.catalogue.data['Cluster_Index'] = cluster_index
        self.catalogue.data['Cluster_Flag'] = cluster_flag

        cluster_index_idx = self.field_idx('Cluster_Index')
        cluster_flag_idx = self.field_idx('Cluster_Flag')

        for i in range(self.catalogue.get_number_events()):
            index = self.item_model.index(i, cluster_index_idx)
            self.item_model.setData(index, str(cluster_index[i]))
            self.item_model.setData(
                index, self.cluster_color(cluster_index[i]), Qt.ForegroundRole)
            index = self.item_model.index(i, cluster_flag_idx)
            self.item_model.setData(index, str(cluster_flag[i]))
        return True

    def purge_decluster(self):
        self.catalogue.purge_catalogue(
            self.catalogue.data['Cluster_Flag'] == 0)
        self.item_model = self.populate_item_model(self.catalogue)

    def purge_completeness(self):
        self.catalogue.purge_catalogue(
            self.catalogue.data['Completeness_Flag'] == 0)
        self.item_model = self.populate_item_model(self.catalogue)

    def completeness(self, algorithm, config):
        self.completeness_table = algorithm(self.catalogue, config)
        self.last_computed_completeness_table = self.completeness_table

        # FIXME(lp). Refactor with Catalogue#catalogue_mt_filter
        flag = numpy.zeros(self.catalogue.get_number_events(), dtype=int)

        for comp_val in self.completeness_table:
            flag[numpy.logical_and(
                self.catalogue.data['year'].astype(float) < comp_val[0],
                self.catalogue.data['magnitude'] < comp_val[1])] = 1
        self.catalogue.data['Completeness_Flag'] = flag

        comp_flag_idx = self.field_idx('Completeness_Flag')

        for i in range(self.catalogue.get_number_events()):
            index = self.item_model.index(i, comp_flag_idx)
            self.item_model.setData(index, str(flag[i]))

            if flag[i]:
                self.item_model.setData(
                    index, QtGui.QColor(200, 200, 200), Qt.BackgroundRole)
        return getattr(algorithm, 'model', None)

    def recurrence_model(self, algorithm, config):
        rec_params = algorithm(self.catalogue, config, self.completeness_table)
        return (config.get('reference_magnitude', None),) + rec_params

    def max_magnitude(self, algorithm, config):
        return algorithm(self.catalogue, config)

    def smoothed_seismicity(self, algorithm, config):
        return algorithm(self.catalogue, config, self.completeness_table)

    def histogram(self, algorithm, config):
        return algorithm(self.catalogue, config)

    def field_idx(self, field):
        return self.catalogue_keys().index(field)

    def cluster_color(self, cluster):
        max_cluster = numpy.max(self.catalogue.data['Cluster_Index'])
        min_cluster = numpy.min(self.catalogue.data['Cluster_Index'])
        breaks = numpy.linspace(min_cluster, max_cluster, 4)
        cluster_range = max_cluster - min_cluster

        if max_cluster == min_cluster:
            return QtGui.QColor(0, 0, 0)

        case = numpy.searchsorted(breaks, cluster)
        if case <= 1:
            r = 0
            g = 255. / cluster_range * (cluster - breaks[0]) * 3.
            b = 255.
        elif case == 2:
            r = 255. / cluster_range * (cluster - breaks[1]) * 3.
            g = 255.
            b = 255. - 255. / cluster_range * (cluster - breaks[1]) * 3.
        elif case >= 3:
            r = 255.
            g = 255. - 255. / cluster_range * (cluster - breaks[2]) * 3.
            b = 0

        return QtGui.QColor(int(r), int(g), int(b))

    def save(self, filename):
        writer = csv.CsvCatalogueWriter(tempfile.mktemp())
        writer.output_file = filename

        writer.write_file(self.catalogue)
