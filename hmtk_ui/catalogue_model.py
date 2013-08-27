import tempfile

import numpy

from PyQt4 import QtGui
from PyQt4.QtCore import (QVariant, Qt)

from hmtk.parsers.catalogue import csv_catalogue_parser as csv
from hmtk.seismicity.declusterer import (
    dec_gardner_knopoff, dec_afteran, distance_time_windows)
from hmtk.seismicity.completeness.comp_stepp_1971 import Stepp1971


class CatalogueModel(object):
    def __init__(self, catalogue, observer):
        self.catalogue = catalogue
        self.magnitude_table = None

        catalogue.data['Cluster_Index'] = numpy.zeros(
            catalogue.get_number_events())
        catalogue.data['Cluster_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())
        catalogue.data['Completeness_Flag'] = numpy.zeros(
            self.catalogue.get_number_events())
        self.item_model = QtGui.QStandardItemModel(
            catalogue.get_number_events(),
            len(catalogue.data),
            observer)
        self.populate_item_model()

    def populate_item_model(self):
        keys = sorted(self.catalogue.data.keys())

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

    def event_at(self, modelIndex):
        return int(
            self.item_model.data(
                self.item_model.index(
                    modelIndex.row(), self.field_idx('eventID'))).toPyObject())

    @classmethod
    def from_csv_file(cls, fname, observer):
        return cls(csv.CsvCatalogueParser(fname).read_file(), observer)

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
        else:
            return False

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
        if self.catalogue.purge_catalogue(
                self.catalogue.data['Cluster_Flag'] == 0):
            self.populate_item_model()

    def completeness(self, magnitude_bin, time_bin, increment_lock):
        try:
            magnitude_bin = float(magnitude_bin)
            time_bin = float(time_bin)
            increment_lock = [None, True, False][increment_lock]
        except ValueError:
            magnitude_bin = -1
            time_bin = -1
            increment_lock = None

        if magnitude_bin > 0 and time_bin > 0 and increment_lock is not None:
            comp_config = {'magnitude_bin': magnitude_bin,
                           'time_bin': time_bin,
                           'increment_lock': increment_lock}
            analysis = Stepp1971()
            self.magnitude_table = analysis.completeness(
                self.catalogue, comp_config)

            # FIXME(lp). Refactor with Catalogue#catalogue_mt_filter
            flag = numpy.zeros(self.catalogue.get_number_events(), dtype=int)

            for comp_val in self.magnitude_table:
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
            return analysis

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
