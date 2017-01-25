#!/bin/bash

#display each command before executing it
set -x

UBUNTU_VERSION="xenial"
QGIS_VERSION="debian-ltr"
IRMT_BRANCH='recovery-play'

export DISPLAY=:1
echo "deb http://qgis.org/$QGIS_VERSION $UBUNTU_VERSION main" | sudo tee /etc/apt/sources.list.d/qgis.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key 073D307A618E5811
sudo apt update
sudo apt install -y qgis python-mock python-nose python-coverage python-scipy
git clone --depth=1 -b $IRMT_BRANCH https://github.com/gem/oq-irmt-qgis.git
cd oq-irmt-qgis/svir
source ../scripts/run-env-linux.sh /usr
make test
