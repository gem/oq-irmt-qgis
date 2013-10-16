if [ -d /Applications/QGIS.app/ ]; then
    QGIS_APP=/Applications/QGIS.app

#   nightly build
#    QGIS_APP=/Applications/QGIS_2.1-dev.app

#    echo "Mac OS X detected"
    export LD_LIBRARY_PATH=$QGIS_APP/Contents/MacOS/lib/
    export QGIS_PREFIX_PATH=$QGIS_APP/Contents/MacOS/
    export PYTHONPATH=${PYTHONPATH}:/Library/Frameworks/GDAL.framework/Versions/1.9/Python/2.7/site-packages/
    export PYTHONPATH=$PYTHONPATH:$QGIS_APP/Contents/Resources/python/
else
#    echo "GNU/Linux detected"
    export QGIS_PREFIX_PATH=/usr/
    export PYTHONPATH=${QGIS_PREFIX_PATH}/share/qgis/python:${PYTHONPATH}
fi

export PYTHONPATH=$PYTHONPATH:~/.qgis2/python/plugins/

python `dirname $0`/main.py $1
