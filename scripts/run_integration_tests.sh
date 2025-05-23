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
 qgis/qgis:release-3_16

docker exec -it qgis sh -c "apt update --allow-releaseinfo-change; DEBIAN_FRONTEND=noninteractive apt install -y python3-matplotlib python3-pyqt5.qtwebkit"

docker exec -it qgis sh -c "git clone -q -b $BRANCH --depth=1 https://github.com/gem/oq-engine.git && echo 'Running against oq-engine/$BRANCH'"

docker exec -it qgis sh -c "qgis_setup.sh svir"

docker exec -it qgis sh -c "cd /tests_directory && qgis_testrunner.sh svir.test.integration.test_drive_oq_engine"
