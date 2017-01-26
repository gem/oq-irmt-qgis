#!/bin/bash

#display each command before executing it
if [ -n $GEM_SET_DEBUG ]; then
    set -x
fi

SOURCE="${BASH_SOURCE[0]}"
REPODIR="$( cd -P "$( dirname "$SOURCE" )/.." && pwd )"

if [ -z $UBUNTU_VERSION ]; then
    UBUNTU_VERSION="xenial"
fi
if [ -z $QGIS_VERSION ]; then
    QGIS_VERSION="debian-ltr"
fi
if [ -z $IRMT_BRANCH ]; then
    IRMT_BRANCH="master"
fi

export DISPLAY=:1

echo "deb http://qgis.org/$QGIS_VERSION $UBUNTU_VERSION main" | sudo tee /etc/apt/sources.list.d/qgis.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key 073D307A618E5811
sudo apt update
sudo apt install -y qgis python-mock python-nose python-scipy

source $REPODIR/scripts/run-env-linux.sh /usr

cd $REPODIR/svir
make test
