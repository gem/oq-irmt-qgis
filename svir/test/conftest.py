import pytest
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QMenu


@pytest.fixture(scope="session", autouse=True)
def configure_qgis_env(qgis_iface):
    QSettings().setValue("locale/userLocale", "en_US")
    menu = QMenu()
    qgis_iface.firstRightStandardMenu.return_value = menu
    # Keep a reference so it doesn't get garbage collected
    qgis_iface._menu_ref = menu
