INSTALLATION
==================================

In order to installs this plugin from the git repository one needs to
perform the following steps:


1. install QGIS 2.0+ by following the instructions in the QGIS page
   (NB: in Ubuntu do not use ubuntugis unstable, use the debian packages)

2. install the requests Python library

   # apt-get install python-request

3. clone the qt-experiments repository:
   git clone https://github.com/gem/qt-experiments

4. put the repository in the PYTHONPATH

5. make a symlink to the exposure_tool directory

   $ cd $HOME/.qgis2/python/plugins
   $ ln -s $HOME/qt-experiments/exposure_tool

6. open QGIS and enable the plugin from the plugins menu

Usage
==============================

From the "Download Exposure" submenu open the application to select
the platform settings (host, username and password).  Having done that, you
can zoom on the map, click the "Draw" button, select the region of
interest and then click the "Download" button.  The "Clear" button is
used to cancel the selection. If you select a region which is too
large, a window with an error message will pop up.

