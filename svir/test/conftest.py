import pytest
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QMenu


def _patch_first_right_standard_menu(qgis_iface):
    menu = QMenu()
    qgis_iface.firstRightStandardMenu.return_value = menu
    qgis_iface._menu_ref = menu


@pytest.fixture(scope="session", autouse=True)
def configure_qgis_env(qgis_iface):
    QSettings().setValue("locale/userLocale", "en_US")
    _patch_first_right_standard_menu(qgis_iface)

    # Wrap newProject so the patch is re-applied after _mock_methods is cleared
    original_new_project = qgis_iface.newProject

    def patched_new_project(*args, **kwargs):
        result = original_new_project(*args, **kwargs)
        _patch_first_right_standard_menu(qgis_iface)
        return result

    qgis_iface.newProject = patched_new_project
