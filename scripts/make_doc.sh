#!/usr/bin/env bash

set -e

docker run --rm -d -t --name qgis-ltr-make-doc -v /tmp/.X11-unix:/tmp/.X11-unix -v ${PWD}/../.:/oq-irmt-qgis qgis/qgis:ltr bash -c "apt update --allow-releaseinfo-change; \
    DEBIAN_FRONTEND=noninteractive apt install -y latexmk texlive-latex-extra python3-matplotlib python3-sphinx python3-sphinx-rtd-theme dvipng; \
    export DISPLAY=:1.0; \
    export PYTHONPATH=$PYTHONPATH:/oq-irmt-qgis; \
    cd /oq-irmt-qgis/svir/help; \
    make latexpdf; \
    make html"
docker logs --follow qgis-ltr-make-doc
