#!/bin/bash

if [ -z $1 ]; then
    echo "ERROR: missing argument" >&2
    exit 1
fi

sudo apt update
sudo apt upgrade -y

# Load OSGEO_QGIS_* credentials from a local file
# this information are exposed to scripts used by Makefile
if [ -f .osgeo_credentials ]; then . .osgeo_credentials; fi

# Start Xvfb on :99
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -ac -screen 0 1280x1024x16 2>&1 >/dev/null &
cd svir && source ../scripts/run-env-linux.sh /usr
make $*
