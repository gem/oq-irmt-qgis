import numpy

from PyQt4 import QtGui, QtCore

from hmtk.registry import Registry
from hmtk.seismicity.smoothing.smoothed_seismicity import Grid

from widgets import GridInputWidget


class Tab(object):
    """
    This class is responsible to model a tab frame with the following
    structure:

    1) a method selector got from a `registry`
    2) a set of input fields, where fields depend on the selected method
    3) one or more action buttons

    :attr str name: the form name. E.g. declustering
    :attr layout: the layout into which the form will be inserted
    :attr registry: a hmtk CatalogueFunctionRegistry instance
    :attr list action_buttons: a list of submit buttons
    """
    def __init__(self, name, layout, registry, action_buttons):
        self.name = name
        self.layout = layout
        self.registry = registry
        self.action_buttons = action_buttons

        # to be set in setup_form
        self.form = None
        self.method_combo = None

        # to be set in update_form
        self.param_fields = None

    def method(self):
        """
        :returns: the current method selected (a callable)
        """
        # we decrease by one the index as we assume that the first
        # choice in the combo box is the "No method selected"
        return self.registry.values()[self.method_combo.currentIndex() - 1]

    def setup_form(self, method_select_cb):
        """
        Setup the form with a combo box for selecting the method

        :param method_select_cb:
            a callback to be called when a method is selected
        """

        # create the form layout
        self.form = QtGui.QFormLayout()
        self.form.setFieldGrowthPolicy(QtGui.QFormLayout.FieldsStayAtSizeHint)
        self.form.setObjectName("%s_form" % self.name)

        # create the combo box for the methods
        label = self._create_label("method")
        self.form.setWidget(0, QtGui.QFormLayout.LabelRole, label)

        self.method_combo = create_combo("method", self.name, self.registry)
        self.form.setWidget(0, QtGui.QFormLayout.FieldRole, self.method_combo)

        self.layout.insertLayout(0, self.form)

        # hide action buttons
        self.hide_action_buttons()

        self.method_combo.currentIndexChanged.connect(method_select_cb)

    def _create_label(self, name):
        """
        Utility to create a label from `name`
        """
        label = QtGui.QLabel()
        label.setText(
            QtGui.QApplication.translate(
                "HMTKWindow", name, None, QtGui.QApplication.UnicodeUTF8))
        label.setObjectName("%s_%s_label" % (name, self.name))
        return label

    def hide_action_buttons(self):
        for b in self.action_buttons:
            b.hide()

    def show_action_buttons(self):
        for b in self.action_buttons:
            b.show()

    def clear_form(self):
        """
        Reset form by removing all the fields
        """
        while self.form.count() > 2:
            item = self.form.takeAt(2)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.param_fields = {}

    def update_form(self, catalogue, completeness_cb):
        """
        Once that a method has been selected, we reset the form, by
        populating it with fields taken from `registry`. If the method
        takes in input a positional argument of type completeness, then
        we add a proper combo box to the bottom of the form.

        :param catalogue:
            a hmtk.seismicity.catalogue.Catalogue instance (used to
            get default values)
        :param completeness_cv:
            a callback to be called when a method to select a completeness
            table is chosen
        """
        self.clear_form()

        method = self.method()
        for i, (field_name, field_spec) in enumerate(method.fields.items(), 1):
            label = self._create_label(field_name)
            self.form.setWidget(i, QtGui.QFormLayout.LabelRole, label)

            field_type, value = Field.type_value(field_spec, catalogue)
            field = FIELD_REGISTRY[field_type](field_name, self, catalogue)
            self.form.setWidget(
                i, QtGui.QFormLayout.FieldRole, field.create_widget(value))
            self.param_fields[field_name] = field

        if method.completeness:
            pos = len(self.param_fields) + 1

            label = self._create_label("completeness")
            self.form.setWidget(pos, QtGui.QFormLayout.LabelRole, label)

            inp = create_combo(
                "completeness", self.name,
                ["Use the whole catalogue",
                 "Use the computed completeness table",
                 "Specify a completeness threshold",
                 "Input your own table"],
                no_opt=False)
            self.form.setWidget(pos, QtGui.QFormLayout.FieldRole, inp)
            inp.activated.connect(completeness_cb)

    def get_config(self):
        """
        Get a config object filled with values got from the form
        """
        config = {}

        for f in self.method().fields:
            value = self.param_fields[f].get_value()

            if value is None:
                raise ValueError("Field %s is missing" % f)

            config[f] = value

        return config


def create_combo(field_name, prefix_name, choices, no_opt=True):
    """
    Utility to create a combo box from `choices`

    :param choices: an iterable over strings used as option names
    :param bool no_opt: True if an empty option should be inserted
    """
    combo_box = QtGui.QComboBox()
    combo_box.setObjectName("%s_%s_combo" % (field_name, prefix_name))

    if no_opt:
        combo_box.addItem("")

    # add each method as options for the combo box
    for i, name in enumerate(choices, 1):
        combo_box.addItem(name)
        combo_box.setItemText(i, QtGui.QApplication.translate(
            "HMTKWindow", name, None, QtGui.QApplication.UnicodeUTF8))
    return combo_box


FIELD_REGISTRY = Registry()


class Field(object):
    """
    a Field object models a form field meant to be used for input
    parameters of catalogue functions (i.e. hmtk functions registered
    in a hmtk.Registry).

    Derived classes must implement #create_widget (that builds a Qt
    Widget), and #get_value (which extracts the value from the Qt
    Widget)
    """
    def __init__(self, field_name, tab, catalogue):
        self.field_name = field_name
        self.tab = tab
        self.catalogue = catalogue

        # to be set in #create_widget
        self.widget = None

    @staticmethod
    def type_value(field_spec, catalogue):
        """
        :param field_spec:
           a field_spec as registered in a hmtk registry.
        :returns:
           a tuple with a field_type object (a `type` instance, or a list)
           and a value (which represents a default value or a list of possible
           choices).
        """
        if not isinstance(field_spec, type):
            if isinstance(field_spec, type(lambda x: x)):
                field_spec = field_spec(catalogue)
            field_type = type(field_spec)
            value = field_spec
        else:
            field_type = field_spec
            value = None
        return field_type, value

    def create_widget(self, value):
        self.widget = self._create_widget(value)
        self.widget.setObjectName(
            "%s_%s_input" % (self.tab.name, self.field_name))
        return self.widget

    def _create_widget(self, value):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError


@FIELD_REGISTRY.add(float)
@FIELD_REGISTRY.add(numpy.float64)
class FloatField(Field):
    def _create_widget(self, default_value):
        inp = QtGui.QLineEdit()
        inp.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        if default_value is not None:
            inp.setText(str(default_value))
        return inp

    def get_value(self):
        if self.widget_text():
            value = float(self.widget.text())
        else:
            value = None

        return value


@FIELD_REGISTRY.add(int)
class IntField(FloatField):
    def get_value(self):
        if self.widget_text():
            value = int(self.widget.text())
        else:
            value = None

        return value


@FIELD_REGISTRY.add(list)
class ChoiceField(Field):
    def __init__(self, *args, **kwargs):
        super(ChoiceField, self).__init__(*args, **kwargs)
        self.choices = False

    def _create_widget(self, choices):
        self.choices = choices
        if choices is None:  # list of values
            inp = QtGui.QLineEdit()
        else:
            inp = create_combo(self.field_name, self.tab.name, choices)
        return inp

    def get_value(self):
        if self.choices is None:
            try:
                value = [float(v) for v in self.widget.text().split(',')]
                if not value:
                    value = None
            except ValueError:
                value = None
        else:
            idx = self.widget.currentIndex()
            if not idx:
                value = None
            else:
                value = self.choices[idx - 1]

        return value


@FIELD_REGISTRY.add(Registry)
class RegistryField(ChoiceField):
    def _create_widget(self, choices):
        inp = super(RegistryField, self)._create_widget(choices)
        self.choices = [v() for v in choices.values()]
        return inp


@FIELD_REGISTRY.add(bool)
class BooleanField(Field):
    def _create_widget(self, _value):
        return create_combo(self.field_name, self.tab.name, ["True", "False"])

    def get_value(self):
        idx = self.widget.currentIndex()
        if idx == 0:
            value = None
        elif idx == 1:
            value = True
        elif idx == 2:
            value = False
        return value


@FIELD_REGISTRY.add(Grid)
class GridField(Field):
    def _create_widget(self, value):
        return GridInputWidget(self.catalogue, self.tab.param_fields)

    def get_value(self):
        return self.widget.grid
