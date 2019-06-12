#!/usr/bin/env bash

set -e

docker rm -f qgis || true
docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/tests_directory \
 -e DISPLAY=:99 \
 qgis/qgis:latest

docker exec -it qgis sh -c "apt install -y python3-scipy python3-matplotlib python3-pyqt5.qtwebkit python3-nose"

docker exec -it qgis sh -c "export PYTHONPATH=/usr/share/qgis/python/plugins/:$PYTHONPATH; nosetests3 -v /tests_directory/svir/test/unit/"
