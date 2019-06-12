#!/usr/bin/env bash

set -e

docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/tests_directory \
 -e DISPLAY=:99 \
 -e OQ_ENGINE_HOST='http://172.17.0.1:8800' \
 qgis/qgis:latest

docker exec -it qgis sh -c "apt update; apt install -y python3-scipy python3-matplotlib python3-pyqt5.qtwebkit"

docker exec -it qgis sh -c "qgis_setup.sh svir"

docker exec -it qgis sh -c "cd /tests_directory && qgis_testrunner.sh svir.test.integration.test_drive_oq_engine"
