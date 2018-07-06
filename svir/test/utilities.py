
# coding=utf-8
"""Helper module for gui test suite."""


import codecs
import hashlib
import logging
import os
import re
import sys

import processing
from qgis.core import QgsCoordinateReferenceSystem, QgsRectangle
from qgis.PyQt import QtWidgets
from qgis.utils import iface

QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None
LOGGER = logging.getLogger('OpenQuake')
GEOCRS = 4326  # constant for EPSG:GEOCRS Geographic CRS id
GOOGLECRS = 3857  # constant for EPSG:GOOGLECRS Google Mercator id
# DEVNULL = open(os.devnull, 'w')


__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'


def qgis_iface():
    """Helper method to get the iface for testing.

    :return: The QGIS interface.
    :rtype: QgsInterface
    """
    from qgis.utils import iface
    if iface is not None:
        return iface
    else:
        from qgis.testing.mocked import get_iface
        return get_iface()


def get_qgis_app():
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """
    global QGIS_APP, PARENT, IFACE, CANVAS  # pylint: disable=W0603

    if iface:
        from qgis.core import QgsApplication
        QGIS_APP = QgsApplication
        CANVAS = iface.mapCanvas()
        PARENT = iface.mainWindow()
        IFACE = iface
        return QGIS_APP, CANVAS, IFACE, PARENT

    try:
        from qgis.core import QgsApplication
        from qgis.gui import QgsMapCanvas  # pylint: disable=no-name-in-module
        # noinspection PyPackageRequirements
        from qgis.PyQt import QtWidgets, QtCore  # pylint: disable=W0621
        # noinspection PyPackageRequirements
        from qgis.PyQt.QtCore import QCoreApplication, QSettings
        from svir.test.qgis_interface import QgisInterface
    except ImportError:
        return None, None, None, None

    if QGIS_APP is None:
        gui_flag = True  # All test will run qgis in gui mode

        # AG: For testing purposes, we use our own configuration file instead
        # of using the QGIS apps conf of the host
        # noinspection PyCallByClass,PyArgumentList
        QCoreApplication.setOrganizationName('QGIS')
        # noinspection PyCallByClass,PyArgumentList
        QCoreApplication.setOrganizationDomain('qgis.org')
        # noinspection PyCallByClass,PyArgumentList
        QCoreApplication.setApplicationName('QGIS3_OpenQuake_Testing')

        # noinspection PyPep8Naming
        if 'argv' in dir(sys):
            QGIS_APP = QgsApplication([p.encode('utf-8')
                                       for p in sys.argv], gui_flag)
        else:
            QGIS_APP = QgsApplication([], gui_flag)

        # Make sure QGIS_PREFIX_PATH is set in your env if needed!
        QGIS_APP.initQgis()

        # Initialize processing
        processing.Processing.initialize()

        s = QGIS_APP.showSettings()
        LOGGER.debug(s)

        # Save some settings
        settings = QSettings()
        settings.setValue('locale/overrideFlag', True)
        settings.setValue('locale/userLocale', 'en_US')

    if PARENT is None:
        # noinspection PyPep8Naming
        PARENT = QtWidgets.QWidget()

    if CANVAS is None:
        # noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QtCore.QSize(400, 400))

    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        # noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGIS_APP, CANVAS, IFACE, PARENT


def get_dock():
    """Get a dock for testing.

    If you call this function from a QGIS Desktop, you will get the real dock,
    however, you use a fake QGIS interface, it will create a fake dock for you.

    :returns: A dock.
    :rtype: QDockWidget
    """
    # Don't move this import.
    from svir.dialogs.viewer_dock import ViewerDock as DockObject
    if iface:
        docks = iface.mainWindow().findChildren(QtWidgets.QDockWidget)
        for dock in docks:
            if isinstance(dock, DockObject):
                return dock
        else:
            return DockObject(iface)
    else:
        return DockObject(IFACE)


def assert_hash_for_file(hash_string, filename):
    """Assert that a files hash matches its expected hash.
    :param filename:
    :param hash_string:
    """
    file_hash = hash_for_file(filename)
    message = (
        'Unexpected hash'
        '\nGot: %s'
        '\nExpected: %s' % (file_hash, hash_string))
    if file_hash != hash_string:
        raise Exception(message)


def hash_for_file(filename):
    """Return an md5 checksum for a file
    :param filename:
    """
    path = filename
    with open(path, 'rb') as f:
        data = f.read()
    data_hash = hashlib.md5()
    data_hash.update(data)
    data_hash = data_hash.hexdigest()
    return data_hash


def standard_data_path(*args):
    """Return the absolute path to the InaSAFE test data or directory path.

    .. versionadded:: 3.0

    :param *args: List of path e.g. ['control', 'files',
        'test-error-message.txt'] or ['control', 'scenarios'] to get the path
        to scenarios dir.
    :type *args: str

    :return: Absolute path to the test data or dir path.
    :rtype: str

    """
    path = os.path.dirname(__file__)
    path = os.path.abspath(os.path.join(path, 'data'))
    for item in args:
        path = os.path.abspath(os.path.join(path, item))

    return path


def set_canvas_crs(epsg_id, enable_projection=False):
    """Helper to set the crs for the CANVAS before a test is run.

    :param epsg_id: Valid EPSG identifier
    :type epsg_id: int

    :param enable_projection: whether on the fly projections should be
        enabled on the CANVAS. Default to False.
    :type enable_projection: bool

    """

    # Create CRS Instance
    crs = QgsCoordinateReferenceSystem()
    crs.createFromSrid(epsg_id)

    # Reproject all layers to WGS84 geographic CRS
    CANVAS.setDestinationCrs(crs)


def set_jakarta_extent(dock=None):
    """Zoom to an area occupied by both Jakarta layers in Geo.

    :param dock: A dock widget - if supplied, the extents will also be
        set as the user extent and an appropriate CRS set.
    :type dock: Dock
    """
    rect = QgsRectangle(106.52, -6.38, 107.14, -6.07)
    CANVAS.setExtent(rect)
    if dock is not None:
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        dock.define_user_analysis_extent(rect, crs)


def set_jakarta_google_extent(dock=None):
    """Zoom to an area occupied by both Jakarta layers in 900913 crs.

    :param dock: A dock widget - if supplied, the extents will also be
        set as the user extent and an appropriate CRS set.
    :type dock: Dock
    """
    rect = QgsRectangle(11873524, -695798, 11913804, -675295)
    CANVAS.setExtent(rect)
    if dock is not None:
        crs = QgsCoordinateReferenceSystem('EPSG:3857')
        dock.define_user_analysis_extent(rect, crs)


def set_yogya_extent(dock=None):
    """Zoom to an area occupied by both Jakarta layers in Geo.

    :param dock: A dock widget - if supplied, the extents will also be
        set as the user extent and an appropriate CRS set.
    :type dock: Dock
    """
    rect = QgsRectangle(110.348, -7.732, 110.368, -7.716)
    CANVAS.setExtent(rect)
    if dock is not None:
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        dock.define_user_analysis_extent(rect, crs)


def set_small_jakarta_extent(dock=None):
    """Zoom to an area occupied by both Jakarta layers in Geo.

    :param dock: A dock widget - if supplied, the extents will also be
        set as the user extent and an appropriate CRS set.
    :type dock: Dock
    """
    rect = QgsRectangle(106.8382152, -6.1649805, 106.8382152, -6.1649805)
    CANVAS.setExtent(rect)
    if dock is not None:
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        dock.define_user_analysis_extent(rect, crs)


def compare_two_vector_layers(control_layer, test_layer):
    """Compare two vector layers (same geometries and same attributes)

    :param control_layer: The control layer.
    :type control_layer: QgsVectorLayer

    :param test_layer: The layer being checked.
    :type test_layer: QgsVectorLayer

    :returns: Success or failure indicator, message providing notes.
    :rtype: bool, str
    """

    if test_layer.geometryType() != control_layer.geometryType():
        return False, 'These two layers are not using the same geometry type.'

    if test_layer.crs().authid() != control_layer.crs().authid():
        return False, 'These two layers are not using the same CRS.'

    if test_layer.featureCount() != control_layer.featureCount():
        return False, 'These two layers haven\'t the same number of features'

    for feature in test_layer.getFeatures():
        for expected in control_layer.getFeatures():
            if feature.attributes() == expected.attributes():
                if feature.geometry().isGeosEqual(expected.geometry()):
                    break
        else:
            return False, 'A feature could not be found in the control layer.'
    else:
        return True, None


class RedirectStreams():
    """Context manager for redirection of stdout and stderr.

    This is from
    http://stackoverflow.com/questions/6796492/
    python-temporarily-redirect-stdout-stderr

    In this context, the class is used to get rid of QGIS
    output in the test suite - BUT IT DOESN'T WORK (Maybe
    because QGIS starts its providers in a different process?)

    Usage:

    devnull = open(os.devnull, 'w')
    print('Fubar')

    with RedirectStreams(stdout=devnull, stderr=devnull):
        print("You'll never see me")

    print("I'm back!")
    """

    def __init__(self, stdout=None, stderr=None):
        """

        :param stdout:
        :param stderr:
        """
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr
        self.old_stdout = None
        self.old_stderr = None

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr


def get_ui_state(dock):
    """Get state of the 3 combos on the DOCK dock.

    This method is purely for testing and not to be confused with the
    saveState and restoreState methods of dock.

    :param dock: The dock instance to get the state from.
    :type dock: Dock

    :returns: A dictionary of key, value pairs. See below for details.
    :rtype: dict

    Example return:: python

        {'Hazard': 'flood',
         'Exposure': 'population',
         'Run Button Enabled': False}

    """

    hazard = str(dock.hazard_layer_combo.currentText())
    exposure = str(dock.exposure_layer_combo.currentText())
    run_button = dock.run_button.isEnabled()

    return {'Hazard': hazard,
            'Exposure': exposure,
            'Run Button Enabled': run_button}


def canvas_list():
    """Return a string representing the list of canvas layers.

    :returns: The returned string will list layers in correct order but
        formatted with line breaks between each entry.
    :rtype: str
    """
    list_string = ''
    for layer in CANVAS.layers():
        list_string += layer.name() + '\n'
    return list_string


def combos_to_string(dock):
    """Helper to return a string showing the state of all combos.

    :param dock: A dock instance to get the state of combos from.
    :type dock: Dock

    :returns: A descriptive list of the contents of each combo with the
        active combo item highlighted with a >> symbol.
    :rtype: unicode
    """

    string = 'Hazard Layers\n'
    string += '-------------------------\n'
    current_id = dock.hazard_layer_combo.currentIndex()
    for count in range(0, dock.hazard_layer_combo.count()):
        item_text = dock.hazard_layer_combo.itemText(count)
        if count == current_id:
            string += '>> '
        else:
            string += '   '
        string += item_text + '\n'
    string += '\n'
    string += 'Exposure Layers\n'
    string += '-------------------------\n'
    current_id = dock.exposure_layer_combo.currentIndex()
    for count in range(0, dock.exposure_layer_combo.count()):
        item_text = dock.exposure_layer_combo.itemText(count)
        if count == current_id:
            string += '>> '
        else:
            string += '   '
        string += item_text + '\n'

    string += '\n'
    string += 'Aggregation Layers\n'
    string += '-------------------------\n'
    current_id = dock.aggregation_layer_combo.currentIndex()
    for count in range(0, dock.aggregation_layer_combo.count()):
        item_text = dock.aggregation_layer_combo.itemText(count)
        if count == current_id:
            string += '>> '
        else:
            string += '   '
        string += item_text + '\n'

    string += '\n\n >> means combo item is selected'
    return string


def setup_scenario(
        dock,
        hazard,
        exposure,
        ok_button_flag=True,
        aggregation_layer=None,
        aggregation_enabled_flag=None):
    """Helper function to set the gui state to a given scenario.

    :param dock: Dock instance.
    :type dock: Dock

    :param hazard: Name of the hazard combo entry to set.
    :type hazard: str

    :param exposure: Name of exposure combo entry to set.
    :type exposure: str

    :param function: Name of the function combo entry to set.
    :type function: str

    :param function_id: Impact function id that should be used.
    :type function_id: str

    :param ok_button_flag: Optional - whether the ok button should be enabled
            after this scenario is set up.
    :type ok_button_flag: bool

    :param aggregation_layer: Optional - which layer should be used for
            aggregation
    :type aggregation_layer: str

    :param aggregation_enabled_flag: Optional -whether it is expected that
            aggregation should be enabled when the scenario is loaded.
    :type aggregation_enabled_flag: bool

    We require both function and function_id because safe allows for
    multiple functions with the same name but different id's so we need to be
    sure we have the right one.

    .. note:: Layers are not actually loaded - the calling function is
        responsible for that.

    :returns: Two tuple indicating if the setup was successful, and a message
        indicating why it may have failed.
    :rtype: (bool, str)
    """
    if hazard is not None:
        index = dock.hazard_layer_combo.findText(hazard)
        message = ('\nHazard Layer Not Found: %s\n Combo State:\n%s' %
                   (hazard, combos_to_string(dock)))
        if index == -1:
            return False, message
        dock.hazard_layer_combo.setCurrentIndex(index)

    if exposure is not None:
        index = dock.exposure_layer_combo.findText(exposure)
        message = ('\nExposure Layer Not Found: %s\n Combo State:\n%s' %
                   (exposure, combos_to_string(dock)))
        if index == -1:
            return False, message
        dock.exposure_layer_combo.setCurrentIndex(index)

    if aggregation_layer is not None:
        index = dock.aggregation_layer_combo.findText(aggregation_layer)
        message = ('Aggregation layer Not Found: %s\n Combo State:\n%s' %
                   (aggregation_layer, combos_to_string(dock)))
        if index == -1:
            return False, message
        dock.aggregation_layer_combo.setCurrentIndex(index)

    if aggregation_enabled_flag is not None:
        combo_enabled_flag = dock.aggregation_layer_combo.isEnabled()
        if combo_enabled_flag != aggregation_enabled_flag:
            message = (
                'The aggregation combobox should be %s' %
                ('enabled' if aggregation_enabled_flag else 'disabled'))
            return False, message

    # Check that layers and impact function are correct
    state = get_ui_state(dock)

    expected_state = {'Run Button Enabled': ok_button_flag,
                      'Hazard': hazard,
                      'Exposure': exposure}

    message = 'Expected versus Actual State\n'
    message += '--------------------------------------------------------\n'

    for key in list(expected_state.keys()):
        message += 'Expected %s: %s\n' % (key, expected_state[key])
        message += 'Actual   %s: %s\n' % (key, state[key])
        message += '----\n'
    message += '--------------------------------------------------------\n'
    message += combos_to_string(dock)

    if state != expected_state:
        return False, message

    return True, 'Matched ok.'


def compare_wkt(a, b, tol=0.000001):
    """Helper function to compare WKT geometries with given tolerance
    Taken from QGIS test suite

    :param a: Input WKT geometry
    :type a: str

    :param b: Expected WKT geometry
    :type b: str

    :param tol: compare tolerance
    :type tol: float

    :return: True on success, False on failure
    :rtype: bool
    """
    r = re.compile(r'-?\d+(?:\.\d+)?(?:[eE]\d+)?')

    # Text might upper or lower case
    a = a.upper()
    b = b.upper()

    # Might have a space between the text and coordinates
    geometry_type = a.split('(', 1)
    a = geometry_type[0].replace(' ', '') + '('.join(geometry_type[1:])
    geometry_type = b.split('(', 1)
    b = geometry_type[0].replace(' ', '') + '('.join(geometry_type[1:])

    # compare the structure
    a0 = r.sub("#", a)
    b0 = r.sub("#", b)
    if a0 != b0:
        return False

    # compare the numbers with given tolerance
    a0 = r.findall(a)
    b0 = r.findall(b)
    if len(a0) != len(b0):
        return False

    for (a1, b1) in zip(a0, b0):
        if abs(float(a1) - float(b1)) > tol:
            return False

    return True


def remove_vector_temp_file(file_path):
    """Helper function that removes temp file created during test.

    Also its keywords file will be removed.

    :param file_path: File path to be removed.
    :type file_path: str
    """
    file_path = file_path[:-4]
    extensions = ['.shp', '.shx', '.dbf', '.prj', '.xml']
    extensions.extend(['.prj', '.sld', 'qml'])
    for ext in extensions:
        if os.path.exists(file_path + ext):
            os.remove(file_path + ext)


class FakeLayer():

    """A Mock layer.

    :param source:
    """

    def __init__(self, source=None):
        self.layer_source = source

    def source(self):
        """Get the sources as defined in init

        :return: sources
        """
        return self.layer_source


def get_control_text(file_name):
    """Helper to get control text for string compares.

    :param file_name: filename
    :type file_name: str

    :returns: A string containing the contents of the file.
    """
    control_file_path = standard_data_path(
        'control',
        'files',
        file_name
    )
    with codecs.open(
            control_file_path,
            mode='r',
            encoding='utf-8') as f:
        return f.readlines()
    return ''


def dict_values_sorted(d):
    """
    Make sure dict values are sorted when they are sortable.
    This also works for lists of dicts nd discts of lists
    """
    if isinstance(d, list):
        _l = [dict_values_sorted(v) for v in d]
        _l.sort(key=lambda x: x if not isinstance(x, dict)
                else ''.join([str(_x)
                              for _x in x.values()]))
        return _l
    elif isinstance(d, dict):
        return {k: dict_values_sorted(v) for k, v in d.items()}
    else:
        return d


def assert_and_emit(signal, assertion, p1, p2, msg):
    try:
        assertion(p1, p2, msg)
    except Exception as exc:
        signal.emit(exc)
        raise exc
