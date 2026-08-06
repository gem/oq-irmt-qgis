#!/usr/bin/env bash

set -e

DOCKER_HOST=$(/sbin/ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')

if [ "$TRAVIS_PULL_REQUEST_BRANCH" != "" ]; then
    BRANCH=$TRAVIS_PULL_REQUEST_BRANCH
elif [ "$TRAVIS_BRANCH" != "" ]; then
    BRANCH=$TRAVIS_BRANCH
else
    BRANCH='master'
fi
if [ "$(git ls-remote --heads https://github.com/gem/oq-engine.git ${BRANCH})" == "" ]; then
    BRANCH='master'
fi
export BRANCH

docker rm -f qgis || true
docker run -d --name qgis -v /tmp/.X11-unix:/tmp/.X11-unix \
 -v `pwd`/../.:/tests_directory \
 -e DISPLAY=:99 \
 -e OQ_ENGINE_HOST="http://${DOCKER_HOST}:8800" \
 -e BRANCH="$BRANCH" \
 -e ONLY_CALC_ID="$ONLY_CALC_ID" \
 -e ONLY_OUTPUT_TYPE="$ONLY_OUTPUT_TYPE" \
 -e GEM_QGIS_TEST=y \
 qgis/qgis:ltr

docker exec -it qgis sh -c "apt update --allow-releaseinfo-change; DEBIAN_FRONTEND=noninteractive apt install -y python3-matplotlib python3-pyqt6 python3-pytest"

docker exec -it qgis sh -c "git clone -q -b $BRANCH --depth=1 https://github.com/gem/oq-engine.git && echo 'Running against oq-engine/$BRANCH'"

docker exec -it qgis sh -c "export PYTHONPATH=/usr/share/qgis/python/:/usr/share/qgis/python/plugins/:$PYTHONPATH; python3 -m pytest -v -s -ra /tests_directory/svir/test/integration/"

