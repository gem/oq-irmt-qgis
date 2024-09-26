import subprocess
import os
import pip
from qgis.core import QgsMessageLog, Qgis

def install_packages():
    for package_name in ['pytest', 'matplotlib', 'scipy', 'pyqt5', 'pytest-qgis']:
        subprocess.run(['pip', 'install', package_name], check=True)
    # subprocess.run(['pip', 'uninstall', '-y', 'pdbpp'], check=True)
    # for package_name in ['pytest', 'matplotlib', 'scipy', 'pyqt5']:
    #     subprocess.run(['pip', 'install', '-y', package_name], check=True)
    #     # pip.main('install', '-y', package_name], check=True)
    # try:
    #     pytest_args = ['pytest', '-v', os.path.join('svir', 'test', 'unit')]
    #     subprocess.run(pytest_args, check=True)
    # except subprocess.CalledProcessError as e:
    #     print(f"Pytest failed with return code {e.returncode}.")
    #     print(e.output.decode())
    # else:
    #     print("Pytest completed successfully.")
    #pip.main(['pytest', 'pyqt5', 'matplotlib', 'scipy'])

def run_pytest():
    # pytest_args = ['pytest', '-v', os.path.join('svir', 'test', 'unit')]
    pytest_args = ['pytest', '-v', os.path.join('C:', 'Users', 'paolo.tormene', 'GIT', 'oq-irmt-qgis', 'svir', 'test', 'unit')]
    sp = subprocess.run(pytest_args, check=False, shell=True, capture_output=True, text=True)
    sp2 = subprocess.run(['echo', '%cd%'], check=False, shell=True, capture_output=True, text=True)
    QgsMessageLog.logMessage("Unit tests completed: %s" % sp, level=Qgis.Info)
    QgsMessageLog.logMessage("Unit tests completed: %s" % sp2, level=Qgis.Info)

if __name__ == "__main__":
    install_packages()
    run_pytest()
    # pip.main(['install', 'pytest']) #, 'pyqt5', 'matplotlib', 'scipy'])
