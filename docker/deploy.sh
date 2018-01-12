#!/bin/bash

# Start Xvfb on :99
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -ac -screen 0 1280x1024x16 2>&1 >/dev/null &
cd svir && source ../scripts/run-env-linux.sh /usr
make deploy
