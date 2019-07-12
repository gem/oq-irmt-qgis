#!/usr/bin/env bash

set -e

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
 -e OQ_ENGINE_HOST='http://172.17.0.1:8800' \
 -e BRANCH="$BRANCH" \
 -e SELECTED_CALC_ID="$SELECTED_CALC_ID" \
 qgis/qgis:latest

docker exec -it qgis sh -c "apt update; DEBIAN_FRONTEND=noninteractive apt install -y python3-scipy python3-matplotlib python3-pyqt5.qtwebkit"

docker exec -it qgis sh -c "git clone -q -b $BRANCH --depth=1 https://github.com/gem/oq-engine.git && echo 'Running against oq-engine/$BRANCH'"

docker exec -it qgis sh -c "qgis_setup.sh svir"

docker exec -it qgis sh -c "cd /tests_directory && SELECTED_CALC_ID=$SELECTED_CALC_ID qgis_testrunner.sh svir.test.integration.test_drive_oq_engine"
