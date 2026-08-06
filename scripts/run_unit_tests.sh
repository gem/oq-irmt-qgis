#!/usr/bin/env bash

set -e

docker rm -f qgis || true
docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/tests_directory \
 -e DISPLAY=:99 \
 -e GEM_QGIS_TEST=y \
 qgis/qgis:ltr

docker exec -it qgis bash -c "apt update --allow-releaseinfo-change; DEBIAN_FRONTEND=noninteractive apt install -y python3-matplotlib python3-pyqt6 python3-pytest"

# OGR_SQLITE_JOURNAL=delete prevents QGIS from using WAL, which modifies geopackages even if they are just read
docker exec -it qgis bash -c "export PYTHONPATH=/usr/share/qgis/python/:/usr/share/qgis/python/plugins/:$PYTHONPATH; OGR_SQLITE_JOURNAL=delete python3 -m pytest -v /tests_directory/svir/test/unit/"

