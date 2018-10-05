.. _chap-installation:

********************************
Installation and troubleshooting
********************************

This plugin runs with `QGIS 3.0 <http://qgis.org/it/site/forusers/alldownloads.html>`_
and above.

On Microsoft Windows, QGIS includes all the software dependencies needed by the plugin.

On macOS and Linux, please make sure that `Scipy <https://www.scipy.org/install.html>`_
and `Matplotlib <https://matplotlib.org/users/installing.html>`_ with Qt5 backend
are installed.

On macOS:

.. code-block:: bash

    $ sudo pip3.6 install matplotlib scipy

.. warning::
    matplotlib v3.0.0 on macOS and on Microsoft Windows has a known bug importing pyplot.
    In order to fix that issue, an earlier version of matplotlib can be installed:
    $ sudo pip3.6 install matplotlib==2.2.3

On Ubuntu (Debian and similar):

.. code-block:: bash

    $ sudo apt install python3-scipy python3-matplotlib python3-pyqt5.qtwebkit

On Fedora and similar:

.. code-block:: bash

    $ sudo dnf install python3-scipy python3-matplotlib python3-matplotlib-qt5

On Fedora, please follow these `instructions <https://copr.fedorainfracloud.org/coprs/dani/qgis/>`_.

The plugin can be installed using the QGIS Plugins Manager, that is accessible
through the QGIS menu as :guilabel:`Plugins -> Manage and install plugins`.
Please note that the :guilabel:`Settings` of the Plugins Manager contain a
checkbox to :guilabel:`Show also experimental plugins`. If that option is
checked, the latest version of the plugin that is marked as *experimental* will
be available for installation. Otherwise, the latest *stable* version will be
installable. Experimental versions contain new functionalities that may have
not been properly tested yet, and that could cause the plugin or QGIS to break
or to behave unexpectedly.

Some users reported issues about `upgrading` the plugin to its latest version.
We recommend to `reinstall` the plugin instead, in order to make sure the new installation is
done in a clean folder.


How to run tests on Ubuntu 18.04 LTS
====================================

In order to run tests on Ubuntu 18.04 LTS and above, QGIS has to be installed
as described above and the following additional packages are required:
``python3-scipy``, ``python3-nose``, ``python3-coverage``, ``python3-mock``

If the environment is not already set, run the script ``run-env-linux.sh``,
providing the required argument (in most cases, specifying the directory `/usr`)

.. code-block:: bash

    $ source scripts/run-env-linux.sh /usr

Then, move to the ``svir`` directory and run

.. code-block:: bash

    $ make test
