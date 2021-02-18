#!/usr/bin/env bash

set -e

docker rm -f qgis || true
docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/tests_directory \
 -e DISPLAY=:99 \
 -e GEM_QGIS_TEST=y \
 qgis/qgis:final-3_8_3
 # qgis/qgis:release-3_10

docker exec -it qgis bash -c "apt update --allow-releaseinfo-change; DEBIAN_FRONTEND=noninteractive apt install -y python3-scipy python3-matplotlib python3-pyqt5.qtwebkit"
docker exec -it qgis bash -c "python3 -m pip install pytest"

# OGR_SQLITE_JOURNAL=delete prevents QGIS from using WAL, which modifies geopackages even if they are just read
docker exec -it qgis bash -c "export PYTHONPATH=/usr/share/qgis/python/plugins/:$PYTHONPATH; OGR_SQLITE_JOURNAL=delete pytest -v /tests_directory/svir/test/unit/"
