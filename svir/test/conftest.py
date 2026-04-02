import pytest
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QMenu


@pytest.fixture(scope="session", autouse=True)
def configure_qgis_env(qgis_iface):
    QSettings().setValue("locale/userLocale", "en_US")
    qgis_iface.firstRightStandardMenu.return_value = QMenu()
