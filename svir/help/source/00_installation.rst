************
Installation
************

This plugin runs with `QGIS 2.14LTR <http://qgis.org/it/site/forusers/alldownloads.html>`_
and above.

On Microsoft Windows and Mac OS X, QGIS includes all the software dependencies needed by the plugin.

On Linux, please make sure that `Scipy <https://www.scipy.org/install.html>`_ is installed.

The plugin can be installed using the QGIS Plugins Manager, that is accessible
through the QGIS menu as :guilabel:`Plugins -> Manage and install plugins`.
Please note that the :guilabel:`Settings` of the Plugins Manager contain a
checkbox to :guilabel:`Show also experimental plugins`. If that option is
checked, the latest version of the plugin that is marked as *experimental* will
be available for installation. Otherwise, the latest *stable* version will be
installable. Experimental versions contain new functionalities that may have
not been properly tested yet, and that could cause the plugin or QGIS to break
or to behave unexpectedly.


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
