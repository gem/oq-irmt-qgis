# QGIS plugin to drive the OpenQuake Engine, to develop Social Vulnerability and Integrated Risk composite indices, and to predict building recovery times following an earthquake

This QGIS plugin allows users to drive [OpenQuake Engine](https://github.com/gem/oq-engine/)
calculations of physical hazard and risk, and to load the corresponding outputs
as QGIS layers. Those outputs are automatically styled and can be further explored
through interactive data visualization tools that are provided by the plugin.

The toolkit also enables users to develop composite indicators to
measure and quantify social characteristics, and to combine them with estimates of
human or infrastructure loss. The users can directly interact with the
[OpenQuake Platform](https://platform.openquake.org/), in order to
browse and download socioeconomic data or existing projects, to edit
projects locally in QGIS, then to upload and share them through the Platform.

A post-earthquake recovery modeling framework is incorporated into the toolkit,
to produce building level and/or community level recovery functions, that
predict recovery times following an earthquake.

This plugin has been created by the [GEM Foundation](http://www.globalquakemodel.org/gem/).


## Installation and troubleshooting

This plugin runs with [QGIS 2.14LTR](http://qgis.org/en/site/forusers/alldownloads.html)
and above.

On Microsoft Windows and Mac OS X, QGIS includes all the software dependencies needed by the plugin.
On Microsoft Windows, we recommend to use the 32 bit version of QGIS, because some library issues are
still open in the 64 bit version.

On Linux, please make sure that [Scipy](https://www.scipy.org/install.html) and
[Matplotlib](https://matplotlib.org/users/installing.html) with Qt4 backend are installed.

On Ubuntu (Debian and similar):

```bash
$ sudo apt install python-scipy python-matplotlib
```

On Fedora and similar:

```bash
$ sudo dnf install python2-scipy python2-matplotlib python2-matplotlib-qt4
```

On Fedora, please follow these [instructions](https://copr.fedorainfracloud.org/coprs/dani/QGIS-latest-stable/).

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

Please note that QGIS 2.18.8 contained some
[critical bugs](http://www.mail-archive.com/qgis-user@lists.osgeo.org/msg37309.html)
that were fixed in version 2.18.9.


## User manual

The user manual for each of the released versions of this plugin is available
[here](http://docs.openquake.org/oq-irmt-qgis/).
