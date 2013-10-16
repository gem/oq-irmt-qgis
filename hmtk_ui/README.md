Hazard Modeller's Toolkit GUI
====

**Dependencies**

*oq-hazardlib and oq-nrmllib*

You can get them on github or via apt:

  $ sudo apt-get install python-software-properties
  $ sudo add-apt-repository ppa:openquake/ppa
  $ sudo apt-get update
  $ sudo apt-get install python-oq-hazardlib python-oq-nrmllib

*Hazard Modeller Toolkit*

Get it from github:

  $ git clone https://github.com/GEMScienceTools/hmtk.git

Then, add it to the PYTHONPATH  (e.g. export PYTHONPATH=$PYTHONPATH:~/hmtk)

*QGIS 2.0*
Get and install QGIS 2.0 (see www.qgis.org).

In QGIS 2.0 install OpenLayers Plugin (menu plugins -> others -> openlayers plugin -> install)

**Installation**

Clone the repository:

  $ git clone https://github.com/gem/qt-experiments.git
  $ cd qt-experiments

Get the right branch (until the qgis2 branch is not merged into master):
  $ git checkout qgis2  

Then, issue:
  $ ./hmtk_ui/start.sh


