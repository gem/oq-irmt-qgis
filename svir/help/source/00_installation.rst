.. _chap-installation:

********************************
Installation and troubleshooting
********************************

This plugin runs with `QGIS 2.14LTR <http://qgis.org/it/site/forusers/alldownloads.html>`_
and above.

On Microsoft Windows and Mac OS X, QGIS includes all the software dependencies needed by the plugin.
On Microsoft Windows, we recommend to use the 32 bit version of QGIS, because some library issues are
still open in the 64 bit version.

On Linux, please make sure that `Matplotlib <https://matplotlib.org/users/installing.html>`_ with Qt5 backend
are installed.

On Ubuntu (Debian and similar):

.. code-block:: bash

    $ sudo apt install python-matplotlib

On Fedora and similar:

.. code-block:: bash

    $ sudo dnf install python3-matplotlib python3-matplotlib-qt5

On Fedora, please follow these `instructions <https://copr.fedorainfracloud.org/coprs/dani/QGIS-latest-stable/>`_.

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

Please note that QGIS 2.18.8 contained some
`critical bugs <http://www.mail-archive.com/qgis-user@lists.osgeo.org/msg37309.html>`_
that were fixed in version 2.18.9.


How to run tests on Ubuntu 16.04 LTS
====================================

In order to run tests on Ubuntu 16.04 LTS and above, QGIS has to be installed
as described above and the following additional packages are required:
``python-nose``, ``python-coverage``, ``python-mock``

If the environment is not already set, run the script ``run-env-linux.sh``,
providing the required argument (in most cases, specifying the directory `/usr`)

.. code-block:: bash

    $ source scripts/run-env-linux.sh /usr

Then, move to the ``svir`` directory and run

.. code-block:: bash

    $ make test
