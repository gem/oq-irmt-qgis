import pytest
from qgis.PyQt.QtCore import QSettings

@pytest.fixture(scope="session", autouse=True)
def set_qgis_locale():
    QSettings().setValue("locale/userLocale", "en_US")
