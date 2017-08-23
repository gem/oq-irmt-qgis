#!/bin/bash
set -e

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONPATH=$REPODIR/oq-irmt-qgis:$PYTHONPATH

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

if [ "$(git ls-remote --heads https://github.com/gem/oq-engine.git ${IRMT_BRANCH})" == "" ]; then
  BRANCH='master';
fi;
echo "deb http://qgis.org/$QGIS_VERSION $UBUNTU_VERSION main" | sudo tee /etc/apt/sources.list.d/qgis.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key CAEB3DC3BDF7FB45
sudo add-apt-repository -y ppa:openquake/saga
sudo apt-get update -q
sudo apt install -y qgis python-mock python-nose python-nose-exclude python-scipy saga python-saga curl
sudo pip install sphinx==1.4.9 sphinx_rtd_theme

# curl -sfO http://artifacts.openquake.org/travis/oqdata-master.zip || ( echo "Dump for master unavailable"; exit 1 )
# git clone -q -b master --depth=1 https://github.com/gem/oq-engine.git && echo "Running against oq-engine/master"

# virtualenv oqe27
# oqe27/bin/pip -q install -U pip
# oqe27/bin/pip -q install -r oq-engine/requirements-py27-linux64.txt
# oqe27/bin/pip -q install -e oq-engine

# oqe27/bin/oq restore oqdata-master.zip ~/oqdata
# oqe27/bin/oq webui start --skip-browser &> webui.log &

source $REPODIR/scripts/run-env-linux.sh /usr

cd $REPODIR/svir
# make test
echo $REPODIR
make build_apidoc
# make build_manual_html
