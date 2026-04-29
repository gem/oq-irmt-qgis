import os
import sys
import time
import pytest
from qgis.gui import QgsMapCanvas, QgsLayerTreeView
from qgis.core import QgsProject, QgsApplication, QgsLayerTreeModel
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QMenuBar, QMenu, QToolBar, QMainWindow
from qgis.testing.mocked import get_iface
from qgis.testing import start_app


os.environ['GEM_QGIS_TEST'] = '1'


# Update sys.path BEFORE any svir or processing imports
standard_plugin_path = '/usr/share/qgis/python/plugins'
if (os.path.exists(standard_plugin_path)
        and standard_plugin_path not in sys.path):
    sys.path.append(standard_plugin_path)


@pytest.fixture(scope="session")
def qgis_app():
    """Initializes QGIS and Processing."""
    # Use start_app to handle the instance creation properly
    app = start_app()

    # Set required QSettings defaults for headless test environment
    QSettings().setValue("locale/userLocale", "en_US")
    QSettings().setValue("locale/overrideFlag", False)

    # Initialize Processing within the fixture
    try:
        import processing  # NOQA
        from processing.core.Processing import Processing
        Processing.initialize()
    except ImportError:
        pytest.fail("Could not import 'processing'.")
    yield app
    # QgsApplication.exitQgis()


@pytest.fixture(scope="session")
def irmt_plugin(qgis_app):
    """Initializes the IRMT plugin and logs into the OQ Engine."""
    from svir.irmt import Irmt
    iface = get_iface()

    # Provide real Qt objects where the mock returns values used directly by Qt
    main_window = QMainWindow()
    menu_bar = QMenuBar(main_window)
    main_window.setMenuBar(menu_bar)

    dummy_menu = QMenu("OpenQuake IRMT", menu_bar)
    menu_bar.addMenu(dummy_menu)

    toolbar = QToolBar()
    canvas = QgsMapCanvas(main_window)
    iface.mapCanvas.return_value = canvas

    layer_tree_view = QgsLayerTreeView(main_window)
    # Connect the tree view to the project's layer tree, in order to ensure
    # that the view actually sees layers added via project.addMapLayer()
    model = QgsLayerTreeModel(QgsProject.instance().layerTreeRoot())
    layer_tree_view.setModel(model)
    iface.layerTreeView.return_value = layer_tree_view

    # This makes the mock return the actual last-added layer from the project
    def get_real_active_layer():
        layers = list(QgsProject.instance().mapLayers().values())
        return layers[-1] if layers else None
    iface.activeLayer.side_effect = get_real_active_layer

    iface.mainWindow.return_value = main_window
    iface.addToolBar.return_value = toolbar
    iface.firstRightStandardMenu.return_value = dummy_menu

    initial_experimental_enabled = QSettings().value(
        '/irmt/experimental_enabled', False, type=bool)
    QSettings().setValue('irmt/experimental_enabled', True)

    plugin = Irmt(iface)
    plugin.initGui()

    # Prevent Python garbage collection of Qt objects during the session
    plugin._main_window_ref = main_window
    plugin._layer_tree_view_ref = layer_tree_view

    hostname = os.environ.get('OQ_ENGINE_HOST', 'http://localhost:8800')
    plugin.drive_oq_engine_server(
        show=False, hostname=hostname,
        username='level_0_user', password='level_0_password')
    yield plugin
    # Teardown
    QSettings().setValue('irmt/experimental_enabled',
                         initial_experimental_enabled)


@pytest.fixture(scope="session")
def oq_calculations(irmt_plugin):
    """Retrieves and filters the list of calculations."""
    calc_list = irmt_plugin.drive_oq_engine_server_dlg.calc_list
    if isinstance(calc_list, Exception):
        raise calc_list
    try:
        only_calc_id = int(os.environ.get('ONLY_CALC_ID'))
        return [calc for calc in calc_list if calc['id'] == only_calc_id]
    except (ValueError, TypeError):
        return calc_list


@pytest.fixture(scope="session")
def oq_outputs(irmt_plugin, oq_calculations):
    """
    Maps calculation IDs to their respective output lists.
    """
    output_map = {}
    for calc in oq_calculations:
        calc_id = calc['id']
        calc_output_list = \
            irmt_plugin.drive_oq_engine_server_dlg.get_output_list(calc_id)
        if isinstance(calc_output_list, Exception):
            raise calc_output_list
        output_map[calc_id] = calc_output_list
    return output_map


@pytest.fixture(scope="session")
def oq_engine_data(oq_calculations, oq_outputs):
    """
    A convenience fixture that combines calculations and outputs.
    """
    return {
        'calc_list': oq_calculations,
        'output_list': oq_outputs
    }


@pytest.fixture(autouse=True)
def empty_project(qgis_app):
    """
    Ensures each test starts with a clean QGIS project.
    """
    QgsProject.instance().clear()
    yield
    # Wait for all background extraction tasks to finish before cleaning up
    manager = QgsApplication.taskManager()

    timeout = 10  # seconds
    start_time = time.time()
    while manager.countActiveTasks() > 0:
        qgis_app.processEvents()
        if time.time() - start_time > timeout:
            print("Timeout reached: Killing remaining background tasks.")
            manager.cancelAll()
            break
        time.sleep(0.05)

    QgsProject.instance().clear()
