import tempfile

import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import (QVariant, Qt)

from hmtk.parsers.catalogue import csv_catalogue_parser as csv


class CatalogueModel(object):
    def __init__(self, catalogue, observer):
        self.catalogue = catalogue
        self.completeness_table = None

        catalogue.data['Cluster_Index'] = numpy.zeros(
            catalogue.get_number_events())
        catalogue.data['Cluster_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())
        catalogue.data['Completeness_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())

        self.observer = observer
        self.item_model = self.populate_item_model(self.catalogue)

    def populate_item_model(self, catalogue):
        """
        Populate the item model with the data from event catalogue
        """
        item_model = QtGui.QStandardItemModel(
            catalogue.get_number_events(),
            len(catalogue.data),
            self.observer)

        keys = sorted(catalogue.data.keys())

        for j, key in enumerate(keys):
            item_model.setHorizontalHeaderItem(
                j, QtGui.QStandardItem(key))
            for i in range(catalogue.get_number_events()):
                event_data = catalogue.data[key]
                if len(event_data):
                    item_model.setItem(
                        i, j, QtGui.QStandardItem(str(event_data[i])))
        return item_model

    def at(self, modelIndex):
        return self.item_model.data(modelIndex).toPyObject()

    def event_at(self, modelIndex):
        return int(
            self.item_model.data(
                self.item_model.index(
                    modelIndex.row(), self.field_idx('eventID'))).toPyObject())

    @classmethod
    def from_csv_file(cls, fname, observer):
        return cls(csv.CsvCatalogueParser(fname).read_file(), observer)

    def decluster(self, method, config):
        cluster_index, cluster_flag = method(self.catalogue, config)
        self.catalogue.data['Cluster_Index'] = cluster_index
        self.catalogue.data['Cluster_Flag'] = cluster_flag

        cluster_index_idx = self.field_idx('Cluster_Index')
        cluster_flag_idx = self.field_idx('Cluster_Flag')

        for i in range(self.catalogue.get_number_events()):
            index = self.item_model.index(i, cluster_index_idx)
            self.item_model.setData(
                index, QVariant(str(cluster_index[i])))
            self.item_model.setData(
                index, self.cluster_color(cluster_index[i]), Qt.ForegroundRole)
            index = self.item_model.index(i, cluster_flag_idx)
            self.item_model.setData(
                index, QVariant(str(cluster_flag[i])))
        return True

    def purge_decluster(self):
        self.catalogue.purge_catalogue(
            self.catalogue.data['Cluster_Flag'] == 0)
        self.item_model = self.populate_item_model(self.catalogue)

    def purge_completeness(self):
        self.catalogue.purge_catalogue(
            self.catalogue.data['Completeness_Flag'] == 0)
        self.item_model = self.populate_item_model(self.catalogue)

    def completeness(self, method, config):
        self.completeness_table = method(self.catalogue, config)

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
            self.item_model.setData(index, QVariant(str(flag[i])))

            if flag[i]:
                self.item_model.setData(
                    index, QtGui.QColor(200, 200, 200), Qt.BackgroundRole)
        return getattr(method, 'model', None)

    def field_idx(self, field):
        return sorted(self.catalogue.data.keys()).index(field)

    def cluster_color(self, cluster):
        r = cluster % 255
        g = (cluster + 85) % 255
        b = (cluster + 170) % 255
        return QtGui.QColor(r, g, b)

    def save(self, filename):
        writer = csv.CsvCatalogueWriter(tempfile.mktemp())
        writer.output_file = filename

        writer.write_file(self.catalogue)
