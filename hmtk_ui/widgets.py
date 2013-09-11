from PyQt4 import QtGui, QtCore

from plot_occurrence_model import GutenbergRichterModel, plotSeismicityRates
from completeness_dialog import Ui_Dialog
import numpy

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from hmtk.registry import Registry
from utils import alert


class FigureCanvasQTAggWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=3, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        FigureCanvasQTAgg.__init__(self, self.fig)
        self.setParent(parent)
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.updateGeometry()

    def get_default_filetype(self):
        return "png"

    def draw_occurrences(self, catalogue):
        self.axes.hist(catalogue.data['magnitude'], color="w")
        self.axes.set_xlabel('Magnitude', dict(fontsize=13))
        self.axes.set_ylabel('Occurrences', dict(fontsize=13))
        self.draw()

    def draw_seismicity_rate(self, catalogue, mag, *args):
        self.axes.cla()
        if mag and args:
            b_value, sigma_b, a_value, sigma_a = args
            model = GutenbergRichterModel(b_value,
                                          10 ** (a_value - b_value * mag),
                                          a_val=a_value,
                                          sigma_b=sigma_b,
                                          sigma_a=sigma_a)
        else:
            model = None
        plotSeismicityRates(catalogue).plot(self.axes, model=model)
        self.draw()

    def draw_timeline(self, cat):
        self.axes.plot(cat.get_decimal_time(), cat.data['magnitude'])
        self.axes.set_xlabel('Time', dict(fontsize=13))
        self.axes.set_ylabel('Magnitude', dict(fontsize=13))
        self.draw()

    def draw_completeness(self, model):
        # FIXME(lp). refactor with plot_stepp_1972.py in hmtk
        valid_markers = ['*', '+', '1', '2', '3', '4', '8', '<', '>', 'D', 'H',
                         '^', '_', 'd', 'h', 'o', 'p', 's', 'v', 'x', '|']

        legend_list = [(str(model.magnitude_bin[iloc] + 0.01) + ' - ' +
                        str(model.magnitude_bin[iloc + 1]))
                       for iloc in range(0, len(model.magnitude_bin) - 1)]
        rgb_list, marker_vals = [], []
        # Get marker from valid list
        while len(valid_markers) < len(model.magnitude_bin):
            valid_markers.append(valid_markers)
        marker_sampler = numpy.arange(0, len(valid_markers), 1)
        numpy.random.shuffle(marker_sampler)
        # Get colour for each bin
        for value in range(0, len(model.magnitude_bin) - 1):
            rgb_samp = numpy.random.uniform(0., 1., 3)
            rgb_list.append((rgb_samp[0], rgb_samp[1], rgb_samp[2]))
            marker_vals.append(valid_markers[marker_sampler[value]])
        # Plot observed Sigma lambda
        for iloc in range(0, len(model.magnitude_bin) - 1):
            self.axes.loglog(
                model.time_values, model.sigma[:, iloc],
                linestyle='None', marker=marker_vals[iloc],
                color=rgb_list[iloc])

        self.axes.legend(legend_list)
        # Plot expected Poisson rate
        for iloc in range(0, len(model.magnitude_bin) - 1):
            self.axes.loglog(
                model.time_values, model.model_line[:, iloc],
                linestyle='-', marker='None', color=rgb_list[iloc])
            xmarker = model.end_year - model.completeness_table[iloc, 0]
            id0 = model.model_line[:, iloc] > 0.
            ymarker = 10.0 ** numpy.interp(
                numpy.log10(xmarker), numpy.log10(model.time_values[id0]),
                numpy.log10(model.model_line[id0, iloc]))
            self.axes.loglog(xmarker, ymarker, 'ks')
        self.axes.set_xlabel('Time (years)', dict(fontsize=13))
        self.axes.set_ylabel(
            '$\sigma_{\lambda} = \sqrt{\lambda} / \sqrt{T}$', dict(fontsize=13))
        self.draw()


def add_form(parent, registry, name):
    """
    :param parent: the widget object which contains the form, e.g. a groupbox
    :param registry: a hmtk CatalogueFunctionRegistry instance
    :param str name: the form name. E.g. declustering
    """
    form = QtGui.QFormLayout()
    form.setFieldGrowthPolicy(QtGui.QFormLayout.FieldsStayAtSizeHint)
    form.setObjectName("%s_form" % name)

    method_label = QtGui.QLabel(parent)
    method_label.setText(
        QtGui.QApplication.translate(
            "HMTKWindow", "Method", None, QtGui.QApplication.UnicodeUTF8))
    method_label.setObjectName("%s_method_label" % name)
    form.setWidget(0, QtGui.QFormLayout.LabelRole, method_label)
    combo_box = QtGui.QComboBox(parent)
    combo_box.setObjectName("%s_method_combo" % name)

    combo_box.addItem("")
    for i, name in enumerate(registry, 1):
        combo_box.addItem(name)
        combo_box.setItemText(i, QtGui.QApplication.translate(
            "HMTKWindow", name, None, QtGui.QApplication.UnicodeUTF8))
    form.setWidget(0, QtGui.QFormLayout.FieldRole, combo_box)

    return form, combo_box


def add_fields(form, name, fields, completeness):
    # remove old elements
    while form.count() > 2:
        item = form.takeAt(2)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

    inp_fields = {}
    for i, (field_name, field_spec) in enumerate(fields.items(), 1):
        label = QtGui.QLabel()
        label.setObjectName("%s_%s_label" % (name, field_name))
        label.setText(QtGui.QApplication.translate(
            "HMTKWindow", field_name, None, QtGui.QApplication.UnicodeUTF8))
        form.setWidget(i, QtGui.QFormLayout.LabelRole, label)

        if not isinstance(field_spec, type):
            field_type = type(field_spec)
            value = field_spec
        else:
            field_type = field_spec
            value = None

        if field_type in [float, int]:
            inp = QtGui.QLineEdit()
            inp.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        elif field_type == list:
            if value is None:
                inp = QtGui.QLineEdit()
            else:
                inp = QtGui.QComboBox()
                inp.addItem("")
                inp.setItemText(0, "")

                for j, tag in enumerate(value, 1):
                    inp.addItem(tag)
                    inp.setItemText(j, tag)

        elif field_type == Registry:
            assert value is not None

            inp = QtGui.QComboBox()
            inp.addItem("")
            inp.setItemText(0, "")

            for j, tag in enumerate(value, 1):
                inp.addItem(tag)
                inp.setItemText(j, tag)
        elif field_type == bool:
            value = [str(True), str(False)]
            inp = QtGui.QComboBox()
            inp.addItem("")
            inp.setItemText(0, "")

            for j, tag in enumerate(value, 1):
                inp.addItem(tag)
                inp.setItemText(j, tag)
        else:
            raise RuntimeError("type not recognized %s" % field_type)

        form.setWidget(i, QtGui.QFormLayout.FieldRole, inp)
        inp.setObjectName("%s_%s_input" % (name, field_name))
        inp_fields[field_name] = inp

    if completeness:
        pos = len(inp_fields) + 1

        label = QtGui.QLabel()
        label.setObjectName("%s_completeness_label" % name)
        label.setText(
            QtGui.QApplication.translate(
                "HMTKWindow",
                "Completeness",
                None,
                QtGui.QApplication.UnicodeUTF8))
        form.setWidget(pos, QtGui.QFormLayout.LabelRole, label)

        inp = QtGui.QComboBox()
        options = ["Use the whole catalogue",
                   "Use the computed completeness table",
                   "Specify a completeness threshold",
                   "Input your own table"]
        for i, opt in enumerate(options):
            inp.addItem(opt)
            inp.setItemText(i, opt)
        form.setWidget(pos, QtGui.QFormLayout.FieldRole, inp)
        inp.setObjectName("%s_completeness_input" % name)
        inp_fields["completeness"] = inp

    return inp_fields


def get_config(method, fields):
    config = {}

    for f, field_spec in method.fields.items():
        if not isinstance(field_spec, type):
            field_type = type(field_spec)
            default = field_spec
        else:
            field_type = field_spec
            default = None

        if field_type in [int, float]:
            try:
                value = float(fields[f].text())
            except ValueError:
                value = None
        elif field_type == list:
            if default is None:
                try:
                    value = [float(v) for v in fields[f].text().split(',')]
                    if not value:
                        value = None
                except ValueError:
                    value = None
            else:
                idx = fields[f].currentIndex()
                if not idx:
                    value = None
                else:
                    value = default[idx - 1]
                default = None
        elif field_type == Registry:
            idx = fields[f].currentIndex()
            if not idx:
                value = None
            else:
                value = default.values()[idx - 1]

                if isinstance(value, type):
                    value = value()
            default = None
        elif field_type == bool:
            idx = fields[f].currentIndex()
            if idx == 0:
                value = None
            elif idx == 1:
                value = True
            elif idx == 2:
                value = False

        if value is None:
            if default is None:
                raise ValueError("Field %s is missing" % f)
            else:
                value = default

        config[f] = value

    return config


class CompletenessDialog(QtGui.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(CompletenessDialog, self).__init__(parent)
        self.setupUi(self)
        self.addRowButton.clicked.connect(self.add_row)
        self.removeRowButton.clicked.connect(self.remove_row)

    def add_row(self):
        self.tableWidget.insertRow(self.tableWidget.rowCount())

    def remove_row(self):
        self.tableWidget.removeRow(self.tableWidget.currentRow())

    def get_table(self):
        table = self.tableWidget

        ret = []

        for row in range(table.rowCount()):
            data = [table.item(row, 0).data(0).toString(),
                    table.item(row, 1).data(0).toString()]

            if not data[0]:
                break

            ret.append([float(d) for d in data])

        if not ret:
            alert("Invalid completeness table")

        # sort by year (most recent to oldest)
        ret = sorted(ret, key=lambda row: -row[0])

        # check that magnitude is increasing
        if all(x < y for x, y in zip(ret, ret[1:])):
            alert("""Your completeness table is not properly ordered.
This might cause instability (E.g. in Weichert)""")

        return ret
