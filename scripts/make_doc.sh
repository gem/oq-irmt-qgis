#!/usr/bin/env bash

set -e

docker rm -f qgis || true
docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/oq-irmt-qgis \
 -e DISPLAY=:99 \
 qgis/qgis:latest

docker exec -it qgis sh -c "apt update; apt install -y latexmk texlive-latex-extra python3-matplotlib python3-sphinx python3-sphinx-rtd-theme dvipng"
docker exec -it qgis sh -c "export PYTHONPATH=$PYTHONPATH:/oq-irmt-qgis; cd /oq-irmt-qgis/svir; make doc"
