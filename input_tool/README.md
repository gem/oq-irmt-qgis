INSTALLATION
==================================

In order to installs the Input Tool GUI one needs to perform the following
steps:

1. clone the oq-common repository
   git clone https://github.com/gem/oq-common
2. clone the oq-nrmllib repository
   git clone https://github.com/gem/oq-nrmllib
2. clone the qt-experiments repository
   git clone https://github.com/gem/qt-experiments
3. put the three repositories in the PYTHONPATH
4. run the application as follow:

   $ cd ~/qt-experiments
   $ python input_tool/tripletable.py input_tool/examples/vm.xml
