# QGIS plugin to drive the OpenQuake Engine

This QGIS plugin allows users to drive [OpenQuake Engine](https://github.com/gem/oq-engine/)
calculations of physical hazard and risk, and to load the corresponding outputs
as QGIS layers. Those outputs are automatically styled and can be further explored
through interactive data visualization tools that are provided by the plugin.

This plugin has been created by the [GEM Foundation](http://www.globalquakemodel.org/gem/).


## Installation and troubleshooting

This plugin runs with [QGIS 3.0](http://qgis.org/en/site/forusers/alldownloads.html)
and above.

On Microsoft Windows, QGIS includes all the software dependencies needed by the plugin.

On macOS and Linux, please make sure that [Scipy](https://www.scipy.org/install.html) and
[Matplotlib](https://matplotlib.org/users/installing.html) with Qt5 backend are installed.
On macOS, please also make sure
that [Pillow](https://pillow.readthedocs.io/en/stable/installation.html)
is installed.


On macOS:

```bash
$ python3 -m pip install --upgrade pip
$ python3 -m pip install --upgrade matplotlib scipy Pillow
```

On Ubuntu (Debian and similar):

```bash
$ sudo apt install python3-scipy python3-matplotlib python3-pyqt5.qtwebkit
```

On Fedora and similar:

```bash
$ sudo dnf install python3-scipy python3-matplotlib python3-matplotlib-qt5
```

On macOS make sure to run the script located under
`/Applications/Python 3.6/Install Certificates.command`,
after Python has been installed, to update the SSL certificates bundle.

On Fedora, please follow these [instructions](https://copr.fedorainfracloud.org/coprs/dani/qgis/).

The plugin can be installed using the QGIS Plugins Manager, that is accessible through the
QGIS menu as **Plugins -> Manage and install plugins**. Please note that the **Settings** of
the Plugins Manager contain a checkbox to **Show also experimental plugins**. If that option
is checked, the latest version of the plugin that is marked as **experimental**
will be available for installation. Otherwise, the latest **stable** version
will be installable. Experimental versions contain new functionalities that may
have not been properly tested yet, and that could cause the plugin or QGIS to
break or to behave unexpectedly.

Some users reported issues about `upgrading` the plugin to its latest version.
We recommend to `reinstall` the plugin instead, in order to make sure the new installation is
done in a clean folder.

## User manual

The user manual for each of the released versions of this plugin is available
[here](http://docs.openquake.org/oq-irmt-qgis/).
