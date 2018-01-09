.. _chap-installation:

********************************
Installation and troubleshooting
********************************

This plugin runs with `QGIS 2.14LTR <http://qgis.org/it/site/forusers/alldownloads.html>`_
and above.

On Microsoft Windows and Mac OS X, QGIS includes all the software dependencies needed by the plugin.
On Microsoft Windows, we recommend to use the 32 bit version of QGIS, because some library issues are
still open in the 64 bit version.

On Linux, please make sure that `Scipy <https://www.scipy.org/install.html>`_
and `Matplotlib <https://matplotlib.org/users/installing.html>`_ with Qt4 backend
are installed.

On Ubuntu (Debian and similar):

.. code-block:: bash

    $ sudo apt install python-scipy python-matplotlib

On Fedora and similar:

.. code-block:: bash

    $ sudo dnf install python2-scipy python2-matplotlib python2-matplotlib-qt4

For geospatial analysis, the plugin leverages SAGA `Clip points with polygons` algorithm.
In case SAGA is not installed or its version is too outdated, the plugin is able to perform
the same analysis using a fallback (slower) algorithm. For best performance, we recommend to
install SAGA or to update it at least to version 2.3. On Ubuntu, this can be done as follows:

.. code-block:: bash

    $ sudo add-apt-repository ppa:openquake/saga
    $ sudo apt-get update
    $ sudo apt-get install saga python-saga

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
``python-scipy``, ``python-nose``, ``python-coverage``, ``python-mock``

If the environment is not already set, run the script ``run-env-linux.sh``,
providing the required argument (in most cases, specifying the directory `/usr`)

.. code-block:: bash

    $ source scripts/run-env-linux.sh /usr

Then, move to the ``svir`` directory and run

.. code-block:: bash

    $ make test
