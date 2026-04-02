import pytest
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QMenu


def _patch_iface(qgis_iface):
    menu = QMenu()
    qgis_iface.firstRightStandardMenu.return_value = menu
    qgis_iface._menu_ref = menu


@pytest.fixture(scope="session", autouse=True)
def configure_qgis_env(qgis_iface):
    QSettings().setValue("locale/userLocale", "en_US")
    _patch_iface(qgis_iface)


@pytest.fixture(autouse=True)
def reset_iface_between_classes(qgis_iface):
    _patch_iface(qgis_iface)
