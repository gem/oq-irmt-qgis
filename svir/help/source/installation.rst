.. _chap-installation:

********************************
Installation and troubleshooting
********************************

This plugin runs with `QGIS 3.0 <http://qgis.org/it/site/forusers/alldownloads.html>`_
and above.

On Microsoft Windows, QGIS includes all the software dependencies needed by the plugin.

On macOS and Linux, please make sure that
`Matplotlib <https://matplotlib.org/users/installing.html>`_ with Qt5 backend
is installed.

On macOS:

.. code-block:: bash

    $ python3 -m pip install --upgrade pip
    $ python3 -m pip install --upgrade matplotlib

On Ubuntu (Debian and similar):

.. code-block:: bash

    $ sudo apt install python3-matplotlib python3-pyqt5.qtwebkit

On Fedora and similar:

.. code-block:: bash

    $ sudo dnf install python3-matplotlib python3-matplotlib-qt5

On macOS make sure to run the script located under
`/Applications/Python X.Y/Install Certificates.command`,
after Python has been installed, to update the SSL certificates bundle.

On Fedora, please follow these `instructions <https://copr.fedorainfracloud.org/coprs/dani/qgis/>`_.

The plugin can be installed using the QGIS Plugins Manager, that is accessible
through the QGIS menu as :guilabel:`Plugins -> Manage and install plugins`.
Please note that the :guilabel:`Settings` of the Plugins Manager contain a
checkbox to :guilabel:`Show also experimental plugins`. If that option is
checked, the latest version of the plugin that is marked as *experimental* will
be available for installation. Otherwise, the latest *stable* version will be
installable.

.. note::
    The latest *stable* version of the plugin is compatible with the Long Term Support version
    of the OpenQuake engine, whereas the latest *experimental* version of the plugin is aligned
    with the latest version of the OpenQuake engine.

    Experimental versions contain new functionalities that may have
    not been properly tested yet, and that could cause the plugin or QGIS to break
    or to behave unexpectedly.

Some users reported issues about `upgrading` the plugin to its latest version.
We recommend to `reinstall` the plugin instead, in order to make sure the new installation is
done in a clean folder.


How to run tests and build the documentation
============================================

Tests run on a QGIS docker container based on Ubuntu Xenial (16.04LTS), launching one of the following commands from the `svir` directory:

.. code-block:: bash

   $ ../scripts/run_unit_tests.sh
   $ ../scripts/run_integration_tests.sh

The user manual, both in the html and pdf versions can be built by the same QGIS docker container running the following command from the `svir` directory:

.. code-block:: bash

   $ ../scripts/make_doc.sh
