import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import (QVariant, Qt)

from hmtk.parsers.catalogue import CsvCatalogueParser
from hmtk.seismicity.declusterer import (
    dec_gardner_knopoff, dec_afteran, distance_time_windows)


class CatalogueModel(object):
    def __init__(self, catalogue, observer):
        self.catalogue = catalogue
        catalogue.data['Cluster_Index'] = numpy.zeros(
            catalogue.get_number_events())
        catalogue.data['Cluster_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())

        self.item_model = QtGui.QStandardItemModel(
            catalogue.get_number_events(),
            len(catalogue.data),
            observer)

        keys = sorted(catalogue.data.keys())

        for j, key in enumerate(keys):
            self.item_model.setHorizontalHeaderItem(
                j, QtGui.QStandardItem(key))
            for i in range(self.catalogue.get_number_events()):
                event_data = self.catalogue.data[key]
                if len(event_data):
                    self.item_model.setItem(
                        i, j, QtGui.QStandardItem(str(event_data[i])))

    def at(self, modelIndex):
        return self.item_model.data(modelIndex).toPyObject()

    def eventIdAt(self, modelIndex):
        return int(
            self.item_model.data(
                self.item_model.index(
                    modelIndex.row(), self.field_idx('eventID'))).toPyObject())

    @classmethod
    def from_csv_file(cls, fname, observer):
        return cls(CsvCatalogueParser(fname).read_file(), observer)

    def decluster(self, method_index, twf_index, tw):
        method = [None,
                  dec_gardner_knopoff.GardnerKnopoffType1,
                  dec_afteran.Afteran][method_index]
        twf = [None,
               distance_time_windows.UhrhammerWindow,
               distance_time_windows.GardnerKnopoffWindow][twf_index]

        try:
            time_window = float(tw)
        except ValueError:
            time_window = -1

        if method is not None and twf is not None and time_window > 0:
            cluster_index, cluster_flag = method().decluster(
                self.catalogue, {'time_distance_window': twf(),
                                 'fs_time_prop': time_window,
                                 'time_window': time_window})
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

    def purge_decluster(self):
        self.catalogue.purge_catalogue(
            self.catalogue.data['Cluster_Flag'] == 0)

    def field_idx(self, field):
        return sorted(self.catalogue.data.keys()).index(field)

    def cluster_color(self, cluster):
        r = cluster % 255
        g = (cluster + 85) % 255
        b = (cluster + 170) % 255
        return QtGui.QColor(r, g, b)
